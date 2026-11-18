#!/usr/bin/env bash
# After queue_t08b: parallel Researchers (fan-out) at k=3, a large-payload run (k=16, fan-out), and a
# 24-turn budget check for the file channels; judge each, then stop the servers.
cd "$(dirname "$0")/.."
source env.local.sh
PY=.venv/bin/python
URLS="http://localhost:8100 http://localhost:8101 http://localhost:8102"
log() { echo "$(date +%H:%M:%S) $*"; }
until grep -qE "QUEUE_DONE|FAIL|SKIP" logs/queue_t08b.log; do sleep 60; done
grep -qE "FAIL|SKIP" logs/queue_t08b.log && { log "SKIP: queue_t08b failed"; exit 1; }
for g in 5:8100 1:8101 2:8102; do scripts/serve.sh "${g%:*}" "${g#*:}"; done
for i in $(seq 1 90); do
  ok=0; for u in $URLS; do curl -sf "$u/v1/models" > /dev/null && ok=$((ok+1)); done
  [ "$ok" = 3 ] && break; sleep 10
done
[ "$ok" = 3 ] || { log "SERVER_FAIL"; scripts/stop_servers.sh; exit 1; }
for c in t08_fanout t08_turns24 t08_large; do
  $PY -m agentipc.run "configs/$c.yaml" > "logs/$c.log" 2>&1 || log "RUN_FAIL $c"
  R=$(grep "^done:" "logs/$c.log" | awk '{print $2}')
  [ -n "$R" ] && $PY -m agentipc.judge_all "$R" --urls $URLS > "logs/judge_$c.log" 2>&1 && log "done $c $R"
done
scripts/stop_servers.sh
log QUEUE_DONE
