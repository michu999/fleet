"""
Admin module schemas for request/response validation.
Used for Ops Panel - super admin operations.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.enums import TenantPlan, UserRole


# =============================================================================
# Tenant Schemas for Admin
# =============================================================================

class TenantCreateAdmin(BaseModel):
    """Schema for creating a tenant via admin panel."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    domain: str | None = Field(None, max_length=255)
    plan: TenantPlan = TenantPlan.TRIAL
    max_users: int = Field(default=10, ge=1, le=1000)


class TenantUpdateAdmin(BaseModel):
    """Schema for updating a tenant via admin panel."""
    name: str | None = Field(None, min_length=1, max_length=255)
    domain: str | None = Field(None, max_length=255)
    is_active: bool | None = None
    plan: TenantPlan | None = None
    max_users: int | None = Field(None, ge=1, le=1000)


class TenantResponse(BaseModel):
    """Schema for tenant response in admin panel."""
    id: UUID
    name: str
    slug: str
    domain: str | None
    plan: str
    is_active: bool
    max_users: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TenantStatsResponse(BaseModel):
    """Schema for tenant statistics."""
    tenant_id: UUID
    tenant_name: str
    users_count: int
    vehicles_count: int
    orders_count: int
    active_trips_count: int


# =============================================================================
# User Schemas for Admin
# =============================================================================

class UserCreateAdmin(BaseModel):
    """Schema for creating a user via admin panel."""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    role: UserRole = UserRole.ADMIN

    @field_validator("role")
    @classmethod
    def role_cannot_be_super_admin(cls, v: UserRole) -> UserRole:
        """Prevent creating SUPER_ADMIN users via this endpoint."""
        if v == UserRole.SUPER_ADMIN:
            raise ValueError("Cannot create SUPER_ADMIN via this endpoint")
        return v


class UserUpdateAdmin(BaseModel):
    """Schema for updating a user via admin panel."""
    role: UserRole | None = None
    is_active: bool | None = None

    @field_validator("role")
    @classmethod
    def role_cannot_be_super_admin(cls, v: UserRole | None) -> UserRole | None:
        """Prevent changing role to SUPER_ADMIN."""
        if v == UserRole.SUPER_ADMIN:
            raise ValueError("Cannot set role to SUPER_ADMIN")
        return v


class UserResponseAdmin(BaseModel):
    """Schema for user response in admin panel."""
    id: UUID
    email: str
    name: str
    role: UserRole
    tenant_id: UUID | None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
