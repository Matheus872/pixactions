from uuid import uuid4

from solders.keypair import Keypair
from solders.pubkey import Pubkey
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import User
from ..config import Settings
from ..errors import ApiError, ErrorCode
from ..links import explorer_url, ticket_url
from ..models import EventRow, OrderRow
from ..pix.base import PixProvider
from ..pix.qr import qr_png_base64
from ..schemas.orders import OrderOut, PixChargeOut, TicketRef
from ..solana.gateway import SolanaGateway
from ..solana.instructions import buy_ticket_ix
from ..solana.pda import ata_address, ticket_pda
from ..solana.spl import create_ata_idempotent_ix, mint_to_ix
from ..solana.tx import build_tx, cosign, message_hash, tx_to_b64
from ..timeutil import as_utc, utcnow
from .events import read_event_account

SELF_PURCHASE_MESSAGE = "O organizador não pode comprar ingresso do próprio evento com a mesma carteira"
OPEN_STATUSES = ("pending_payment", "paid", "funding", "funded")
FUNDING_TIMEOUT_SECONDS = 90


async def create_order(
    *, session: AsyncSession, event: EventRow, user: User, wallet: str,
    pix: PixProvider, gateway: SolanaGateway,
) -> OrderRow:
    if wallet == event.organizer_wallet:
        # Same wallet would pay and receive: the program rejects it (duplicate mutable token account).
        raise ApiError(ErrorCode.VALIDATION_ERROR, SELF_PURCHASE_MESSAGE)
    existing = await session.scalar(
        select(OrderRow).where(
            OrderRow.event_id == event.id,
            OrderRow.buyer_did == user.did,
            OrderRow.buyer_wallet == wallet,
            OrderRow.status.in_(OPEN_STATUSES),
        )
    )
    if existing is not None:
        return existing
    acc = await read_event_account(gateway, event)
    if acc is not None and acc.sold >= acc.capacity:
        raise ApiError(ErrorCode.SOLD_OUT, "Event is sold out")
    order_id = str(uuid4())
    charge = await pix.create_charge(
        order_id=order_id, amount_brl_cents=event.price_brl_cents, description=event.title
    )
    order = OrderRow(
        id=order_id,
        event_id=event.id,
        buyer_did=user.did,
        buyer_wallet=wallet,
        amount_brl_cents=event.price_brl_cents,
        amount_token=event.price_token,
        status="pending_payment",
        pix_provider=pix.name,
        pix_charge_id=charge.charge_id,
        pix_brcode=charge.brcode,
        pix_expires_at=charge.expires_at,
    )
    session.add(order)
    await session.commit()
    return order


async def get_buyer_order(session: AsyncSession, order_id: str, user: User) -> tuple[OrderRow, EventRow]:
    order = await session.get(OrderRow, order_id)
    if order is None or order.buyer_did != user.did:
        raise ApiError(ErrorCode.NOT_FOUND, "Order not found")
    event = await session.get(EventRow, order.event_id)
    assert event is not None
    return order, event


async def _claim_funding(session: AsyncSession, order: OrderRow) -> bool:
    """Atomically move paid → funding so only one request mints (no double funding)."""
    result = await session.execute(
        update(OrderRow)
        .where(OrderRow.id == order.id, OrderRow.status == "paid")
        .values(status="funding", updated_at=utcnow())
    )
    await session.commit()
    await session.refresh(order)
    return result.rowcount == 1


async def _fund(
    order: OrderRow, event: EventRow, *, session: AsyncSession, gateway: SolanaGateway, service: Keypair
) -> None:
    """Mock on-ramp: deliver the order amount of mock USDC to the buyer's wallet."""
    if not await _claim_funding(session, order):
        return
    buyer = Pubkey.from_string(order.buyer_wallet)
    mint = Pubkey.from_string(event.payment_mint)
    ixs = [
        create_ata_idempotent_ix(payer=service.pubkey(), owner=buyer, mint=mint),
        mint_to_ix(mint=mint, destination=ata_address(buyer, mint), authority=service.pubkey(), amount=order.amount_token),
    ]
    tx = build_tx(ixs, service.pubkey(), await gateway.latest_blockhash())
    tx.partial_sign([service], tx.message.recent_blockhash)
    try:
        sig = await gateway.send_and_confirm(tx)
    except ApiError as exc:
        order.status, order.error = "paid", exc.code.value
        await session.commit()
        raise
    order.status, order.funding_tx_sig, order.error = "funded", sig, None
    await session.commit()


