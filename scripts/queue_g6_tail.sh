#!/usr/bin/env bash
# Finish GPU 6: wait for the running k=16 job (its queue script was stopped so fan-out could move to
# the morning queue), judge it on the same server, then stop the GPU 6 server.
cd "$(dirname "$0")/.."
source env.local.sh
PY=.venv/bin/python
URL=http://localhost:8103
log() { echo "$(date +%H:%M:%S) $*"; }
while kill -0 "$1" 2>/dev/null; do sleep 60; done
R=$(grep "^done:" logs/t08_large.log | awk '{print $2}')
if [ -n "$R" ]; then
  $PY -m agentipc.judge_all "$R" --urls $URL > logs/judge_t08_large.log 2>&1 && log "done t08_large $R" || log "JUDGE_FAIL t08_large"
else
  log "RUN_FAIL t08_large"
fi
kill "$(cat logs/g6/vllm.pid)"
for i in $(seq 1 60); do [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i 6)" -lt 1000 ] && break; sleep 5; done
log "server stopped g6: $(nvidia-smi --query-gpu=memory.used --format=csv,noheader -i 6)"
log QUEUE_DONE
