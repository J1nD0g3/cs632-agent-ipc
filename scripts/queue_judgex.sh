#!/usr/bin/env bash
# After queue_fix: cross-check the fact judge on the main run, Qwen3-8B (GPU 5) against
# Llama-3-8B-Instruct (GPU 1, from the cs506 model store, 8k context), then stop both servers.
cd "$(dirname "$0")/.."
source env.local.sh
log() { echo "$(date +%H:%M:%S) $*"; }
until grep -qE "QUEUE_DONE|FAIL" logs/queue_fix.log; do sleep 60; done
scripts/serve.sh 5 8100
SERVE_MODEL=/mnt/sda/heojin/cs506-store/hf/hub/models--meta-llama--Meta-Llama-3-8B-Instruct/snapshots/8afb486c1db24fe5011ec46dfbe5b5dccdb575c2/ SERVED_NAME=llama3-8b MAX_LEN=8192 scripts/serve.sh 1 8101
for i in $(seq 1 90); do
  ok=0; for p in 8100 8101; do curl -sf "http://localhost:$p/v1/models" > /dev/null && ok=$((ok+1)); done
  [ "$ok" = 2 ] && break; sleep 10
done
[ "$ok" = 2 ] || { log "SERVER_FAIL"; scripts/stop_servers.sh; exit 1; }
R=$(ls -d results/t07_main/2*/ | tail -1)
.venv/bin/python -m agentipc.judge_cross "$R" --qwen http://localhost:8100 --other http://localhost:8101 \
  --other-name llama3-8b --n 360 > logs/judge_cross.log 2>&1 && log "done judge_cross $R" || log "JUDGE_FAIL cross"
scripts/stop_servers.sh
log QUEUE_DONE
