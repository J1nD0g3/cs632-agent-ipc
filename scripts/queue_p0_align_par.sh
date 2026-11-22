#!/usr/bin/env bash
# AlignScore for the PRO 6000 runs, one worker per GPU. Usage: scripts/queue_p0_align_par.sh "gpu:exp,exp" ...
# The p01_cache_35k scorer started by queue_p0_align.sh is finished here (alignfacts) once its output exists.
cd "$(dirname "$0")/.."
source env.local.sh
log() { echo "$(date +%H:%M:%S) $*"; }
one() {  # gpu exp
  local g=$1 e=$2 R P S
  R=$(ls -d results/$e/2*/ | tail -1); P=$STORE/factcheck/$e.jsonl; S=$STORE/factcheck/${e}_as.jsonl
  [ -s "$P" ] || .venv/bin/python -m agentipc.factpairs --export "$R" "$P" > /dev/null 2>&1 || { log "EXPORT_FAIL $e"; return; }
  "$STORE"/alignscore/venv/bin/python scripts/alignscore_score.py "$P" "$S" "$g" > logs/alignscore_$e.log 2>&1 \
    && .venv/bin/python -m agentipc.alignfacts "$R" "$S" > logs/alignfacts_$e.log 2>&1 && log "done $e gpu$g $(wc -l < $P) pairs" \
    || log "SCORE_FAIL $e"
}
pids=()
for spec in "$@"; do
  g=${spec%%:*}
  ( IFS=, read -ra list <<< "${spec#*:}"; for e in "${list[@]}"; do one "$g" "$e"; done ) &
  pids+=($!)
done
# The orphaned p01_cache_35k scorer: wait for it, then build its metrics.
( while pgrep -f "alignscore_score.py .*p01_cache_35k.jsonl" > /dev/null; do sleep 30; done
  R=$(ls -d results/p01_cache_35k/2*/ | tail -1); S=$STORE/factcheck/p01_cache_35k_as.jsonl
  [ -s "$S" ] && .venv/bin/python -m agentipc.alignfacts "$R" "$S" > logs/alignfacts_p01_cache_35k.log 2>&1 \
    && log "done p01_cache_35k gpu5" || log "SCORE_FAIL p01_cache_35k" ) &
pids+=($!)
for p in "${pids[@]}"; do wait "$p"; done
log QUEUE_DONE
