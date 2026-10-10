import hashlib
import hmac
import json
from collections.abc import Mapping
from datetime import timedelta

from ..config import Settings
from ..errors import ApiError, ErrorCode
from ..timeutil import utcnow
from .base import PaymentState, PixCharge
from .brcode import build_brcode


class MockPixProvider:
    """Sandbox Pix: auto-confirms after MOCK_PIX_AUTOPAY_SECONDS, or via the dev endpoint/webhook."""

    name = "mock"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def create_charge(self, *, order_id: str, amount_brl_cents: int, description: str) -> PixCharge:
        charge_id = "MOCK" + order_id.replace("-", "")[:21].upper()
        brcode = build_brcode(
            pix_key="SANDBOX-NAO-PAGUE",  # not a valid Pix key type: no bank can pay it
            amount_brl_cents=amount_brl_cents,
            merchant_name="PIX ACTIONS SANDBOX",
            merchant_city="SAO PAULO",
            txid=charge_id,
        )
        expires_at = utcnow() + timedelta(seconds=self._settings.pix_expiration_seconds)
        return PixCharge(charge_id=charge_id, brcode=brcode, expires_at=expires_at)

    async def is_paid(self, order: PaymentState) -> bool:
        if order.pix_paid_at is not None:
            return True
        delay = self._settings.mock_pix_autopay_seconds
        return delay > 0 and (utcnow() - order.created_at).total_seconds() >= delay

    def parse_webhook(self, body: bytes, headers: Mapping[str, str]) -> str:
        expected = hmac.new(self._settings.pix_webhook_secret.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, headers.get("x-pix-signature", "")):
            raise ApiError(ErrorCode.UNAUTHORIZED, "Invalid webhook signature")
        try:
            return str(json.loads(body)["charge_id"])
        except (ValueError, KeyError, TypeError) as exc:
            raise ApiError(ErrorCode.VALIDATION_ERROR, "Webhook body must be JSON with charge_id") from exc
