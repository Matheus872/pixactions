import asyncio
import hashlib
import hmac
import json

from solders.hash import Hash
from solders.keypair import Keypair

from pixactions_api.errors import ApiError, ErrorCode
from pixactions_api.solana.constants import PROGRAM_ID, TOKEN_PROGRAM_ID
from pixactions_api.solana.tx import tx_from_b64
from tests.helpers import create_draft, seed_event_account, sent_to_program, sign_b64

BOB = "did:privy:bob"


async def new_order(client, auth, slug, buyer, did=BOB):
    r = await client.post("/v1/orders", json={"event_slug": slug, "wallet": str(buyer.pubkey())}, headers=auth(did))
    assert r.status_code == 201, r.text
    return r.json()


async def get_order(client, auth, order_id, did=BOB):
    r = await client.get(f"/v1/orders/{order_id}", headers=auth(did))
    assert r.status_code == 200, r.text
    return r.json()


async def pay(client, order_id):
    r = await client.post(f"/v1/dev/orders/{order_id}/simulate-payment")
    assert r.status_code == 200, r.text


async def funded_order(client, auth, live_event, buyer):
    o = await new_order(client, auth, live_event["event"]["slug"], buyer)
    await pay(client, o["id"])
    o = await get_order(client, auth, o["id"])
    assert o["status"] == "funded", o
    return o


async def submit(client, auth, order_id, tx_b64, did=BOB):
    return await client.post(f"/v1/orders/{order_id}/submit", json={"transaction": tx_b64}, headers=auth(did))


async def test_create_order_returns_pix_charge(client, auth, live_event):
    o = await new_order(client, auth, live_event["event"]["slug"], Keypair())
    assert o["status"] == "pending_payment"
    assert o["pix"]["brcode"].startswith("000201") and "540520.00" in o["pix"]["brcode"]
    assert len(o["pix"]["qr_png_base64"]) > 100
    assert o["transaction"] is None
    assert o["amount_brl_cents"] == 2000


async def test_reuses_open_order(client, auth, live_event):
    buyer = Keypair()
    a = await new_order(client, auth, live_event["event"]["slug"], buyer)
    b = await new_order(client, auth, live_event["event"]["slug"], buyer)
    assert a["id"] == b["id"]


async def test_order_on_draft_event_404(client, auth):
    draft = await create_draft(client, auth, Keypair())
    r = await client.post(
        "/v1/orders",
        json={"event_slug": draft["event"]["slug"], "wallet": str(Keypair().pubkey())},
        headers=auth(BOB),
    )
    assert r.status_code == 404


