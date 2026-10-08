from typing import Annotated

from fastapi import Depends, Request
from solders.keypair import Keypair
from sqlalchemy.ext.asyncio import AsyncSession

from .config import Settings
from .db import get_session
from .pix.base import PixProvider
from .solana.gateway import SolanaGateway


def _settings(request: Request) -> Settings:
    return request.app.state.settings


def _gateway(request: Request) -> SolanaGateway:
    return request.app.state.gateway


def _pix(request: Request) -> PixProvider:
    return request.app.state.pix


def _service(request: Request) -> Keypair:
    return request.app.state.service


SettingsDep = Annotated[Settings, Depends(_settings)]
GatewayDep = Annotated[SolanaGateway, Depends(_gateway)]
PixDep = Annotated[PixProvider, Depends(_pix)]
ServiceDep = Annotated[Keypair, Depends(_service)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]
