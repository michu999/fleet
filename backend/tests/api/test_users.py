"""
API tests for user/auth endpoints.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.core.enums import UserRole
from app.modules.auth.models import Tenant, User


@pytest.fixture
async def test_tenant(db_session: AsyncSession) -> Tenant:
    """Create a test tenant."""
    tenant = Tenant(
        name="Test Company",
        slug="test-company",
        domain="test.com",
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest.fixture
async def test_user(db_session: AsyncSession, test_tenant: Tenant) -> User:
    """Create a test user."""
    user = User(
        tenant_id=test_tenant.id,
        email="test@test.com",
        name="Test User",
        role=UserRole.ADMIN,
        google_id="google123",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, test_user: User):
    """Test getting current authenticated user."""
    # Create JWT token for test user
    token = create_access_token({
        "sub": str(test_user.id),
        "tenant_id": str(test_user.tenant_id),
        "role": test_user.role.value,
    })

    # Set cookie in request
    client.cookies.set("access_token", token)

    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@test.com"
    assert data["name"] == "Test User"
    assert data["id"] == str(test_user.id)


@pytest.mark.asyncio
async def test_get_current_user_unauthorized(client: AsyncClient):
    """Test getting current user without authentication returns 401."""
    # No cookie set
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(client: AsyncClient):
    """Test getting current user with invalid token returns 401."""
    client.cookies.set("access_token", "invalid-token")

    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


@pytest.mark.asyncio
async def test_get_current_user_inactive(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
):
    """Test that inactive users cannot authenticate."""
    # Create inactive user
    inactive_user = User(
        tenant_id=test_tenant.id,
        email="inactive@test.com",
        name="Inactive User",
        role=UserRole.DRIVER,
        is_active=False,
    )
    db_session.add(inactive_user)
    await db_session.commit()
    await db_session.refresh(inactive_user)

    # Create token for inactive user
    token = create_access_token({
        "sub": str(inactive_user.id),
        "tenant_id": str(inactive_user.tenant_id),
        "role": inactive_user.role.value,
    })

    client.cookies.set("access_token", token)

    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "User account is deactivated"
