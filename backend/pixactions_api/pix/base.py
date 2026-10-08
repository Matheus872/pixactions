from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class PixCharge:
    charge_id: str
    brcode: str
    expires_at: datetime  # naive UTC


class PaymentState(Protocol):
    created_at: datetime
    pix_paid_at: datetime | None


class PixProvider(Protocol):
    """A Pix on-ramp: charges BRL via Pix; production providers deliver stablecoins onchain."""

    name: str

    async def create_charge(self, *, order_id: str, amount_brl_cents: int, description: str) -> PixCharge: ...

    async def is_paid(self, order: PaymentState) -> bool: ...

    def parse_webhook(self, body: bytes, headers: Mapping[str, str]) -> str:
        """Validate a provider webhook and return the paid charge id (raises ApiError)."""
        ...
