"""Per-channel tables with paired differences against a reference channel.

python -m agentipc.analyze results/<exp>/<run_id> [--ref A1]
Writes paired.json next to summary.json: for every (dataset, k, channel) the mean of each metric and the
paired bootstrap 95% CI of (channel - ref) over the tasks both channels ran.
"""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[2]
METRICS = ("acc", "total_tokens", "prefill_tokens", "completion_tokens", "llm_calls", "file_io", "wall_s",
           "turn_limit", "judge_recall_notes", "judge_kept_writer_input", "judge_kept_final", "judge_info_loss",
           "q_research_miss", "q_delivery_miss", "q_writer_wrong", "q_reviewer_broke", "q_reviewer_fixed",
           "q_no_answer", "jq_research_miss", "jq_delivery_miss", "jq_writer_wrong", "jq_reviewer_broke",
           "jq_reviewer_fixed", "jq_no_answer", "jq_overflow", "as_recall_notes", "as_kept_writer_input",
           "aq_research_miss", "aq_delivery_miss", "aq_writer_wrong", "aq_reviewer_broke", "aq_no_answer")


def load_rows(run_dir: Path) -> list[dict]:
    cfg = yaml.safe_load((run_dir / "config.yaml").read_text())
    raw = ROOT / "results_raw" / cfg["exp"] / run_dir.name
    rows = {(r["task_id"], r["channel"]): r for r in map(json.loads, gzip.open(raw / "rows.jsonl.gz", "rt"))}
    judged = raw / "judged.jsonl.gz"
    if judged.exists():
        for j in map(json.loads, gzip.open(judged, "rt")):
            r = rows.get((j["task_id"], j["channel"]))
            if r is not None:
                r.update({k: v for k, v in j.items() if k.startswith(("judge_", "jq_"))})
    aligned = raw / "alignscore_rows.jsonl.gz"
    if aligned.exists():
        for j in map(json.loads, gzip.open(aligned, "rt")):
            r = rows.get((j["task_id"], j["channel"]))
            if r is not None:
                r.update({k: v for k, v in j.items() if k.startswith(("as_", "aq_"))})
    return [r for r in rows.values() if not r.get("error")]


def paired(a: np.ndarray, b: np.ndarray, n_boot: int = 2000, seed: int = 0) -> tuple[float, float, float]:
    d = a - b
    rng = np.random.default_rng(seed)
    boots = d[rng.integers(0, d.size, size=(n_boot, d.size))].mean(axis=1)
    return float(d.mean()), float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))


def analyze(rows: list[dict], ref: str) -> dict:
    by = {}
    for r in rows:
        by.setdefault((r["dataset"], r["k"]), {}).setdefault(r["channel"], {})[r["task_id"]] = r
    out = {}
    for (ds, k), chans in sorted(by.items()):
        base = chans.get(ref, {})
        for ch, runs in sorted(chans.items()):
            g = {"n": len(runs)}
            common = sorted(set(runs) & set(base))
            for m in METRICS:
                vals = [runs[t][m] for t in runs if m in runs[t]]
                if not vals:
                    continue
                g[m] = round(float(np.mean(vals)), 4)
                pairs = [(runs[t][m], base[t][m]) for t in common if m in runs[t] and m in base[t]]
                if ch != ref and len(pairs) > 1:
                    a, b = np.array(pairs, dtype=float).T
                    mean, lo, hi = paired(a, b)
                    g[f"{m}_diff"] = [round(mean, 4), round(lo, 4), round(hi, 4)]
            out[f"{ds}|k{k}|{ch}"] = g
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("run_dir")
    ap.add_argument("--ref", default="A1")
    a = ap.parse_args()
    run_dir = Path(a.run_dir)
    res = analyze(load_rows(run_dir), a.ref)
    (run_dir / "paired.json").write_text(json.dumps(res, indent=1))
    cols = ("acc", "total_tokens", "prefill_tokens", "file_io", "judge_recall_notes", "judge_kept_writer_input")
    print(f"{'group':<20}{'n':>5}" + "".join(f"{c[:14]:>16}" for c in cols))
    for key, g in res.items():
        cells = []
        for c in cols:
            v, d = g.get(c), g.get(f"{c}_diff")
            s = "-" if v is None else (f"{v:.0f}" if abs(v) >= 100 else f"{v:.2f}")
            if d:
                sig = "*" if d[1] > 0 or d[2] < 0 else ""
                s += f"({d[0]:+.0f}{sig})" if abs(v or 0) >= 100 else f"({d[0]:+.2f}{sig})"
            cells.append(f"{s:>16}")
        print(f"{key:<20}{g['n']:>5}" + "".join(cells))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
