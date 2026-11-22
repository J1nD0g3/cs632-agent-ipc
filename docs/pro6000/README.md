# Running on the RTX PRO 6000 server

The `p*` experiments ran on a second server with RTX PRO 6000 Blackwell Server Edition GPUs (96 GB), one GPU per
run. This note records how that server was set up and how the runs were queued, so they can be repeated. The
code, configs, and task draws are the same as on the RTX 3090 server, so the two servers' runs pair task by task.

The first batch, run by `scripts/queue_pro6000.sh` (one GPU) or `scripts/queue_pro6000_multi.sh` (several GPUs):

| Batch | Fixed | Varied | Configs | Pipelines |
| --- | --- | --- | --- | --- |
| Cache runs | Qwen3-8B, k = 8 tasks of `t08_k8` (first 50 per dataset), 6 pipelines at a time | KV cache 34,864 / 100,000 / 400,000 tokens | `configs/p01_cache_*.yaml` | 3 x 600 |
| Size runs | k = 3 tasks of `t07_main` (first 100 per dataset), 100,000-token KV cache | Qwen3-4B / 8B / 14B / 32B | `configs/p02_size_*.yaml` | 4 x 1,200 |

Later batches (`p03`-`p18`, see [../experiments.md](../experiments.md)) used the same server settings with one
fresh server per config; their queue scripts are `scripts/queue_p04_32b_100k_k8.sh` and
`scripts/queue_round*.sh`.

## Setup

1. Local paths. Create `env.local.sh` (not committed) that puts large files on a disk with about 150 GB free:
   ```bash
   export STORE=/path/with/space/cs632-store
   export HF_HOME=$STORE/hf UV_CACHE_DIR=$STORE/uv-cache PIP_CACHE_DIR=$STORE/pip-cache
   export VLLM_CACHE_ROOT=$STORE/vllm-cache TRITON_CACHE_DIR=$STORE/triton-cache TMPDIR=$STORE/tmp
   export VLLM_BIN=$STORE/venv/bin/vllm
   export MODEL=Qwen/Qwen3-8B
   ```
   Then `mkdir -p $STORE/{hf,tmp,data,logs,results_raw}` and link `data`, `logs`, and `results_raw` into the
   repository root.
2. One environment for client and server, with the same vLLM version as the RTX 3090 runs:
   ```bash
   source env.local.sh
   uv venv -p 3.12 $STORE/venv && ln -sfn $STORE/venv .venv
   uv pip install -p .venv/bin/python "vllm==0.33.0" pyarrow
   uv pip install -p .venv/bin/python -e ".[dev]"
   .venv/bin/python -c "import vllm, torch; print(vllm.__version__, torch.cuda.get_device_name(0))"
   .venv/bin/python -m pytest -q
   ```
3. Data (about 85 MB), as in the main README.
4. Models (about 125 GB in total): `hf download Qwen/Qwen3-4B`, `Qwen/Qwen3-8B`, `Qwen/Qwen3-14B`, and
   `Qwen/Qwen3-32B` (safetensors only).

## Checks before a long run

- Smoke test: `scripts/serve.sh <gpu> 8200`, then
  `.venv/bin/python -m agentipc.run configs/t01_smoke.yaml --urls http://localhost:8200 --gpus <gpu> --n-tasks 1`;
  expect no errors. Stop the server by its PID (`logs/vllm_gpu<gpu>.pid`) and move the smoke run to
  `results/_failed/` with a `notes.txt`, as it is not a result.
- KV size: start with `KV_BLOCKS=2179` and check that the server log says `GPU KV cache size: 34,864 tokens`.
  Every run's KV size and memory utilization, read from its server log, is recorded in
  `results/pro6000*_kv_used.txt`.
- Qwen3-32B with `KV_BLOCKS=6250` (100,000 tokens) needs `GPU_UTIL=0.95`. It loaded, so every size run used
  6,250 blocks; the fallback, had it not loaded, was 5,000 blocks for every size.

## Run

```bash
nohup scripts/queue_pro6000.sh <gpu> > logs/queue_pro6000.log 2>&1 &
scripts/watchdog.sh queue_pro6000:<queue pid>:<gpu>     # exits on a finished job, a dead queue, or a hang
```

A batch takes several hours. Bash reads a script as it runs, so a running queue script must not be edited; stop
a queue by its PID.

## After a run

- `python -m agentipc.report results/<exp>/<run_id>` prints the per-channel summary.
- `results/<exp>/<run_id>/` already holds the config, environment, and summaries. Copy the per-task files
  (`rows`, `records`, and, once scored, `judged` and `alignscore_rows`, see [../data.md](../data.md)) from
  `results_raw/<exp>/<run_id>/` next to them before committing; keep `workspaces.tar.gz` and server logs out of git.

## Fact scoring with AlignScore

Fact coverage is scored after the runs with AlignScore-large (Zha et al., ACL 2023), from
`records.jsonl.gz`. AlignScore needs its own environment: Python 3.10, `torch==1.13.1`, `numpy<2`,
`transformers>=4.30,<4.40`, `pytorch_lightning>=1.9,<2`, `spacy>=3.7,<3.8` with `en_core_web_sm-3.7.1`, `nltk`,
and `setuptools<70`. Install the official code with `uv pip install --no-deps` from a clone of
github.com/yuh-zha/AlignScore, put `AlignScore-large.ckpt` (huggingface.co/yzha/AlignScore) in
`$STORE/alignscore/ckpt/`, and keep NLTK's `punkt_tab` in a directory that is not group-writable (NLTK refuses
such directories). Then, per run:

```bash
.venv/bin/python -m agentipc.factpairs --export results/<exp>/<run_id> pairs.jsonl
$STORE/alignscore/venv/bin/python scripts/alignscore_score.py pairs.jsonl scored.jsonl <gpu>
.venv/bin/python -m agentipc.alignfacts results/<exp>/<run_id> scored.jsonl
```

`scripts/queue_p0_align*.sh` ran these steps for the PRO 6000 runs.
