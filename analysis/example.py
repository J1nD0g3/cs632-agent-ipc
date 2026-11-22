"""Recompute headline numbers of the paper from the committed per-task rows and check them against paper/numbers.tex.

python analysis/example.py

Uses only results/t07_main/<run_id>/rows.jsonl.gz (+ alignscore/judge columns), through agentipc.load.
Main run: Qwen3-8B, k = 3 questions per task, HotpotQA and 2Wiki pooled (150 tasks each).
"""
import re
import sys
from pathlib import Path

import numpy as np

from agentipc.load import load_rows

ROOT = Path(__file__).resolve().parents[1]


def macros() -> dict[str, str]:
    text = (ROOT / "paper" / "numbers.tex").read_text()
    out = {}
    for name, value in re.findall(r"\\newcommand\{\\n(\w+)\}\{(.*)\\xspace\}", text):
        out[name] = re.sub(r"\\mbox\{\$(.)\$(.*)\}", r"\1\2", value)
    return out


def paired_ci(a: np.ndarray, b: np.ndarray, n_boot: int = 2000, seed: int = 0) -> tuple[float, float, float]:
    """Mean of a - b and its 95% bootstrap interval, resampling tasks with replacement."""
    d = a - b
    boots = d[np.random.default_rng(seed).integers(0, d.size, size=(n_boot, d.size))].mean(axis=1)
    return d.mean(), np.percentile(boots, 2.5), np.percentile(boots, 97.5)


def main() -> int:
    df = load_rows("t07_main")
    k3 = df[df["k"] == 3]
    ours: dict[str, str] = {}

    # 1. Accuracy per channel (share of questions answered correctly), and per-task means of tokens and prefill.
    names = {"A1": "AOne", "A1zc": "AZc", "A2": "ATwo", "B": "B", "C": "C", "D": "D"}
    per_ch = k3.groupby("channel")[["acc", "total_tokens", "prefill_tokens"]].mean()
    print(per_ch.rename(columns={"total_tokens": "sent", "prefill_tokens": "prefill"}).round(3).to_string(), "\n")
    for ch, n in names.items():
        ours[f"Acc{n}"] = f"{per_ch.loc[ch, 'acc'] * 100:.1f}"

    # 2. Prefill: zero-copy's cut against broadcast, and files' prefill relative to broadcast.
    a1, zc, b = (per_ch.loc[c, "prefill_tokens"] for c in ("A1", "A1zc", "B"))
    ours["ZcCut"] = f"{(1 - zc / a1) * 100:.0f}"
    ours["CompRatioB"] = f"{b / a1:.2f}"

    # 3. Zero-copy minus broadcast accuracy, paired by (dataset, task), with a 95% bootstrap interval.
    acc = k3.pivot_table(index=["dataset", "task_id"], columns="channel", values="acc").sort_index()
    both = acc[["A1", "A1zc"]].dropna()
    mean, lo, hi = paired_ci(both["A1zc"].to_numpy(), both["A1"].to_numpy())
    ours["ZcPooledDiff"], ours["ZcPooledDiffLo"], ours["ZcPooledDiffHi"] = (f"{x * 100:.1f}" for x in (mean, lo, hi))
    ours["ZcPooledDiffN"] = str(len(both))

    # 4. B minus broadcast, paired by task, in each of the six settings (dataset x k = 1, 3, 5).
    gaps = []
    for (ds, k), g in df.pivot_table(index=["dataset", "k", "task_id"], columns="channel", values="acc").groupby(
            level=["dataset", "k"]):
        p = g[["A1", "B"]].dropna()
        m, l, h = paired_ci(p["B"].to_numpy(), p["A1"].to_numpy())
        gaps.append(-m)
        print(f"B - A1, {ds:<8} k={k}: {m * 100:+5.1f} points (95% CI {l * 100:+.1f} to {h * 100:+.1f}, {len(p)} tasks)")
    print()
    ours["GapBMin"], ours["GapBMax"] = f"{min(gaps) * 100:.1f}", f"{max(gaps) * 100:.1f}"

    paper = macros()
    bad = 0
    for name, value in ours.items():
        ok = paper.get(name) == value
        bad += not ok
        print(f"{'ok ' if ok else 'MISMATCH'} \\n{name:<16} recomputed {value:>6}   paper/numbers.tex {paper.get(name)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
