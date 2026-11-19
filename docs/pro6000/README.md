# Running the PRO 6000 experiments

Two experiments that need a GPU with more memory than an RTX 3090:

| Run | Fixed | Varied | Configs | Runs |
| --- | --- | --- | --- | --- |
| P1 cache capacity | Qwen3-8B, k = 8 tasks of `t08_k8` (first 50 per dataset), six concurrent runs | KV cache 34,864 / 100k / 400k tokens | `configs/p01_cache_*.yaml` | 3 x 600 |
| P2 model size | k = 3 tasks of `t07_main` (first 100 per dataset), 100k-token KV cache | Qwen3-4B / 8B / 14B / 32B | `configs/p02_size_*.yaml` | 4 x 1200 |

`scripts/queue_pro6000.sh <gpu>` runs both, then judges every run with Qwen3-8B. The tasks are drawn from the
same seeds as the RTX 3090 runs, so results pair with them task by task.

## Setup (once)

1. Clone and branch. Results go to the `pro6000` branch, never to `main`.
   ```bash
   git clone <repo> cs632 && cd cs632 && git switch -c pro6000
   ```
2. Local paths. Create `env.local.sh` (not committed) with large files on a disk that has about 150 GB free:
   ```bash
   export STORE=/path/with/space/cs632-store
   export HF_HOME=$STORE/hf UV_CACHE_DIR=$STORE/uv-cache PIP_CACHE_DIR=$STORE/pip-cache
   export VLLM_CACHE_ROOT=$STORE/vllm-cache TRITON_CACHE_DIR=$STORE/triton-cache TMPDIR=$STORE/tmp
   export VLLM_BIN=$STORE/venv/bin/vllm
   export MODEL=Qwen/Qwen3-8B
   ```
   Then `mkdir -p $STORE/{hf,tmp,data,logs,results_raw}` and link `data`, `logs`, `results_raw` into the repo.
3. Environment (one venv for client and server; vLLM 0.33.0 as on the RTX 3090 runs):
   ```bash
   source env.local.sh
   uv venv -p 3.12 $STORE/venv && ln -sfn $STORE/venv .venv
   uv pip install -p .venv/bin/python "vllm==0.33.0" pyarrow
   uv pip install -p .venv/bin/python -e ".[dev]"
   .venv/bin/python -c "import vllm, torch; print(vllm.__version__, torch.cuda.get_device_name(0))"
   .venv/bin/python -m pytest -q
   ```
   If vLLM 0.33.0 does not start on this GPU (Blackwell), stop and report; do not change versions silently.
4. Data (about 85 MB):
   ```bash
   mkdir -p data/raw
   curl -sL -o data/raw/hotpot_distractor_validation.parquet \
     https://huggingface.co/datasets/hotpotqa/hotpot_qa/resolve/main/distractor/validation-00000-of-00001.parquet
   curl -sL -o data/raw/2wiki_dev.json \
     https://huggingface.co/datasets/voidful/2WikiMultihopQA/resolve/main/dev.json
   ```
5. Models (about 125 GB; check `df -h` first): `hf download Qwen/Qwen3-4B`, `Qwen/Qwen3-8B`, `Qwen/Qwen3-14B`,
   `Qwen/Qwen3-32B` (safetensors only; the repos have no other weights).

## Checks before the long run

- Smoke: `scripts/serve.sh <gpu> 8200`, then `.venv/bin/python -m agentipc.run configs/t01_smoke.yaml --urls
  http://localhost:8200 --gpus <gpu> --n-tasks 1`; expect 0 errors. Stop the server by its PID
  (`logs/vllm_gpu<gpu>.pid`). Move the smoke run to `results/_failed/` with a note, as it is not a result.
- KV override: start with `KV_BLOCKS=2179` and check the log says `GPU KV cache size: 34,864 tokens`.
- Qwen3-32B with `KV_BLOCKS=6250` and `GPU_UTIL=0.95` must load; if it does not, use 5,000 blocks (80k tokens)
  for **all** P2 sizes, edit the queue before starting it, and say so in the report.

## Run

```bash
nohup scripts/queue_pro6000.sh <gpu> > logs/queue_pro6000.log 2>&1 &
scripts/watchdog.sh queue_pro6000:<queue pid>:<gpu>     # wakes on each finished job, a dead queue, or a hang
```

Expect several hours. Never edit a queue script while it runs; kill by PID only.

## After

- `python -m agentipc.report results/<exp>/<run>` per run; commit `results/p0*/` (config, env, summaries), never
  `results_raw/`; push the `pro6000` branch.
- Report per run: errors, accuracy and tokens sent/computed per channel, and anything odd.
