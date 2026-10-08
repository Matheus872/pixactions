from dataclasses import dataclass
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
            settings.privy_key_pem,
            algorithms=["ES256"],
            audience=settings.privy_app_id,
            issuer="privy.io",
        )
    except jwt.PyJWTError as exc:
        raise ApiError(ErrorCode.UNAUTHORIZED, "Invalid or expired access token") from exc
    return User(did=str(claims["sub"]))


UserDep = Annotated[User, Depends(current_user)]
