import struct
from decimal import Decimal

import pytest
from solders.hash import Hash
from solders.keypair import Keypair
from spl.token.instructions import get_associated_token_address

from pixactions_api.errors import ApiError, ErrorCode
from pixactions_api.pricing import brl_cents_to_token_units, fee_units, format_token
from pixactions_api.solana.accounts import (
    ConfigAccount,
    EventAccount,
    TicketAccount,
    account_discriminator,
    decode_config,
    decode_event,
    decode_ticket,
    encode_config,
    encode_event,
    encode_ticket,
)
from pixactions_api.solana.constants import IDL, PROGRAM_ID
from pixactions_api.solana.gateway import map_rpc_error
from pixactions_api.solana.instructions import (
    BUY_TICKET_ACCOUNTS,
    CHECK_IN_ACCOUNTS,
    CREATE_EVENT_ACCOUNTS,
    INITIALIZE_CONFIG_ACCOUNTS,
    buy_ticket_ix,
    create_event_ix,
    ix_discriminator,
)
from pixactions_api.solana.pda import ata_address, event_pda, ticket_pda
from pixactions_api.solana.tx import build_tx, cosign, message_hash, tx_to_b64
from tests.helpers import sign_b64

ORGANIZER = Keypair().pubkey()
MINT = Keypair().pubkey()
EVENT = event_pda(ORGANIZER, 1)
BLOCKHASH = Hash.new_unique()


def test_instruction_discriminators_match_idl():
    for ix in IDL["instructions"]:
        assert ix_discriminator(ix["name"]) == bytes(ix["discriminator"]), ix["name"]


def test_account_discriminators_match_idl():
    for acc in IDL["accounts"]:
        assert account_discriminator(acc["name"]) == bytes(acc["discriminator"]), acc["name"]


def test_account_order_matches_idl():
    expected = {
        "initialize_config": INITIALIZE_CONFIG_ACCOUNTS,
        "create_event": CREATE_EVENT_ACCOUNTS,
        "buy_ticket": BUY_TICKET_ACCOUNTS,
        "check_in": CHECK_IN_ACCOUNTS,
    }
    for ix in IDL["instructions"]:
        assert tuple(a["name"] for a in ix["accounts"]) == expected[ix["name"]], ix["name"]


def test_create_event_ix_encodes_args():
    payer = Keypair().pubkey()
    ix = create_event_ix(
        payer=payer, organizer=ORGANIZER, payment_mint=MINT, event_id=42,
        price=3_636_364, capacity=50, starts_at=1_760_000_000, checkin_authority=ORGANIZER,
    )
    data = bytes(ix.data)
    assert ix.program_id == PROGRAM_ID
    assert data[:8] == ix_discriminator("create_event")
    assert struct.unpack_from("<QQIq", data, 8) == (42, 3_636_364, 50, 1_760_000_000)
    assert data[36:68] == bytes(ORGANIZER)
    assert len(data) == 68
    assert ix.accounts[3].pubkey == event_pda(ORGANIZER, 42)
    assert ix.accounts[0].is_signer and ix.accounts[0].is_writable
    assert ix.accounts[1].is_signer and not ix.accounts[1].is_writable


def test_buy_ticket_ix_accounts():
    payer, buyer, treasury = Keypair().pubkey(), Keypair().pubkey(), Keypair().pubkey()
    ix = buy_ticket_ix(
        payer=payer, buyer=buyer, organizer=ORGANIZER, event=EVENT,
        payment_mint=MINT, treasury=treasury, serial=7,
    )
    keys = [m.pubkey for m in ix.accounts]
    assert bytes(ix.data) == ix_discriminator("buy_ticket")
    assert keys[5] == ata_address(buyer, MINT)
    assert keys[6] == ata_address(ORGANIZER, MINT)
    assert keys[7] == ata_address(treasury, MINT)
    assert keys[8] == ticket_pda(EVENT, 7)
    assert ix.accounts[1].is_signer


def test_ata_matches_spl_library():
    owner = Keypair().pubkey()
    assert ata_address(owner, MINT) == get_associated_token_address(owner, MINT)


def test_account_roundtrips():
    ev = EventAccount(ORGANIZER, 9, MINT, 1_000_000, 50, 3, 1_760_000_000, ORGANIZER, 254)
    tk = TicketAccount(EVENT, ORGANIZER, 3, True, 253)
    cf = ConfigAccount(ORGANIZER, 100, MINT, 252)
    assert decode_event(encode_event(ev)) == ev
    assert decode_ticket(encode_ticket(tk)) == tk
    assert decode_config(encode_config(cf)) == cf


def test_decode_rejects_wrong_account_type():
    with pytest.raises(ValueError):
        decode_event(encode_ticket(TicketAccount(EVENT, ORGANIZER, 0, False, 1)))


def _buy_tx(service: Keypair, buyer: Keypair, serial: int = 0):
    ix = buy_ticket_ix(
        payer=service.pubkey(), buyer=buyer.pubkey(), organizer=ORGANIZER, event=EVENT,
        payment_mint=MINT, treasury=service.pubkey(), serial=serial,
    )
    return build_tx([ix], service.pubkey(), BLOCKHASH)


def test_cosign_accepts_tx_signed_by_user():
    service, buyer = Keypair(), Keypair()
    tx = _buy_tx(service, buyer)
    final = cosign(sign_b64(tx_to_b64(tx), buyer), message_hash(tx), service)
    assert all(final.verify_with_results())
    assert final.message.account_keys[0] == service.pubkey()


def test_cosign_rejects_tampered_tx():
    service, buyer = Keypair(), Keypair()
    issued = _buy_tx(service, buyer, serial=0)
    tampered = _buy_tx(service, buyer, serial=1)
    with pytest.raises(ApiError) as err:
        cosign(sign_b64(tx_to_b64(tampered), buyer), message_hash(issued), service)
    assert err.value.code == ErrorCode.TX_MISMATCH


def test_cosign_rejects_missing_user_signature():
    service, buyer = Keypair(), Keypair()
    tx = _buy_tx(service, buyer)
    with pytest.raises(ApiError) as err:
        cosign(tx_to_b64(tx), message_hash(tx), service)
    assert err.value.code == ErrorCode.TX_MISMATCH


def test_cosign_rejects_garbage():
    with pytest.raises(ApiError) as err:
        cosign("not base64 !!", "deadbeef", Keypair())
    assert err.value.code == ErrorCode.VALIDATION_ERROR


@pytest.mark.parametrize(
    ("text", "code"),
    [
        ("Transaction simulation failed: Blockhash not found", ErrorCode.TX_EXPIRED),
        ("custom program error: 0x1770", ErrorCode.SOLD_OUT),
        ("Program log: AnchorError ... custom program error: 0x1771", ErrorCode.ALREADY_CHECKED_IN),
        ("InstructionErrorCustom(6000)", ErrorCode.SOLD_OUT),
        ("Allocate: account Address { address: 9x.. } already in use", ErrorCode.TX_STALE),
        ("custom program error: 0x7d6", ErrorCode.TX_STALE),
        ("InstructionErrorCustom(2006)", ErrorCode.TX_STALE),
        ("connection reset", ErrorCode.RPC_ERROR),
    ],
)
def test_map_rpc_error(text, code):
    assert map_rpc_error(text).code == code


def test_pricing():
    assert brl_cents_to_token_units(2000, Decimal("5.50")) == 3_636_364
    assert fee_units(3_636_364, 100) == 36_363
    assert format_token(3_636_364) == "3.64"
