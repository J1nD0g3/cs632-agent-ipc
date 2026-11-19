"""Cross-check the fact judge: Qwen3-8B vs a judge from another family vs lexical matching.

python -m agentipc.judge_cross results/<exp>/<run_id> --qwen URL... --other URL... --other-name NAME [--n 300]
Uses the same batched prompt as judge_all (all facts of one question against one stage text). Units are
sampled evenly across channels from the Researcher's output and what the Writer received, and only
texts short enough for both judges' context are used, so Qwen sees exactly what it saw in judge_all.
"""
from __future__ import annotations

import argparse
import asyncio
import gzip
import json
import random
from pathlib import Path

import yaml

from .data import LOADERS, make_tasks
from .judge import kappa
from .judge_all import PROMPT, parse
from .llm import ChatClient
from .metrics import fact_present
from .run import datasets

ROOT = Path(__file__).resolve().parents[2]


def sample_units(run_dir: Path, n: int, max_chars: int, seed: int) -> list[tuple]:
    """(channel, stage, question, text) units, evenly across channels; deterministic for a seed."""
    cfg = yaml.safe_load((run_dir / "config.yaml").read_text())
    raw = ROOT / "results_raw" / cfg["exp"] / run_dir.name
    by_task = {}
    for name, path in datasets(cfg).items():
        qs = LOADERS[name](ROOT / path)
        for s in cfg["seeds"]:
            for k in cfg["k"]:
                for t in make_tasks(qs, cfg["n_tasks"], k, s):
                    by_task[t.task_id] = t
    units: dict[str, list] = {}
    for line in gzip.open(raw / "records.jsonl.gz", "rt"):
        rec = json.loads(line)
        if "error" in rec or rec["k"] != 3:
            continue
        for stage in ("notes", "writer_input"):
            text = rec["stage"].get(stage, "")
            if not text.strip() or len(text) > max_chars:
                continue
            for q in by_task[rec["task_id"]].questions:
                units.setdefault(rec["channel"], []).append((rec["channel"], stage, q, text))
    rng = random.Random(seed)
    per = max(1, n // len(units))
    return [u for ch in sorted(units) for u in rng.sample(units[ch], min(per, len(units[ch])))]


async def run(run_dir: Path, n: int, qwen: list[str], other: list[str], other_name: str, max_chars: int, seed: int) -> dict:
    sample = sample_units(run_dir, n, max_chars, seed)
    cfg = yaml.safe_load((run_dir / "config.yaml").read_text())
    raw = ROOT / "results_raw" / cfg["exp"] / run_dir.name

    async def judge_all_units(urls: list[str], name: str) -> list[list[bool | None]]:
        clients = [ChatClient(u, name, max_tokens=64) for u in urls]
        sem = asyncio.Semaphore(12 * len(clients))

        async def one(i, u):
            _, _, q, text = u
            async with sem:
                r = await clients[i % len(clients)].chat([{"role": "user", "content": PROMPT.format(
                    facts="\n".join(f"F{j + 1}: {f.text}" for j, f in enumerate(q.facts)), text=text)}])
            return parse(r.content, len(q.facts))

        out = await asyncio.gather(*(one(i, u) for i, u in enumerate(sample)))
        for c in clients:
            await c.aclose()
        return out

    a, b = await asyncio.gather(judge_all_units(qwen, "qwen3-8b"), judge_all_units(other, other_name))
    rows, qv, ov, lv = [], [], [], []
    for (ch, stage, q, text), qa, ob in zip(sample, a, b):
        for j, f in enumerate(q.facts):
            if qa[j] is None or ob[j] is None:
                continue
            lex = fact_present(f, q, text)
            qv.append(qa[j]); ov.append(ob[j]); lv.append(lex)
            rows.append({"channel": ch, "stage": stage, "fact": f.text, "qwen": qa[j], "other": ob[j], "lexical": lex})
    with gzip.open(raw / "judge_cross.jsonl.gz", "wt") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    agree = lambda x, y: sum(p == q for p, q in zip(x, y)) / len(x)
    by_ch = {}
    for ch in sorted({r["channel"] for r in rows}):
        rs = [r for r in rows if r["channel"] == ch]
        by_ch[ch] = {"n": len(rs), "qwen_yes": sum(r["qwen"] for r in rs) / len(rs),
                     "other_yes": sum(r["other"] for r in rs) / len(rs),
                     "agree": sum(r["qwen"] == r["other"] for r in rs) / len(rs)}
    return {"units": len(sample), "facts": len(rows), "other_judge": other_name, "max_chars": max_chars,
            "qwen_vs_other": {"agree": agree(qv, ov), "kappa": kappa(qv, ov)},
            "qwen_vs_lexical": {"agree": agree(qv, lv), "kappa": kappa(qv, lv)},
            "other_vs_lexical": {"agree": agree(ov, lv), "kappa": kappa(ov, lv)},
            "yes_rate": {"qwen": sum(qv) / len(qv), "other": sum(ov) / len(ov), "lexical": sum(lv) / len(lv)},
            "by_channel": by_ch}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("run_dir")
    ap.add_argument("--qwen", nargs="+", required=True)
    ap.add_argument("--other", nargs="+", required=True)
    ap.add_argument("--other-name", required=True)
    ap.add_argument("--n", type=int, default=360)
    ap.add_argument("--max-chars", type=int, default=16000)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    run_dir = Path(a.run_dir)
    out = asyncio.run(run(run_dir, a.n, a.qwen, a.other, a.other_name, a.max_chars, a.seed))
    (run_dir / "judge_cross.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