async def _ensure_buy_tx(
    order: OrderRow, event: EventRow, *, session: AsyncSession, settings: Settings,
    gateway: SolanaGateway, service: Keypair,
) -> None:
    """Keep one stable buy_ticket tx per order for `tx_cache_seconds` (polling must not change it)."""
    now = utcnow()
    if order.buy_tx_b64 and order.buy_tx_built_at and (now - order.buy_tx_built_at).total_seconds() < settings.tx_cache_seconds:
        return
    acc = await read_event_account(gateway, event)
    if acc is None:
        raise ApiError(ErrorCode.RPC_ERROR, "Event account not found onchain")
    if acc.sold >= acc.capacity:
        order.status, order.error = "failed", ErrorCode.SOLD_OUT.value
        await session.commit()
        return
    event_pk = Pubkey.from_string(event.onchain_pubkey)
    organizer = Pubkey.from_string(event.organizer_wallet)
    mint = Pubkey.from_string(event.payment_mint)
    treasury = service.pubkey()
    ixs = [
        create_ata_idempotent_ix(payer=service.pubkey(), owner=organizer, mint=mint),
        create_ata_idempotent_ix(payer=service.pubkey(), owner=treasury, mint=mint),
        buy_ticket_ix(
            payer=service.pubkey(), buyer=Pubkey.from_string(order.buyer_wallet), organizer=organizer,
            event=event_pk, payment_mint=mint, treasury=treasury, serial=acc.sold,
        ),
    ]
    tx = build_tx(ixs, service.pubkey(), await gateway.latest_blockhash())
    order.buy_tx_b64 = tx_to_b64(tx)
    order.buy_tx_hash = message_hash(tx)
    order.buy_tx_built_at = now
    order.buy_tx_ticket = str(ticket_pda(event_pk, acc.sold))
    await session.commit()


async def advance_order(
    order: OrderRow, event: EventRow, *, session: AsyncSession, settings: Settings,
    gateway: SolanaGateway, pix: PixProvider, service: Keypair,
) -> OrderRow:
    """Drive the state machine as far as it can go right now (called on every GET)."""
    now = utcnow()
    if order.status == "funding" and (now - order.updated_at).total_seconds() > FUNDING_TIMEOUT_SECONDS:
        order.status = "paid"
        await session.commit()
    if order.status == "pending_payment":
        if await pix.is_paid(order):
            order.status = "paid"
            order.pix_paid_at = order.pix_paid_at or now
            await session.commit()
        elif now >= order.pix_expires_at:
            order.status = "expired"
            await session.commit()
    if order.status == "paid":
        await _fund(order, event, session=session, gateway=gateway, service=service)
    if order.status == "funded":
        await _ensure_buy_tx(order, event, session=session, settings=settings, gateway=gateway, service=service)
    return order


async def submit_order(
    order: OrderRow, signed_b64: str, *, session: AsyncSession, gateway: SolanaGateway, service: Keypair
) -> OrderRow:
    if order.status == "confirmed":
        return order
    if order.status != "funded" or not order.buy_tx_hash:
        raise ApiError(ErrorCode.ORDER_NOT_FUNDED, "Order is not ready to be signed yet")
    tx = cosign(signed_b64, order.buy_tx_hash, service)
    try:
        sig = await gateway.send_and_confirm(tx)
    except ApiError as exc:
        if exc.code in (ErrorCode.TX_STALE, ErrorCode.TX_EXPIRED):
            order.buy_tx_b64 = order.buy_tx_hash = order.buy_tx_built_at = None
        elif exc.code == ErrorCode.SOLD_OUT:
            order.status, order.error = "failed", exc.code.value
        await session.commit()
        raise
    order.status, order.buy_tx_sig, order.ticket_pubkey = "confirmed", sig, order.buy_tx_ticket
    await session.commit()
    return order


def order_out(order: OrderRow, event: EventRow, settings: Settings) -> OrderOut:
    pix = None
    if order.status == "pending_payment" and order.pix_brcode:
        pix = PixChargeOut(
            provider=order.pix_provider,
            charge_id=order.pix_charge_id or "",
            brcode=order.pix_brcode,
            qr_png_base64=qr_png_base64(order.pix_brcode),
            expires_at=as_utc(order.pix_expires_at),
        )
    ticket = None
    if order.ticket_pubkey:
        ticket = TicketRef(
            pubkey=order.ticket_pubkey,
            url=ticket_url(settings, order.ticket_pubkey),
            explorer_url=explorer_url(settings, order.ticket_pubkey),
        )
    return OrderOut(
        id=order.id,
        status=order.status,
        event_slug=event.slug,
        amount_brl_cents=order.amount_brl_cents,
        amount_token=order.amount_token,
        pix=pix,
        transaction=order.buy_tx_b64 if order.status == "funded" else None,
        ticket=ticket,
        funding_tx_sig=order.funding_tx_sig,
        buy_tx_sig=order.buy_tx_sig,
        error=order.error,
        created_at=as_utc(order.created_at),
    )
