#!/usr/bin/env bash
# Start the vLLM server for this project:
#   [SERVE_MODEL=.. SERVED_NAME=.. MAX_LEN=.. GPU_UTIL=.. KV_BLOCKS=..] scripts/serve.sh <gpu> [port]
# KV_BLOCKS fixes the KV cache size (16-token blocks) so runs on different GPUs see the same cache.
set -euo pipefail
cd "$(dirname "$0")/.."
source env.local.sh
mkdir -p logs
GPU=${1:?gpu index}
PORT=${2:-8100}
export HF_HUB_OFFLINE=1
export PATH="$(dirname "$VLLM_BIN"):$PATH"  # ninja and other build tools the server needs
LOG=logs/vllm_gpu${GPU}_$(date +%Y%m%d_%H%M%S).log
SERVE_MODEL=${SERVE_MODEL:-$MODEL}
SERVED_NAME=${SERVED_NAME:-qwen3-8b}
CUDA_VISIBLE_DEVICES=$GPU nohup "$VLLM_BIN" serve "$SERVE_MODEL" \
  --served-model-name "$SERVED_NAME" --port "$PORT" \
  --max-model-len "${MAX_LEN:-32768}" --gpu-memory-utilization "${GPU_UTIL:-0.90}" \
  ${KV_BLOCKS:+--num-gpu-blocks-override "$KV_BLOCKS"} \
  --enable-prefix-caching --enable-prompt-tokens-details \
  --enable-auto-tool-choice --tool-call-parser hermes \
  --seed 0 > "$LOG" 2>&1 &
echo "$!" > "logs/vllm_gpu${GPU}.pid"
echo "pid $! log $LOG"
