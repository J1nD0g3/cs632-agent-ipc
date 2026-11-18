#!/usr/bin/env bash
# After the main run: judge it, run the k=8 and four-agent sensitivity runs on Qwen3-8B,
# then Qwen3-4B, judge everything with Qwen3-8B, and stop the servers.
cd "$(dirname "$0")/.."
source env.local.sh
PY=.venv/bin/python
URLS="http://localhost:8100 http://localhost:8101 http://localhost:8102"
log() { echo "$(date +%H:%M:%S) $*"; }
run_dir() { grep "^done:" "logs/$1.log" | awk '{print $2}'; }
start_servers() {  # $1 model, $2 served name
  for g in 5:8100 1:8101 2:8102; do SERVE_MODEL=$1 SERVED_NAME=$2 scripts/serve.sh "${g%:*}" "${g#*:}"; done
  for i in $(seq 1 90); do
    ok=0; for u in $URLS; do curl -sf "$u/v1/models" > /dev/null && ok=$((ok+1)); done
    [ "$ok" = 3 ] && { log "servers up: $2"; return 0; }
    sleep 10
  done
  log "SERVER_FAIL $2"; return 1
}
run() {  # $1 config name
  $PY -m agentipc.run "configs/$1.yaml" > "logs/$1.log" 2>&1 || log "RUN_FAIL $1"
  [ -n "$(run_dir "$1")" ] && log "done $1 $(run_dir "$1")"
}
judge() {  # $1 config name
  local r; r=$(run_dir "$1"); [ -z "$r" ] && return
  $PY -m agentipc.judge_all "$r" --urls $URLS > "logs/judge_$1.log" 2>&1 && log "done judge $1" || log "JUDGE_FAIL $1"
}

until grep -qE "^done:|Traceback" logs/t07_main.log; do sleep 60; done
grep -q Traceback logs/t07_main.log && { log "RUN_FAIL t07_main"; exit 1; }
log "done t07_main $(run_dir t07_main)"
judge t07_main
run t08_k8; judge t08_k8
run t08_chain4; judge t08_chain4
scripts/stop_servers.sh
start_servers Qwen/Qwen3-4B qwen3-4b || exit 1
run t08_qwen4b
scripts/stop_servers.sh
start_servers Qwen/Qwen3-8B qwen3-8b || exit 1
judge t08_qwen4b
scripts/stop_servers.sh
log QUEUE_DONE
