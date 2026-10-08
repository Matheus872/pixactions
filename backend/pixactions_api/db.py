from collections.abc import AsyncIterator
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool, StaticPool


class Base(DeclarativeBase):
    pass


def normalize_db_url(url: str) -> tuple[str, dict[str, Any]]:
    """Turn a Neon/Vercel Postgres URL into an asyncpg URL + connect_args (PgBouncer-safe)."""
    if url.startswith("sqlite"):
        return url, {}
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query))
    connect_args: dict[str, Any] = {}
    if query.pop("sslmode", None) in {"require", "verify-ca", "verify-full", "prefer"}:
        connect_args["ssl"] = "require"
    query.pop("channel_binding", None)
    query["prepared_statement_cache_size"] = "0"
    connect_args["statement_cache_size"] = 0
    return urlunsplit(("postgresql+asyncpg", parts.netloc, parts.path, urlencode(query), "")), connect_args


def make_engine(url: str) -> AsyncEngine:
    url, connect_args = normalize_db_url(url)
    if url.startswith("sqlite"):
        kwargs: dict[str, Any] = {"connect_args": {"check_same_thread": False}}
        if ":memory:" in url:
            kwargs["poolclass"] = StaticPool
        return create_async_engine(url, **kwargs)
    return create_async_engine(url, poolclass=NullPool, connect_args=connect_args)


async def init_db(engine: AsyncEngine) -> None:
    from . import models  # noqa: F401  (registers tables on Base.metadata)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    state = request.app.state
    if not state.db_ready:
        await init_db(state.engine)
        state.db_ready = True
    async with state.sessionmaker() as session:
        yield session
