#!/usr/bin/env bash
# Stop this project's vLLM servers by PID and wait until their GPUs are free.
cd "$(dirname "$0")/.."
GPUS=$(ls logs/vllm_gpu*.pid 2>/dev/null | sed -E 's/.*gpu([0-9]+).pid/\1/' | tr '\n' ' ')
for f in logs/vllm_gpu*.pid; do
  [ -f "$f" ] || continue
  pid=$(cat "$f")
  if kill -0 "$pid" 2>/dev/null; then kill "$pid"; echo "stopped $pid ($f)"; fi
  rm -f "$f"
done
for i in $(seq 1 60); do
  used=$(for g in $GPUS; do nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i "$g"; done | awk '$1 > 1000' | wc -l)
  [ "$used" = "0" ] && break
  sleep 5
done
echo "servers stopped; GPUs $GPUS: $(for g in $GPUS; do nvidia-smi --query-gpu=memory.used --format=csv,noheader -i "$g"; done | tr '\n' ' ')"
