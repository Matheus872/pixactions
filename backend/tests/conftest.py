import time

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from httpx import ASGITransport, AsyncClient
from solders.keypair import Keypair

from pixactions_api.config import Settings
from pixactions_api.main import create_app
from pixactions_api.pix.mock import MockPixProvider
from tests.helpers import FakeSolanaGateway, create_draft, seed_event_account, sign_b64


@pytest.fixture
def privy_keys():
    priv = ec.generate_private_key(ec.SECP256R1())
    pub = priv.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
    return priv, pub


@pytest.fixture
def service() -> Keypair:
    return Keypair()


@pytest.fixture
def settings(privy_keys, service) -> Settings:
    return Settings(
        _env_file=None,
        env="test",
        database_url="sqlite+aiosqlite:///:memory:",
        service_keypair=str(service),
        mock_usdc_mint=str(Keypair().pubkey()),
        privy_app_id="test-app",
        privy_verification_key=privy_keys[1],
        pix_webhook_secret="whsec",
        mock_pix_autopay_seconds=0,
        public_web_url="https://pixactions.test",
        public_api_url="https://api.pixactions.test",
    )


@pytest.fixture
def gateway() -> FakeSolanaGateway:
    return FakeSolanaGateway()


@pytest.fixture
def app(settings, gateway):
    return create_app(settings, gateway=gateway, pix=MockPixProvider(settings))


@pytest.fixture
async def client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
def auth(privy_keys, settings):
    def make(did: str = "did:privy:alice") -> dict[str, str]:
        now = int(time.time())
        claims = {"sub": did, "iss": "privy.io", "aud": settings.privy_app_id, "iat": now, "exp": now + 3600}
        return {"Authorization": f"Bearer {jwt.encode(claims, privy_keys[0], algorithm='ES256')}"}

    return make


@pytest.fixture
async def live_event(client, auth, gateway):
    organizer = Keypair()
    draft = await create_draft(client, auth, organizer)
    signed = sign_b64(draft["transaction"], organizer)
    r = await client.post(f"/v1/events/{draft['event']['id']}/submit", json={"transaction": signed}, headers=auth())
    assert r.status_code == 200, r.text
    event = r.json()
    seed_event_account(gateway, event)
    return {"event": event, "organizer": organizer}
