#!/usr/bin/env bash
# Protege o WSL: o solana-test-validator cresce ~130 MB/min sem limite. Este watchdog o derruba quando
#   - o validador passa de VALIDATOR_MAX_MB de memória (padrão 1200), ou
#   - a memória livre do sistema cai abaixo de MIN_AVAILABLE_MB (padrão 600).
# É iniciado pelo dev-up.sh e termina sozinho quando o validador para.
set -uo pipefail

MAX_MB=${VALIDATOR_MAX_MB:-1200}
MIN_FREE_MB=${MIN_AVAILABLE_MB:-600}
INTERVAL=${WATCHDOG_INTERVAL:-10}
PATTERN=${WATCHDOG_PATTERN:-solana-test-validator}

while true; do
  PID=$(pgrep -f -- "$PATTERN" | grep -v "^$$\$" | head -1)
  [ -z "$PID" ] && { echo "$(date +%T) validador não está rodando; watchdog encerrado"; exit 0; }
  RSS_MB=$(( $(ps -o rss= -p "$PID" 2>/dev/null || echo 0) / 1024 ))
  FREE_MB=$(awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo)
  if [ "$RSS_MB" -gt "$MAX_MB" ] || [ "$FREE_MB" -lt "$MIN_FREE_MB" ]; then
    kill "$PID"
    echo "$(date +%T) validador derrubado (uso ${RSS_MB}MB, livre ${FREE_MB}MB). Rode ./scripts/dev-up.sh para recomeçar."
    exit 0
  fi
  sleep "$INTERVAL"
done
