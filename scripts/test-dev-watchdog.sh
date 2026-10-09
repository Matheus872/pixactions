#!/usr/bin/env bash
# Teste do watchdog: com um teto baixo de memória, o validador local precisa ser derrubado em até 90 s.
# Uso: ./scripts/test-dev-watchdog.sh   (sai com 0 se o watchdog funcionou)
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"
TMP=$(mktemp -d)

setsid -f solana-test-validator --reset --quiet --ledger "$TMP/ledger" --rpc-port 18899 --gossip-port 18000 \
  --faucet-port 19900 --dynamic-port-range 18100-18200 >"$TMP/validator.log" 2>&1 </dev/null
sleep 5
PID=$(pgrep -f -- "--ledger $TMP/ledger" | head -1)
[ -n "$PID" ] || { echo "FAIL: validador de teste não subiu"; exit 1; }

VALIDATOR_MAX_MB=150 WATCHDOG_INTERVAL=3 WATCHDOG_PATTERN="--ledger $TMP/ledger" \
  timeout 90 "$ROOT/scripts/dev-watchdog.sh" >"$TMP/watchdog.log" 2>&1 &
WD=$!

for _ in $(seq 1 30); do
  if ! kill -0 "$PID" 2>/dev/null; then
    echo "PASS: watchdog derrubou o validador ($(tail -1 "$TMP/watchdog.log"))"
    kill "$WD" 2>/dev/null
    exit 0
  fi
  sleep 3
done

kill "$PID" "$WD" 2>/dev/null
echo "FAIL: validador continuou rodando acima do teto"
exit 1
