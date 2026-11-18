#!/usr/bin/env bash
# GPU 6 alone, alongside the main queue: batched reads (Bb), the 24-turn check, the large-payload run
# (k=16, parallel Researchers) and fan-out at k=3; each judged on the same server, then the server stops.
cd "$(dirname "$0")/.."
source env.local.sh
PY=.venv/bin/python
URL=http://localhost:8103
log() { echo "$(date +%H:%M:%S) $*"; }
mkdir -p logs/g6
scripts/serve.sh 6 8103
mv logs/vllm_gpu6.pid logs/g6/vllm.pid   # keep it out of stop_servers.sh, which the main queue calls
for i in $(seq 1 90); do curl -sf "$URL/v1/models" > /dev/null && break; sleep 10; done
curl -sf "$URL/v1/models" > /dev/null || { log "SERVER_FAIL g6"; kill "$(cat logs/g6/vllm.pid)"; exit 1; }
log "server up g6"
for c in t08_batch t08_turns24 t08_large t08_fanout; do
  $PY -m agentipc.run "configs/$c.yaml" --urls $URL --gpus 6 > "logs/$c.log" 2>&1 || log "RUN_FAIL $c"
  R=$(grep "^done:" "logs/$c.log" | awk '{print $2}')
  [ -n "$R" ] && $PY -m agentipc.judge_all "$R" --urls $URL > "logs/judge_$c.log" 2>&1 && log "done $c $R"
done
kill "$(cat logs/g6/vllm.pid)"
for i in $(seq 1 60); do [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i 6)" -lt 1000 ] && break; sleep 5; done
log "server stopped g6: $(nvidia-smi --query-gpu=memory.used --format=csv,noheader -i 6)"
log QUEUE_DONE
