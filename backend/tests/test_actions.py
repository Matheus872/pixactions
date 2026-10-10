from solders.keypair import Keypair

from pixactions_api.solana.tx import tx_from_b64
from tests.helpers import seed_event_account, sign_b64


async def test_actions_json(client):
    r = await client.get("/actions.json")
    assert r.status_code == 200
    assert r.json() == {"rules": [{"pathPattern": "/actions/**", "apiPath": "/actions/**"}]}


async def test_action_get(client, live_event):
    slug = live_event["event"]["slug"]
    r = await client.get(f"/actions/events/{slug}")
    assert r.status_code == 200
    assert r.headers["x-action-version"] == "2.4"
    assert r.headers["x-blockchain-ids"].startswith("solana:")
    body = r.json()
    assert body["type"] == "action" and body["disabled"] is False
    assert body["links"]["actions"][0]["href"] == f"/actions/events/{slug}"
    assert body["icon"].startswith("https://")


async def test_action_get_sold_out_is_disabled(client, live_event, gateway):
    seed_event_account(gateway, live_event["event"], sold=50)
    body = (await client.get(f"/actions/events/{live_event['event']['slug']}")).json()
    assert body["disabled"] is True


async def test_action_get_unknown_uses_actions_error_shape(client):
    r = await client.get("/actions/events/nope")
    assert r.status_code == 404
    assert set(r.json()) == {"message"}


async def test_action_post_returns_partially_signed_tx(client, live_event):
    buyer = Keypair()
    r = await client.post(f"/actions/events/{live_event['event']['slug']}", json={"account": str(buyer.pubkey())})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["type"] == "transaction"
    tx = tx_from_b64(body["transaction"])
    results = tx.verify_with_results()
    assert results[0] is True  # API signed as fee payer
    assert not all(results)  # buyer still has to sign
    assert all(tx_from_b64(sign_b64(body["transaction"], buyer)).verify_with_results())


async def test_action_post_invalid_account(client, live_event):
    r = await client.post(f"/actions/events/{live_event['event']['slug']}", json={"account": "nope"})
    assert r.status_code == 400
    assert "message" in r.json()


async def test_action_cors_preflight(client):
    r = await client.options(
        "/actions/events/x",
        headers={"Origin": "https://dial.to", "Access-Control-Request-Method": "POST"},
    )
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == "*"


async def test_action_post_rejects_the_organizer_wallet(client, live_event):
    r = await client.post(
        f"/actions/events/{live_event['event']['slug']}",
        json={"account": live_event["event"]["organizer_wallet"]},
    )
    assert r.status_code == 400
    assert "organizador" in r.json()["message"]


async def test_action_post_is_rate_limited_per_client(client, live_event, settings):
    settings.actions_rate_limit = 3
    slug = live_event["event"]["slug"]
    codes = [
        (await client.post(f"/actions/events/{slug}", json={"account": str(Keypair().pubkey())}, headers={"x-forwarded-for": "203.0.113.7"})).status_code
        for _ in range(4)
    ]
    assert codes == [200, 200, 200, 429]
    other = await client.post(f"/actions/events/{slug}", json={"account": str(Keypair().pubkey())}, headers={"x-forwarded-for": "198.51.100.9"})
    assert other.status_code == 200
