"""Extract the Writer's LLM calls of one pilot task, per channel, for Fig. 1.

python -m agentipc.fig1_data results/t06_pilot/<run_id> <task_id>  ->  paper/figs/data/fig1_writer_calls.json
Each call is split into prompt segments by content: the first prompt by character share of its messages,
later growth by the prompt-token difference between consecutive calls (own turn + tool result).
"""
from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import yaml

from .data import LOADERS, make_tasks
from .pipeline import build_messages, system_prompt
from .run import datasets

ROOT = Path(__file__).resolve().parents[2]


def kind_of(op: dict) -> str:
    if "error" in op:
        return "own"  # a failed call returns only an error line
    if op["op"] == "list":
        return "list"
    p = op.get("path", "")
    if op["op"] == "read":
        return "docs" if p.startswith("docs/") else "notes"
    return "own"


def main() -> int:
    run_dir, task_id = Path(sys.argv[1]), sys.argv[2]
    cfg = yaml.safe_load((run_dir / "config.yaml").read_text())
    raw = ROOT / "results_raw" / cfg["exp"] / run_dir.name
    task = None
    for name, path in datasets(cfg).items():
        for s in cfg["seeds"]:
            for k in cfg["k"]:
                for t in make_tasks(LOADERS[name](ROOT / path), cfg["n_tasks"], k, s):
                    if t.task_id == task_id:
                        task = t
    out = {"task_id": task_id, "source": str(run_dir), "channels": {}}
    for line in gzip.open(raw / "records.jsonl.gz", "rt"):
        rec = json.loads(line)
        if rec["task_id"] != task_id:
            continue
        ch = rec["channel"]
        calls = [c for c in rec["agents"]["writer"]["calls"] if "error" not in c]
        replies = {r: a["reply"] for r, a in rec["agents"].items()}
        msgs = build_messages("writer", ch, ("researcher", "writer", "reviewer"), task, replies)
        # Split the first prompt by the characters each kind of content takes.
        kinds = []
        for m in msgs:
            c = m["content"]
            if m["role"] == "system":
                kinds.append(("task", len(c)))
            elif c.startswith("[Researcher"):
                kinds.append(("notes", len(c)))
            elif "[Researcher]" in c:  # A2: questions and the Researcher's output in one message
                head = c.split("[Researcher]")[0]
                kinds += [("task", len(head)), ("notes", len(c) - len(head))]
            elif "Documents:" in c:
                qpart = c.split("Documents:")[0]
                kinds += [("task", len(qpart)), ("docs", len(c) - len(qpart))]
            else:
                kinds.append(("task", len(c)))
        total = sum(n for _, n in kinds)
        first = calls[0]["prompt_tokens"]
        base = [[k, round(first * n / total)] for k, n in kinds]
        writer_ops = [o for o in rec["io_ops"] if o["agent"] == "writer"]
        seq, segs, oi = [], base, 0
        for i, c in enumerate(calls):
            label = ",".join(c["tools"]) or "reply"
            seq.append({"label": label, "prompt": c["prompt_tokens"], "cached": c["cached_tokens"],
                        "forced": bool(c.get("forced_write")), "segments": [list(s) for s in segs]})
            if i + 1 < len(calls):
                grow = calls[i + 1]["prompt_tokens"] - c["prompt_tokens"]
                own = min(c["completion_tokens"], grow)
                kind = "own"
                if c["tools"]:
                    kind = kind_of(writer_ops[oi]) if oi < len(writer_ops) else "own"
                    oi += len(c["tools"])
                segs = segs + [["own", own]] + ([[kind, grow - own]] if grow - own > 0 else [])
        out["channels"][ch] = {"acc": rec["score"]["acc"], "calls": seq,
                               "reads": [o.get("path", "") for o in writer_ops if o["op"] == "read"]}
    dst = ROOT / "paper" / "figs" / "data" / "fig1_writer_calls.json"
    dst.write_text(json.dumps(out, indent=1))
    print(dst)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
