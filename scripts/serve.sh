#!/usr/bin/env bash
# Start the vLLM server for this project: scripts/serve.sh <gpu> [port]
set -euo pipefail
cd "$(dirname "$0")/.."
source env.local.sh
GPU=${1:?gpu index}
PORT=${2:-8100}
export HF_HUB_OFFLINE=1
LOG=logs/vllm_gpu${GPU}_$(date +%Y%m%d_%H%M%S).log
CUDA_VISIBLE_DEVICES=$GPU nohup "$VLLM_BIN" serve "$MODEL" \
  --served-model-name qwen3-8b --port "$PORT" \
  --max-model-len 32768 --gpu-memory-utilization 0.90 \
  --enable-prefix-caching --enable-prompt-tokens-details \
  --enable-auto-tool-choice --tool-call-parser hermes \
  --seed 0 > "$LOG" 2>&1 &
echo "$!" > "logs/vllm_gpu${GPU}.pid"
echo "pid $! log $LOG"
