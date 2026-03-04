"""
Admin module router.
API endpoints for Ops Panel - super admin operations.

All endpoints require SUPER_ADMIN role.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_role
from app.core.enums import UserRole
from app.modules.auth.models import User
from app.modules.auth.schemas import TenantUpdate
from app.modules.admin.schemas import (
    TenantCreateAdmin,
    TenantResponse,
    TenantStatsResponse,
    TenantUpdateAdmin,
    UserCreateAdmin,
    UserUpdateAdmin,
    UserResponseAdmin,
)
from app.modules.admin.service import AdminTenantService, AdminUserService

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependency: require SUPER_ADMIN for all endpoints
require_super_admin = require_role(UserRole.SUPER_ADMIN)


# =============================================================================
# Tenant Endpoints
# =============================================================================

@router.get("/tenants", response_model=list[TenantResponse])
async def list_tenants(
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    active_only: bool = Query(False),
):
    """
    List all tenants with pagination.
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 50, max: 100)
    - **active_only**: Filter to show only active tenants (default: False)
    """
    logger.info(f"ADMIN: List tenants by {current_user.email}")
    
    service = AdminTenantService(db)
    tenants = await service.list_tenants(skip=skip, limit=limit, active_only=active_only)
    return [TenantResponse.model_validate(t) for t in tenants]


@router.post("/tenants", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    data: TenantCreateAdmin,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new tenant.
    
    Returns 409 if tenant with same slug already exists.
    """
    logger.info(f"ADMIN: Create tenant '{data.slug}' by {current_user.email}")
    
    service = AdminTenantService(db)
    tenant = await service.create_tenant(data)
    
    logger.info(f"ADMIN: Created tenant '{tenant.slug}' (id={tenant.id}) by {current_user.email}")
    return TenantResponse.model_validate(tenant)


@router.get("/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: UUID,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific tenant by ID.
    
    Returns 404 if tenant not found.
    """
    logger.info(f"ADMIN: Get tenant {tenant_id} by {current_user.email}")
    
    service = AdminTenantService(db)
    tenant = await service.get_tenant(tenant_id)
    
    if not tenant:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return TenantResponse.model_validate(tenant)


@router.patch("/tenants/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: UUID,
    data: TenantUpdateAdmin,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a tenant.
    
    Returns 404 if tenant not found.
    """
    logger.info(f"ADMIN: Update tenant {tenant_id} by {current_user.email}")
    
    service = AdminTenantService(db)
    tenant = await service.get_tenant(tenant_id)
    
    if not tenant:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    updated = await service.update_tenant(tenant, data)
    
    logger.info(f"ADMIN: Updated tenant {tenant_id} by {current_user.email}")
    return TenantResponse.model_validate(updated)


@router.get("/tenants/{tenant_id}/stats", response_model=TenantStatsResponse)
async def get_tenant_stats(
    tenant_id: UUID,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get statistics for a tenant.
    
    Returns counts of users, vehicles, orders, and active trips.
    Returns 404 if tenant not found.
    """
    logger.info(f"ADMIN: Get stats for tenant {tenant_id} by {current_user.email}")
    
    service = AdminTenantService(db)
    stats = await service.get_tenant_stats(tenant_id)
    return TenantStatsResponse(**stats)


# =============================================================================
# User Endpoints
# =============================================================================

@router.get("/tenants/{tenant_id}/users", response_model=list[UserResponseAdmin])
async def list_users_for_tenant(
    tenant_id: UUID,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    List all users for a specific tenant.
    """
    logger.info(f"ADMIN: List users for tenant {tenant_id} by {current_user.email}")
    
    service = AdminUserService(db)
    users = await service.list_users_for_tenant(tenant_id)
    return [UserResponseAdmin.model_validate(u) for u in users]


@router.post(
    "/tenants/{tenant_id}/users",
    response_model=UserResponseAdmin,
    status_code=status.HTTP_201_CREATED,
)
async def create_user_for_tenant(
    tenant_id: UUID,
    data: UserCreateAdmin,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new user for a tenant.
    
    Returns 404 if tenant not found or inactive.
    Returns 409 if email already exists or user limit reached.
    """
    logger.info(f"ADMIN: Create user '{data.email}' for tenant {tenant_id} by {current_user.email}")
    
    service = AdminUserService(db)
    user = await service.create_user_for_tenant(tenant_id, data)
    
    logger.info(f"ADMIN: Created user '{user.email}' (id={user.id}) by {current_user.email}")
    return UserResponseAdmin.model_validate(user)


@router.patch("/users/{user_id}", response_model=UserResponseAdmin)
async def update_user(
    user_id: UUID,
    data: UserUpdateAdmin,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a user.
    
    Returns 404 if user not found.
    Returns 400 if trying to change own role.
    """
    logger.info(f"ADMIN: Update user {user_id} by {current_user.email}")
    
    service = AdminUserService(db)
    update_data = data.model_dump(exclude_unset=True)
    user = await service.update_user(user_id, update_data, current_user.id)
    
    logger.info(f"ADMIN: Updated user {user_id} by {current_user.email}")
    return UserResponseAdmin.model_validate(user)
