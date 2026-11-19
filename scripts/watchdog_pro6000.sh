#!/usr/bin/env bash
# Watchdog for scripts/queue_pro6000_multi.sh workers. Exits (so the operator is woken) on the first event:
#   EVENT     a worker log gets a new line (a job started, finished or failed)
#   DEAD      a worker process is gone without QUEUE_DONE
#   STALL     a live vLLM server of a worker has not logged for STALL_MIN minutes
#   LOW_DISK  free space on the disk holding results_raw/logs below DISK_MIN_GB
#   LOW_SHM   free space in /dev/shm (models, venv) below SHM_MIN_GB
#   LOW_MEM   MemAvailable below MEM_MIN_GB (models in /dev/shm use RAM shared with other users)
#   HEARTBEAT every BEAT_MIN minutes, with per-run progress
# Usage: scripts/watchdog_pro6000.sh <worker_log_name>:<pid>:<gpu> ...
#   e.g. scripts/watchdog_pro6000.sh queue_pro6000_g2:123:2 queue_pro6000_g3:124:3
cd "$(dirname "$0")/.."
STALL_MIN=${STALL_MIN:-12}
BEAT_MIN=${BEAT_MIN:-60}
DISK_MIN_GB=${DISK_MIN_GB:-10}
SHM_MIN_GB=${SHM_MIN_GB:-30}
MEM_MIN_GB=${MEM_MIN_GB:-100}
START=$(date +%s)
declare -A seen
for spec in "$@"; do q=${spec%%:*}; seen[$q]=$(grep -cvE "^pid " "logs/$q.log" 2>/dev/null); done
avail_gb() { df -BG --output=avail "$1" | tail -1 | tr -dc 0-9; }
progress() {
  for f in logs/p0*.log; do
    [ -e "$f" ] || continue
    l=$(grep -E '^[0-9]+/[0-9]+ runs' "$f" | tail -1)
    grep -q '^done:' "$f" && l="done"
    echo -n "$(basename "$f" .log): ${l:-starting}; "
  done
}
while true; do
  for spec in "$@"; do
    IFS=: read -r q pid g <<< "$spec"
    n=$(grep -cvE "^pid " "logs/$q.log" 2>/dev/null)
    if [ "$n" != "${seen[$q]}" ]; then
      echo "EVENT $q: $(grep -vE '^pid ' "logs/$q.log" | tail -n $((n - ${seen[$q]})) | tr '\n' ' ')"; exit 0
    fi
    if ! kill -0 "$pid" 2>/dev/null; then
      grep -q QUEUE_DONE "logs/$q.log" || { echo "DEAD $q: process $pid gone without QUEUE_DONE"; exit 0; }
      continue
    fi
    # Only a live server counts: a worker may wait (for weights or other GPUs) with no server.
    spid=$(cat "logs/vllm_gpu$g.pid" 2>/dev/null)
    if [ -n "$spid" ] && kill -0 "$spid" 2>/dev/null; then
      f=$(ls -t logs/vllm_gpu${g}_*.log 2>/dev/null | head -1)
      if [ -n "$f" ]; then
        age=$(( ($(date +%s) - $(stat -c %Y "$f")) / 60 ))
        [ "$age" -ge "$STALL_MIN" ] && { echo "STALL $q: $f silent for $age min"; exit 0; }
      fi
    fi
  done
  d=$(avail_gb "$(readlink -f logs)"); [ "$d" -lt "$DISK_MIN_GB" ] && { echo "LOW_DISK ${d} GB free"; exit 0; }
  s=$(avail_gb /dev/shm); [ "$s" -lt "$SHM_MIN_GB" ] && { echo "LOW_SHM ${s} GB free"; exit 0; }
  m=$(( $(awk '/MemAvailable/ {print $2}' /proc/meminfo) / 1048576 ))
  [ "$m" -lt "$MEM_MIN_GB" ] && { echo "LOW_MEM ${m} GB available"; exit 0; }
  if [ $(( ($(date +%s) - START) / 60 )) -ge "$BEAT_MIN" ]; then
    echo "HEARTBEAT disk ${d}G shm ${s}G mem ${m}G | $(progress)"; exit 0
  fi
  sleep 60
done
