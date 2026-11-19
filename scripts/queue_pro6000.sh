#!/usr/bin/env bash
# PRO 6000 runs (one GPU): P1 fixes the model (Qwen3-8B) and varies only the KV cache size; P2 fixes the
# cache (100k tokens) and varies the model size. Every run is judged afterwards with Qwen3-8B.
# Usage: scripts/queue_pro6000.sh <gpu>     (port 8200; logs/queue_pro6000.log via nohup)
cd "$(dirname "$0")/.."
source env.local.sh
GPU=${1:?gpu index}
PORT=8200
URL=http://localhost:$PORT
PY=.venv/bin/python
log() { echo "$(date +%H:%M:%S) $*"; }
up() {  # model served_name kv_blocks gpu_util
  SERVE_MODEL=$1 SERVED_NAME=$2 KV_BLOCKS=$3 GPU_UTIL=$4 scripts/serve.sh "$GPU" "$PORT" > /dev/null
  for i in $(seq 1 120); do curl -sf "$URL/v1/models" > /dev/null && { log "server up $2 kv=$3"; return 0; }; sleep 10; done
  log "SERVER_FAIL $2 kv=$3"; return 1
}
down() {
  kill "$(cat logs/vllm_gpu$GPU.pid)" 2>/dev/null
  for i in $(seq 1 60); do [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i "$GPU")" -lt 2000 ] && break; sleep 5; done
}
run() {  # config
  $PY -m agentipc.run "configs/$1.yaml" --urls "$URL" --gpus "$GPU" > "logs/$1.log" 2>&1 \
    && log "done $1 $(grep '^done:' "logs/$1.log" | awk '{print $2}')" || log "RUN_FAIL $1"
}
# P1: 2,179 blocks = 34,864 tokens (the RTX 3090 setting), then 100k and 400k tokens.
for spec in 35k:2179 100k:6250 400k:25000; do
  up Qwen/Qwen3-8B qwen3-8b "${spec#*:}" 0.92 && run "p01_cache_${spec%%:*}"; down
done
# P2: 6,250 blocks = 100k tokens for every size (32B needs most of the 96 GB).
for spec in 4b:Qwen/Qwen3-4B 8b:Qwen/Qwen3-8B 14b:Qwen/Qwen3-14B 32b:Qwen/Qwen3-32B; do
  util=0.92; [ "${spec%%:*}" = 32b ] && util=0.95
  up "${spec#*:}" "qwen3-${spec%%:*}" 6250 "$util" && run "p02_size_${spec%%:*}"; down
done
# Judge everything with Qwen3-8B, as on the RTX 3090 runs.
up Qwen/Qwen3-8B qwen3-8b "" 0.92 || exit 1
for c in p01_cache_35k p01_cache_100k p01_cache_400k p02_size_4b p02_size_8b p02_size_14b p02_size_32b; do
  R=$(grep "^done:" "logs/$c.log" 2>/dev/null | awk '{print $2}')
  [ -n "$R" ] && { $PY -m agentipc.judge_all "$R" --urls "$URL" > "logs/judge_$c.log" 2>&1 && log "done judge $c" || log "JUDGE_FAIL $c"; }
done
down
log QUEUE_DONE
