"""Devnet smoke: create event → fund buyer → buy → check in → double check-in rejected.

Usage (from backend/): uv run python scripts/smoke_devnet.py
"""

import asyncio
import secrets
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from solders.compute_budget import set_compute_unit_limit
from solders.keypair import Keypair
from solders.pubkey import Pubkey

from pixactions_api.config import Settings
from pixactions_api.errors import ApiError, ErrorCode
from pixactions_api.solana.accounts import decode_event, decode_ticket
from pixactions_api.solana.gateway import RpcSolanaGateway
from pixactions_api.solana.instructions import (
    buy_ticket_ix,
    check_in_ix,
    create_event_ix,
)
from pixactions_api.solana.pda import ata_address, event_pda, ticket_pda
from pixactions_api.solana.spl import create_ata_idempotent_ix, mint_to_ix
from pixactions_api.solana.tx import build_tx


async def send(gateway, ixs, payer: Keypair, *signers: Keypair) -> str:
    tx = build_tx(ixs, payer.pubkey(), await gateway.latest_blockhash())
    tx.partial_sign([payer, *signers], tx.message.recent_blockhash)
    return await gateway.send_and_confirm(tx)


async def main() -> None:
    s = Settings()
    service = Keypair.from_base58_string(s.service_keypair)
    gw = RpcSolanaGateway(s.solana_rpc_url)
    mint = Pubkey.from_string(s.mock_usdc_mint)
    organizer, buyer = Keypair(), Keypair()
    event_id, price = secrets.randbits(63), 1_000_000
    event = event_pda(organizer.pubkey(), event_id)
    sp = service.pubkey()

    print("create_event", await send(gw, [create_event_ix(
        payer=sp, organizer=organizer.pubkey(), payment_mint=mint, event_id=event_id, price=price,
        capacity=2, starts_at=int(time.time()) + 3600, checkin_authority=organizer.pubkey(),
    )], service, organizer))
    print("fund buyer", await send(gw, [
        create_ata_idempotent_ix(payer=sp, owner=buyer.pubkey(), mint=mint),
        mint_to_ix(mint=mint, destination=ata_address(buyer.pubkey(), mint), authority=sp, amount=price),
    ], service))
    print("buy_ticket", await send(gw, [
        create_ata_idempotent_ix(payer=sp, owner=organizer.pubkey(), mint=mint),
        create_ata_idempotent_ix(payer=sp, owner=sp, mint=mint),
        buy_ticket_ix(payer=sp, buyer=buyer.pubkey(), organizer=organizer.pubkey(), event=event,
                      payment_mint=mint, treasury=sp, serial=0),
    ], service, buyer))

    ticket = ticket_pda(event, 0)
    assert decode_ticket(await gw.get_account_data(ticket)).owner == buyer.pubkey()
    assert decode_event(await gw.get_account_data(event)).sold == 1
    print("check_in", await send(gw, [check_in_ix(checkin_authority=organizer.pubkey(), event=event, ticket=ticket)], service, organizer))
    assert decode_ticket(await gw.get_account_data(ticket)).checked_in
    try:
        await send(gw, [set_compute_unit_limit(200_001), check_in_ix(
            checkin_authority=organizer.pubkey(), event=event, ticket=ticket)], service, organizer)
    except ApiError as exc:
        assert exc.code == ErrorCode.ALREADY_CHECKED_IN, (exc.code, exc.details)
        print("double check-in rejected ✓")
    else:
        raise AssertionError("double check-in should have failed")
    print(f"OK · https://explorer.solana.com/address/{ticket}?cluster=devnet")


if __name__ == "__main__":
    asyncio.run(main())
