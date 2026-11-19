#!/usr/bin/env bash
# Round-1 review experiments. GPU 1 (its server moved out of stop_servers.sh's reach) starts at once with
# A1w; when the morning queue ends, GPUs 5 and 2 join for the Researcher replay and the A/A repeat.
# Every run is judged on the same servers; all servers stop at the end.
cd "$(dirname "$0")/.."
source env.local.sh
PY=.venv/bin/python
log() { echo "$(date +%H:%M:%S) $*"; }
run_judge() {  # $1 config, $2.. urls
  local c=$1; shift
  $PY -m agentipc.run "configs/$c.yaml" --urls "$@" > "logs/$c.log" 2>&1 || { log "RUN_FAIL $c"; return; }
  R=$(grep "^done:" "logs/$c.log" | awk '{print $2}')
  $PY -m agentipc.judge_all "$R" --urls "$@" > "logs/judge_$c.log" 2>&1 && log "done $c $R" || log "JUDGE_FAIL $c"
}
run_judge t09_a1w http://localhost:8101
until grep -qE "QUEUE_DONE|FAIL|SKIP" logs/queue_morning.log; do sleep 60; done
scripts/serve.sh 5 8100; scripts/serve.sh 2 8102
for i in $(seq 1 90); do
  ok=0; for p in 8100 8102; do curl -sf "http://localhost:$p/v1/models" > /dev/null && ok=$((ok+1)); done
  [ "$ok" = 2 ] && break; sleep 10
done
[ "$ok" = 2 ] || log "SERVER_FAIL 5/2 (continuing on GPU 1 only)"
URLS="http://localhost:8101"; [ "$ok" = 2 ] && URLS="http://localhost:8100 http://localhost:8101 http://localhost:8102"
log "servers: $URLS"
run_judge t09_replay $URLS
run_judge t09_repeat $URLS
scripts/stop_servers.sh
kill "$(cat logs/g1/vllm.pid)"; rm -f logs/g1/vllm.pid
for i in $(seq 1 60); do [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i 1)" -lt 1000 ] && break; sleep 5; done
log "servers stopped: GPUs 5 1 2: $(for g in 5 1 2; do nvidia-smi --query-gpu=memory.used --format=csv,noheader -i $g; done | tr '\n' ' ')"
log QUEUE_DONE
