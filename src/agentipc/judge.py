"""Check lexical fact matching against an LLM judge on a sample of (fact, stage text) pairs.

python -m agentipc.judge results/<exp>/<run_id> --n 300
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
from .llm import ChatClient
from .metrics import fact_present
from .run import datasets

ROOT = Path(__file__).resolve().parents[2]

PROMPT = ("Does the TEXT state the FACT, possibly in other words? The FACT counts as stated only if the "
          "information it adds (names, dates, places, numbers, relations) is in the TEXT.\n\n"
          "FACT: {fact}\n\nTEXT:\n{text}\n\nAnswer with one word: yes or no.")


def kappa(a: list[bool], b: list[bool]) -> float:
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


async def main_async(run_dir: Path, n: int, seed: int) -> dict:
    cfg = yaml.safe_load((run_dir / "config.yaml").read_text())
    raw = ROOT / "results_raw" / cfg["exp"] / run_dir.name
    by_task = {}
    for name, path in datasets(cfg).items():
        questions = LOADERS[name](ROOT / path)
        for s in cfg["seeds"]:
            for k in cfg["k"]:
                for t in make_tasks(questions, cfg["n_tasks"], k, s):
                    by_task[t.task_id] = t
    pairs = []
    with gzip.open(raw / "records.jsonl.gz", "rt") as f:
        for line in f:
            rec = json.loads(line)
            if "error" in rec:
                continue
            t = by_task[rec["task_id"]]
            for stage in ("notes", "final"):
                text = rec["stage"].get(stage, "")
                for q in t.questions:
                    for fact in q.facts:
                        pairs.append((rec["channel"], stage, fact.text, q, text))
    rng = random.Random(seed)
    sample = rng.sample(pairs, min(n, len(pairs)))
    client = ChatClient(cfg["server"]["base_url"], cfg["server"].get("served_name", cfg["model"]), max_tokens=4)
    sem = asyncio.Semaphore(16)

    async def judge(fact, text):
        async with sem:
            r = await client.chat([{"role": "user", "content": PROMPT.format(fact=fact, text=text[:12000])}])
            return r.content.strip().lower().startswith("yes")

    llm = await asyncio.gather(*(judge(fact, text) for _, _, fact, _, text in sample))
    await client.aclose()
    lex = [fact_present(next(f for f in q.facts if f.text == fact), q, text) for _, _, fact, q, text in sample]
    out = {"n": len(sample), "agree": sum(a == b for a, b in zip(lex, llm)) / len(sample),
           "kappa": kappa(lex, llm), "lexical_yes": sum(lex) / len(sample), "judge_yes": sum(llm) / len(sample),
           "lex_yes_judge_no": sum(a and not b for a, b in zip(lex, llm)),
           "lex_no_judge_yes": sum(b and not a for a, b in zip(lex, llm))}
    rows = [{"channel": c, "stage": s, "fact": fa, "lexical": a, "judge": b}
            for (c, s, fa, _, _), a, b in zip(sample, lex, llm)]
    with gzip.open(raw / "judge_pairs.jsonl.gz", "wt") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("run_dir")
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    run_dir = Path(a.run_dir)
    out = asyncio.run(main_async(run_dir, a.n, a.seed))
    (run_dir / "judge_agreement.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
