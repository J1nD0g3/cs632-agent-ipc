#!/usr/bin/env bash
# Round-6 phase 3 on GPUs chosen by the user (1 and 2; GPU 3 is kept out of phase 3). Runs ONE config on <gpu>
# after the phase-2 timing runs are done (logs/round6_claims/phase2.done), with exactly the same per-run steps as
# scripts/queue_round6.sh: fresh server, KV check (100,000 tokens), /metrics check, run, ledger line, .finished,
# server stopped. The claim files for p12/p13 were created by the operator so the queue_round6.sh workers skip them;
# the GPU 3 worker starts phase 4 only after both have .finished.
# Usage: nohup scripts/queue_round6_p3.sh <gpu> <port> <cfg> > logs/queue_round6_p3_g<gpu>.log 2>&1 &
cd "$(dirname "$0")/.."
source env.local.sh
GPU=${1:?gpu index}
PORT=${2:?port}
CFG=${3:?config}
URL=http://localhost:$PORT
PY=.venv/bin/python
CLAIMS=logs/round6_claims
LEDGER=logs/round6_ledger.tsv
log() { echo "$(date +%H:%M:%S) $*"; }
echo "pid $$ gpu $GPU port $PORT cfg $CFG"
model_of() { case $1 in *_32b) echo Qwen/Qwen3-32B;; *_14b) echo Qwen/Qwen3-14B;; *_4b) echo Qwen/Qwen3-4B;; *) echo Qwen/Qwen3-8B;; esac; }
gpu_mem() { nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i "$GPU"; }
down() {
  kill "$(cat logs/vllm_gpu$GPU.pid)" 2>/dev/null
  for i in $(seq 1 60); do [ "$(gpu_mem)" -lt 2000 ] && break; sleep 5; done
  log "server stopped; GPU $GPU memory $(gpu_mem) MiB"
}
stop_worker() { down; touch "$CLAIMS/$1.finished"; log "WORKER_STOP"; exit 1; }
job() {  # cfg [timing]
  local cfg=$1 timing=$2 model name util blocks expect out slog ok kv mc t0 t1 R mon hpid hs
  model=$(model_of "$cfg"); name=$(echo "${model#Qwen/}" | tr 'A-Z' 'a-z')
  util=0.92; [ "$model" = Qwen/Qwen3-32B ] && util=0.95
  blocks=6250; expect="GPU KV cache size: 100,000 tokens"
  case $cfg in p11_c32_*) blocks=25000; expect="GPU KV cache size: 400,000 tokens";; esac
  until [ "$(gpu_mem)" -lt 1000 ]; do sleep 30; done
  out=$(SERVE_MODEL=$model SERVED_NAME=$name KV_BLOCKS=$blocks GPU_UTIL=$util scripts/serve.sh "$GPU" "$PORT")
  slog=$(echo "$out" | awk '{print $4}')
  log "start $cfg on GPU $GPU ($model, blocks $blocks, server $slog)"
  ok=0; for i in $(seq 1 120); do curl -sf "$URL/v1/models" | grep -q "\"$name\"" && { ok=1; break; }; sleep 10; done
  [ $ok = 1 ] || { log "SERVER_FAIL $cfg"; stop_worker "$cfg"; }
  kv=$(grep -oE "GPU KV cache size: [0-9,]+ tokens" "$slog" | head -1)
  [ "$kv" = "$expect" ] || { log "KV_MISMATCH $cfg: '$kv' (expected '$expect'); run not started"; stop_worker "$cfg"; }
  mc=$(curl -s "$URL/metrics" | grep -c request_prefill_time)
  log "server up $name: $kv; metrics request_prefill_time lines: $mc"
  [ "$mc" -gt 0 ] || log "METRICS_ZERO $cfg (request_prefill_time not found in /metrics)"
  hs="-"
  if [ -n "$timing" ]; then mon=logs/round6_hostmon_$cfg.log; : > "$mon"; hostmon "$mon" & hpid=$!; fi
  t0=$(date '+%F %T')
  if $PY -m agentipc.run "configs/$cfg.yaml" --urls "$URL" --gpus "$GPU" > "logs/$cfg.log" 2>&1; then
    R=$(grep '^done:' "logs/$cfg.log" | awk '{print $2}'); log "done $cfg $R"
  else
    R=RUN_FAIL; log "RUN_FAIL $cfg"
  fi
  t1=$(date '+%F %T')
  if [ -n "$timing" ]; then kill "$hpid" 2>/dev/null; wait "$hpid" 2>/dev/null; hs=$(host_summary "$mon"); log "host during $cfg: $hs"; fi
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$cfg" "$R" "$GPU" "$model" "$blocks" "$kv" "$slog" "$t0" "$t1" "$mc" "$hs" >> "$LEDGER"
  touch "$CLAIMS/$cfg.finished"
  down
}
until [ -e "$CLAIMS/phase2.done" ]; do sleep 30; done
log "phase 3: $CFG on GPU $GPU"
job "$CFG"
log QUEUE_DONE
