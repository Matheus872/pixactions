from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference
from solders.keypair import Keypair
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from . import __version__
from .config import Settings, get_settings
from .db import make_engine
from .docs_meta import API_DESCRIPTION, TAGS
from .errors import install_error_handlers
from .pix.base import PixProvider
from .pix.mock import MockPixProvider
from .routers import actions, dev, events, health, orders, tickets, waitlist, webhooks
from .solana.gateway import RpcSolanaGateway, SolanaGateway

ACTION_HEADERS = [
    "Content-Type", "Authorization", "Content-Encoding", "Accept-Encoding",
    "X-Action-Version", "X-Blockchain-Ids",
]


def create_app(
    settings: Settings | None = None,
    *,
    gateway: SolanaGateway | None = None,
    pix: PixProvider | None = None,
    engine: AsyncEngine | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(
        title="Pix Actions API",
        version=__version__,
        description=API_DESCRIPTION,
        openapi_tags=TAGS,
        docs_url=None,
        redoc_url="/redoc",
        servers=[{"url": settings.public_api_url, "description": settings.env}],
    )
    engine = engine or make_engine(settings.database_url)
    app.state.settings = settings
    app.state.engine = engine
    app.state.sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    app.state.db_ready = False
    app.state.gateway = gateway or RpcSolanaGateway(settings.solana_rpc_url)
    app.state.pix = pix or MockPixProvider(settings)
    app.state.service = (
        Keypair.from_base58_string(settings.service_keypair) if settings.service_keypair else Keypair()
    )

    # Bearer tokens (no cookies), so a wildcard origin is safe; Solana Actions require it.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "PUT", "OPTIONS"],
        allow_headers=ACTION_HEADERS,
        expose_headers=["X-Action-Version", "X-Blockchain-Ids"],
    )
    install_error_handlers(app)
    for router in (health.router, waitlist.router, events.router, orders.router, webhooks.router,
                   tickets.router, actions.router):
        app.include_router(router)
    if not settings.is_production:
        app.include_router(dev.router)

    @app.get("/docs", include_in_schema=False)
    async def scalar_docs():
        return get_scalar_api_reference(openapi_url=app.openapi_url, title=app.title)

    return app


app = create_app()
