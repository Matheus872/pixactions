import secrets

from fastapi import APIRouter
from solders.pubkey import Pubkey
from sqlalchemy import select

from ..auth import UserDep
from ..deps import GatewayDep, ServiceDep, SessionDep, SettingsDep
from ..errors import ApiError, ErrorCode, error_responses
from ..models import EventRow
from ..pricing import brl_cents_to_token_units
from ..schemas.common import SignedTransaction
from ..schemas.events import EventCreate, EventDraft, EventOut, EventPublic
from ..services.events import (
    build_create_event_tx,
    event_out,
    event_public,
    get_live_event_by_slug,
    get_owned_event,
    read_event_account,
    read_sold,
    slugify,
)
from ..solana.pda import event_pda
from ..solana.tx import cosign
from ..timeutil import to_naive_utc

router = APIRouter(prefix="/v1", tags=["Events"])
E = ErrorCode


@router.post(
    "/events",
    status_code=201,
    response_model=EventDraft,
    summary="Create an event (draft)",
    responses=error_responses(E.UNAUTHORIZED, E.VALIDATION_ERROR, E.RPC_ERROR),
)
async def create_event(
    body: EventCreate, user: UserDep, session: SessionDep, settings: SettingsDep,
    gateway: GatewayDep, service: ServiceDep,
) -> EventDraft:
    """Creates the event in `draft` status and returns the unsigned `create_event` transaction.

    Next step: sign `transaction` with the organizer wallet and call `POST /v1/events/{id}/submit`.
    The price is converted from BRL to payment-token units at creation time."""
    event_id = secrets.randbits(63)
    organizer = Pubkey.from_string(body.wallet)
    row = EventRow(
        slug=slugify(body.title),
        event_id=event_id,
        onchain_pubkey=str(event_pda(organizer, event_id)),
        organizer_did=user.did,
        organizer_wallet=body.wallet,
        title=body.title,
        description=body.description,
        venue=body.venue,
        image_url=str(body.image_url) if body.image_url else None,
        starts_at=to_naive_utc(body.starts_at),
        price_brl_cents=body.price_brl_cents,
        price_token=brl_cents_to_token_units(body.price_brl_cents, settings.mock_brl_per_usd),
        payment_mint=settings.mock_usdc_mint,
        capacity=body.capacity,
        status="draft",
    )
    await build_create_event_tx(row, gateway=gateway, service=service)
    session.add(row)
    await session.commit()
    return EventDraft(event=event_out(row, settings, sold=0), transaction=row.create_tx_b64)


@router.post(
    "/events/{event_id}/transaction",
    response_model=EventDraft,
    summary="Re-issue the create_event transaction",
    responses=error_responses(E.UNAUTHORIZED, E.NOT_FOUND, E.VALIDATION_ERROR, E.RPC_ERROR),
)
async def reissue_event_transaction(
    event_id: str, user: UserDep, session: SessionDep, settings: SettingsDep,
    gateway: GatewayDep, service: ServiceDep,
) -> EventDraft:
    """Builds a fresh `create_event` transaction for a draft. Use it after `TX_EXPIRED`
    (the organizer took longer than the blockhash lifetime to sign)."""
    row = await get_owned_event(session, event_id, user)
    if row.status == "live":
        raise ApiError(E.VALIDATION_ERROR, "Event is already live")
    await build_create_event_tx(row, gateway=gateway, service=service)
    await session.commit()
    return EventDraft(event=event_out(row, settings, sold=0), transaction=row.create_tx_b64)


@router.post(
    "/events/{event_id}/submit",
    response_model=EventOut,
    summary="Publish the event onchain",
    responses=error_responses(
        E.UNAUTHORIZED, E.NOT_FOUND, E.TX_MISMATCH, E.TX_EXPIRED, E.VALIDATION_ERROR, E.RPC_ERROR
    ),
)
async def submit_event(
    event_id: str, body: SignedTransaction, user: UserDep, session: SessionDep,
    settings: SettingsDep, gateway: GatewayDep, service: ServiceDep,
) -> EventOut:
    """Receives the organizer-signed `create_event` transaction, verifies it is exactly the one issued,
    co-signs as fee payer, broadcasts and marks the event `live`. Idempotent once live."""
    row = await get_owned_event(session, event_id, user)
    if row.status == "live":
        return event_out(row, settings, sold=await read_sold(gateway, row))
    tx = cosign(body.transaction, row.create_tx_hash or "", service)
    try:
        await gateway.send_and_confirm(tx)
    except ApiError:
        if await read_event_account(gateway, row) is None:
            raise  # really not onchain: surface the error
    row.status = "live"
    row.create_tx_b64 = None
    await session.commit()
    return event_out(row, settings, sold=0)


@router.get(
    "/me/events",
    response_model=list[EventOut],
    summary="List my events",
    responses=error_responses(E.UNAUTHORIZED, E.RPC_ERROR),
)
async def list_my_events(
    user: UserDep, session: SessionDep, settings: SettingsDep, gateway: GatewayDep
) -> list[EventOut]:
    """Events created by the authenticated organizer, newest first. `sold` is read onchain, so it
    includes tickets bought through Blinks."""
    rows = (
        await session.scalars(
            select(EventRow).where(EventRow.organizer_did == user.did).order_by(EventRow.created_at.desc())
        )
    ).all()
    return [
        event_out(r, settings, sold=await read_sold(gateway, r) if r.status == "live" else 0) for r in rows
    ]


@router.get(
    "/events/{slug}",
    response_model=EventPublic,
    summary="Get a public event",
    responses=error_responses(E.NOT_FOUND, E.RPC_ERROR),
)
async def get_public_event(
    slug: str, session: SessionDep, settings: SettingsDep, gateway: GatewayDep
) -> EventPublic:
    """Public data for the checkout page. Drafts are not visible (404). `remaining` comes from the
    onchain `sold` counter."""
    row = await get_live_event_by_slug(session, slug)
    return event_public(row, settings, sold=await read_sold(gateway, row))
