from fastapi import APIRouter
from sqlalchemy import select

from ..auth import UserDep
from ..deps import GatewayDep, PixDep, ServiceDep, SessionDep, SettingsDep
from ..errors import ErrorCode, error_responses
from ..models import OrderRow
from ..schemas.common import SignedTransaction
from ..schemas.orders import OrderCreate, OrderOut, OrderSummary
from ..services.events import get_live_event_by_slug, get_owned_event
from ..services.orders import advance_order, create_order, get_buyer_order, order_out, submit_order
from ..timeutil import as_utc

router = APIRouter(prefix="/v1", tags=["Orders"])
E = ErrorCode


@router.post(
    "/orders",
    status_code=201,
    response_model=OrderOut,
    summary="Create an order (Pix charge)",
    responses=error_responses(E.UNAUTHORIZED, E.NOT_FOUND, E.SOLD_OUT, E.VALIDATION_ERROR, E.RPC_ERROR),
)
async def create_order_route(
    body: OrderCreate, user: UserDep, session: SessionDep, settings: SettingsDep,
    gateway: GatewayDep, pix: PixDep,
) -> OrderOut:
    """Opens an order for a live event and returns its Pix charge (`brcode` + QR). If the same buyer
    already has an open order for this event and wallet, that order is returned instead (safe on reload)."""
    event = await get_live_event_by_slug(session, body.event_slug)
    order = await create_order(session=session, event=event, user=user, wallet=body.wallet, pix=pix, gateway=gateway)
    return order_out(order, event, settings)


@router.get(
    "/orders/{order_id}",
    response_model=OrderOut,
    summary="Get (and advance) an order",
    responses=error_responses(E.UNAUTHORIZED, E.NOT_FOUND, E.RPC_ERROR),
)
async def get_order_route(
    order_id: str, user: UserDep, session: SessionDep, settings: SettingsDep,
    gateway: GatewayDep, pix: PixDep, service: ServiceDep,
) -> OrderOut:
    """Poll this every ~2 s from the checkout. Each call advances the order as far as possible:
    `pending_payment → paid → funding → funded`. When `funded`, `transaction` holds the `buy_ticket`
    transaction to sign; it stays identical for `tx_cache_seconds` so polling never invalidates it."""
    order, event = await get_buyer_order(session, order_id, user)
    await advance_order(order, event, session=session, settings=settings, gateway=gateway, pix=pix, service=service)
    return order_out(order, event, settings)


@router.post(
    "/orders/{order_id}/submit",
    response_model=OrderOut,
    summary="Submit the signed purchase",
    responses=error_responses(
        E.UNAUTHORIZED, E.NOT_FOUND, E.ORDER_NOT_FUNDED, E.TX_MISMATCH, E.TX_EXPIRED,
        E.TX_STALE, E.SOLD_OUT, E.VALIDATION_ERROR, E.RPC_ERROR,
    ),
)
async def submit_order_route(
    order_id: str, body: SignedTransaction, user: UserDep, session: SessionDep,
    settings: SettingsDep, gateway: GatewayDep, service: ServiceDep,
) -> OrderOut:
    """Receives the buyer-signed `buy_ticket` transaction, verifies it, co-signs as fee payer and
    broadcasts. On `TX_EXPIRED`/`TX_STALE` just poll `GET /v1/orders/{id}` again for a fresh
    transaction. Idempotent once `confirmed`."""
    order, event = await get_buyer_order(session, order_id, user)
    await submit_order(order, body.transaction, session=session, gateway=gateway, service=service)
    return order_out(order, event, settings)


@router.get(
    "/events/{event_id}/orders",
    response_model=list[OrderSummary],
    summary="List an event's orders",
    tags=["Events"],
    responses=error_responses(E.UNAUTHORIZED, E.NOT_FOUND),
)
async def list_event_orders(event_id: str, user: UserDep, session: SessionDep) -> list[OrderSummary]:
    """Orders of an event owned by the authenticated organizer, newest first. No personal data:
    buyers are identified only by wallet."""
    event = await get_owned_event(session, event_id, user)
    rows = (
        await session.scalars(
            select(OrderRow).where(OrderRow.event_id == event.id).order_by(OrderRow.created_at.desc())
        )
    ).all()
    return [
        OrderSummary(
            id=o.id, status=o.status, buyer_wallet=o.buyer_wallet, amount_brl_cents=o.amount_brl_cents,
            ticket_pubkey=o.ticket_pubkey, created_at=as_utc(o.created_at),
        )
        for o in rows
    ]
