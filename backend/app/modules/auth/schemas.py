"""
Auth module schemas for request/response validation.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# =============================================================================
# Tenant Schemas
# =============================================================================

class TenantBase(BaseModel):
    """Base schema for Tenant."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    domain: str | None = Field(None, max_length=255)


class TenantCreate(TenantBase):
    """Schema for creating a new tenant."""
    pass


class TenantUpdate(BaseModel):
    """Schema for updating a tenant."""
    name: str | None = Field(None, min_length=1, max_length=255)
    domain: str | None = Field(None, max_length=255)
    is_active: bool | None = None


class TenantRead(TenantBase):
    """Schema for reading a tenant."""
    id: UUID
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# User Schemas
# =============================================================================

class UserBase(BaseModel):
    """Base schema for User."""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)


class UserRead(UserBase):
    """Schema for reading a user."""
    id: UUID
    tenant_id: UUID
    picture: str | None
    google_id: str | None
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    name: str | None = Field(None, min_length=1, max_length=255)
    role: str | None = None
    is_active: bool | None = None


# =============================================================================
# DriverProfile Schemas
# =============================================================================

class DriverProfileBase(BaseModel):
    """Base schema for DriverProfile."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=20)


class DriverProfileCreate(DriverProfileBase):
    """Schema for creating a driver profile."""
    user_id: UUID
    license_number: str | None = Field(None, max_length=50)
    license_expiry: datetime | None = None
    card_number: str | None = Field(None, max_length=50)
    date_of_birth: datetime | None = None
    hire_date: datetime | None = None


class DriverProfileUpdate(BaseModel):
    """Schema for updating a driver profile."""
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=20)
    license_number: str | None = Field(None, max_length=50)
    license_expiry: datetime | None = None
    card_number: str | None = Field(None, max_length=50)


class DriverProfileRead(DriverProfileBase):
    """Schema for reading a driver profile."""
    id: UUID
    user_id: UUID
    tenant_id: UUID
    license_number: str | None
    license_expiry: datetime | None
    card_number: str | None
    date_of_birth: datetime | None
    hire_date: datetime | None

    model_config = ConfigDict(from_attributes=True)
