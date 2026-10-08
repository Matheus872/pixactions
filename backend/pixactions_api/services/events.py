import re
import secrets
import unicodedata

from solders.keypair import Keypair
from solders.pubkey import Pubkey
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import User
from ..config import Settings
from ..errors import ApiError, ErrorCode
from ..links import event_links
from ..models import EventRow
from ..pricing import format_token
from ..schemas.events import EventOut, EventPublic
from ..solana.accounts import EventAccount, decode_event
from ..solana.gateway import SolanaGateway
from ..solana.instructions import create_event_ix
from ..solana.tx import build_tx, message_hash, tx_to_b64
from ..timeutil import as_utc


def slugify(title: str) -> str:
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode().lower()
    base = re.sub(r"[^a-z0-9]+", "-", ascii_title).strip("-")[:40].strip("-") or "evento"
    return f"{base}-{secrets.token_hex(2)}"


async def build_create_event_tx(row: EventRow, *, gateway: SolanaGateway, service: Keypair) -> None:
    organizer = Pubkey.from_string(row.organizer_wallet)
    ix = create_event_ix(
        payer=service.pubkey(),
        organizer=organizer,
        payment_mint=Pubkey.from_string(row.payment_mint),
        event_id=row.event_id,
        price=row.price_token,
        capacity=row.capacity,
        starts_at=int(as_utc(row.starts_at).timestamp()),
        checkin_authority=organizer,
    )
    tx = build_tx([ix], service.pubkey(), await gateway.latest_blockhash())
    row.create_tx_b64 = tx_to_b64(tx)
    row.create_tx_hash = message_hash(tx)


async def read_event_account(gateway: SolanaGateway, row: EventRow) -> EventAccount | None:
    data = await gateway.get_account_data(Pubkey.from_string(row.onchain_pubkey))
    return decode_event(data) if data else None


async def read_sold(gateway: SolanaGateway, row: EventRow) -> int:
    acc = await read_event_account(gateway, row)
    return acc.sold if acc else 0


def event_out(row: EventRow, settings: Settings, *, sold: int) -> EventOut:
    return EventOut(
        id=row.id,
        slug=row.slug,
        status=row.status,
        title=row.title,
        description=row.description,
        venue=row.venue,
        image_url=row.image_url,
        starts_at=as_utc(row.starts_at),
        price_brl_cents=row.price_brl_cents,
        price_token=row.price_token,
        price_token_display=format_token(row.price_token),
        payment_mint=row.payment_mint,
        capacity=row.capacity,
        sold=sold,
        onchain_pubkey=row.onchain_pubkey,
        organizer_wallet=row.organizer_wallet,
        links=event_links(settings, row.slug),
    )


def event_public(row: EventRow, settings: Settings, *, sold: int) -> EventPublic:
    remaining = max(row.capacity - sold, 0)
    return EventPublic(
        slug=row.slug,
        title=row.title,
        description=row.description,
        venue=row.venue,
        image_url=row.image_url,
        starts_at=as_utc(row.starts_at),
        price_brl_cents=row.price_brl_cents,
        price_token=row.price_token,
        price_token_display=format_token(row.price_token),
        capacity=row.capacity,
        sold=sold,
        remaining=remaining,
        sold_out=remaining == 0,
        onchain_pubkey=row.onchain_pubkey,
        links=event_links(settings, row.slug),
    )


async def get_owned_event(session: AsyncSession, event_id: str, user: User) -> EventRow:
    row = await session.get(EventRow, event_id)
    if row is None or row.organizer_did != user.did:
        raise ApiError(ErrorCode.NOT_FOUND, "Event not found")
    return row


async def get_live_event_by_slug(session: AsyncSession, slug: str) -> EventRow:
    row = await session.scalar(select(EventRow).where(EventRow.slug == slug))
    if row is None or row.status != "live":
        raise ApiError(ErrorCode.NOT_FOUND, "Event not found")
    return row
