import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def test_health(client: AsyncClient) -> None:
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}
