"""Labeled (context, fact) pairs for validating fact-presence measures, and real pairs to score.

python -m agentipc.factpairs results/t07_main/<run_id> OUT_DIR       (synthetic.jsonl, real.jsonl)
python -m agentipc.factpairs --export results/<exp>/<run_id> OUT.jsonl [k]   (pairs of one run to score)

synthetic.jsonl: labels known by construction, from the task's own documents. For a supporting sentence
F of a question, the context is the sentences of the question's paragraphs, shuffled:
  present   F is in the context;
  dropped   F is removed (its paragraph's other sentences stay);
  swapped   F is in the context with its key entity (the answer, or a supporting title other than the
            sentence's own paragraph) replaced by the same kind of entity from another question.
real.jsonl: the judge_cross sample (Researcher output and Writer input texts with the Qwen3-8B and
Llama-3-8B labels per fact), so every measure is scored on the same real pairs.
"""
from __future__ import annotations

import gzip
import json
import random
import re
import sys
from pathlib import Path

import yaml

from .data import LOADERS, make_tasks
from .metrics import fact_present
from .run import datasets

ROOT = Path(__file__).resolve().parents[2]


def raw_of(cfg: dict, run_dir: Path, name: str = "records.jsonl.gz") -> Path:
    """results_raw/<exp>/<run_id> if it holds `name`, else the copies committed in run_dir."""
    raw = ROOT / "results_raw" / cfg["exp"] / run_dir.name
    return raw if (raw / name).exists() else run_dir


def tasks_of(run_dir: Path):
    cfg = yaml.safe_load((run_dir / "config.yaml").read_text())
    out = {}
    for name, path in datasets(cfg).items():
        qs = LOADERS[name](ROOT / path)
        for s in cfg["seeds"]:
            for k in cfg["k"]:
                for t in make_tasks(qs, cfg["n_tasks"], k, s):
                    out[t.task_id] = t
    return cfg, out


def synthetic(tasks, n_per_kind: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    qs = [q for t in tasks.values() for q in t.questions]
    answers = [q.answer for q in qs if len(q.answer.split()) <= 4]
    rows = []
    rng.shuffle(qs)
    for q in qs:
        if len(rows) >= 3 * n_per_kind:
            break
        fact = rng.choice(q.facts)
        paras = {t: s for t, s in q.paragraphs if t in {f.title for f in q.facts}}
        sents = [x.strip() for t, ss in paras.items() for x in ss if x.strip()]
        if fact.text not in sents or len(sents) < 4:
            continue
        # The entity to swap: the answer if the fact states it, else another supporting title it names.
        keys = [q.answer] + [f.title for f in q.facts if f.title != fact.title]
        key = next((k for k in keys if k and re.search(rf"(?<!\w){re.escape(k)}(?!\w)", fact.text)), None)
        if key is None:
            continue
        other = rng.choice([a for a in answers if a.lower() != key.lower()])
        swapped = re.sub(rf"(?<!\w){re.escape(key)}(?!\w)", other, fact.text)
        base = [x for x in sents if x != fact.text]
        for kind, ctx in (("present", base + [fact.text]), ("dropped", base), ("swapped", base + [swapped])):
            ctx = ctx[:]
            rng.shuffle(ctx)
            text = " ".join(ctx)
            rows.append({"kind": kind, "label": kind == "present", "question": q.question, "fact": fact.text,
                         "context": text, "lexical": fact_present(fact, q, text)})
    return rows


def export_run(run_dir: Path, out_file: Path, k: int | None = None) -> int:
    """One (context, fact) pair per supporting fact, run, and stage (Researcher output, Writer input)."""
    cfg, tasks = tasks_of(run_dir)
    raw = raw_of(cfg, run_dir)
    n = 0
    with open(out_file, "w") as out:
        for line in gzip.open(raw / "records.jsonl.gz", "rt"):
            rec = json.loads(line)
            if "error" in rec or (k is not None and rec["k"] != k):
                continue
            for stage in ("notes", "writer_input"):
                text = rec["stage"].get(stage, "") or " "
                for qi, q in enumerate(tasks[rec["task_id"]].questions):
                    for fi, f in enumerate(q.facts):
                        out.write(json.dumps({"task_id": rec["task_id"], "channel": rec["channel"], "k": rec["k"],
                                              "stage": stage, "q": qi, "f": fi, "fact": f.text,
                                              "context": text}) + "\n")
                        n += 1
    return n


def main() -> int:
    if sys.argv[1] == "--export":
        k = int(sys.argv[4]) if len(sys.argv) > 4 else None
        print(export_run(Path(sys.argv[2]), Path(sys.argv[3]), k), "pairs")
        return 0
    run_dir, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    cfg, tasks = tasks_of(run_dir)
    syn = synthetic(tasks, 150, 0)
    with open(out / "synthetic.jsonl", "w") as f:
        for r in syn:
            f.write(json.dumps(r) + "\n")
    raw = raw_of(cfg, run_dir, "judge_cross.jsonl.gz")
    cross = [json.loads(l) for l in gzip.open(raw / "judge_cross.jsonl.gz", "rt")]
    jx = json.loads((run_dir / "judge_cross.json").read_text())
    # Rebuild judge_cross's sample (same seed and limits) to recover each fact's text.
    from .judge_cross import sample_units
    units = sample_units(run_dir, jx["units"], jx["max_chars"], 0)
    queue = list(cross)
    real = []
    for ch, stage, q, text in units:
        for f in q.facts:
            if queue and queue[0]["fact"] == f.text and queue[0]["channel"] == ch and queue[0]["stage"] == stage:
                r = queue.pop(0)
                real.append({**r, "context": text, "question": q.question})
    with open(out / "real.jsonl", "w") as f:
        for r in real:
            f.write(json.dumps(r) + "\n")
    print(f"synthetic {len(syn)} ({sum(r['label'] for r in syn)} present); real {len(real)} of {len(cross)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
