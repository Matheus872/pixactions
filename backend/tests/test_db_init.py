import asyncio

from httpx import ASGITransport, AsyncClient

from pixactions_api.main import create_app
from pixactions_api.pix.mock import MockPixProvider
from tests.helpers import FakeSolanaGateway


async def test_concurrent_first_requests_create_tables_once(settings, tmp_path):
    """The dashboard fires several requests at once on a cold start; none may fail creating tables."""
    settings.database_url = f"sqlite+aiosqlite:///{tmp_path / 'cold.db'}"
    app = create_app(settings, gateway=FakeSolanaGateway(), pix=MockPixProvider(settings))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        responses = await asyncio.gather(*(c.get(f"/v1/events/missing-{i}") for i in range(8)))
    assert [r.status_code for r in responses] == [404] * 8
