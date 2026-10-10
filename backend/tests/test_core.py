from pixactions_api.db import normalize_db_url
from pixactions_api.solana.constants import PROGRAM_ID


async def test_health(client, settings, service):
    r = await client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["cluster"] == "devnet"
    assert body["program_id"] == str(PROGRAM_ID)
    assert body["service_wallet"] == str(service.pubkey())
    assert body["payment_mint"] == settings.mock_usdc_mint


async def test_docs_ui_is_scalar(client):
    r = await client.get("/docs")
    assert r.status_code == 200
    assert "scalar" in r.text.lower()


async def test_openapi_is_served(client):
    r = await client.get("/openapi.json")
    assert r.status_code == 200
    assert r.json()["info"]["title"] == "Pix Actions API"


async def test_waitlist_does_not_reveal_existing_emails(client):
    """Same answer for new and existing emails: the endpoint must not let anyone probe who signed up."""
    body = {"email": "Ana@Example.com", "role": "organizer", "lang": "pt"}
    r1 = await client.post("/v1/waitlist", json=body)
    r2 = await client.post("/v1/waitlist", json=body | {"role": "buyer"})
    assert r1.status_code == r2.status_code == 200
    assert r1.json() == r2.json() == {"received": True}


async def test_validation_error_has_standard_shape(client):
    r = await client.post("/v1/waitlist", json={"email": "nope", "role": "organizer"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"
    assert r.json()["error"]["details"]["errors"]


async def test_unknown_route_has_standard_shape(client):
    r = await client.get("/nope")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"


def test_normalize_db_url():
    assert normalize_db_url("postgresql://u:p@h/db?sslmode=require&channel_binding=require") == (
        "postgresql+asyncpg://u:p@h/db?prepared_statement_cache_size=0",
        {"ssl": "require", "statement_cache_size": 0},
    )
    assert normalize_db_url("postgres://u:p@h/db") == (
        "postgresql+asyncpg://u:p@h/db?prepared_statement_cache_size=0",
        {"statement_cache_size": 0},
    )
    assert normalize_db_url("sqlite+aiosqlite:///:memory:") == ("sqlite+aiosqlite:///:memory:", {})
