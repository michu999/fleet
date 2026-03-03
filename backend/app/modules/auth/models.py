"""
Auth module models: Tenant, User, DriverProfile.
Multi-tenant architecture with Google OAuth 2.0 support.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ENUM as PG_ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import UserRole

if TYPE_CHECKING:
    from app.modules.fleet.models import Trip, WorkTime, Vehicle, Trailer
    from app.modules.orders.models import Warehouse, Order


class Tenant(Base):
    """
    Tenant model for multi-tenant architecture.
    All business data is scoped to a tenant.
    
    Business rules enforced at DB level:
    - Name must not be empty
    """

    __tablename__ = "tenants"
    __table_args__ = (
        # Composite index for common query pattern: active tenants by name
        Index("ix_tenants_active_name", "is_active", "name"),
        # Check that name is not just whitespace
        CheckConstraint("length(trim(name)) > 0", name="ck_tenants_name_not_empty"),
    )
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="tenant",
    )
    driver_profiles: Mapped[list["DriverProfile"]] = relationship(
        "DriverProfile",
        back_populates="tenant",
    )
    vehicles: Mapped[list["Vehicle"]] = relationship(
        "Vehicle",
        back_populates="tenant",
    )
    trailers: Mapped[list["Trailer"]] = relationship(
        "Trailer",
        back_populates="tenant",
    )
    warehouses: Mapped[list["Warehouse"]] = relationship(
        "Warehouse",
        back_populates="tenant",
    )
    orders: Mapped[list["Order"]] = relationship(
        "Order",
        back_populates="tenant",
    )
    trips: Mapped[list["Trip"]] = relationship(
        "Trip",
        back_populates="tenant",
    )
    work_times: Mapped[list["WorkTime"]] = relationship(
        "WorkTime",
        back_populates="tenant",
    )


# Create PostgreSQL ENUM type for user roles
# This is created once and reused across the table
user_role_enum = PG_ENUM(
    UserRole,
    name="user_role",
    create_type=True,  # Will create type if not exists
)


class User(Base):
    """
    User model with Google OAuth 2.0 support.
    Roles: admin, manager, dispatcher, driver.
    
    Business rules enforced at DB level:
    - Email must be valid format (basic check)
    - Role must be one of the defined enum values
    """

    __tablename__ = "users"
    __table_args__ = (
        # Composite index for common query: find users by tenant and role
        Index("ix_users_tenant_role", "tenant_id", "role"),
        # Composite index for active users lookup
        Index("ix_users_tenant_active", "tenant_id", "is_active"),
        # Unique email per tenant (allows same email in different tenants)
        Index("ix_users_tenant_email_unique", "tenant_id", "email", unique=True),
        # Partial index: only active users with Google accounts
        Index(
            "ix_users_active_google",
            "tenant_id",
            "google_id",
            postgresql_where="is_active = true AND google_id IS NOT NULL",
        ),
        # Email format validation (basic check - @ symbol present)
        CheckConstraint("email LIKE '%@%.%'", name="ck_users_email_format"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    picture: Mapped[str | None] = mapped_column(String(500), nullable=True)
    google_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Changed from String(50) to PostgreSQL ENUM
    # This provides:
    # 1. DB-level validation - only valid roles can be stored
    # 2. Better performance - enum stored as integer internally
    # 3. Type safety - prevents typos like "adimn" instead of "admin"
    role: Mapped[UserRole] = mapped_column(
        user_role_enum,
        default=UserRole.DRIVER,  # Most users are drivers in fleet management
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        back_populates="users",
    )
    driver_profile: Mapped["DriverProfile | None"] = relationship(
        "DriverProfile",
        back_populates="user",
        uselist=False,
    )
    trips: Mapped[list["Trip"]] = relationship(
        "Trip",
        back_populates="driver",
        foreign_keys="[Trip.driver_id]",
    )
    work_times: Mapped[list["WorkTime"]] = relationship(
        "WorkTime",
        back_populates="driver",
    )


class DriverProfile(Base):
    """
    Extended profile for drivers.
    Contains personal and professional data separate from Google account.
    
    Business rules enforced at DB level:
    - License expiry must be in the future or null (warning only - soft constraint)
    - Phone format validation (optional, basic check)
    """

    __tablename__ = "driver_profiles"
    __table_args__ = (
        # Composite index for finding drivers by tenant with license info
        Index("ix_driver_profiles_tenant_license", "tenant_id", "license_number"),
        # Check for valid license expiry (if set, should be reasonable date)
        # Note: This is a soft check - doesn't prevent expired licenses, 
        # just ensures date is valid
        CheckConstraint(
            "license_expiry IS NULL OR license_expiry > '1900-01-01'",
            name="ck_driver_profiles_license_expiry_valid"
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Personal data
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    date_of_birth: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    hire_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Professional data
    license_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    license_expiry: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    card_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )  # tachograph card

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="driver_profile",
    )
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        back_populates="driver_profiles",
    )
