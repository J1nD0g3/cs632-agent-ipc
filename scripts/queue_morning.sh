#!/usr/bin/env bash
# After queue_t08, on GPUs 5, 1, 2 in parallel: cache pressure at 1 and 2 concurrent runs per server
# (k=16 tasks of t08_large), and fan-out at k=3 on 50 tasks paired with the main run. Judge, stop.
cd "$(dirname "$0")/.."
source env.local.sh
PY=.venv/bin/python
log() { echo "$(date +%H:%M:%S) $*"; }
until grep -qE "QUEUE_DONE|FAIL" logs/queue_t08.log; do sleep 60; done
grep -q FAIL logs/queue_t08.log && { log "SKIP: queue_t08 failed"; exit 1; }
scripts/serve.sh 5 8100; scripts/serve.sh 1 8101; scripts/serve.sh 2 8102
for i in $(seq 1 90); do
  ok=0; for p in 8100 8101 8102; do curl -sf "http://localhost:$p/v1/models" > /dev/null && ok=$((ok+1)); done
  [ "$ok" = 3 ] && break; sleep 10
done
[ "$ok" = 3 ] || { log "SERVER_FAIL"; scripts/stop_servers.sh; exit 1; }
log "servers up"
run_one() {  # $1 config, $2 url, $3 gpu
  $PY -m agentipc.run "configs/$1.yaml" --urls "$2" --gpus "$3" > "logs/$1.log" 2>&1 || { log "RUN_FAIL $1"; return; }
  R=$(grep "^done:" "logs/$1.log" | awk '{print $2}')
  $PY -m agentipc.judge_all "$R" --urls "$2" > "logs/judge_$1.log" 2>&1 && log "done $1 $R" || log "JUDGE_FAIL $1"
}
run_one t08_pressure_c1 http://localhost:8100 5 & p1=$!
run_one t08_pressure_c2 http://localhost:8101 1 & p2=$!
run_one t08_fanout http://localhost:8102 2 & p3=$!
wait $p1 $p2 $p3
scripts/stop_servers.sh
log QUEUE_DONE
