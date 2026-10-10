from datetime import datetime
from uuid import uuid4

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base
from .timeutil import utcnow


def _uuid() -> str:
    return str(uuid4())


class EventRow(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    event_id: Mapped[int] = mapped_column(BigInteger)
    onchain_pubkey: Mapped[str] = mapped_column(String(44), index=True)
    organizer_did: Mapped[str] = mapped_column(String(128), index=True)
    organizer_wallet: Mapped[str] = mapped_column(String(44))
    title: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(Text, default="")
    venue: Mapped[str] = mapped_column(String(120), default="")
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime)
    price_brl_cents: Mapped[int] = mapped_column(Integer)
    price_token: Mapped[int] = mapped_column(BigInteger)
    payment_mint: Mapped[str] = mapped_column(String(44))
    capacity: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), default="draft")
    create_tx_b64: Mapped[str | None] = mapped_column(Text, nullable=True)
    create_tx_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class OrderRow(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    event_id: Mapped[str] = mapped_column(ForeignKey("events.id"), index=True)
    buyer_did: Mapped[str] = mapped_column(String(128), index=True)
    buyer_wallet: Mapped[str] = mapped_column(String(44))
    amount_brl_cents: Mapped[int] = mapped_column(Integer)
    amount_token: Mapped[int] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(24), default="pending_payment")
    pix_provider: Mapped[str] = mapped_column(String(32))
    pix_charge_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    pix_brcode: Mapped[str | None] = mapped_column(Text, nullable=True)
    pix_expires_at: Mapped[datetime] = mapped_column(DateTime)
    pix_paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    funding_tx_sig: Mapped[str | None] = mapped_column(String(100), nullable=True)
    buy_tx_b64: Mapped[str | None] = mapped_column(Text, nullable=True)
    buy_tx_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    buy_tx_built_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    buy_tx_ticket: Mapped[str | None] = mapped_column(String(44), nullable=True)
    buy_tx_sig: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ticket_pubkey: Mapped[str | None] = mapped_column(String(44), nullable=True)
    error: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class WaitlistRow(Base):
    __tablename__ = "waitlist"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(16))
    lang: Mapped[str] = mapped_column(String(2))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ActionHitRow(Base):
    """One unauthenticated Solana Actions purchase request, for per-client rate limiting."""

    __tablename__ = "action_hits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    client_key: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
