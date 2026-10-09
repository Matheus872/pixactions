#!/usr/bin/env bash
# Sobe o ambiente local completo: validador Solana (com o programa), API (porta 8001) e web (porta 3000).
# Uso: ./scripts/dev-up.sh        Logs em /tmp/pixactions-dev/   Para desligar: ./scripts/dev-down.sh
# O validador começa do zero a cada execução; a carteira de serviço e o mint de teste da localnet
# são recriados e gravados em backend/.env (apenas quando SOLANA_RPC_URL aponta para 127.0.0.1).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOGS=/tmp/pixactions-dev
PROGRAM_ID=DZ5ddra1TXhkbS9ZBnimtZPVeTxoXmxbCGvFHJqKVPa9
export PATH="$HOME/.local/bin:$HOME/.local/share/solana/install/active_release/bin:$HOME/.bun/bin:$PATH"
mkdir -p "$LOGS"

wait_for() { # wait_for <descrição> <comando...>
  local what=$1; shift
  for _ in $(seq 1 90); do "$@" >/dev/null 2>&1 && { echo "  ✓ $what"; return 0; }; sleep 2; done
  echo "  ✗ $what não respondeu; veja $LOGS"; exit 1
}

if ! grep -q "^SOLANA_RPC_URL=http://127.0.0.1:8899" "$ROOT/backend/.env"; then
  echo "backend/.env não aponta para a localnet (SOLANA_RPC_URL=http://127.0.0.1:8899). Abortando." >&2
  exit 1
fi

echo "1/4 validador local"
FRESH=0
if ! solana -u localhost cluster-version >/dev/null 2>&1; then
  FRESH=1
  setsid -f solana-test-validator --reset --quiet --ledger "$LOGS/ledger" \
    --bpf-program "$PROGRAM_ID" "$ROOT/onchain/target/deploy/pixactions.so" \
    >"$LOGS/validator.log" 2>&1 </dev/null
fi
wait_for "validador em http://127.0.0.1:8899" solana -u localhost cluster-version
pgrep -f "^bash [^ ]*scripts/dev-watchdog\.sh$" >/dev/null || \
  setsid -f "$ROOT/scripts/dev-watchdog.sh" >>"$LOGS/watchdog.log" 2>&1 </dev/null
echo "  ✓ watchdog de memória ativo (derruba o validador se a memória livre cair abaixo de 700 MB)"

echo "2/4 carteira de serviço e USDC de teste"
if [ "$FRESH" = 1 ]; then
(cd "$ROOT/backend" && SERVICE_KEYPAIR= MOCK_USDC_MINT= uv run python scripts/bootstrap_devnet.py >"$LOGS/bootstrap.txt" 2>&1)
python3 - "$ROOT/backend/.env" "$LOGS/bootstrap.txt" <<'EOF'
import re, sys
from pathlib import Path
env, boot = Path(sys.argv[1]), Path(sys.argv[2]).read_text()
vals = dict(l.split("=", 1) for l in boot.splitlines() if l.startswith(("SERVICE_KEYPAIR=", "MOCK_USDC_MINT=")))
if len(vals) != 2:
    sys.exit("bootstrap falhou: veja " + sys.argv[2])
text = env.read_text()
for key, value in vals.items():
    text = re.sub(rf"^{key}=.*$", f"{key}={value}", text, flags=re.M)
env.write_text(text)
print("  ✓ backend/.env atualizado")
EOF
rm -f "$ROOT/backend/dev.db"
  # A API em execução (se houver) leu o .env antigo: reinicia.
  for pid in $(ss -ltnpH 'sport = :8001' 2>/dev/null | grep -o 'pid=[0-9]*' | cut -d= -f2); do kill "$pid"; done
  sleep 1
else
  echo "  ✓ validador já estava no ar: mantendo carteira de serviço e mint atuais"
fi

echo "3/4 API"
if ! curl -s -m 3 localhost:8001/health >/dev/null 2>&1; then
  setsid -f bash -c "cd '$ROOT/backend' && exec uv run uvicorn pixactions_api.main:app --port 8001" \
    >"$LOGS/api.log" 2>&1 </dev/null
fi
wait_for "API em http://localhost:8001 (docs em /docs)" curl -sf -m 3 localhost:8001/health

echo "4/4 web"
if ! curl -s -m 3 -o /dev/null localhost:3000 2>/dev/null; then
  setsid -f bash -c "cd '$ROOT/web' && exec npx next dev" >"$LOGS/web.log" 2>&1 </dev/null
fi
wait_for "web em http://localhost:3000" curl -sf -m 60 -o /dev/null localhost:3000/dashboard

echo "Pronto: abra http://localhost:3000/dashboard"
echo "Ao terminar de testar, rode ./scripts/dev-down.sh (o validador consome memória enquanto está ligado)."
