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


def datasets(cfg: dict) -> dict[str, str]:
    return cfg.get("datasets") or {cfg["dataset"]: cfg["data_path"]}


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
    # One client per server; each run stays on one server so its prefix cache stays local.
    urls = cfg["server"].get("base_urls") or [cfg["server"]["base_url"]]
    clients = [ChatClient(u, cfg["server"].get("served_name", cfg["model"]),
                          max_tokens=cfg.get("max_tokens", 2048), seed=cfg.get("llm_seed", 0)) for u in urls]
    jobs, tstats = [], {}
    for name, path in datasets(cfg).items():
        questions = LOADERS[name](ROOT / path)
        for seed in cfg["seeds"]:
            for k in cfg["k"]:
                # use_tasks keeps the first N of the same draw, so smaller runs stay paired with larger ones.
                tasks = make_tasks(questions, cfg["n_tasks"], k, seed)[:cfg.get("use_tasks", cfg["n_tasks"])]
                tstats[f"{name}_k{k}_s{seed}"] = task_stats(tasks)
                jobs += [(t, ch) for t in tasks for ch in cfg["channels"]]
    # Interleave channels and task sizes so server load and drift hit every condition alike.
    random.Random(cfg.get("order_seed", 0)).shuffle(jobs)
    (run_dir / "task_stats.json").write_text(json.dumps(tstats, indent=1))
    sems = [asyncio.Semaphore(cfg.get("concurrency", 8)) for _ in clients]
    replay = {}
    if cfg.get("replay_from"):
        # Replay one channel's Researcher output from an earlier run into every channel (reading-side test).
        src_exp, src_ch = cfg["replay_from"], cfg.get("replay_channel", "A1")
        src = sorted(p.parent for p in (ROOT / "results" / src_exp).glob("2*/summary.json"))[-1]
        for line in gzip.open(ROOT / "results_raw" / src_exp / src.name / "records.jsonl.gz", "rt"):
            rec = json.loads(line)
            if rec["channel"] == src_ch and "error" not in rec:
                replay[rec["task_id"]] = rec["agents"]["researcher"]["reply"]
        (run_dir / "replay_source.txt").write_text(f"results/{src_exp}/{src.name} channel {src_ch}\n")
    work = raw_dir / "workspaces"
    out_f = gzip.open(raw_dir / "records.jsonl.gz", "wt")
    rows, done = [], 0

    async def one(i, task, ch):
        nonlocal done
        client = clients[i % len(clients)]
        async with sems[i % len(clients)]:
            try:
                rec = await run_task(task, ch, client, work, cfg.get("max_turns", 12),
                                     tuple(cfg.get("chain", ["researcher", "writer", "reviewer"])),
                                     cfg.get("researchers", 1), replay.get(task.task_id) if replay else None,
                                     cfg.get("normalize_paths", False))
            except Exception as e:  # keep going; a failed run is recorded, not dropped
                rec = {"task_id": task.task_id, "channel": ch, "dataset": task.dataset, "k": len(task.questions),
                       "error": f"{type(e).__name__}: {e}"[:500], "agents": {}, "stage": {}}
        rec["seed"] = int(task.task_id.split("-s")[1].split("-")[0])
        rec["server"] = client.url
        if "error" not in rec:
            rec["score"] = score_run(rec, task.questions)
        out_f.write(json.dumps(rec) + "\n")
        row = {k: rec[k] for k in ("task_id", "channel", "dataset", "k", "seed")}
        row["wall_s"] = rec.get("wall_s", 0)
        row["error"] = rec.get("error", "")
        row.update({k: v for k, v in rec.get("score", {}).items() if k != "preds"})
        rows.append(row)
        done += 1
        if done % 20 == 0 or done == len(jobs):
            print(f"{done}/{len(jobs)} runs", flush=True)

    await asyncio.gather(*(one(i, t, ch) for i, (t, ch) in enumerate(jobs)))
    out_f.close()
    for c in clients:
        await c.aclose()
    if work.exists():
        with tarfile.open(raw_dir / "workspaces.tar.gz", "w:gz") as tar:
            tar.add(work, arcname="workspaces")
        shutil.rmtree(work)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("config")
    ap.add_argument("--n-tasks", type=int, help="override n_tasks (smoke runs)")
    ap.add_argument("--urls", nargs="*", help="override the config's servers")
    ap.add_argument("--gpus", nargs="*", type=int, help="GPUs behind --urls (recorded only)")
    a = ap.parse_args()
    cfg = yaml.safe_load(Path(a.config).read_text())
    if a.urls:
        cfg["server"]["base_url"], cfg["server"]["base_urls"] = a.urls[0], a.urls
    if a.gpus:
        cfg["server"]["gpu"], cfg["server"]["gpus"] = a.gpus[0], a.gpus
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
    t_start = dt.datetime.now()
    rows = asyncio.run(run(cfg, run_dir, raw_dir))
    # Whole-run wall time: with one channel per server this is that channel's serving time for the task set.
    (run_dir / "run_time.json").write_text(json.dumps({"start": t_start.isoformat(timespec="seconds"),
                                                       "end": dt.datetime.now().isoformat(timespec="seconds"),
                                                       "elapsed_s": round((dt.datetime.now() - t_start).total_seconds(), 1)}))
    with gzip.open(raw_dir / "rows.jsonl.gz", "wt") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    (run_dir / "summary.json").write_text(json.dumps(summarize(rows), indent=1))
    print(f"done: {run_dir}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
