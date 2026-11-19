"""Score the LLM judges on the synthetic pairs whose labels are known by construction.

python -m agentipc.judge_synth SYNTH.jsonl --qwen URL --other URL --other-name NAME --out OUT.json
Uses judge_all's prompt with one fact per call. Reports accuracy per pair kind (present / dropped /
swapped) for each judge and for lexical matching.
"""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from .judge_all import PROMPT, parse
from .llm import ChatClient


async def judge(rows: list[dict], url: str, name: str) -> list[bool | None]:
    client = ChatClient(url, name, max_tokens=16)
    sem = asyncio.Semaphore(24)

    async def one(r):
        async with sem:
            out = await client.chat([{"role": "user", "content": PROMPT.format(facts=f"F1: {r['fact']}", text=r["context"])}])
        return parse(out.content, 1)[0]

    res = await asyncio.gather(*(one(r) for r in rows))
    await client.aclose()
    return res


def accuracy(rows: list[dict], preds: list) -> dict:
    out = {}
    for kind in ("present", "dropped", "swapped"):
        rs = [(r, p) for r, p in zip(rows, preds) if r["kind"] == kind and p is not None]
        out[kind] = round(sum(p == r["label"] for r, p in rs) / len(rs), 4) if rs else None
    valid = [(r, p) for r, p in zip(rows, preds) if p is not None]
    out["all"] = round(sum(p == r["label"] for r, p in valid) / len(valid), 4)
    out["unparsed"] = sum(p is None for p in preds)
    return out


async def main_async(a) -> dict:
    rows = [json.loads(l) for l in open(a.synth)]
    q, o = await asyncio.gather(judge(rows, a.qwen, "qwen3-8b"), judge(rows, a.other, a.other_name))
    return {"n": len(rows), "qwen3-8b": accuracy(rows, q), a.other_name: accuracy(rows, o),
            "lexical": accuracy(rows, [r["lexical"] for r in rows])}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("synth")
    ap.add_argument("--qwen", required=True)
    ap.add_argument("--other", required=True)
    ap.add_argument("--other-name", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    res = asyncio.run(main_async(a))
    Path(a.out).write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
