"""
Admin module service layer.
Business logic for super admin operations.

Note: No tenant_id filtering - super admin sees everything.
"""

import logging
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import TenantPlan, TripStatus
from app.core.security import create_access_token, jwt, ALGORITHM
from app.core.config import settings
from app.modules.auth.models import Tenant, User
from app.modules.admin.schemas import (
    TenantCreateAdmin,
    TenantUpdateAdmin,
    UserCreateAdmin,
)

logger = logging.getLogger(__name__)


class AdminTenantService:
    """
    Service for tenant management by super admin.
    No tenant_id scoping - super admin sees all tenants.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_tenants(
        self,
        skip: int = 0,
        limit: int = 50,
        active_only: bool = False,
    ) -> list[Tenant]:
        """List all tenants with optional filtering."""
        query = select(Tenant).order_by(Tenant.created_at.desc())

        if active_only:
            query = query.where(Tenant.is_active == True)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_tenant(self, tenant_id: UUID) -> Tenant | None:
        """Get a tenant by ID."""
        result = await self.db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def create_tenant(self, data: TenantCreateAdmin) -> Tenant:
        """
        Create a new tenant.

        Raises:
            HTTPException 409: If tenant with same slug already exists.
        """
        existing = await self.db.execute(
            select(Tenant).where(Tenant.slug == data.slug)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail="Tenant with this slug already exists",
            )

        tenant = Tenant(
            name=data.name,
            slug=data.slug,
            domain=data.domain,
            plan=data.plan.value,
            max_users=data.max_users,
        )
        self.db.add(tenant)
        await self.db.commit()
        await self.db.refresh(tenant)
        return tenant

    async def update_tenant(
        self,
        tenant: Tenant,
        data: TenantUpdateAdmin,
    ) -> Tenant:
        """
        Update an existing tenant.
        If deactivated, also deactivates all users in the tenant.
        """
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if field == "plan" and value is not None:
                setattr(tenant, field, value.value if isinstance(value, TenantPlan) else value)
            else:
                setattr(tenant, field, value)

        if update_data.get("is_active") is False:
            await self.db.execute(
                update(User)
                .where(User.tenant_id == tenant.id)
                .values(is_active=False)
            )

        await self.db.commit()
        await self.db.refresh(tenant)
        return tenant

    async def get_tenant_stats(self, tenant_id: UUID) -> dict:
        """
        Get statistics for a tenant.

        Returns counts of users, vehicles, orders, and active trips.
        """
        from app.modules.fleet.models import Vehicle, Trip
        from app.modules.orders.models import Order

        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")

        users_count = await self.db.scalar(
            select(func.count(User.id)).where(
                User.tenant_id == tenant_id,
                User.is_active == True,
            )
        )
        vehicles_count = await self.db.scalar(
            select(func.count(Vehicle.id)).where(Vehicle.tenant_id == tenant_id)
        )
        orders_count = await self.db.scalar(
            select(func.count(Order.id)).where(Order.tenant_id == tenant_id)
        )
        active_trips_count = await self.db.scalar(
            select(func.count(Trip.id)).where(
                Trip.tenant_id == tenant_id,
                Trip.status == TripStatus.IN_PROGRESS,
            )
        )

        return {
            "tenant_id": tenant_id,
            "tenant_name": tenant.name,
            "users_count": users_count or 0,
            "vehicles_count": vehicles_count or 0,
            "orders_count": orders_count or 0,
            "active_trips_count": active_trips_count or 0,
        }


class AdminUserService:
    """
    Service for user management by super admin.
    Operates across all tenants.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_users_for_tenant(self, tenant_id: UUID) -> list[User]:
        """List all users for a specific tenant."""
        result = await self.db.execute(
            select(User)
            .where(User.tenant_id == tenant_id)
            .order_by(User.created_at)
        )
        return list(result.scalars().all())

    async def get_user(self, user_id: UUID) -> User | None:
        """Get a user by ID (global, no tenant filter)."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_user_for_tenant(
        self,
        tenant_id: UUID,
        data: UserCreateAdmin,
    ) -> User:
        """
        Create a new user for a tenant.

        Raises:
            HTTPException 404: If tenant not found or inactive.
            HTTPException 409: If user limit reached or email exists.
        """
        tenant = await self.db.get(Tenant, tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        if not tenant.is_active:
            raise HTTPException(status_code=400, detail="Tenant is inactive")

        current_count = await self.db.scalar(
            select(func.count(User.id)).where(
                User.tenant_id == tenant_id,
                User.is_active == True,
            )
        )
        if current_count >= tenant.max_users:
            raise HTTPException(
                status_code=409,
                detail=f"Tenant has reached maximum users limit ({tenant.max_users})",
            )

        existing = await self.db.execute(
            select(User).where(User.email == data.email)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail="User with this email already exists",
            )

        user = User(
            tenant_id=tenant_id,
            email=data.email,
            name=data.name,
            role=data.role,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_user(
        self,
        user_id: UUID,
        data: dict,
        current_user_id: UUID,
    ) -> User:
        """
        Update a user.

        Raises:
            HTTPException 404: If user not found.
            HTTPException 400: If trying to modify own role.
        """
        user = await self.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if "role" in data and user_id == current_user_id:
            raise HTTPException(
                status_code=400,
                detail="Cannot change your own role",
            )

        for field, value in data.items():
            setattr(user, field, value)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def impersonate_user(
        self,
        target_user_id: UUID,
        super_admin: User,
    ) -> tuple[str, User]:
        """
        Generate impersonation token for a tenant user.

        Raises:
            HTTPException 404: If user not found.
            HTTPException 400: If user is inactive or is a super admin.

        Returns:
            Tuple of (impersonation_token, target_user)
        """
        target_user = await self.get_user(target_user_id)

        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        if not target_user.is_active:
            raise HTTPException(status_code=400, detail="Cannot impersonate inactive user")
        if target_user.role.value == "super_admin":
            raise HTTPException(status_code=400, detail="Cannot impersonate another super admin")

        token = create_access_token({
            "sub": str(target_user.id),
            "tenant_id": str(target_user.tenant_id),
            "role": target_user.role.value,
            "impersonated_by": str(super_admin.id),
            "impersonated_by_email": super_admin.email,
        })

        return token, target_user

    async def stop_impersonation(self, original_token: str) -> User:
        """
        Decode original super admin token and return super admin user.

        Raises:
            HTTPException 401: If token is invalid.
            HTTPException 404: If super admin user not found.

        Returns:
            Super admin User object.
        """
        try:
            payload = jwt.decode(
                original_token,
                settings.SECRET_KEY,
                algorithms=[ALGORITHM],
            )
            super_admin_id = UUID(payload["sub"])
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Original session expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid original session token")

        result = await self.db.execute(
            select(User).where(User.id == super_admin_id)
        )
        super_admin = result.scalar_one_or_none()

        if not super_admin:
            raise HTTPException(status_code=404, detail="Super admin user not found")

        return super_admin