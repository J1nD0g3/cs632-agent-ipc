#!/usr/bin/env bash
# After queue_t08: cache-pressure check on the large-payload tasks. Same model and tasks as t08_large
# (which ran 6 concurrent runs per server); here 1 and 2 concurrent runs, one level per GPU, in parallel.
cd "$(dirname "$0")/.."
source env.local.sh
PY=.venv/bin/python
log() { echo "$(date +%H:%M:%S) $*"; }
until grep -qE "QUEUE_DONE|FAIL" logs/queue_t08.log; do sleep 60; done
grep -q FAIL logs/queue_t08.log && { log "SKIP: queue_t08 failed"; exit 1; }
scripts/serve.sh 5 8100; scripts/serve.sh 1 8101
for i in $(seq 1 90); do
  ok=0; for u in http://localhost:8100 http://localhost:8101; do curl -sf "$u/v1/models" > /dev/null && ok=$((ok+1)); done
  [ "$ok" = 2 ] && break; sleep 10
done
[ "$ok" = 2 ] || { log "SERVER_FAIL"; scripts/stop_servers.sh; exit 1; }
log "servers up"
run_one() {  # $1 config, $2 url, $3 gpu
  $PY -m agentipc.run "configs/$1.yaml" --urls "$2" --gpus "$3" > "logs/$1.log" 2>&1 || { log "RUN_FAIL $1"; return; }
  R=$(grep "^done:" "logs/$1.log" | awk '{print $2}')
  $PY -m agentipc.judge_all "$R" --urls "$2" > "logs/judge_$1.log" 2>&1 && log "done $1 $R" || log "JUDGE_FAIL $1"
}
run_one t08_pressure_c1 http://localhost:8100 5 &
p1=$!
run_one t08_pressure_c2 http://localhost:8101 1 &
p2=$!
wait $p1 $p2
scripts/stop_servers.sh
log QUEUE_DONE
