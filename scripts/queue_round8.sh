#!/usr/bin/env bash
# Round-8 runs on one PRO 6000 GPU, one after another:
#   1. p14_read_{32b,14b,8b,4b}: one fresh server per config.
#   2. p15_k8_one then p15_k8_three: ONE Qwen3-8B server, back to back, not restarted between the two.
# Every server: KV_BLOCKS=6250 (100,000 tokens), GPU_UTIL 0.92 (0.95 for Qwen3-32B); the server log must say
# "GPU KV cache size: 100,000 tokens" before a run, else the queue stops the server and exits (KV_MISMATCH).
# Before each run: curl <url>/metrics | grep -c request_prefill_time (logged). No judge.
# Ledger: logs/round8_ledger.tsv (cfg, run dir, gpu, model, blocks, KV line, server log, start, end, metric lines).
# Usage: nohup scripts/queue_round8.sh <gpu> <port> > logs/queue_round8_g<gpu>.log 2>&1 &
cd "$(dirname "$0")/.."
source env.local.sh
GPU=${1:?gpu index}
PORT=${2:?port}
URL=http://localhost:$PORT
PY=.venv/bin/python
LEDGER=logs/round8_ledger.tsv
EXPECT="GPU KV cache size: 100,000 tokens"
log() { echo "$(date +%H:%M:%S) $*"; }
echo "pid $$ gpu $GPU port $PORT"
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

for spec in p14_read_32b:Qwen/Qwen3-32B p14_read_14b:Qwen/Qwen3-14B p14_read_8b:Qwen/Qwen3-8B p14_read_4b:Qwen/Qwen3-4B; do
  cfg=${spec%%:*}; model=${spec#*:}
  up "$model"; run "$cfg" "$model"; down
done
up Qwen/Qwen3-8B
run p15_k8_one Qwen/Qwen3-8B
run p15_k8_three Qwen/Qwen3-8B      # same server, not restarted
down
log QUEUE_DONE
