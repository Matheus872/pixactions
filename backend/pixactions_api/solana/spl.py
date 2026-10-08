"""Minimal SPL Token / Associated Token instructions, hand-encoded to avoid version drift."""

import struct

from solders.instruction import AccountMeta, Instruction
from solders.pubkey import Pubkey

from .constants import ASSOCIATED_TOKEN_PROGRAM_ID, SYSTEM_PROGRAM_ID, TOKEN_PROGRAM_ID
from .pda import ata_address

MINT_SIZE = 82


def create_ata_idempotent_ix(*, payer: Pubkey, owner: Pubkey, mint: Pubkey) -> Instruction:
    return Instruction(
        ASSOCIATED_TOKEN_PROGRAM_ID,
        bytes([1]),  # CreateIdempotent
        [
            AccountMeta(payer, True, True),
            AccountMeta(ata_address(owner, mint), False, True),
            AccountMeta(owner, False, False),
            AccountMeta(mint, False, False),
            AccountMeta(SYSTEM_PROGRAM_ID, False, False),
            AccountMeta(TOKEN_PROGRAM_ID, False, False),
        ],
    )


def mint_to_ix(*, mint: Pubkey, destination: Pubkey, authority: Pubkey, amount: int) -> Instruction:
    return Instruction(
        TOKEN_PROGRAM_ID,
        bytes([7]) + struct.pack("<Q", amount),  # MintTo
        [
            AccountMeta(mint, False, True),
            AccountMeta(destination, False, True),
            AccountMeta(authority, True, False),
        ],
    )


def initialize_mint2_ix(*, mint: Pubkey, decimals: int, mint_authority: Pubkey) -> Instruction:
    data = bytes([20, decimals]) + bytes(mint_authority) + bytes([0])  # no freeze authority
    return Instruction(TOKEN_PROGRAM_ID, data, [AccountMeta(mint, False, True)])
