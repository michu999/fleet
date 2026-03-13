"""
FastAPI dependency injection functions.
Authentication and authorization dependencies.
"""

from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.core.enums import UserRole
from app.modules.auth.models import User

import logging

logger = logging.getLogger(__name__)

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get current authenticated user from JWT cookie.

    Extracts token from httpOnly cookie, validates it,
    and returns the User object from database.

    Raises:
        HTTPException 401: If not authenticated or token invalid.
    """
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
        )

    result = await db.execute(
        select(User).where(User.id == user_uuid)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated",
        )
    user.impersonated_by = payload.get("impersonated_by")

    # Set RLS context for tenant isolation (parametrized to prevent SQL injection)
    if user.tenant_id and user.role != UserRole.SUPER_ADMIN:
        try:
            validated_tenant_id = UUID(str(user.tenant_id))
            await db.execute(text(f"SET LOCAL app.tenant_id = '{validated_tenant_id}'"))

        except (ValueError, TypeError) as e:
            logger.error(f"Invalid tenant_id for user {user.tenant_id: {e}}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid tenant_id for user {user.tenant_id: {e}}",
            )

    return user


def require_role(*roles: UserRole):
    """
    Dependency factory for role-based access control.

    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(
            user: User = Depends(require_role(UserRole.ADMIN))
        ):
            ...

        # Multiple roles:
        @router.get("/managers")
        async def managers_endpoint(
            user: User = Depends(require_role(UserRole.ADMIN, UserRole.MANAGER))
        ):
            ...

    Note:
        SUPER_ADMIN always passes regardless of required roles.

    Returns:
        Dependency function that validates user role.

    Raises:
        HTTPException 403: If user doesn't have required role.
    """
    async def checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        # SUPER_ADMIN bypasses all role checks
        if current_user.role == UserRole.SUPER_ADMIN:
            return current_user

        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return checker

def require_role_with_tenant(*roles: UserRole):
    """
    Like require_role but also ensures user has tenant_id if the user doesnt have tenant_id then he is a super admin.
    Use for all endpoints that create/modify operational data.
    """
    async def checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role == UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Super admin must use a tenant account for this operation.",
            )
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user
    return checker


# Convenience dependencies for common role checks
require_admin = require_role(UserRole.ADMIN)
require_manager = require_role(UserRole.ADMIN, UserRole.MANAGER)
require_dispatcher = require_role(UserRole.ADMIN, UserRole.MANAGER, UserRole.DISPATCHER)
require_driver = require_role(UserRole.ADMIN, UserRole.MANAGER, UserRole.DISPATCHER, UserRole.DRIVER)

# Convenience dependencies for role checks that also require tenant_id (for operational data endpoints)
require_admin_tenant = require_role_with_tenant(UserRole.ADMIN)
require_manager_tenant = require_role_with_tenant(UserRole.ADMIN, UserRole.MANAGER)
require_dispatcher_tenant = require_role_with_tenant(UserRole.ADMIN, UserRole.MANAGER, UserRole.DISPATCHER)
require_driver_tenant = require_role_with_tenant(UserRole.ADMIN, UserRole.MANAGER, UserRole.DISPATCHER, UserRole.DRIVER)
