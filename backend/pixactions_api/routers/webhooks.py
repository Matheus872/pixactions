from fastapi import APIRouter, Request
from sqlalchemy import select

from ..deps import PixDep, SessionDep
from ..errors import ApiError, ErrorCode, error_responses
from ..models import OrderRow
from ..schemas.orders import WebhookAck
from ..timeutil import utcnow

router = APIRouter(prefix="/v1/webhooks", tags=["Webhooks"])


@router.post(
    "/pix/{provider}",
    response_model=WebhookAck,
    summary="Pix payment webhook",
    responses=error_responses(ErrorCode.UNAUTHORIZED, ErrorCode.NOT_FOUND, ErrorCode.VALIDATION_ERROR),
)
async def pix_webhook(provider: str, request: Request, session: SessionDep, pix: PixDep) -> WebhookAck:
    """Called by the Pix provider when a charge is paid. The body is verified by the provider adapter
    (mock: `X-Pix-Signature` = hex HMAC-SHA256 of the raw body with `PIX_WEBHOOK_SECRET`; body
    `{"charge_id": "..."}`). Unknown charges are acknowledged so the provider stops retrying."""
    if provider != pix.name:
        raise ApiError(ErrorCode.NOT_FOUND, f"Unknown Pix provider '{provider}'")
    charge_id = pix.parse_webhook(await request.body(), request.headers)
    order = await session.scalar(select(OrderRow).where(OrderRow.pix_charge_id == charge_id))
    if order is None:
        return WebhookAck(received=True, order_id=None)
    order.pix_paid_at = order.pix_paid_at or utcnow()
    await session.commit()
    return WebhookAck(received=True, order_id=order.id)
