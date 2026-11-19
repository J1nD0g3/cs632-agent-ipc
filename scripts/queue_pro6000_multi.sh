#!/usr/bin/env bash
# Multi-GPU version of scripts/queue_pro6000.sh: the same seven runs with the same server settings
# (model, KV blocks, GPU_UTIL) and the same Qwen3-8B judge, spread over several GPUs.
# Start one worker per GPU; each worker takes the next unclaimed job from a shared list, so faster GPUs
# simply take more jobs. Every run gets a fresh server (as in queue_pro6000.sh). After the run jobs,
# workers judge finished runs; a worker waits while runs are still going on other GPUs.
# P2 waits for the gate file logs/pro6000_claims/p2_kv_blocks, written by the operator after the Qwen3-32B load
# check: it holds 6250 (100k tokens), or 5000 (80k) for all P2 sizes if 32B does not load with 6250 (see README).
# Usage: nohup scripts/queue_pro6000_multi.sh <gpu> <port> > logs/queue_pro6000_g<gpu>.log 2>&1 &
cd "$(dirname "$0")/.."
source env.local.sh
GPU=${1:?gpu index}
PORT=${2:?port}
URL=http://localhost:$PORT
PY=.venv/bin/python
CLAIMS=logs/pro6000_claims
mkdir -p "$CLAIMS"
log() { echo "$(date +%H:%M:%S) $*"; }
echo "pid $$ gpu $GPU port $PORT"

# config:model:served_name:kv_blocks:gpu_util   (identical to scripts/queue_pro6000.sh; P2 = gate file value)
JOBS=(
  p01_cache_35k:Qwen/Qwen3-8B:qwen3-8b:2179:0.92
  p01_cache_100k:Qwen/Qwen3-8B:qwen3-8b:6250:0.92
  p01_cache_400k:Qwen/Qwen3-8B:qwen3-8b:25000:0.92
  p02_size_32b:Qwen/Qwen3-32B:qwen3-32b:P2:0.95
  p02_size_14b:Qwen/Qwen3-14B:qwen3-14b:P2:0.92
  p02_size_8b:Qwen/Qwen3-8B:qwen3-8b:P2:0.92
  p02_size_4b:Qwen/Qwen3-4B:qwen3-4b:P2:0.92
)

claim() {  # atomically claim a job name; succeeds only for the first worker
  ( set -o noclobber; echo "$GPU $(date +%s)" > "$CLAIMS/$1" ) 2>/dev/null
}
model_ready() {  # weights fully downloaded (marker written by the download step)
  [ -e "$STORE/hf/ready_${1//\//--}" ]
}
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
  touch "$CLAIMS/$1.finished"
}

# Phase 1: runs.
for spec in "${JOBS[@]}"; do
  IFS=: read -r cfg model name kv util <<< "$spec"
  claim "$cfg" || continue
  until model_ready "$model"; do sleep 60; done
  if [ "${cfg%%_*}" = p02 ]; then
    until [ -s "$CLAIMS/p2_kv_blocks" ]; do sleep 60; done
    kv=$(cat "$CLAIMS/p2_kv_blocks")
  fi
  log "start $cfg on GPU $GPU"
  up "$model" "$name" "$kv" "$util" && run "$cfg" || touch "$CLAIMS/$cfg.finished"
  down
done

# Phase 2: judge every finished run with Qwen3-8B (default KV size, as in queue_pro6000.sh).
server=0
while :; do
  pending=0
  for spec in "${JOBS[@]}"; do
    cfg=${spec%%:*}
    [ -e "$CLAIMS/judge_$cfg" ] && continue
    if [ ! -e "$CLAIMS/$cfg.finished" ]; then pending=1; continue; fi
    R=$(grep "^done:" "logs/$cfg.log" 2>/dev/null | awk '{print $2}')
    if [ -z "$R" ]; then claim "judge_$cfg"; continue; fi   # failed run: nothing to judge
    claim "judge_$cfg" || continue
    if [ $server = 0 ]; then up Qwen/Qwen3-8B qwen3-8b "" 0.92 || { log "JUDGE_FAIL $cfg (server)"; touch "$CLAIMS/judge_$cfg.failed"; continue; }; server=1; fi
    $PY -m agentipc.judge_all "$R" --urls "$URL" > "logs/judge_$cfg.log" 2>&1 && log "done judge $cfg" || log "JUDGE_FAIL $cfg"
  done
  [ $pending = 0 ] && break
  # Nothing to judge right now: free the GPU while other workers are still running.
  [ $server = 1 ] && { down; server=0; }
  sleep 60
done
[ $server = 1 ] && down
log QUEUE_DONE
