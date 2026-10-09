#!/usr/bin/env bash
# Protege o WSL: o solana-test-validator cresce ~130 MB/min sem limite. Este watchdog o derruba quando
#   - o validador passa de VALIDATOR_MAX_MB de memória (padrão 3000), ou
#   - a memória livre do sistema cai abaixo de MIN_AVAILABLE_MB (padrão 700): a proteção principal.
# É iniciado pelo dev-up.sh e termina sozinho quando o validador para.
set -uo pipefail

MAX_MB=${VALIDATOR_MAX_MB:-3000}
MIN_FREE_MB=${MIN_AVAILABLE_MB:-700}
INTERVAL=${WATCHDOG_INTERVAL:-10}
PATTERN=${WATCHDOG_PATTERN:-}

find_validator() {
  # Padrão: casa o executável pelo nome exato (comm), nunca por texto na linha de comando.
  if [ -n "$PATTERN" ]; then pgrep -f -- "$PATTERN" | grep -v "^$$\$"; else pgrep -x solana-test-val; fi
}

while true; do
  PID=$(find_validator | head -1)
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
