"""
API tests for authentication endpoints.
Tests Google OAuth flow with mocked Google verification.
"""

import pytest
from unittest.mock import patch
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.core.enums import UserRole
from app.modules.auth.models import Tenant, User


@pytest.fixture
async def existing_tenant(db_session: AsyncSession) -> Tenant:
    """Create an existing tenant for tests."""
    tenant = Tenant(
        name="existing.com",
        slug="existing-com",
        domain="existing.com",
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest.fixture
async def existing_user(db_session: AsyncSession, existing_tenant: Tenant) -> User:
    """Create an existing user for tests."""
    user = User(
        tenant_id=existing_tenant.id,
        email="existing@existing.com",
        name="Existing User",
        role=UserRole.ADMIN,
        google_id="existing-google-id",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestGoogleAuth:
    """Tests for POST /api/v1/auth/google endpoint."""

    @pytest.mark.asyncio
    async def test_google_auth_new_user(self, client: AsyncClient, db_session: AsyncSession):
        """Test Google auth creates new user and tenant."""
        mock_google_data = {
            "email": "newuser@newcompany.com",
            "name": "New User",
            "picture": "https://example.com/photo.jpg",
            "google_id": "google-id-12345",
        }

        with patch("app.modules.auth.router.verify_google_token") as mock_verify:
            mock_verify.return_value = mock_google_data

            response = await client.post(
                "/api/v1/auth/google",
                json={"credential": "fake-google-token"},
            )

        assert response.status_code == 200
        data = response.json()

        assert data["is_new_user"] is True
        assert data["user"]["email"] == "newuser@newcompany.com"
        assert data["user"]["name"] == "New User"
        assert data["user"]["role"] == UserRole.ADMIN.value

        # Check cookie was set
        assert "access_token" in response.cookies

    @pytest.mark.asyncio
    async def test_google_auth_existing_user(
        self,
        client: AsyncClient,
        existing_user: User,
    ):
        """Test Google auth for existing user updates profile."""
        mock_google_data = {
            "email": "existing@existing.com",
            "name": "Updated Name",
            "picture": "https://example.com/new-photo.jpg",
            "google_id": "updated-google-id",
        }

        with patch("app.modules.auth.router.verify_google_token") as mock_verify:
            mock_verify.return_value = mock_google_data

            response = await client.post(
                "/api/v1/auth/google",
                json={"credential": "fake-google-token"},
            )

        assert response.status_code == 200
        data = response.json()

        assert data["is_new_user"] is False
        assert data["user"]["email"] == "existing@existing.com"
        assert data["user"]["name"] == "Updated Name"

        # Check cookie was set
        assert "access_token" in response.cookies

    @pytest.mark.asyncio
    async def test_google_auth_invalid_token(self, client: AsyncClient):
        """Test Google auth with invalid token returns 401."""
        from fastapi import HTTPException

        with patch("app.modules.auth.router.verify_google_token") as mock_verify:
            mock_verify.side_effect = HTTPException(status_code=401, detail="Invalid Google token: test")

            response = await client.post(
                "/api/v1/auth/google",
                json={"credential": "invalid-token"},
            )

        assert response.status_code == 401
        assert "Invalid Google token" in response.json()["detail"]


class TestLogout:
    """Tests for POST /api/v1/auth/logout endpoint."""

    @pytest.mark.asyncio
    async def test_logout_clears_cookie(self, client: AsyncClient):
        """Test logout clears the auth cookie."""
        # First, set a cookie
        client.cookies.set("access_token", "some-token")

        response = await client.post("/api/v1/auth/logout")

        assert response.status_code == 200
        assert response.json()["message"] == "Logged out successfully"

        # Cookie should be cleared (set to empty or deleted)
        # Note: httpx handles this differently, we check the Set-Cookie header
        set_cookie_header = response.headers.get("set-cookie", "")
        assert "access_token" in set_cookie_header
        # Cookie deletion sets max-age=0 or expires in past
        assert "max-age=0" in set_cookie_header.lower() or "expires=" in set_cookie_header.lower()

    @pytest.mark.asyncio
    async def test_logout_without_cookie(self, client: AsyncClient):
        """Test logout works even without existing cookie."""
        response = await client.post("/api/v1/auth/logout")

        assert response.status_code == 200
        assert response.json()["message"] == "Logged out successfully"


class TestGetMe:
    """Tests for GET /api/v1/auth/me endpoint."""

    @pytest.mark.asyncio
    async def test_get_me_success(self, client: AsyncClient, existing_user: User):
        """Test getting current user with valid token."""
        token = create_access_token({
            "sub": str(existing_user.id),
            "tenant_id": str(existing_user.tenant_id),
            "role": existing_user.role.value,
        })

        client.cookies.set("access_token", token)

        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == existing_user.email
        assert data["id"] == str(existing_user.id)

    @pytest.mark.asyncio
    async def test_get_me_no_cookie(self, client: AsyncClient):
        """Test getting current user without cookie returns 401."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"



