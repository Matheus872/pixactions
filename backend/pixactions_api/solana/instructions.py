"""Instruction builders for the pixactions Anchor program (discriminator + borsh args)."""

import hashlib
import struct

from solders.instruction import AccountMeta, Instruction
from solders.pubkey import Pubkey

from .constants import PROGRAM_ID, SYSTEM_PROGRAM_ID, TOKEN_PROGRAM_ID
from .pda import ata_address, config_pda, event_pda, ticket_pda

INITIALIZE_CONFIG_ACCOUNTS = ("payer", "admin", "config", "system_program")
CREATE_EVENT_ACCOUNTS = ("payer", "organizer", "payment_mint", "event", "system_program")
BUY_TICKET_ACCOUNTS = (
    "payer", "buyer", "config", "event", "payment_mint", "buyer_token",
    "organizer_token", "treasury_token", "ticket", "token_program", "system_program",
)
CHECK_IN_ACCOUNTS = ("checkin_authority", "event", "ticket")


def ix_discriminator(name: str) -> bytes:
    return hashlib.sha256(f"global:{name}".encode()).digest()[:8]


def initialize_config_ix(*, payer: Pubkey, admin: Pubkey, fee_bps: int, treasury: Pubkey) -> Instruction:
    data = ix_discriminator("initialize_config") + struct.pack("<H", fee_bps) + bytes(treasury)
    return Instruction(
        PROGRAM_ID,
        data,
        [
            AccountMeta(payer, True, True),
            AccountMeta(admin, True, False),
            AccountMeta(config_pda(), False, True),
            AccountMeta(SYSTEM_PROGRAM_ID, False, False),
        ],
    )


def create_event_ix(
    *, payer: Pubkey, organizer: Pubkey, payment_mint: Pubkey, event_id: int, price: int,
    capacity: int, starts_at: int, checkin_authority: Pubkey,
) -> Instruction:
    data = (
        ix_discriminator("create_event")
        + struct.pack("<QQIq", event_id, price, capacity, starts_at)
        + bytes(checkin_authority)
    )
    return Instruction(
        PROGRAM_ID,
        data,
        [
            AccountMeta(payer, True, True),
            AccountMeta(organizer, True, False),
            AccountMeta(payment_mint, False, False),
            AccountMeta(event_pda(organizer, event_id), False, True),
            AccountMeta(SYSTEM_PROGRAM_ID, False, False),
        ],
    )


def buy_ticket_ix(
    *, payer: Pubkey, buyer: Pubkey, organizer: Pubkey, event: Pubkey, payment_mint: Pubkey,
    treasury: Pubkey, serial: int,
) -> Instruction:
    return Instruction(
        PROGRAM_ID,
        ix_discriminator("buy_ticket"),
        [
            AccountMeta(payer, True, True),
            AccountMeta(buyer, True, False),
            AccountMeta(config_pda(), False, False),
            AccountMeta(event, False, True),
            AccountMeta(payment_mint, False, False),
            AccountMeta(ata_address(buyer, payment_mint), False, True),
            AccountMeta(ata_address(organizer, payment_mint), False, True),
            AccountMeta(ata_address(treasury, payment_mint), False, True),
            AccountMeta(ticket_pda(event, serial), False, True),
            AccountMeta(TOKEN_PROGRAM_ID, False, False),
            AccountMeta(SYSTEM_PROGRAM_ID, False, False),
        ],
    )


def check_in_ix(*, checkin_authority: Pubkey, event: Pubkey, ticket: Pubkey) -> Instruction:
    return Instruction(
        PROGRAM_ID,
        ix_discriminator("check_in"),
        [
            AccountMeta(checkin_authority, True, False),
            AccountMeta(event, False, False),
            AccountMeta(ticket, False, True),
        ],
    )
