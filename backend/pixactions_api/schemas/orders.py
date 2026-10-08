from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .common import EXAMPLE_WALLET, SolanaAddress

OrderStatus = Literal["pending_payment", "paid", "funding", "funded", "confirmed", "failed", "expired"]

_TICKET = "8sLbNZoA1cfnvMJLPfp98ZLAnFSYCFApfJKMbiXNLwxj"
EXAMPLE_ORDER = {
    "id": "c0ffee00-1111-4222-8333-444455556666",
    "status": "pending_payment",
    "event_slug": "meetup-solana-sp-3f9a",
    "amount_brl_cents": 2000,
    "amount_token": 3636364,
    "pix": {
        "provider": "mock",
        "charge_id": "MOCKC0FFEE001111422283",
        "brcode": "00020101021226...6304ABCD",
        "qr_png_base64": "iVBORw0KGgoAAAANSUhEUg...",
        "expires_at": "2026-10-10T18:15:00Z",
    },
    "transaction": None,
    "ticket": None,
    "funding_tx_sig": None,
    "buy_tx_sig": None,
    "error": None,
    "created_at": "2026-10-10T18:00:00Z",
}


class OrderCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"event_slug": "meetup-solana-sp-3f9a", "wallet": EXAMPLE_WALLET}]})

    event_slug: str = Field(min_length=1, max_length=64)
    wallet: SolanaAddress = Field(description="Buyer's embedded wallet; receives the stablecoins and the ticket.")


class PixChargeOut(BaseModel):
    provider: str
    charge_id: str
    brcode: str = Field(description="Pix 'copia e cola' payload.")
    qr_png_base64: str = Field(description="QR code of `brcode`, PNG, base64.")
    expires_at: datetime


class TicketRef(BaseModel):
    pubkey: str = Field(description="Ticket PDA address.")
    url: str = Field(description="Public verification page (encode this in the entry QR).")
    explorer_url: str


class OrderOut(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                EXAMPLE_ORDER,
                EXAMPLE_ORDER | {"status": "funded", "pix": None, "transaction": "AgAAAA...==", "funding_tx_sig": "5xTq...9Kd"},
                EXAMPLE_ORDER | {
                    "status": "confirmed", "pix": None, "funding_tx_sig": "5xTq...9Kd", "buy_tx_sig": "3Hn2...pQ1",
                    "ticket": {
                        "pubkey": _TICKET,
                        "url": f"https://pixactions.app/t/{_TICKET}",
                        "explorer_url": f"https://explorer.solana.com/address/{_TICKET}?cluster=devnet",
                    },
                },
            ]
        }
    )

    id: str
    status: OrderStatus
    event_slug: str
    amount_brl_cents: int
    amount_token: int
    pix: PixChargeOut | None = Field(description="Present while `pending_payment`.")
    transaction: str | None = Field(description="Base64 `buy_ticket` tx to sign; present when `funded`.")
    ticket: TicketRef | None = Field(description="Present when `confirmed`.")
    funding_tx_sig: str | None
    buy_tx_sig: str | None
    error: str | None
    created_at: datetime


class OrderSummary(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": EXAMPLE_ORDER["id"], "status": "confirmed", "buyer_wallet": EXAMPLE_WALLET,
                    "amount_brl_cents": 2000, "ticket_pubkey": _TICKET, "created_at": "2026-10-10T18:00:00Z",
                }
            ]
        }
    )

    id: str
    status: OrderStatus
    buyer_wallet: str
    amount_brl_cents: int
    ticket_pubkey: str | None
    created_at: datetime


class SimulatedPayment(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"order_id": EXAMPLE_ORDER["id"], "pix_paid_at": "2026-10-10T18:00:08Z"}]})

    order_id: str
    pix_paid_at: datetime


class WebhookAck(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"received": True, "order_id": EXAMPLE_ORDER["id"]}]})

    received: bool
    order_id: str | None = Field(description="Matched order, or null when the charge is unknown.")
