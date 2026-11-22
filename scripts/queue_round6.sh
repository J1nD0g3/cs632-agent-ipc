#!/usr/bin/env bash
# Round-6 runs on the PRO 6000 (p10-p13). One worker per GPU; phases follow the requested priority:
#   1. p10_write_{32b,14b,8b,4b}       shared list, any GPU
#   2. p11_alone_* (12 timing runs)     timing GPU only, one at a time, after phase 1 is finished everywhere
#   3. p12_k16_clobber, p13_k8_fanout   shared list, any GPU, after phase 2
#   4. p11_c32_* (6 timing runs)        timing GPU only, one at a time, after phase 3 is finished everywhere
# Timing runs use the order in logs/round6_timing_order.txt (shuffled once, recorded). While a timing run is in
# progress no other run of ours is on the host; other users' GPU processes and the load average are sampled
# every 15 s into logs/round6_hostmon_<cfg>.log and summarized in the ledger.
# Every run gets a freshly started server; the "GPU KV cache size" line must match the intended size
# (6,250 blocks = 100,000 tokens; 25,000 blocks = 400,000 tokens for p11_c32), else the worker stops.
# Before each run: curl <url>/metrics | grep -c request_prefill_time (logged; METRICS_ZERO if 0). No judge.
# Ledger: logs/round6_ledger.tsv (cfg, run dir, gpu, model, blocks, KV line, server log, start, end,
#   prefill_metric_count, host_other).
# Usage: nohup scripts/queue_round6.sh <gpu> <port> <timing_gpu> > logs/queue_round6_g<gpu>.log 2>&1 &
cd "$(dirname "$0")/.."
source env.local.sh
GPU=${1:?gpu index}
PORT=${2:?port}
TGPU=${3:?timing gpu}
URL=http://localhost:$PORT
PY=.venv/bin/python
CLAIMS=logs/round6_claims
LEDGER=logs/round6_ledger.tsv
ORDER=logs/round6_timing_order.txt
mkdir -p "$CLAIMS"
log() { echo "$(date +%H:%M:%S) $*"; }
echo "pid $$ gpu $GPU port $PORT timing_gpu $TGPU"

P1=(p10_write_32b p10_write_14b p10_write_8b p10_write_4b)
P3=(p12_k16_clobber p13_k8_fanout)
P2=($(grep '^p11_alone_' "$ORDER"))
P4=($(grep '^p11_c32_' "$ORDER"))
[ ${#P2[@]} = 12 ] && [ ${#P4[@]} = 6 ] || { log "ORDER_FILE_BAD"; log "WORKER_STOP"; exit 1; }

model_of() { case $1 in *_32b) echo Qwen/Qwen3-32B;; *_14b) echo Qwen/Qwen3-14B;; *_4b) echo Qwen/Qwen3-4B;; *) echo Qwen/Qwen3-8B;; esac; }
claim() { ( set -o noclobber; echo "$GPU $(date +%s)" > "$CLAIMS/$1" ) 2>/dev/null; }
gpu_mem() { nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i "$GPU"; }
all_finished() { for c in "$@"; do [ -e "$CLAIMS/$c.finished" ] || return 1; done; }
down() {
  kill "$(cat logs/vllm_gpu$GPU.pid)" 2>/dev/null
  for i in $(seq 1 60); do [ "$(gpu_mem)" -lt 2000 ] && break; sleep 5; done
  log "server stopped; GPU $GPU memory $(gpu_mem) MiB"
}
stop_worker() { down; touch "$CLAIMS/$1.finished"; log "WORKER_STOP"; exit 1; }
hostmon() {  # sample everything else on the host while a timing run is going
  local f=$1
  while :; do
    {
      echo "== $(date '+%F %T') load $(cut -d' ' -f1-3 /proc/loadavg)"
      nvidia-smi --query-gpu=index,utilization.gpu,memory.used --format=csv,noheader
      for p in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader); do
        echo "app $(ps -o pid=,user=,comm= -p "$p" 2>/dev/null) gpu_uuid $(nvidia-smi --query-compute-apps=pid,gpu_uuid --format=csv,noheader | awk -F', ' -v p="$p" '$1==p{print $2}')"
      done
    } >> "$f"
    sleep 15
  done
}
host_summary() {  # other GPU processes (not our server on this GPU) seen during the run
  local f=$1 me
  me=$(nvidia-smi --query-gpu=uuid --format=csv,noheader -i "$GPU")
  local other
  other=$(grep '^app ' "$f" | grep -v "$me" | awk '{print $3"("$2")"}' | sort -u | tr '\n' ' ')
  local busy
  busy=$(grep -E '^[0-9], ' "$f" | awk -F', ' -v g="$GPU" '$1!=g && $2+0>0 {print "GPU"$1}' | sort -u | tr '\n' ' ')
  local n; n=$(grep -c '^== ' "$f")
  if [ -z "$other" ] && [ -z "$busy" ]; then echo "none (no other GPU process in $n samples)"; else echo "OTHER: procs ${other:-none}; busy ${busy:-none} ($n samples)"; fi
}

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

# Phase 1
for c in "${P1[@]}"; do claim "$c" && job "$c"; done
until all_finished "${P1[@]}"; do sleep 30; done
# Phase 2 (timing GPU only)
if [ "$GPU" = "$TGPU" ]; then
  log "phase 2: ${#P2[@]} timing runs, nothing else of ours on the host"
  for c in "${P2[@]}"; do claim "$c" && job "$c" timing; done
  touch "$CLAIMS/phase2.done"
fi
until [ -e "$CLAIMS/phase2.done" ]; do sleep 30; done
# Phase 3
for c in "${P3[@]}"; do claim "$c" && job "$c"; done
# Phase 4 (timing GPU only)
if [ "$GPU" = "$TGPU" ]; then
  until all_finished "${P3[@]}"; do sleep 30; done
  log "phase 4: ${#P4[@]} timing runs (400k cache, 32 at a time), nothing else of ours on the host"
  for c in "${P4[@]}"; do claim "$c" && job "$c" timing; done
fi
log QUEUE_DONE
