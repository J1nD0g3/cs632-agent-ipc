"""Write the data files the paper figures plot, from results/ only.

python -m agentipc.figdata   ->  paper/figs/data/fig2_tradeoff.json, fig3_loss.json (and a csv beside each)
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

from .analyze import load_rows
from .stats import ci

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "paper" / "figs" / "data"
CHANNELS = ("A1", "A1zc", "A2", "B", "C", "D")


def latest(exp: str) -> Path:
    runs = sorted(p.parent for p in (ROOT / "results" / exp).glob("2*/summary.json"))
    return runs[-1]


def pooled(rows: list[dict], ch: str, k: int, metric: str) -> tuple[float, float, float]:
    vals = [r[metric] for r in rows if r["channel"] == ch and r["k"] == k and metric in r]
    return ci(vals)


def write(name: str, data: dict, table: list[dict]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps(data, indent=1))
    with open(OUT / f"{name}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(table[0]))
        w.writeheader()
        w.writerows(table)


def fig2(rows: list[dict], src: Path, k: int = 3) -> None:
    table = []
    for ch in CHANNELS:
        row = {"channel": ch, "k": k}
        for m in ("acc", "total_tokens", "prefill_tokens"):
            mean, lo, hi = pooled(rows, ch, k, m)
            row.update({m: round(mean, 4), f"{m}_lo": round(lo, 4), f"{m}_hi": round(hi, 4)})
        table.append(row)
    write("fig2_tradeoff", {"source": str(src.relative_to(ROOT)), "k": k, "pooled": "hotpotqa+2wiki",
                            "channels": table}, table)


FAIL = ("q_research_miss", "q_delivery_miss", "q_writer_wrong", "q_reviewer_broke", "q_no_answer")


def fig3(rows: list[dict], src: Path, k: int = 3) -> None:
    table = []
    for ch in CHANNELS:
        row = {"channel": ch, "k": k}
        for m in ("judge_recall_notes", "judge_kept_writer_input", "acc") + FAIL:
            mean, lo, hi = pooled(rows, ch, k, m)
            row.update({m: round(mean, 4), f"{m}_lo": round(lo, 4), f"{m}_hi": round(hi, 4)})
        table.append(row)
    write("fig3_loss", {"source": str(src.relative_to(ROOT)), "k": k, "pooled": "hotpotqa+2wiki",
                        "channels": table}, table)


def main() -> int:
    src = latest("t07_main")
    rows = load_rows(src)
    fig2(rows, src)
    fig3(rows, src)
    print(f"wrote {OUT}/fig2_tradeoff.json, fig3_loss.json from {src.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
