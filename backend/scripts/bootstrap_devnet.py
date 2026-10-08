"""Bootstrap devnet: service wallet + SOL, mock USDC mint and the program Config.

Usage (from backend/): uv run python scripts/bootstrap_devnet.py
Idempotent: reuses SERVICE_KEYPAIR / MOCK_USDC_MINT from .env when set.
Never change SERVICE_KEYPAIR afterwards: it is the Config treasury and the mock mint authority.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solders.keypair import Keypair
from solders.system_program import CreateAccountParams, create_account

from pixactions_api.config import Settings
from pixactions_api.solana.constants import PROGRAM_ID, TOKEN_PROGRAM_ID
from pixactions_api.solana.gateway import RpcSolanaGateway
from pixactions_api.solana.instructions import initialize_config_ix
from pixactions_api.solana.pda import config_pda
from pixactions_api.solana.spl import MINT_SIZE, initialize_mint2_ix
from pixactions_api.solana.tx import build_tx

MIN_LAMPORTS = 1_000_000_000


async def send(gateway: RpcSolanaGateway, ixs, payer: Keypair, *signers: Keypair) -> str:
    tx = build_tx(ixs, payer.pubkey(), await gateway.latest_blockhash())
    tx.partial_sign([payer, *signers], tx.message.recent_blockhash)
    return await gateway.send_and_confirm(tx)


async def main() -> int:
    s = Settings()
    service = Keypair.from_base58_string(s.service_keypair) if s.service_keypair else Keypair()
    gateway = RpcSolanaGateway(s.solana_rpc_url)
    async with AsyncClient(s.solana_rpc_url, commitment=Confirmed) as client:
        if (await client.get_balance(service.pubkey())).value < MIN_LAMPORTS:
            try:
                sig = (await client.request_airdrop(service.pubkey(), 2 * MIN_LAMPORTS)).value
                await client.confirm_transaction(sig, commitment=Confirmed)
            except Exception as exc:  # noqa: BLE001 (devnet faucet is rate limited)
                print(f"Airdrop falhou ({exc}).")
                print(f"Envie SOL de devnet para {service.pubkey()} em https://faucet.solana.com e rode de novo com:")
                print(f"SERVICE_KEYPAIR={service}")
                return 1
        mint = s.mock_usdc_mint
        if not mint:
            mint_kp = Keypair()
            rent = (await client.get_minimum_balance_for_rent_exemption(MINT_SIZE)).value
            await send(
                gateway,
                [
                    create_account(CreateAccountParams(
                        from_pubkey=service.pubkey(), to_pubkey=mint_kp.pubkey(), lamports=rent,
                        space=MINT_SIZE, owner=TOKEN_PROGRAM_ID,
                    )),
                    initialize_mint2_ix(mint=mint_kp.pubkey(), decimals=6, mint_authority=service.pubkey()),
                ],
                service,
                mint_kp,
            )
            mint = str(mint_kp.pubkey())
    if await gateway.get_account_data(config_pda()) is None:
        await send(
            gateway,
            [initialize_config_ix(payer=service.pubkey(), admin=service.pubkey(), fee_bps=100, treasury=service.pubkey())],
            service,
        )
    print("# Cole em backend/.env (e nas env vars da Vercel):")
    print(f"SERVICE_KEYPAIR={service}")
    print(f"MOCK_USDC_MINT={mint}")
    print(f"# program={PROGRAM_ID} config={config_pda()} service={service.pubkey()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
