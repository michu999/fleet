"""
Admin module router.
API endpoints for Ops Panel - super admin operations.

All endpoints require SUPER_ADMIN role.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status,  Response, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, jwt, ALGORITHM
from app.core.config import settings
from app.modules.auth.schemas import UserRead
from app.modules.auth.models import User
from app.core.dependencies import get_current_user
from app.core.dependencies import require_role
from app.core.enums import UserRole
from app.modules.auth.models import User
from app.modules.auth.router import AuthResponse
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
from sqlalchemy import select

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

# =============================================================================
# Impersonation endpoints
# =============================================================================

@router.post("/impersonate/stop", response_model=AuthResponse)
async def stop_impersonation(
        request: Request,
        response: Response,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    """
    Stop impersonation and restore original super admin session
    """
    original_token = request.cookies.get("access_token_original")
    if not original_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No original session found. Please log in again."
        )
    # Restore original token
    response.set_cookie(
        key="access_token",
        value=original_token,
        httponly=True,
        secure=settings.ENVIRONMENT != "development",
        samesite="lax",
        max_age=86400,  # 24 hours
    )
    # Clear impersonation token
    response.delete_cookie(key="access_token_original")

    # Decode original token to get super admin user info
    try:
        payload = jwt.decode(
            original_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM])

        super_admin_id = UUID(payload["sub"])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    result = await db.execute(
        select(User).where(User.id == super_admin_id)
    )
    super_admin = result.scalar_one_or_none()
    if not super_admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User Not Found",
        )
    logger.info(f"ADMIN: Stop impersonation by {super_admin_id}")
    return AuthResponse(
        user=UserRead.model_validate(super_admin),
        is_new_user=False,
    )

@router.post("/impersonate/{user_id}", response_model=AuthResponse)
async def impersonate_user(
        user_id: UUID,
        request: Request,
        response: Response,
        current_user: User = Depends(require_super_admin),
        db: AsyncSession = Depends(get_db),):
    """
    Impersonate a tenant user as a Super Admin.
    Generates a short lived JWT (1h) with the target user's context
    and an 'impersonated_by' claim containing super admin's ID.
    The original super admin token is preserved in a separate cookie.
    """

    logger.info(f"ADMIN: Impersonate user {user_id} by {current_user.email}")
    service = AdminUserService(db)
    target_user = await service.get_user(user_id)

    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User Not Found")
    if not target_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot impersonate inactive user")

    if target_user.role == UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot impersonate another super admin")

    # Preserve original super admin token in a separate cookie
    original_token = request.cookies.get("access_token")
    if original_token:
        response.set_cookie(
            key="access_token_original",
            value=original_token,
            httponly=True,
            secure=settings.ENVIRONMENT != "development",
            samesite="lax",
            max_age=3600,
        )
    impersonation_token = create_access_token({
        "sub": str(target_user.id),
        "tenant_id": str(target_user.tenant_id),
        "role": target_user.role.value,
        "impersonated_by": str(current_user.id),
        "impersonated_by_email": str(current_user.email),
    })
    response.set_cookie(
        key="access_token",
        value=impersonation_token,
        httponly=True,
        secure=settings.ENVIRONMENT != "development",
        samesite="lax",
        max_age=3600,
    )
    logger.info(f"ADMIN: Impersonated user {impersonation_token} by {current_user.email} (tenant_id={target_user.tenant_id})")
    target_user_read = UserRead.model_validate(target_user)
    target_user_read.impersonated_by = str(current_user.id)

    return AuthResponse(
        user=target_user_read,
        is_new_user=False,
    )
