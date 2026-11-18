"""Score fact presence in every run with an LLM judge (one call per question and stage).

python -m agentipc.judge_all results/<exp>/<run_id>
Writes results_raw/.../judged.jsonl.gz and adds judge_* metrics to summary_judge.json.
"""
from __future__ import annotations

import argparse
import asyncio
import gzip
import json
import re
from pathlib import Path

import yaml

from .data import LOADERS, make_tasks
from .llm import ChatClient
from .metrics import correct, parse_answers
from .run import datasets
from .stats import ci

ROOT = Path(__file__).resolve().parents[2]
STAGES = ("notes", "writer_input", "final")

PROMPT = ("Below are numbered FACTS and a TEXT. For each fact, decide whether the TEXT states it, possibly in "
          "other words. A fact counts as stated only if the information it adds (names, dates, places, numbers, "
          "relations) is in the TEXT.\n\nFACTS:\n{facts}\n\nTEXT:\n{text}\n\n"
          "Answer with one line per fact, in order, like `F1: yes` or `F1: no`, and nothing else.")


def parse(reply: str, n: int) -> list[bool | None]:
    out: list[bool | None] = [None] * n
    for m in re.finditer(r"F(\d+)\s*[:.)-]\s*(yes|no)", reply, re.I):
        i = int(m.group(1)) - 1
        if 0 <= i < n and out[i] is None:
            out[i] = m.group(2).lower() == "yes"
    return out


async def judge_run_dir(run_dir: Path, concurrency: int, max_chars: int, urls: list[str] | None = None,
                        judge_name: str = "qwen3-8b") -> Path:
    cfg = yaml.safe_load((run_dir / "config.yaml").read_text())
    raw = ROOT / "results_raw" / cfg["exp"] / run_dir.name
    by_task = {}
    for name, path in datasets(cfg).items():
        qs = LOADERS[name](ROOT / path)
        for s in cfg["seeds"]:
            for k in cfg["k"]:
                for t in make_tasks(qs, cfg["n_tasks"], k, s):
                    by_task[t.task_id] = t
    # The judge is always Qwen3-8B, whichever model produced the runs.
    urls = urls or cfg["server"].get("base_urls") or [cfg["server"]["base_url"]]
    clients = [ChatClient(u, judge_name, max_tokens=64) for u in urls]
    sems = [asyncio.Semaphore(concurrency) for _ in clients]
    recs = [json.loads(l) for l in gzip.open(raw / "records.jsonl.gz", "rt")]
    jobs = []
    for ri, rec in enumerate(recs):
        if "error" in rec:
            continue
        t = by_task[rec["task_id"]]
        for stage in STAGES:
            text = rec["stage"].get(stage, "")
            for qi, q in enumerate(t.questions):
                jobs.append((ri, stage, qi, [f.text for f in q.facts], text))

    async def one(i, job):
        ri, stage, qi, facts, text = job
        if not text.strip():
            return [False] * len(facts), True
        c = clients[i % len(clients)]
        async with sems[i % len(clients)]:
            body = text if len(text) <= max_chars else text[:max_chars]
            r = await c.chat([{"role": "user", "content": PROMPT.format(
                facts="\n".join(f"F{j + 1}: {f}" for j, f in enumerate(facts)), text=body)}])
        got = parse(r.content, len(facts))
        return [bool(x) for x in got], len(text) <= max_chars and None not in got

    res = await asyncio.gather(*(one(i, j) for i, j in enumerate(jobs)))
    for c in clients:
        await c.aclose()
    per = {}
    for (ri, stage, qi, facts, _), (vals, clean) in zip(jobs, res):
        d = per.setdefault(ri, {s: [] for s in STAGES} | {"clean": True, "per_q": {s: {} for s in STAGES}})
        d[stage] += vals
        d["per_q"][stage][qi] = vals
        d["clean"] &= bool(clean)
    out = raw / "judged.jsonl.gz"
    with gzip.open(out, "wt") as f:
        for ri, d in per.items():
            rec = recs[ri]
            notes, got, final = d["notes"], d["writer_input"], d["final"]
            found = [i for i, v in enumerate(notes) if v]
            row = {"task_id": rec["task_id"], "channel": rec["channel"], "dataset": rec["dataset"],
                   "k": rec["k"], "seed": rec.get("seed"), "clean": d["clean"],
                   "judge_recall_notes": sum(notes) / len(notes),
                   "judge_kept_writer_input": sum(got[i] for i in found) / len(found) if found else 0.0,
                   "judge_kept_final": sum(final[i] for i in found) / len(found) if found else 0.0,
                   "judge_recall_final": sum(final) / len(final)}
            row["judge_info_loss"] = 1 - row["judge_kept_final"] if found else 1.0
            row.update(judged_failures(rec, by_task[rec["task_id"]].questions, d["per_q"]))
            f.write(json.dumps(row) + "\n")
    return out


def judged_failures(rec: dict, questions, per_q: dict) -> dict:
    """metrics.failure_types with fact presence from the judge instead of lexical matching."""
    n = len(questions)
    final = parse_answers(rec["stage"].get("final", ""), n)
    draft = parse_answers(rec["stage"].get("draft", ""), n)
    overflow = any(a["overflow"] for a in rec["agents"].values())
    kinds = ("ok", "reviewer_fixed", "overflow", "no_answer", "research_miss", "delivery_miss", "writer_wrong",
             "reviewer_broke")
    counts = dict.fromkeys(kinds, 0)
    for qi, q in enumerate(questions):
        good, d_ok = correct(final[qi], q.answer), correct(draft[qi], q.answer)
        notes_has = all(per_q["notes"].get(qi, [False]))
        got_has = all(per_q["writer_input"].get(qi, [False]))
        if good:
            kind = "ok" if d_ok else "reviewer_fixed"
        elif overflow:
            kind = "overflow"
        elif not final[qi]:
            kind = "no_answer"
        elif d_ok:
            kind = "reviewer_broke"
        elif not notes_has:
            kind = "research_miss"
        elif not got_has:
            kind = "delivery_miss"
        else:
            kind = "writer_wrong"
        counts[kind] += 1
    return {f"jq_{k}": v / n for k, v in counts.items()}


def summarize(path: Path) -> dict:
    rows = [json.loads(l) for l in gzip.open(path, "rt")]
    groups: dict[str, list[dict]] = {}
    for r in rows:
        groups.setdefault(f"{r['dataset']}|k{r['k']}|{r['channel']}", []).append(r)
    out = {}
    for key, rs in sorted(groups.items()):
        g = {"n": len(rs), "clean": sum(r["clean"] for r in rs)}
        for m in ("judge_recall_notes", "judge_kept_writer_input", "judge_kept_final", "judge_info_loss",
                  "judge_recall_final"):
            mean, lo, hi = ci([r[m] for r in rs])
            g[m] = {"mean": round(mean, 4), "lo": round(lo, 4), "hi": round(hi, 4)}
        out[key] = g
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("run_dir")
    ap.add_argument("--concurrency", type=int, default=16)
    ap.add_argument("--max-chars", type=int, default=60000)
    ap.add_argument("--urls", nargs="*", default=None, help="judge servers (default: the run's servers)")
    ap.add_argument("--judge-name", default="qwen3-8b")
    a = ap.parse_args()
    run_dir = Path(a.run_dir)
    path = asyncio.run(judge_run_dir(run_dir, a.concurrency, a.max_chars, a.urls, a.judge_name))
    (run_dir / "summary_judge.json").write_text(json.dumps(summarize(path), indent=1))
    print(f"judged: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
