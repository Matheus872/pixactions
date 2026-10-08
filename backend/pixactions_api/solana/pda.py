from solders.pubkey import Pubkey

from .constants import ASSOCIATED_TOKEN_PROGRAM_ID, PROGRAM_ID, TOKEN_PROGRAM_ID


def config_pda() -> Pubkey:
    return Pubkey.find_program_address([b"config"], PROGRAM_ID)[0]


def event_pda(organizer: Pubkey, event_id: int) -> Pubkey:
    return Pubkey.find_program_address(
        [b"event", bytes(organizer), event_id.to_bytes(8, "little")], PROGRAM_ID
    )[0]


def ticket_pda(event: Pubkey, serial: int) -> Pubkey:
    return Pubkey.find_program_address(
        [b"ticket", bytes(event), serial.to_bytes(4, "little")], PROGRAM_ID
    )[0]


def ata_address(owner: Pubkey, mint: Pubkey) -> Pubkey:
    return Pubkey.find_program_address(
        [bytes(owner), bytes(TOKEN_PROGRAM_ID), bytes(mint)], ASSOCIATED_TOKEN_PROGRAM_ID
    )[0]
