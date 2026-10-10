from solders.keypair import Keypair
from solders.pubkey import Pubkey

from pixactions_api.solana.constants import PROGRAM_ID
from pixactions_api.solana.instructions import ix_discriminator
from pixactions_api.solana.tx import tx_from_b64
from tests.helpers import seed_ticket, sent_to_program, sign_b64


async def test_get_ticket(client, live_event, gateway):
    owner = Keypair().pubkey()
    pk = seed_ticket(gateway, live_event["event"], serial=4, owner=owner)
    r = await client.get(f"/v1/tickets/{pk}")
    assert r.status_code == 200
    body = r.json()
    assert (body["serial"], body["owner"], body["checked_in"]) == (4, str(owner), False)
    assert body["event"]["slug"] == live_event["event"]["slug"]
    assert pk in body["explorer_url"] and body["url"].endswith(f"/t/{pk}")


async def test_get_unknown_ticket_404(client):
    r = await client.get(f"/v1/tickets/{Keypair().pubkey()}")
    assert r.status_code == 404


async def test_checkin_flow(client, auth, live_event, gateway):
    pk = seed_ticket(gateway, live_event["event"])
    r = await client.post(f"/v1/tickets/{pk}/checkin", headers=auth())
    assert r.status_code == 200, r.text
    issued = r.json()
    tx = tx_from_b64(issued["transaction"])
    assert bytes(tx.message.instructions[0].data) == ix_discriminator("check_in")
    before = len(sent_to_program(gateway, PROGRAM_ID))
    r = await client.post(
        f"/v1/tickets/{pk}/checkin/submit",
        json={"transaction": sign_b64(issued["transaction"], live_event["organizer"]), "checkin_token": issued["checkin_token"]},
        headers=auth(),
    )
    assert r.status_code == 200, r.text
    assert r.json()["checked_in"] is True
    assert len(sent_to_program(gateway, PROGRAM_ID)) == before + 1


async def test_checkin_already_used_409(client, auth, live_event, gateway):
    pk = seed_ticket(gateway, live_event["event"], checked_in=True)
    r = await client.post(f"/v1/tickets/{pk}/checkin", headers=auth())
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "ALREADY_CHECKED_IN"


async def test_checkin_by_non_organizer_404(client, auth, live_event, gateway):
    pk = seed_ticket(gateway, live_event["event"])
    r = await client.post(f"/v1/tickets/{pk}/checkin", headers=auth("did:privy:mallory"))
    assert r.status_code == 404


async def test_checkin_bad_token(client, auth, live_event, gateway):
    pk = seed_ticket(gateway, live_event["event"])
    issued = (await client.post(f"/v1/tickets/{pk}/checkin", headers=auth())).json()
    r = await client.post(
        f"/v1/tickets/{pk}/checkin/submit",
        json={"transaction": sign_b64(issued["transaction"], live_event["organizer"]), "checkin_token": "abc.def"},
        headers=auth(),
    )
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "TX_MISMATCH"


async def test_ticket_shaped_account_off_its_pda_is_rejected(client, live_event, gateway):
    """A Ticket-shaped account at an address that is not the program PDA (e.g. written by another program) is not a ticket."""
    from pixactions_api.solana.accounts import TicketAccount, encode_ticket

    event_pk = Pubkey.from_string(live_event["event"]["onchain_pubkey"])
    spoof = Keypair().pubkey()
    gateway.accounts[str(spoof)] = encode_ticket(TicketAccount(event_pk, Keypair().pubkey(), 0, False, 255))
    r = await client.get(f"/v1/tickets/{spoof}")
    assert r.status_code == 404
