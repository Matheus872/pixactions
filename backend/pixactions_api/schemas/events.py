from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from .common import EXAMPLE_WALLET, SolanaAddress

_SLUG = "meetup-solana-sp-3f9a"
EXAMPLE_LINKS = {
    "checkout_url": f"https://pixactions.vercel.app/e/{_SLUG}",
    "action_url": f"https://pixactions.vercel.app/actions/events/{_SLUG}",
    "blink_url": f"https://dial.to/?action=solana-action%3Ahttps%3A%2F%2Fpixactions.vercel.app%2Factions%2Fevents%2F{_SLUG}&cluster=devnet",
}
_COMMON = {
    "slug": _SLUG,
    "title": "Meetup Solana SP",
    "description": "Primeiro meetup da comunidade.",
    "venue": "São Paulo, SP",
    "image_url": None,
    "starts_at": "2026-10-20T22:00:00Z",
    "price_brl_cents": 2000,
    "price_token": 3636364,
    "price_token_display": "3.64",
    "capacity": 50,
    "sold": 12,
    "onchain_pubkey": "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1",
    "links": EXAMPLE_LINKS,
}
EXAMPLE_EVENT = _COMMON | {
    "id": "4b7f2c1e-8a9d-4f3b-9c2e-1d5a6b7c8d9e",
    "status": "live",
    "payment_mint": "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU",
    "organizer_wallet": EXAMPLE_WALLET,
}


class EventCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Meetup Solana SP",
                    "description": "Primeiro meetup da comunidade.",
                    "venue": "São Paulo, SP",
                    "starts_at": "2026-10-20T22:00:00Z",
                    "price_brl_cents": 2000,
                    "capacity": 50,
                    "image_url": None,
                    "wallet": EXAMPLE_WALLET,
                }
            ]
        }
    )

    title: str = Field(min_length=3, max_length=80)
    description: str = Field(default="", max_length=1000)
    venue: str = Field(default="", max_length=120)
    starts_at: datetime = Field(description="Start time (ISO 8601). Naive values are treated as UTC.")
    price_brl_cents: int = Field(ge=100, le=1_000_000, description="Ticket price in BRL cents.")
    capacity: int = Field(ge=1, le=10_000)
    image_url: HttpUrl | None = None
    wallet: SolanaAddress = Field(description="Organizer's Solana wallet: signs create_event and check-ins, receives payments.")


class EventLinks(BaseModel):
    checkout_url: str = Field(description="Pix checkout page to share on WhatsApp.")
    action_url: str = Field(description="Solana Action URL.")
    blink_url: str = Field(description="dial.to link that renders the action as a Blink.")


class EventOut(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [EXAMPLE_EVENT]})

    id: str
    slug: str
    status: Literal["draft", "live"]
    title: str
    description: str
    venue: str
    image_url: str | None
    starts_at: datetime
    price_brl_cents: int
    price_token: int = Field(description="Price in payment-token base units (6 decimals).")
    price_token_display: str
    payment_mint: str
    capacity: int
    sold: int
    onchain_pubkey: str = Field(description="Event PDA address.")
    organizer_wallet: str
    links: EventLinks


class EventPublic(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [_COMMON | {"remaining": 38, "sold_out": False}]}
    )

    slug: str
    title: str
    description: str
    venue: str
    image_url: str | None
    starts_at: datetime
    price_brl_cents: int
    price_token: int
    price_token_display: str
    capacity: int
    sold: int
    remaining: int
    sold_out: bool
    onchain_pubkey: str
    links: EventLinks


class EventDraft(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"event": EXAMPLE_EVENT | {"status": "draft", "sold": 0}, "transaction": "AgAAAA...=="}]}
    )

    event: EventOut
    transaction: str = Field(description="Base64 `create_event` transaction for the organizer wallet to sign.")
