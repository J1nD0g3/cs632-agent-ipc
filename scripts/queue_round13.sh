#!/usr/bin/env bash
# Round-10 runs (p16_store_*), claim-based over several GPUs; same per-run steps as scripts/queue_round8_multi.sh:
# fresh server per config (6,250 blocks; GPU_UTIL 0.92, 0.95 for 32B), KV line must be 100,000 tokens, ledger line.
# Usage: nohup scripts/queue_round13.sh <gpu> <port> > logs/queue_round13_g<gpu>.log 2>&1 &
cd "$(dirname "$0")/.."
source env.local.sh
GPU=${1:?gpu index}
PORT=${2:?port}
URL=http://localhost:$PORT
PY=.venv/bin/python
LEDGER=logs/round13_ledger.tsv
CLAIMS=logs/round13_claims
EXPECT="GPU KV cache size: 100,000 tokens"
mkdir -p "$CLAIMS"
log() { echo "$(date +%H:%M:%S) $*"; }
echo "pid $$ gpu $GPU port $PORT"
claim() { ( set -o noclobber; echo "$GPU $(date +%s)" > "$CLAIMS/$1" ) 2>/dev/null; }
gpu_mem() { nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i "$GPU"; }
down() {
  kill "$(cat logs/vllm_gpu$GPU.pid)" 2>/dev/null
  for i in $(seq 1 60); do [ "$(gpu_mem)" -lt 2000 ] && break; sleep 5; done
  log "server stopped; GPU $GPU memory $(gpu_mem) MiB"
}
up() {  # model -> sets SLOG, KV; exits on failure
  local model=$1 name util out ok
  name=$(echo "${model#Qwen/}" | tr 'A-Z' 'a-z'); util=0.92; [ "$model" = Qwen/Qwen3-32B ] && util=0.95
  until [ "$(gpu_mem)" -lt 1000 ]; do sleep 30; done
  out=$(SERVE_MODEL=$model SERVED_NAME=$name KV_BLOCKS=6250 GPU_UTIL=$util scripts/serve.sh "$GPU" "$PORT")
  SLOG=$(echo "$out" | awk '{print $4}')
  log "serve $model (util $util) on GPU $GPU, server $SLOG"
  ok=0; for i in $(seq 1 120); do curl -sf "$URL/v1/models" | grep -q "\"$name\"" && { ok=1; break; }; sleep 10; done
  [ $ok = 1 ] || { log "SERVER_FAIL $model"; down; log WORKER_STOP; exit 1; }
  KV=$(grep -oE "GPU KV cache size: [0-9,]+ tokens" "$SLOG" | head -1)
  [ "$KV" = "$EXPECT" ] || { log "KV_MISMATCH $model: '$KV'; no run started"; down; log WORKER_STOP; exit 1; }
  log "server up $name: $KV"
}
run() {  # cfg model
  local cfg=$1 model=$2 mc t0 t1 R
  mc=$(curl -s "$URL/metrics" | grep -c request_prefill_time)
  log "start $cfg on GPU $GPU (metrics request_prefill_time lines: $mc)"
  t0=$(date '+%F %T')
  if $PY -m agentipc.run "configs/$cfg.yaml" --urls "$URL" --gpus "$GPU" > "logs/$cfg.log" 2>&1; then
    R=$(grep '^done:' "logs/$cfg.log" | awk '{print $2}'); log "done $cfg $R"
  else
    R=RUN_FAIL; log "RUN_FAIL $cfg"
  fi
  t1=$(date '+%F %T')
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$cfg" "$R" "$GPU" "$model" 6250 "$KV" "$SLOG" "$t0" "$t1" "$mc" >> "$LEDGER"
}

for spec in p18_first_14b:Qwen/Qwen3-14B; do
  cfg=${spec%%:*}; model=${spec#*:}
  claim "$cfg" || continue
  up "$model"
  run "$cfg" "$model"
  down
done
log QUEUE_DONE
