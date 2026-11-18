#!/usr/bin/env bash
# Exit (so the operator is woken) on the first event: a queue logs a new line (a job finished or
# failed), a queue process dies without QUEUE_DONE, or a busy queue's vLLM servers stop logging
# (a hang); also a heartbeat every BEAT_MIN minutes. Usage: scripts/watchdog.sh "<queue_name>:<pid>:<gpu list>" ...   e.g. queue_t08:123:5,1,2
cd "$(dirname "$0")/.."
STALL_MIN=${STALL_MIN:-12}
BEAT_MIN=${BEAT_MIN:-60}   # also wake up this often with a progress line, even without an event
START=$(date +%s)
declare -A seen
for spec in "$@"; do q=${spec%%:*}; seen[$q]=$(grep -cvE "^pid |^stopped " "logs/$q.log" 2>/dev/null); done
while true; do
  for spec in "$@"; do
    IFS=: read -r q pid gpus <<< "$spec"
    n=$(grep -cvE "^pid |^stopped " "logs/$q.log" 2>/dev/null)
    if [ "$n" != "${seen[$q]}" ]; then
      echo "EVENT $q: $(grep -vE '^pid |^stopped ' "logs/$q.log" | tail -n $((n - ${seen[$q]})) | tr '\n' ' ')"; exit 0
    fi
    if ! kill -0 "$pid" 2>/dev/null; then
      grep -q QUEUE_DONE "logs/$q.log" || { echo "DEAD $q: process $pid gone without QUEUE_DONE"; exit 0; }
      continue
    fi
    # A live queue is always running a job, a judge pass or a server start; its servers then log often.
    for g in ${gpus//,/ }; do
      f=$(ls -t logs/vllm_gpu${g}_*.log 2>/dev/null | head -1)
      [ -z "$f" ] && continue
      age=$(( ($(date +%s) - $(stat -c %Y "$f")) / 60 ))
      if [ "$age" -ge "$STALL_MIN" ]; then
        echo "STALL $q: $f silent for $age min"; exit 0
      fi
    done
  done
  if [ $(( ($(date +%s) - START) / 60 )) -ge "$BEAT_MIN" ]; then
    echo "HEARTBEAT $(for f in logs/t0*.log; do l=$(grep -E '^[0-9]+/[0-9]+ runs' "$f" | tail -1); [ -n "$l" ] && echo -n "$(basename "$f" .log): $l; "; done)"
    exit 0
  fi
  sleep 60
done
