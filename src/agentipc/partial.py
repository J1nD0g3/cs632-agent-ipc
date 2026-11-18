"""Summarize a run that is still going, from the records written so far.

python -m agentipc.partial results_raw/<exp>/<run_id> [metric ...]
Reads records.jsonl.gz even while it is open (truncated gzip stream) and prints per-group means.
"""
from __future__ import annotations

import json
import sys
import zlib
from pathlib import Path

from .stats import summarize

DEFAULT = ("acc", "total_tokens", "prefill_tokens", "llm_calls", "file_io", "wall_s", "turn_limit", "overflow")


def read_partial(path: Path) -> list[dict]:
    d = zlib.decompressobj(16 + zlib.MAX_WBITS)
    text = d.decompress(path.read_bytes()).decode("utf-8", "replace")
    recs = []
    for line in text.splitlines():
        try:
            recs.append(json.loads(line))
        except json.JSONDecodeError:
            break  # the last line may be cut off
    return recs


def rows_of(recs: list[dict]) -> list[dict]:
    rows = []
    for rec in recs:
        row = {k: rec[k] for k in ("task_id", "channel", "dataset", "k")}
        row["error"] = rec.get("error", "")
        row["wall_s"] = rec.get("wall_s", 0)
        row.update({k: v for k, v in rec.get("score", {}).items() if k != "preds"})
        rows.append(row)
    return rows


def main() -> int:
    raw = Path(sys.argv[1])
    metrics = sys.argv[2:] or DEFAULT
    recs = read_partial(raw / "records.jsonl.gz")
    summ = summarize(rows_of(recs))
    print(f"{len(recs)} records")
    print(f"{'group':<22}{'n':>4}{'err':>4}" + "".join(f"{m[:12]:>13}" for m in metrics))
    for key, g in summ.items():
        cells = []
        for m in metrics:
            v = g.get(m, {}).get("mean")
            cells.append(f"{'-' if v is None else (f'{v:.0f}' if abs(v) >= 100 else f'{v:.3f}'):>13}")
        print(f"{key:<22}{g['n']:>4}{g['errors']:>4}" + "".join(cells))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
