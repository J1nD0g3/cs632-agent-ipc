#!/usr/bin/env bash
# Scope controls on GPU 5: run t09_scope, stop the server, then score its facts with AlignScore.
cd "$(dirname "$0")/.."
source env.local.sh
log() { echo "$(date +%H:%M:%S) $*"; }
for i in $(seq 1 90); do curl -sf http://localhost:8100/v1/models > /dev/null && break; sleep 10; done
.venv/bin/python -m agentipc.run configs/t09_scope.yaml --urls http://localhost:8100 --gpus 5 > logs/t09_scope.log 2>&1 \
  || log "RUN_FAIL t09_scope"
R=$(grep "^done:" logs/t09_scope.log | awk '{print $2}')
scripts/stop_servers.sh > /dev/null
[ -n "$R" ] || exit 1
log "done t09_scope $R"
.venv/bin/python -m agentipc.factpairs --export "$R" "$STORE/factcheck/t09_scope.jsonl" > /dev/null
"$STORE"/alignscore/venv/bin/python scripts/alignscore_score.py \
  "$STORE/factcheck/t09_scope.jsonl" "$STORE/factcheck/t09_scope_as.jsonl" 5 > logs/alignscore_t09_scope.log 2>&1 \
  && .venv/bin/python -m agentipc.alignfacts "$R" "$STORE/factcheck/t09_scope_as.jsonl" > /dev/null && log "done alignscore t09_scope" \
  || log "SCORE_FAIL t09_scope"
log QUEUE_DONE
