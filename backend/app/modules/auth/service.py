"""
Auth module service layer.
Business logic for tenant, user, and driver profile management.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import Tenant, User, DriverProfile
from app.modules.auth.schemas import (
    TenantCreate,
    TenantUpdate,
    UserUpdate,
    DriverProfileCreate,
    DriverProfileUpdate,
)

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from fastapi import HTTPException, status

from app.core.config import get_settings
from app.core.config import settings
from app.core.enums import UserRole

logger = logging.getLogger(__name__)

# Thread pool for blocking Google API calls
_google_executor = ThreadPoolExecutor(max_workers=4)


class TenantService:
    """Service for tenant operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, tenant_id: UUID) -> Tenant | None:
        """Get tenant by ID."""
        result = await self.db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Tenant | None:
        """Get tenant by slug."""
        result = await self.db.execute(
            select(Tenant).where(Tenant.slug == slug)
        )
        return result.scalar_one_or_none()

    async def create(self, data: TenantCreate) -> Tenant:
        """Create a new tenant."""
        tenant = Tenant(**data.model_dump())
        self.db.add(tenant)
        await self.db.flush()
        return tenant

    async def update(self, tenant: Tenant, data: TenantUpdate) -> Tenant:
        """Update an existing tenant."""
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tenant, field, value)
        await self.db.flush()
        return tenant

    async def delete(self, tenant: Tenant) -> None:
        """Soft delete a tenant by deactivating it."""
        tenant.is_active = False
        await self.db.flush()


class UserService:
    """Service for user operations."""

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Get user by ID within tenant."""
        result = await self.db.execute(
            select(User).where(
                User.id == user_id,
                User.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email within tenant."""
        result = await self.db.execute(
            select(User).where(
                User.email == email,
                User.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_google_id(self, google_id: str) -> User | None:
        """Get user by Google ID within tenant."""
        result = await self.db.execute(
            select(User).where(
                User.google_id == google_id,
                User.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        """List all users in tenant."""
        result = await self.db.execute(
            select(User)
            .where(User.tenant_id == self.tenant_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update(self, user: User, data: UserUpdate) -> User:
        """Update an existing user."""
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        await self.db.flush()
        return user

    async def deactivate(self, user: User) -> User:
        """Deactivate a user."""
        user.is_active = False
        await self.db.flush()
        return user


class DriverProfileService:
    """Service for driver profile operations."""

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def get_by_user_id(self, user_id: UUID) -> DriverProfile | None:
        """Get driver profile by user ID."""
        result = await self.db.execute(
            select(DriverProfile).where(
                DriverProfile.user_id == user_id,
                DriverProfile.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def create(self, data: DriverProfileCreate) -> DriverProfile:
        """Create a new driver profile."""
        profile = DriverProfile(
            **data.model_dump(),
            tenant_id=self.tenant_id,
        )
        self.db.add(profile)
        await self.db.flush()
        return profile

    async def update(
        self, profile: DriverProfile, data: DriverProfileUpdate
    ) -> DriverProfile:
        """Update an existing driver profile."""
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(profile, field, value)
        await self.db.flush()
        return profile


# =============================================================================
# Google OAuth 2.0 Functions
# =============================================================================

async def verify_google_token(credential: str) -> dict:
    """
    Verify Google OAuth token and extract user info.

    Uses thread pool executor to avoid blocking the async event loop
    since google-auth library uses synchronous HTTP requests.

    Args:
        credential: Google ID token from frontend.

    Returns:
        Dict with user info: {email, name, picture, google_id}

    Raises:
        HTTPException 401: If token is invalid or expired.
    """
    settings = get_settings()
    loop = asyncio.get_event_loop()

    def _verify_token():
        return id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=10,
        )

    try:
        idinfo = await loop.run_in_executor(_google_executor, _verify_token)

        return {
            "email": idinfo["email"],
            "name": idinfo.get("name", ""),
            "picture": idinfo.get("picture"),
            "google_id": idinfo["sub"],
        }
    except ValueError as e:
        # Log the actual error for debugging, but return generic message
        logger.warning(f"Google token verification failed: {e}")
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired Google token"
        )


async def get_user_by_email_global(db: AsyncSession, email: str) -> User | None:
    """
    Find user by email across all tenants.
    Used for OAuth login where we don't know tenant yet.

    Args:
        db: Database session.
        email: User's email address.

    Returns:
        User if found, None otherwise.
    """
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()


async def get_or_create_oauth_user(
    db: AsyncSession,
    google_data: dict,
) -> tuple[User, bool]:
    """
    Find existing user by email and authenticate.

    Only allows users pre-created by Super Admin via Ops Panel.
    Self-registration is disabled.

    Returns:
        Tuple of (User, is_new_user: bool)

    Raises:
        HTTPException 403: If email is not registered in the system.
    """
    # Existing user — update profile and allow in

    existing = await get_user_by_email_global(db, google_data["email"])
    if existing:
        existing.name = google_data["name"]
        existing.picture = google_data["picture"]
        existing.google_id = google_data["google_id"]
        await db.commit()
        await db.refresh(existing)
        return existing, False

    # Super admin — create without tenant
    if google_data["email"] in settings.get_super_admin_emails():
        user = User(
            email=google_data["email"],
            name=google_data["name"],
            picture=google_data["picture"],
            google_id=google_data["google_id"],
            role=UserRole.SUPER_ADMIN.value,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user, True

    # Unknown email — deny access
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Brak dostępu. Skontaktuj się z administratorem. (TUTAJ EMAIL ADMINA)",
    )

