import hashlib
import struct
from dataclasses import dataclass

from solders.pubkey import Pubkey


def account_discriminator(name: str) -> bytes:
    return hashlib.sha256(f"account:{name}".encode()).digest()[:8]


@dataclass(frozen=True)
class ConfigAccount:
    admin: Pubkey
    fee_bps: int
    treasury: Pubkey
    bump: int


@dataclass(frozen=True)
class EventAccount:
    organizer: Pubkey
    event_id: int
    payment_mint: Pubkey
    price: int
    capacity: int
    sold: int
    starts_at: int
    checkin_authority: Pubkey
    bump: int


@dataclass(frozen=True)
class TicketAccount:
    event: Pubkey
    owner: Pubkey
    serial: int
    checked_in: bool
    bump: int


_CONFIG = struct.Struct("<32sH32sB")
_EVENT = struct.Struct("<32sQ32sQIIq32sB")
_TICKET = struct.Struct("<32s32sI?B")


def _fields(data: bytes, name: str, layout: struct.Struct) -> tuple:
    if len(data) < 8 + layout.size or data[:8] != account_discriminator(name):
        raise ValueError(f"not a {name} account")
    return layout.unpack_from(data, 8)


def decode_config(data: bytes) -> ConfigAccount:
    admin, fee_bps, treasury, bump = _fields(data, "Config", _CONFIG)
    return ConfigAccount(Pubkey(admin), fee_bps, Pubkey(treasury), bump)


def decode_event(data: bytes) -> EventAccount:
    f = _fields(data, "Event", _EVENT)
    return EventAccount(Pubkey(f[0]), f[1], Pubkey(f[2]), f[3], f[4], f[5], f[6], Pubkey(f[7]), f[8])


def decode_ticket(data: bytes) -> TicketAccount:
    event, owner, serial, checked_in, bump = _fields(data, "Ticket", _TICKET)
    return TicketAccount(Pubkey(event), Pubkey(owner), serial, checked_in, bump)


def encode_config(a: ConfigAccount) -> bytes:
    return account_discriminator("Config") + _CONFIG.pack(bytes(a.admin), a.fee_bps, bytes(a.treasury), a.bump)


def encode_event(a: EventAccount) -> bytes:
    return account_discriminator("Event") + _EVENT.pack(
        bytes(a.organizer), a.event_id, bytes(a.payment_mint), a.price, a.capacity, a.sold,
        a.starts_at, bytes(a.checkin_authority), a.bump,
    )


def encode_ticket(a: TicketAccount) -> bytes:
    return account_discriminator("Ticket") + _TICKET.pack(
        bytes(a.event), bytes(a.owner), a.serial, a.checked_in, a.bump
    )
