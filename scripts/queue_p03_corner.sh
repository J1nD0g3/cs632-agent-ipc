#!/usr/bin/env bash
# p03 corner cell: Qwen3-32B with the 34,864-token KV cache (2,179 blocks) on the k=8 tasks of P1.
# Expects the Qwen3-32B server already up on <gpu>:8200 (KV checked by the operator); runs, stops the
# server, then judges with Qwen3-8B (default KV size) like every other run.
# Usage: nohup scripts/queue_p03_corner.sh <gpu> > logs/queue_p03_corner.log 2>&1 &
cd "$(dirname "$0")/.."
source env.local.sh
GPU=${1:?gpu index}
PORT=8200
URL=http://localhost:$PORT
PY=.venv/bin/python
C=p03_corner_32b_35k
log() { echo "$(date +%H:%M:%S) $*"; }
down() {
  kill "$(cat logs/vllm_gpu$GPU.pid)" 2>/dev/null
  for i in $(seq 1 60); do [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i "$GPU")" -lt 2000 ] && break; sleep 5; done
}
echo "pid $$ gpu $GPU port $PORT"
curl -sf "$URL/v1/models" | grep -q qwen3-32b || { log "SERVER_FAIL qwen3-32b not serving on $URL"; exit 1; }
log "start $C on GPU $GPU"
t0=$(date +%s)
$PY -m agentipc.run "configs/$C.yaml" --urls "$URL" --gpus "$GPU" > "logs/$C.log" 2>&1 \
  && log "done $C $(grep '^done:' "logs/$C.log" | awk '{print $2}') wall $(( ($(date +%s) - t0) / 60 )) min" \
  || log "RUN_FAIL $C wall $(( ($(date +%s) - t0) / 60 )) min"
down
R=$(grep "^done:" "logs/$C.log" 2>/dev/null | awk '{print $2}')
if [ -n "$R" ]; then
  SERVE_MODEL=Qwen/Qwen3-8B SERVED_NAME=qwen3-8b KV_BLOCKS= GPU_UTIL=0.92 scripts/serve.sh "$GPU" "$PORT" > /dev/null
  ok=0; for i in $(seq 1 120); do curl -sf "$URL/v1/models" > /dev/null && { ok=1; break; }; sleep 10; done
  if [ $ok = 1 ]; then
    log "server up qwen3-8b (judge)"
    $PY -m agentipc.judge_all "$R" --urls "$URL" > "logs/judge_$C.log" 2>&1 && log "done judge $C" || log "JUDGE_FAIL $C"
  else
    log "SERVER_FAIL qwen3-8b (judge)"
  fi
  down
fi
log QUEUE_DONE
