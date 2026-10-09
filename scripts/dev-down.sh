#!/usr/bin/env bash
# Desliga o ambiente local (validador, watchdog, API na 8001 e web na 3000) e apaga o ledger temporário.
# Use sempre que parar de testar: o validador local consome memória sem parar enquanto está ligado.
set -uo pipefail

stop_port() {
  for pid in $(ss -ltnpH "sport = :$1" 2>/dev/null | grep -o 'pid=[0-9]*' | cut -d= -f2 | sort -u); do kill "$pid" 2>/dev/null; done
}

pkill -f "scripts/dev-watchdog.sh" 2>/dev/null
pkill -f "solana-test-validator --reset" 2>/dev/null
stop_port 8001
stop_port 3000
sleep 2
rm -rf /tmp/pixactions-dev/ledger
echo "Ambiente local desligado."