async def test_sold_out_on_create(client, auth, live_event, gateway):
    seed_event_account(gateway, live_event["event"], sold=50)
    r = await client.post(
        "/v1/orders",
        json={"event_slug": live_event["event"]["slug"], "wallet": str(Keypair().pubkey())},
        headers=auth(BOB),
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "SOLD_OUT"


async def test_payment_funds_buyer_and_issues_tx(client, auth, live_event, gateway):
    buyer = Keypair()
    o = await funded_order(client, auth, live_event, buyer)
    assert len(sent_to_program(gateway, TOKEN_PROGRAM_ID)) == 1  # mock on-ramp mint
    assert o["funding_tx_sig"]
    tx = tx_from_b64(o["transaction"])
    keys = tx.message.account_keys
    assert any(keys[ix.program_id_index] == PROGRAM_ID for ix in tx.message.instructions)
    assert buyer.pubkey() in keys


async def test_funding_happens_once(client, auth, live_event, gateway):
    o = await funded_order(client, auth, live_event, Keypair())
    await get_order(client, auth, o["id"])
    await get_order(client, auth, o["id"])
    assert len(sent_to_program(gateway, TOKEN_PROGRAM_ID)) == 1


async def test_polling_returns_same_tx(client, auth, live_event, gateway):
    o = await funded_order(client, auth, live_event, Keypair())
    gateway.blockhash = Hash.new_unique()
    again = await get_order(client, auth, o["id"])
    assert again["transaction"] == o["transaction"]


async def test_stale_cache_rebuilds_tx(client, auth, live_event, gateway, settings):
    o = await funded_order(client, auth, live_event, Keypair())
    settings.tx_cache_seconds = 0
    gateway.blockhash = Hash.new_unique()
    again = await get_order(client, auth, o["id"])
    assert again["transaction"] != o["transaction"]


async def test_submit_confirms_and_returns_ticket(client, auth, live_event, gateway):
    buyer = Keypair()
    o = await funded_order(client, auth, live_event, buyer)
    r = await submit(client, auth, o["id"], sign_b64(o["transaction"], buyer))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "confirmed"
    assert body["buy_tx_sig"]
    assert body["ticket"]["url"] == f"https://pixactions.test/t/{body['ticket']['pubkey']}"
    assert len(sent_to_program(gateway, PROGRAM_ID)) == 2  # create_event + buy_ticket
    again = await submit(client, auth, o["id"], sign_b64(o["transaction"], buyer))
    assert again.status_code == 200 and again.json()["ticket"] == body["ticket"]


async def test_submit_rejects_tampered_tx(client, auth, live_event):
    buyer, other_buyer = Keypair(), Keypair()
    o = await funded_order(client, auth, live_event, buyer)
    other = await funded_order(client, auth, live_event, other_buyer)
    r = await submit(client, auth, o["id"], sign_b64(other["transaction"], other_buyer))
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "TX_MISMATCH"


async def test_submit_before_funded(client, auth, live_event):
    o = await new_order(client, auth, live_event["event"]["slug"], Keypair())
    r = await submit(client, auth, o["id"], "AAAA")
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "ORDER_NOT_FUNDED"


async def test_tx_stale_then_refetch(client, auth, live_event, gateway):
    buyer = Keypair()
    o = await funded_order(client, auth, live_event, buyer)
    gateway.fail_next = ApiError(ErrorCode.TX_STALE, "slot taken")
    gateway.blockhash = Hash.new_unique()
    r = await submit(client, auth, o["id"], sign_b64(o["transaction"], buyer))
    assert r.status_code == 409 and r.json()["error"]["code"] == "TX_STALE"
    again = await get_order(client, auth, o["id"])
    assert again["status"] == "funded"
    assert again["transaction"] != o["transaction"]


async def test_other_user_cannot_read_order(client, auth, live_event):
    o = await new_order(client, auth, live_event["event"]["slug"], Keypair())
    r = await client.get(f"/v1/orders/{o['id']}", headers=auth("did:privy:mallory"))
    assert r.status_code == 404


async def test_expired_charge(client, auth, live_event, settings):
    settings.pix_expiration_seconds = 0
    o = await new_order(client, auth, live_event["event"]["slug"], Keypair())
    assert (await get_order(client, auth, o["id"]))["status"] == "expired"


async def test_autopay_after_delay(client, auth, live_event, settings):
    settings.mock_pix_autopay_seconds = 1
    o = await new_order(client, auth, live_event["event"]["slug"], Keypair())
    await asyncio.sleep(1.1)
    assert (await get_order(client, auth, o["id"]))["status"] == "funded"


async def test_webhook_marks_paid(client, auth, live_event):
    o = await new_order(client, auth, live_event["event"]["slug"], Keypair())
    body = json.dumps({"charge_id": o["pix"]["charge_id"]}).encode()
    sig = hmac.new(b"whsec", body, hashlib.sha256).hexdigest()
    r = await client.post(
        "/v1/webhooks/pix/mock", content=body,
        headers={"x-pix-signature": sig, "content-type": "application/json"},
    )
    assert r.status_code == 200 and r.json()["order_id"] == o["id"]
    assert (await get_order(client, auth, o["id"]))["status"] == "funded"


async def test_webhook_rejects_bad_signature(client):
    r = await client.post("/v1/webhooks/pix/mock", content=b'{"charge_id":"x"}', headers={"x-pix-signature": "bad"})
    assert r.status_code == 401


async def test_organizer_lists_orders(client, auth, live_event):
    o = await new_order(client, auth, live_event["event"]["slug"], Keypair())
    r = await client.get(f"/v1/events/{live_event['event']['id']}/orders", headers=auth())
    assert r.status_code == 200 and r.json()[0]["id"] == o["id"]
    assert (await client.get(f"/v1/events/{live_event['event']['id']}/orders", headers=auth(BOB))).status_code == 404


async def test_organizer_cannot_buy_own_ticket(client, auth, live_event):
    """Paying wallet == receiving wallet is rejected onchain (duplicate mutable account): refuse early."""
    organizer_wallet = live_event["event"]["organizer_wallet"]
    r = await client.post(
        "/v1/orders",
        json={"event_slug": live_event["event"]["slug"], "wallet": organizer_wallet},
        headers=auth(BOB),
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "organizador" in r.json()["error"]["message"]
