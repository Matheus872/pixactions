from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .errors import ApiError, ErrorCode


@dataclass(frozen=True)
class User:
    did: str


_bearer = HTTPBearer(
    auto_error=False,
    description="Privy access token, from `getAccessToken()` in the Privy SDK.",
)


@lru_cache(maxsize=4)
def _jwks_client(url: str) -> jwt.PyJWKClient:
    """Cached JWKS client: Privy publishes the app's signing keys and rotates them."""
    return jwt.PyJWKClient(url, cache_keys=True, lifespan=3600)


def _verification_key(token: str, settings) -> object:
    """A configured PEM wins (tests, pinned key); otherwise pick the published key by the token's kid."""
    if settings.privy_verification_key.strip():
        return settings.privy_key_pem
    return _jwks_client(settings.privy_jwks_url).get_signing_key_from_jwt(token).key


async def current_user(
    request: Request,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    if creds is None:
        raise ApiError(ErrorCode.UNAUTHORIZED, "Missing bearer token")
    settings = request.app.state.settings
    try:
        claims = jwt.decode(
            creds.credentials,
            _verification_key(creds.credentials, settings),
            algorithms=["ES256"],
            audience=settings.privy_app_id,
            issuer="privy.io",
        )
    except jwt.PyJWTError as exc:
        raise ApiError(ErrorCode.UNAUTHORIZED, "Invalid or expired access token") from exc
    return User(did=str(claims["sub"]))


UserDep = Annotated[User, Depends(current_user)]
