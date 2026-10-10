from solders.hash import Hash
from solders.keypair import Keypair

from pixactions_api.solana.constants import PROGRAM_ID
from pixactions_api.solana.instructions import ix_discriminator
from pixactions_api.solana.tx import tx_from_b64
from tests.helpers import create_draft, seed_event_account, sign_b64

EVENT_BODY = {
    "title": "Meetup", "starts_at": "2026-10-20T22:00:00Z", "price_brl_cents": 2000, "capacity": 5,
}


async def test_create_requires_auth(client):
    r = await client.post("/v1/events", json=EVENT_BODY | {"wallet": str(Keypair().pubkey())})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHORIZED"


async def test_create_rejects_bad_token(client):
    r = await client.post(
        "/v1/events",
        json=EVENT_BODY | {"wallet": str(Keypair().pubkey())},
        headers={"Authorization": "Bearer not-a-jwt"},
    )
    assert r.status_code == 401


async def test_create_rejects_invalid_wallet(client, auth):
    r = await client.post("/v1/events", json=EVENT_BODY | {"wallet": "not-a-key"}, headers=auth())
    assert r.status_code == 422


async def test_create_returns_draft_and_unsigned_tx(client, auth, service):
    organizer = Keypair()
    d = await create_draft(client, auth, organizer)
    ev = d["event"]
    assert ev["status"] == "draft"
    assert ev["price_token"] == 3_636_364 and ev["price_token_display"] == "3.64"
    assert ev["slug"].startswith("meetup-solana-sp-")
    assert ev["links"]["checkout_url"] == f"https://pixactions.test/e/{ev['slug']}"
    tx = tx_from_b64(d["transaction"])
    keys = tx.message.account_keys
    assert keys[0] == service.pubkey()  # API is the fee payer
    ix = tx.message.instructions[0]
    assert keys[ix.program_id_index] == PROGRAM_ID
    assert bytes(ix.data[:8]) == ix_discriminator("create_event")


async def test_submit_marks_live(client, auth, gateway):
    organizer = Keypair()
    d = await create_draft(client, auth, organizer)
    r = await client.post(
        f"/v1/events/{d['event']['id']}/submit",
        json={"transaction": sign_b64(d["transaction"], organizer)},
        headers=auth(),
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "live"
    assert len(gateway.sent) == 1


async def test_submit_rejects_tampered_tx(client, auth):
    organizer = Keypair()
    d1 = await create_draft(client, auth, organizer)
    d2 = await create_draft(client, auth, organizer)
    r = await client.post(
        f"/v1/events/{d1['event']['id']}/submit",
        json={"transaction": sign_b64(d2["transaction"], organizer)},
        headers=auth(),
    )
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "TX_MISMATCH"


async def test_submit_by_other_user_is_404(client, auth):
    organizer = Keypair()
    d = await create_draft(client, auth, organizer)
    r = await client.post(
        f"/v1/events/{d['event']['id']}/submit",
        json={"transaction": sign_b64(d["transaction"], organizer)},
        headers=auth("did:privy:mallory"),
    )
    assert r.status_code == 404


async def test_reissue_transaction_uses_fresh_blockhash(client, auth, gateway):
    d = await create_draft(client, auth, Keypair())
    gateway.blockhash = Hash.new_unique()
    r = await client.post(f"/v1/events/{d['event']['id']}/transaction", headers=auth())
    assert r.status_code == 200
    assert r.json()["transaction"] != d["transaction"]


async def test_public_get_draft_is_404(client, auth):
    d = await create_draft(client, auth, Keypair())
    r = await client.get(f"/v1/events/{d['event']['slug']}")
    assert r.status_code == 404


async def test_public_get_live_reports_remaining(client, live_event, gateway):
    ev = live_event["event"]
    seed_event_account(gateway, ev, sold=3)
    r = await client.get(f"/v1/events/{ev['slug']}")
    assert r.status_code == 200
    body = r.json()
    assert (body["sold"], body["remaining"], body["sold_out"]) == (3, 47, False)
    assert "organizer_wallet" not in body


async def test_me_events_lists_only_own(client, auth, live_event):
    await create_draft(client, auth, Keypair())
    mine = (await client.get("/v1/me/events", headers=auth())).json()
    theirs = (await client.get("/v1/me/events", headers=auth("did:privy:bob"))).json()
    assert len(mine) == 2 and theirs == []


async def test_submit_event_reconciles_when_confirmation_is_lost_but_event_landed(client, auth, gateway):
    from pixactions_api.errors import ApiError, ErrorCode

    organizer = Keypair()
    d = await create_draft(client, auth, organizer)
    seed_event_account(gateway, d["event"])
    gateway.fail_next = ApiError(ErrorCode.TX_EXPIRED, "not confirmed in time")
    r = await client.post(
        f"/v1/events/{d['event']['id']}/submit",
        json={"transaction": sign_b64(d["transaction"], organizer)},
        headers=auth(),
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "live"
