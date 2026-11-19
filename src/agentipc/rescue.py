"""Accuracy if a final answer written under a prefixed path (workspace/final.md) had been read as final.md.

The harness reads each role's output from a fixed file name. Qwen3-32B sometimes prefixes it with
"workspace/", which the harness scores as no answer. This post-hoc rescore reads that file instead, only
for runs whose final stage parses to no answer at all. It is a sensitivity check, not the measured result.
"""
from __future__ import annotations

import gzip
import json
import tarfile
from pathlib import Path

import numpy as np

from .factpairs import tasks_of
from .metrics import correct, parse_answers

ROOT = Path(__file__).resolve().parents[2]


def rescored(run_dir: Path) -> dict[str, dict]:
    """Per channel: measured and rescued accuracy, and the number of rescued runs."""
    cfg, tasks = tasks_of(run_dir)
    raw = ROOT / "results_raw" / cfg["exp"] / run_dir.name
    alt = {}
    with tarfile.open(raw / "workspaces.tar.gz") as tf:
        for m in tf.getmembers():
            if m.isfile() and m.name.endswith("/workspace/final.md"):
                alt[m.name.split("/")[1]] = tf.extractfile(m).read().decode("utf-8", "replace")
    out: dict[str, dict] = {}
    for line in gzip.open(raw / "records.jsonl.gz", "rt"):
        r = json.loads(line)
        if "error" in r:
            continue
        qs = tasks[r["task_id"]].questions
        fin = r["stage"].get("final", "")
        a0 = parse_answers(fin, len(qs))
        key = next((k for k in alt if k.startswith(f"{r['task_id']}_{r['channel']}_")), None)
        a1, moved = a0, False
        if key and not any(a0):
            a1, moved = parse_answers(alt[key], len(qs)), True
        d = out.setdefault(r["channel"], {"measured": [], "rescued": [], "moved": 0})
        d["measured"].append(np.mean([correct(a, q.answer) for a, q in zip(a0, qs)]))
        d["rescued"].append(np.mean([correct(a, q.answer) for a, q in zip(a1, qs)]))
        d["moved"] += moved
    return {ch: {"measured": float(np.mean(d["measured"])), "rescued": float(np.mean(d["rescued"])),
                 "moved": d["moved"], "runs": len(d["measured"])} for ch, d in out.items()}
