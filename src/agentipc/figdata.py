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


def latest(exp: str) -> Path | None:
    runs = sorted(p.parent for p in (ROOT / "results" / exp).glob("2*/summary.json"))
    return runs[-1] if runs else None


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
        for m in ("acc", "total_tokens", "prefill_tokens", "prompt_tokens"):
            mean, lo, hi = pooled(rows, ch, k, m)
            row.update({m: round(mean, 4), f"{m}_lo": round(lo, 4), f"{m}_hi": round(hi, 4)})
        table.append(row)
    write("fig2_tradeoff", {"source": str(src.relative_to(ROOT)), "k": k, "pooled": "hotpotqa+2wiki",
                            "channels": table}, table)


FAIL = ("aq_research_miss", "aq_delivery_miss", "aq_writer_wrong", "aq_reviewer_broke", "aq_no_answer")


def fig3(rows: list[dict], src: Path, k: int = 3) -> None:
    table = []
    for ch in CHANNELS:
        row = {"channel": ch, "k": k}
        for m in ("as_recall_notes", "as_kept_writer_input", "acc") + FAIL:
            mean, lo, hi = pooled(rows, ch, k, m)
            row.update({m: round(mean, 4), f"{m}_lo": round(lo, 4), f"{m}_hi": round(hi, 4)})
        table.append(row)
    write("fig3_loss", {"source": str(src.relative_to(ROOT)), "k": k, "pooled": "hotpotqa+2wiki",
                        "channels": table}, table)


def fig3_split() -> None:
    """Writing control in one run per model size (p10): facts in the Researcher's output per arm, and the
    paired accuracy effects of wording (A1r-A1), writing through a tool call (A1w-A1r) and reading files (B-A1w)."""
    from .analyze import paired
    table = []
    for size in ("4b", "8b", "14b", "32b"):
        run = latest(f"p10_write_{size}")
        rows = load_rows(run)
        by = {ch: {r["task_id"]: r for r in rows if r["channel"] == ch} for ch in ("A1", "A1r", "A1w", "B")}
        row = {"size": size.upper(), "source": str(run.relative_to(ROOT))}
        for ch, d in by.items():
            row[f"notes_{ch}"] = round(float(np.mean([r["as_recall_notes"] for r in d.values() if "as_recall_notes" in r])), 4)
            row[f"acc_{ch}"] = round(float(np.mean([r["acc"] for r in d.values()])), 4)
        for name, x, y in (("wording", "A1r", "A1"), ("tool_write", "A1w", "A1r"), ("read_files", "B", "A1w")):
            ids = sorted(set(by[x]) & set(by[y]))
            mean, lo, hi = paired(np.array([by[x][i]["acc"] for i in ids], float), np.array([by[y][i]["acc"] for i in ids], float))
            row.update({name: round(mean, 4), f"{name}_lo": round(lo, 4), f"{name}_hi": round(hi, 4), f"{name}_n": len(ids)})
        table.append(row)
    write("fig3_split", {"rows": table}, table)


def fig4(rows_by_k: dict[int, list[dict]], sources: dict[int, str]) -> None:
    """Per k: computed and sent tokens relative to A1, and accuracy relative to A1, both datasets pooled."""
    table = []
    for k, rows in sorted(rows_by_k.items()):
        base = {m: np.mean([r[m] for r in rows if r["channel"] == "A1" and r["k"] == k]) for m in
                ("total_tokens", "prefill_tokens", "acc")}
        a1 = {(r["task_id"]): r for r in rows if r["channel"] == "A1" and r["k"] == k}
        for ch in sorted({r["channel"] for r in rows}):
            rs = [r for r in rows if r["channel"] == ch and r["k"] == k]
            if not rs:
                continue
            diffs = [r["acc"] - a1[r["task_id"]]["acc"] for r in rs if r["task_id"] in a1]
            mean, lo, hi = ci(diffs) if ch != "A1" else (0.0, 0.0, 0.0)
            table.append({"k": k, "channel": ch, "n": len(rs), "source": sources[k],
                          "sent_rel": round(np.mean([r["total_tokens"] for r in rs]) / base["total_tokens"], 4),
                          "comp_rel": round(np.mean([r["prefill_tokens"] for r in rs]) / base["prefill_tokens"], 4),
                          "acc": round(np.mean([r["acc"] for r in rs]), 4),
                          "acc_diff": round(mean, 4), "acc_diff_lo": round(lo, 4), "acc_diff_hi": round(hi, 4)})
    write("fig4_scaling", {"rows": table}, table)


def main() -> int:
    src = latest("t07_main")
    rows = load_rows(src)
    fig2(rows, src)
    fig3(rows, src)
    by_k = {k: [r for r in rows if r["k"] == k] for k in (1, 3, 5)}
    sources = {k: str(src.relative_to(ROOT)) for k in by_k}
    for exp, k in (("t08_k8", 8), ("t08_large", 16)):
        run = latest(exp) if (ROOT / "results" / exp).exists() else None
        if run is not None:
            by_k[k] = load_rows(run)
            sources[k] = str(run.relative_to(ROOT))
    fig4(by_k, sources)
    fig3_split()
    print(f"wrote {OUT}/fig2_tradeoff.json, fig3_loss.json from {src.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
