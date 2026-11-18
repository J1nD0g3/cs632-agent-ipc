#!/usr/bin/env bash
# After queue_t08: run the batched-read channel (Bb) on the main run's first 100 k=3 tasks, judge, stop.
cd "$(dirname "$0")/.."
source env.local.sh
PY=.venv/bin/python
URLS="http://localhost:8100 http://localhost:8101 http://localhost:8102"
log() { echo "$(date +%H:%M:%S) $*"; }
until grep -qE "QUEUE_DONE|FAIL" logs/queue_t08.log; do sleep 60; done
grep -q FAIL logs/queue_t08.log && { log "SKIP: queue_t08 failed"; exit 1; }
for g in 5:8100 1:8101 2:8102; do scripts/serve.sh "${g%:*}" "${g#*:}"; done
for i in $(seq 1 90); do
  ok=0; for u in $URLS; do curl -sf "$u/v1/models" > /dev/null && ok=$((ok+1)); done
  [ "$ok" = 3 ] && break; sleep 10
done
[ "$ok" = 3 ] || { log "SERVER_FAIL"; scripts/stop_servers.sh; exit 1; }
$PY -m agentipc.run configs/t08_batch.yaml > logs/t08_batch.log 2>&1 || log "RUN_FAIL t08_batch"
R=$(grep "^done:" logs/t08_batch.log | awk '{print $2}')
[ -n "$R" ] && $PY -m agentipc.judge_all "$R" --urls $URLS > logs/judge_t08_batch.log 2>&1 && log "done t08_batch $R"
scripts/stop_servers.sh
log QUEUE_DONE
