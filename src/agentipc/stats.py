"""Group per-run scores into means with bootstrap 95% confidence intervals."""
from __future__ import annotations

import numpy as np

METRICS = ("acc", "all_correct", "em", "f1", "answered", "total_tokens", "prompt_tokens", "completion_tokens",
           "prefill_tokens", "llm_calls", "tokens_researcher", "tokens_writer", "tokens_reviewer",
           "file_io", "file_reads", "file_writes", "file_lists", "read_chars", "write_chars",
           "fact_recall_notes", "fact_kept_writer_input", "fact_kept_draft", "fact_kept_final", "info_loss",
           "fact_recall_final", "triple_recall_notes", "triple_recall_final", "overflow", "turn_limit")


def ci(xs, n_boot: int = 2000, seed: int = 0) -> tuple[float, float, float]:
    x = np.asarray(xs, dtype=float)
    if x.size == 0:
        return (float("nan"),) * 3
    rng = np.random.default_rng(seed)
    boots = x[rng.integers(0, x.size, size=(n_boot, x.size))].mean(axis=1)
    return float(x.mean()), float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))


def summarize(rows: list[dict]) -> dict:
    groups: dict[str, list[dict]] = {}
    for r in rows:
        groups.setdefault(f"{r['dataset']}|k{r['k']}|{r['channel']}", []).append(r)
    out = {}
    for key, rs in sorted(groups.items()):
        ok = [r for r in rs if not r.get("error")]
        g = {"n": len(rs), "errors": len(rs) - len(ok)}
        for m in METRICS:
            vals = [r[m] for r in ok if m in r]
            if vals:
                mean, lo, hi = ci(vals)
                g[m] = {"mean": round(mean, 4), "lo": round(lo, 4), "hi": round(hi, 4)}
        out[key] = g
    return out
