"""Judge-free fact tracing from the datasets' own annotations.

Each question's key items are named entities from its gold reasoning chain: for 2WikiMultihopQA the
subject and object of every evidence triple, for HotpotQA the titles of the supporting paragraphs (with
any parenthetical removed). An item is present in a text when its normalized string occurs there. This
misses facts stated only by pronoun, so it is a lower bound, but it is exact and anyone can recheck it.

python -m agentipc.entities results/<exp>/<run_id>   ->  entities.json next to summary.json
"""
from __future__ import annotations

import gzip
import json
import re
import sys
from pathlib import Path

import numpy as np
import yaml

from .data import LOADERS, Question, make_tasks
from .metrics import normalize
from .run import datasets
from .stats import ci

ROOT = Path(__file__).resolve().parents[2]
STAGES = ("notes", "writer_input", "final")


def key_items(q: Question) -> list[str]:
    if q.evidences:
        items = [x for s, _, o in q.evidences for x in (s, o)]
    else:
        items = [f.title for f in q.facts]
    out = []
    for it in items:
        it = re.sub(r"\s*\([^)]*\)\s*$", "", it).strip()
        n = normalize(it)
        if n and n not in out:
            out.append(n)
    return out


def present(item: str, text_norm: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(item)}(?!\w)", text_norm) is not None


def trace(rec: dict, questions: list[Question]) -> dict:
    texts = {s: normalize(rec["stage"].get(s, "")) for s in STAGES}
    items = [it for q in questions for it in key_items(q)]
    have = {s: [present(it, texts[s]) for it in items] for s in STAGES}
    found = [i for i, v in enumerate(have["notes"]) if v]
    n = len(items) or 1
    return {"ent_recall_notes": sum(have["notes"]) / n,
            "ent_kept_writer_input": (sum(have["writer_input"][i] for i in found) / len(found)) if found else 0.0,
            "ent_recall_final": sum(have["final"]) / n}


def run_dir_table(run_dir: Path) -> dict:
    cfg = yaml.safe_load((run_dir / "config.yaml").read_text())
    by_task = {}
    for name, path in datasets(cfg).items():
        qs = LOADERS[name](ROOT / path)
        for s in cfg["seeds"]:
            for k in cfg["k"]:
                for t in make_tasks(qs, cfg["n_tasks"], k, s):
                    by_task[t.task_id] = t
    rows = []
    raw = ROOT / "results_raw" / cfg["exp"] / run_dir.name
    for line in gzip.open(raw / "records.jsonl.gz", "rt"):
        rec = json.loads(line)
        if "error" in rec:
            continue
        r = {"task_id": rec["task_id"], "channel": rec["channel"], "dataset": rec["dataset"], "k": rec["k"]}
        r.update(trace(rec, by_task[rec["task_id"]].questions))
        rows.append(r)
    out = {}
    for key in sorted({(r["dataset"], r["k"], r["channel"]) for r in rows}):
        rs = [r for r in rows if (r["dataset"], r["k"], r["channel"]) == key]
        g = {"n": len(rs)}
        for m in ("ent_recall_notes", "ent_kept_writer_input", "ent_recall_final"):
            mean, lo, hi = ci([r[m] for r in rs])
            g[m] = {"mean": round(mean, 4), "lo": round(lo, 4), "hi": round(hi, 4)}
        out["|".join(map(str, key))] = g
    pooled = {}
    for ch in sorted({r["channel"] for r in rows}):
        for k in sorted({r["k"] for r in rows}):
            rs = [r for r in rows if r["channel"] == ch and r["k"] == k]
            pooled[f"k{k}|{ch}"] = {m: round(float(np.mean([r[m] for r in rs])), 4)
                                    for m in ("ent_recall_notes", "ent_kept_writer_input", "ent_recall_final")}
    return {"by_cell": out, "pooled": pooled}


def main() -> int:
    run_dir = Path(sys.argv[1])
    res = run_dir_table(run_dir)
    (run_dir / "entities.json").write_text(json.dumps(res, indent=1))
    for key, g in res["pooled"].items():
        print(f"{key:<10} notes={g['ent_recall_notes']:.2f} delivered={g['ent_kept_writer_input']:.2f} final={g['ent_recall_final']:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
