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
