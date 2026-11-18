#!/usr/bin/env bash
# After the GPU 6 tail: re-judge the main run with the per-question judge (adds judge-based failure
# types), on GPU 6 alone, then stop its server. The old judged file is kept beside the new one.
cd "$(dirname "$0")/.."
source env.local.sh
PY=.venv/bin/python
log() { echo "$(date +%H:%M:%S) $*"; }
until grep -qE "QUEUE_DONE|FAIL" logs/queue_g6_tail.log; do sleep 60; done
R=$(ls -d results/t07_main/2*/ | tail -1)
RAW=results_raw/t07_main/$(basename "$R")
cp "$RAW/judged.jsonl.gz" "$RAW/judged_v1.jsonl.gz"
cp "$R/summary_judge.json" "$R/summary_judge_v1.json"
mkdir -p logs/g6
scripts/serve.sh 6 8103
mv logs/vllm_gpu6.pid logs/g6/vllm.pid
for i in $(seq 1 90); do curl -sf http://localhost:8103/v1/models > /dev/null && break; sleep 10; done
curl -sf http://localhost:8103/v1/models > /dev/null || { log "SERVER_FAIL g6"; kill "$(cat logs/g6/vllm.pid)"; exit 1; }
$PY -m agentipc.judge_all "$R" --urls http://localhost:8103 --concurrency 24 > logs/judge_t07_main_v2.log 2>&1 \
  && log "done judge t07_main v2" || log "JUDGE_FAIL t07_main v2"
kill "$(cat logs/g6/vllm.pid)"
for i in $(seq 1 60); do [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i 6)" -lt 1000 ] && break; sleep 5; done
log "server stopped g6: $(nvidia-smi --query-gpu=memory.used --format=csv,noheader -i 6)"
log QUEUE_DONE
