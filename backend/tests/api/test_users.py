"""
API tests for user endpoints.

Note: These tests are skipped until auth module is implemented.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.skip(reason="Endpoint /api/v1/users/me not implemented yet")
async def test_get_current_user(client: AsyncClient):
    """Test getting current authenticated user."""
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 200
    assert "email" in response.json()


@pytest.mark.asyncio
@pytest.mark.skip(reason="Endpoint /api/v1/users/me not implemented yet")
async def test_get_current_user_unauthorized(client: AsyncClient):
    """Test getting current user without authentication returns 401."""
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401
