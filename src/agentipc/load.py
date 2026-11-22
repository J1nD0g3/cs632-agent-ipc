"""Load the committed results without a server: experiments(), run_dir(exp), load_rows(exp), load_records(exp).

Every run directory results/<exp>/<run_id>/ holds config.yaml, env.json, summary.json and the per-task files
rows.jsonl.gz, records.jsonl.gz and, where scored, judged.jsonl.gz and alignscore_rows.jsonl.gz (docs/data.md).
These functions read only those committed files, never results_raw/.
"""
from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Iterator

import pandas as pd
import yaml

from .analyze import load_rows as _merge_rows

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"


def experiments() -> list[str]:
    """Experiment IDs that have a finished run with per-task rows."""
    return sorted(p.parent.parent.name for p in RESULTS.glob("*/2*/rows.jsonl.gz"))


def run_dir(exp: str) -> Path:
    """The run of an experiment the paper uses (the latest finished one; each experiment has one)."""
    runs = sorted(p.parent for p in (RESULTS / exp).glob("2*/summary.json"))
    if not runs:
        raise FileNotFoundError(f"no finished run under results/{exp}")
    return runs[-1]


def config(exp: str) -> dict:
    return yaml.safe_load((run_dir(exp) / "config.yaml").read_text())


def load_rows(exp: str, errors: bool = False) -> pd.DataFrame:
    """One row per (task, channel), with judge (judge_*, jq_*) and AlignScore (as_*, aq_*) columns merged in.

    errors=False drops pipelines that failed with an error, as every analysis in the paper does; errors=True returns
    rows.jsonl.gz as written, failed pipelines included, without the merged judge and AlignScore columns."""
    run = run_dir(exp)
    if errors:
        rows = [json.loads(line) for line in gzip.open(run / "rows.jsonl.gz", "rt")]
    else:
        rows = _merge_rows(run, raw=run)
    df = pd.DataFrame(rows)
    df.insert(0, "exp", exp)
    return df


def load_records(exp: str) -> Iterator[dict]:
    """Full per-pipeline records: every model call's token counts, file operations (io_ops) and stage texts."""
    with gzip.open(run_dir(exp) / "records.jsonl.gz", "rt") as f:
        for line in f:
            yield json.loads(line)
