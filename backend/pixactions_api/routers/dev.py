from fastapi import APIRouter

from ..deps import SessionDep
from ..errors import ApiError, ErrorCode, error_responses
from ..models import OrderRow
from ..schemas.orders import SimulatedPayment
from ..timeutil import as_utc, utcnow

router = APIRouter(prefix="/v1/dev", tags=["Dev"])


@router.post(
    "/orders/{order_id}/simulate-payment",
    response_model=SimulatedPayment,
    summary="Simulate a Pix payment",
    responses=error_responses(ErrorCode.NOT_FOUND),
)
async def simulate_payment(order_id: str, session: SessionDep) -> SimulatedPayment:
    """Sandbox only (not mounted when `ENV=production`). Marks the order's Pix as paid; the next
    `GET /v1/orders/{id}` funds the buyer and issues the purchase transaction."""
    order = await session.get(OrderRow, order_id)
    if order is None:
        raise ApiError(ErrorCode.NOT_FOUND, "Order not found")
    order.pix_paid_at = order.pix_paid_at or utcnow()
    await session.commit()
    return SimulatedPayment(order_id=order.id, pix_paid_at=as_utc(order.pix_paid_at))
