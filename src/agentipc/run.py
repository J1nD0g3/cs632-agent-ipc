"""Run the three-agent pipeline over a config: python -m agentipc.run configs/<exp>.yaml"""
from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import gzip
import json
import random
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

import httpx
import yaml

from .data import LOADERS, make_tasks, task_stats
from .llm import ChatClient
from .metrics import score_run
from .pipeline import run_task
from .stats import summarize

ROOT = Path(__file__).resolve().parents[2]


def _sh(cmd: list[str], cwd=None) -> str:
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:
        return ""


def env_info(cfg: dict) -> dict:
    base = cfg["server"]["base_url"]
    try:
        version = httpx.get(base + "/version", timeout=10).json().get("version", "")
        models = httpx.get(base + "/v1/models", timeout=10).json()["data"]
        max_len = models[0].get("max_model_len")
    except Exception:
        version, max_len = "", None
    vllm_dir = cfg["server"].get("vllm_src", "")
    return {
        "git_commit": _sh(["git", "rev-parse", "HEAD"], ROOT),
        "git_dirty": bool(_sh(["git", "status", "--porcelain", "--untracked-files=no"], ROOT)),
        "python": sys.version.split()[0],
        "vllm_version": version,
        "vllm_src_commit": _sh(["git", "rev-parse", "--short", "HEAD"], vllm_dir) if vllm_dir else "",
        "vllm_src_dirty": bool(_sh(["git", "status", "--porcelain", "--untracked-files=no"], vllm_dir)) if vllm_dir else None,
        "gpu": _sh(["nvidia-smi", "--query-gpu=index,name,driver_version", "--format=csv,noheader",
                    "-i", str(cfg["server"].get("gpu", 0))]),
        "model": cfg["model"],
        "max_model_len": max_len,
        "server_flags": cfg["server"].get("flags", ""),
    }


async def run(cfg: dict, run_dir: Path, raw_dir: Path) -> list[dict]:
    questions = LOADERS[cfg["dataset"]](ROOT / cfg["data_path"])
    client = ChatClient(cfg["server"]["base_url"], cfg["server"].get("served_name", cfg["model"]),
                        max_tokens=cfg.get("max_tokens", 2048), seed=cfg.get("llm_seed", 0))
    jobs, tstats = [], {}
    for seed in cfg["seeds"]:
        for k in cfg["k"]:
            tasks = make_tasks(questions, cfg["n_tasks"], k, seed)
            tstats[f"k{k}_s{seed}"] = task_stats(tasks)
            for t in tasks:
                for ch in cfg["channels"]:
                    jobs.append((t, ch))
    # Interleave channels and task sizes so server load and drift hit every condition alike.
    random.Random(cfg.get("order_seed", 0)).shuffle(jobs)
    (run_dir / "task_stats.json").write_text(json.dumps(tstats, indent=1))
    sem = asyncio.Semaphore(cfg.get("concurrency", 8))
    work = raw_dir / "workspaces"
    out_f = gzip.open(raw_dir / "records.jsonl.gz", "wt")
    rows, done = [], 0

    async def one(task, ch):
        nonlocal done
        async with sem:
            try:
                rec = await run_task(task, ch, client, work, cfg.get("max_turns", 12))
            except Exception as e:  # keep going; a failed run is recorded, not dropped
                rec = {"task_id": task.task_id, "channel": ch, "dataset": task.dataset, "k": len(task.questions),
                       "error": f"{type(e).__name__}: {e}"[:500], "agents": {}, "stage": {}}
        rec["seed"] = int(task.task_id.split("-s")[1].split("-")[0])
        if "error" not in rec:
            rec["score"] = score_run(rec, task.questions)
        out_f.write(json.dumps(rec) + "\n")
        row = {k: rec[k] for k in ("task_id", "channel", "dataset", "k", "seed")}
        row["error"] = rec.get("error", "")
        row.update({k: v for k, v in rec.get("score", {}).items() if k != "preds"})
        rows.append(row)
        done += 1
        if done % 20 == 0 or done == len(jobs):
            print(f"{done}/{len(jobs)} runs", flush=True)

    await asyncio.gather(*(one(t, ch) for t, ch in jobs))
    out_f.close()
    await client.aclose()
    if work.exists():
        with tarfile.open(raw_dir / "workspaces.tar.gz", "w:gz") as tar:
            tar.add(work, arcname="workspaces")
        shutil.rmtree(work)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("config")
    ap.add_argument("--n-tasks", type=int, help="override n_tasks (smoke runs)")
    a = ap.parse_args()
    cfg = yaml.safe_load(Path(a.config).read_text())
    if a.n_tasks:
        cfg["n_tasks"] = a.n_tasks
    run_id = dt.datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + (_sh(["git", "rev-parse", "--short", "HEAD"], ROOT) or "nogit")
    run_dir = ROOT / "results" / cfg["exp"] / run_id
    raw_dir = ROOT / "results_raw" / cfg["exp"] / run_id
    run_dir.mkdir(parents=True)
    raw_dir.mkdir(parents=True)
    (run_dir / "config.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False))
    (run_dir / "env.json").write_text(json.dumps(env_info(cfg), indent=1))
    print(f"run dir: {run_dir}", flush=True)
    rows = asyncio.run(run(cfg, run_dir, raw_dir))
    with gzip.open(raw_dir / "rows.jsonl.gz", "wt") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    (run_dir / "summary.json").write_text(json.dumps(summarize(rows), indent=1))
    print(f"done: {run_dir}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
