import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient):
    response = await client.get("/users/me")
    assert response.status_code == 200
    assert "email" in response.json()