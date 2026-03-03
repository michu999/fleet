"""
API tests for health endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint returns OK status."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "environment" in data


@pytest.mark.asyncio
async def test_health_check_returns_environment(client: AsyncClient):
    """Test health check includes environment info."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["environment"] in ["development", "staging", "production"]
