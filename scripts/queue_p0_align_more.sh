#!/usr/bin/env bash
# Follow-up AlignScore lanes on GPUs that are still busy: each lane waits for a PID, then scores its runs.
# Usage: scripts/queue_p0_align_more.sh "gpu:wait_pid:exp,exp" ...
cd "$(dirname "$0")/.."
source env.local.sh
log() { echo "$(date +%H:%M:%S) $*"; }
one() {  # gpu exp
  local g=$1 e=$2 R P S
  R=$(ls -d results/$e/2*/ | tail -1); P=$STORE/factcheck/$e.jsonl; S=$STORE/factcheck/${e}_as.jsonl
  [ -s "$P" ] || .venv/bin/python -m agentipc.factpairs --export "$R" "$P" > /dev/null 2>&1 || { log "EXPORT_FAIL $e"; return; }
  /mnt/sda/heojin/cs632-store/alignscore/venv/bin/python scripts/alignscore_score.py "$P" "$S" "$g" > logs/alignscore_$e.log 2>&1 \
    && .venv/bin/python -m agentipc.alignfacts "$R" "$S" > logs/alignfacts_$e.log 2>&1 && log "done $e gpu$g $(wc -l < $P) pairs" \
    || log "SCORE_FAIL $e"
}
pids=()
for spec in "$@"; do
  IFS=: read -r g w exps <<< "$spec"
  ( while kill -0 "$w" 2>/dev/null; do sleep 30; done
    IFS=, read -ra list <<< "$exps"; for e in "${list[@]}"; do one "$g" "$e"; done ) &
  pids+=($!)
done
for p in "${pids[@]}"; do wait "$p"; done
log QUEUE_DONE
