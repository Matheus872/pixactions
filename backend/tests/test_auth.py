import json
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from httpx import ASGITransport, AsyncClient
from jwt.algorithms import ECAlgorithm

from pixactions_api.auth import _jwks_client
from pixactions_api.main import create_app
from pixactions_api.pix.mock import MockPixProvider
from tests.helpers import FakeSolanaGateway


@pytest.fixture
def jwks_key(settings, monkeypatch):
    """No PEM configured: the API must use the app's published JWKS (served here from memory)."""
    priv = ec.generate_private_key(ec.SECP256R1())
    jwk = json.loads(ECAlgorithm.to_jwk(priv.public_key())) | {"kid": "k1", "alg": "ES256", "use": "sig"}
    monkeypatch.setattr(jwt.PyJWKClient, "fetch_data", lambda self: {"keys": [jwk]})
    _jwks_client.cache_clear()
    settings.privy_verification_key = ""
    return priv


def _token(priv, settings, kid: str) -> str:
    now = int(time.time())
    claims = {"sub": "did:privy:x", "iss": "privy.io", "aud": settings.privy_app_id, "iat": now, "exp": now + 60}
    return jwt.encode(claims, priv, algorithm="ES256", headers={"kid": kid})


async def _get_my_events(settings, token: str) -> int:
    app = create_app(settings, gateway=FakeSolanaGateway(), pix=MockPixProvider(settings))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/v1/me/events", headers={"Authorization": f"Bearer {token}"})
    return r.status_code


async def test_jwks_mode_accepts_token_signed_with_published_key(settings, jwks_key):
    assert await _get_my_events(settings, _token(jwks_key, settings, "k1")) == 200


async def test_jwks_mode_rejects_unknown_kid(settings, jwks_key):
    assert await _get_my_events(settings, _token(jwks_key, settings, "other")) == 401


async def test_jwks_mode_rejects_token_signed_by_another_key(settings, jwks_key):
    stranger = ec.generate_private_key(ec.SECP256R1())
    assert await _get_my_events(settings, _token(stranger, settings, "k1")) == 401


def test_jwks_url_is_derived_from_app_id(settings):
    assert settings.privy_jwks_url == "https://auth.privy.io/api/v1/apps/test-app/jwks.json"
