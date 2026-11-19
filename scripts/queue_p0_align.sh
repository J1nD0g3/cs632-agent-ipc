#!/usr/bin/env bash
# AlignScore for the PRO 6000 runs on one GPU: export fact pairs, score them, build per-run metrics.
cd "$(dirname "$0")/.."
source env.local.sh
GPU=${1:?gpu}
log() { echo "$(date +%H:%M:%S) $*"; }
for e in p01_cache_35k p01_cache_100k p01_cache_400k p03_corner_32b_35k p02_size_4b p02_size_8b p02_size_14b p02_size_32b; do
  R=$(ls -d results/$e/2*/ | tail -1)
  P=$STORE/factcheck/$e.jsonl; S=$STORE/factcheck/${e}_as.jsonl
  .venv/bin/python -m agentipc.factpairs --export "$R" "$P" > /dev/null 2>&1 || { log "EXPORT_FAIL $e"; continue; }
  /mnt/sda/heojin/cs632-store/alignscore/venv/bin/python scripts/alignscore_score.py "$P" "$S" "$GPU" > logs/alignscore_$e.log 2>&1 \
    && .venv/bin/python -m agentipc.alignfacts "$R" "$S" > logs/alignfacts_$e.log 2>&1 && log "done $e $(wc -l < $P) pairs" \
    || log "SCORE_FAIL $e"
done
log QUEUE_DONE
