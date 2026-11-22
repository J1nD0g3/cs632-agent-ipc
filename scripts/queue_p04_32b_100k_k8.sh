#!/usr/bin/env bash
# p04: Qwen3-32B with the 100,000-token KV cache (6,250 blocks) on the k=8 tasks of P1 (same as p03 otherwise).
# Serves on <gpu>:8200, checks the KV size, runs, stops the server by PID. No judge.
# Usage: nohup scripts/queue_p04_32b_100k_k8.sh <gpu> > logs/queue_p04_32b_100k_k8.log 2>&1 &
cd "$(dirname "$0")/.."
source env.local.sh
GPU=${1:?gpu index}
PORT=8200
URL=http://localhost:$PORT
PY=.venv/bin/python
C=p04_32b_100k_k8
log() { echo "$(date +%H:%M:%S) $*"; }
down() {
  kill "$(cat logs/vllm_gpu$GPU.pid)" 2>/dev/null
  for i in $(seq 1 60); do [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i "$GPU")" -lt 2000 ] && break; sleep 5; done
  log "server stopped; GPU $GPU memory $(nvidia-smi --query-gpu=memory.used --format=csv,noheader -i "$GPU")"
}
echo "pid $$ gpu $GPU port $PORT"
out=$(SERVE_MODEL=Qwen/Qwen3-32B SERVED_NAME=qwen3-32b KV_BLOCKS=6250 GPU_UTIL=0.95 scripts/serve.sh "$GPU" "$PORT")
SLOG=$(echo "$out" | awk '{print $4}')
log "serve: $out"
ok=0; for i in $(seq 1 120); do curl -sf "$URL/v1/models" | grep -q qwen3-32b && { ok=1; break; }; sleep 10; done
[ $ok = 1 ] || { log "SERVER_FAIL qwen3-32b"; down; log QUEUE_DONE; exit 1; }
KV=$(grep -oE "GPU KV cache size: [0-9,]+ tokens" "$SLOG" | head -1)
log "server up qwen3-32b: $KV"
[ "$KV" = "GPU KV cache size: 100,000 tokens" ] || { log "KV_MISMATCH ($KV); not running"; down; log QUEUE_DONE; exit 1; }
log "start $C on GPU $GPU"
t0=$(date +%s)
$PY -m agentipc.run "configs/$C.yaml" --urls "$URL" --gpus "$GPU" > "logs/$C.log" 2>&1 \
  && log "done $C $(grep '^done:' "logs/$C.log" | awk '{print $2}') wall $(( ($(date +%s) - t0) / 60 )) min" \
  || log "RUN_FAIL $C wall $(( ($(date +%s) - t0) / 60 )) min"
down
log QUEUE_DONE
