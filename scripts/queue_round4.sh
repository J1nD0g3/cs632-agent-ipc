#!/usr/bin/env bash
# Round-4 runs on the PRO 6000 (E1 p05, E2 p08, E3 p06, E4 p07, E5 p09). One worker per GPU; each worker takes
# the next unclaimed job from the shared list below. Every run gets a freshly started server with the
# 100,000-token KV cache (6,250 blocks; GPU_UTIL 0.92, 0.95 for Qwen3-32B), and the server log must say
# "GPU KV cache size: 100,000 tokens" before the run starts; otherwise the worker stops the server and exits.
# A job pinned to a GPU (E3: all six p06 runs on one GPU, one at a time) is taken only by that GPU's worker.
# Before each server start the worker waits until the GPU is empty, so nothing else shares it. No judge.
# Each job appends one line to logs/round4_ledger.tsv (cfg, run dir, gpu, model, blocks, KV line, server log,
# start, end).
# Usage: nohup scripts/queue_round4.sh <gpu> <port> <e3_gpu> > logs/queue_round4_g<gpu>.log 2>&1 &
cd "$(dirname "$0")/.."
source env.local.sh
GPU=${1:?gpu index}
PORT=${2:?port}
E3_GPU=${3:?gpu for the p06 runs}
URL=http://localhost:$PORT
PY=.venv/bin/python
CLAIMS=logs/round4_claims
LEDGER=logs/round4_ledger.tsv
BLOCKS=6250
KV_EXPECT="GPU KV cache size: 100,000 tokens"
mkdir -p "$CLAIMS"
log() { echo "$(date +%H:%M:%S) $*"; }
echo "pid $$ gpu $GPU port $PORT"

# config:model:served_name:gpu_util:pin  (pin "E3" = only the E3 GPU; longest jobs first among the rest)
JOBS=(
  p06_alone_A1:Qwen/Qwen3-8B:qwen3-8b:0.92:E3
  p06_alone_A1zc:Qwen/Qwen3-8B:qwen3-8b:0.92:E3
  p06_alone_A2:Qwen/Qwen3-8B:qwen3-8b:0.92:E3
  p06_alone_B:Qwen/Qwen3-8B:qwen3-8b:0.92:E3
  p06_alone_C:Qwen/Qwen3-8B:qwen3-8b:0.92:E3
  p06_alone_D:Qwen/Qwen3-8B:qwen3-8b:0.92:E3
  p08_norm_32b:Qwen/Qwen3-32B:qwen3-32b:0.95:
  p07_k16_kv100k:Qwen/Qwen3-8B:qwen3-8b:0.92:
  p05_a1w_32b:Qwen/Qwen3-32B:qwen3-32b:0.95:
  p05_a1r_32b:Qwen/Qwen3-32B:qwen3-32b:0.95:
  p09_zcreplay_8b:Qwen/Qwen3-8B:qwen3-8b:0.92:
  p09_zcreplay_4b:Qwen/Qwen3-4B:qwen3-4b:0.92:
  p07_k16_b24:Qwen/Qwen3-8B:qwen3-8b:0.92:
  p05_a1w_14b:Qwen/Qwen3-14B:qwen3-14b:0.92:
  p05_a1r_14b:Qwen/Qwen3-14B:qwen3-14b:0.92:
  p05_a1w_8b:Qwen/Qwen3-8B:qwen3-8b:0.92:
  p05_a1r_8b:Qwen/Qwen3-8B:qwen3-8b:0.92:
  p05_a1w_4b:Qwen/Qwen3-4B:qwen3-4b:0.92:
  p05_a1r_4b:Qwen/Qwen3-4B:qwen3-4b:0.92:
)

claim() { ( set -o noclobber; echo "$GPU $(date +%s)" > "$CLAIMS/$1" ) 2>/dev/null; }
gpu_mem() { nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i "$GPU"; }
down() {
  kill "$(cat logs/vllm_gpu$GPU.pid)" 2>/dev/null
  for i in $(seq 1 60); do [ "$(gpu_mem)" -lt 2000 ] && break; sleep 5; done
  log "server stopped; GPU $GPU memory $(gpu_mem) MiB"
}

for spec in "${JOBS[@]}"; do
  IFS=: read -r cfg model name util pin <<< "$spec"
  [ "$pin" = E3 ] && [ "$GPU" != "$E3_GPU" ] && continue
  claim "$cfg" || continue
  until [ "$(gpu_mem)" -lt 1000 ]; do sleep 30; done          # nothing else on this GPU
  out=$(SERVE_MODEL=$model SERVED_NAME=$name KV_BLOCKS=$BLOCKS GPU_UTIL=$util scripts/serve.sh "$GPU" "$PORT")
  slog=$(echo "$out" | awk '{print $4}')
  log "start $cfg on GPU $GPU ($model, server $slog)"
  ok=0; for i in $(seq 1 120); do curl -sf "$URL/v1/models" | grep -q "\"$name\"" && { ok=1; break; }; sleep 10; done
  if [ $ok != 1 ]; then log "SERVER_FAIL $cfg"; down; touch "$CLAIMS/$cfg.finished"; log "WORKER_STOP"; exit 1; fi
  kv=$(grep -oE "GPU KV cache size: [0-9,]+ tokens" "$slog" | head -1)
  if [ "$kv" != "$KV_EXPECT" ]; then
    log "KV_MISMATCH $cfg: '$kv'; run not started"; down; touch "$CLAIMS/$cfg.finished"; log "WORKER_STOP"; exit 1
  fi
  log "server up $name: $kv"
  t0=$(date '+%F %T')
  if $PY -m agentipc.run "configs/$cfg.yaml" --urls "$URL" --gpus "$GPU" > "logs/$cfg.log" 2>&1; then
    R=$(grep '^done:' "logs/$cfg.log" | awk '{print $2}'); log "done $cfg $R"
  else
    R="RUN_FAIL"; log "RUN_FAIL $cfg"
  fi
  t1=$(date '+%F %T')
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$cfg" "$R" "$GPU" "$model" "$BLOCKS" "$kv" "$slog" "$t0" "$t1" >> "$LEDGER"
  touch "$CLAIMS/$cfg.finished"
  down
done
log QUEUE_DONE
