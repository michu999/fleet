"""
Fleet module models: Vehicle, Trailer, Trip, WorkTime.
Core fleet management with trip planning and work time tracking.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ENUM as PG_ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import (
    VehicleType,
    VehicleStatus,
    TrailerType,
    TrailerStatus,
    TripStatus,
    WorkType,
)

if TYPE_CHECKING:
    from app.modules.auth.models import Tenant, User
    from app.modules.orders.models import Order


# ============================================================================
# PostgreSQL ENUM types
# ============================================================================
# These are created once in the database and reused.
# The `create_type=True` tells SQLAlchemy to create the type if it doesn't exist.
# Using native PostgreSQL ENUMs instead of String provides:
# 1. Type safety - DB rejects invalid values
# 2. Performance - stored as small integers internally (~4 bytes vs ~50 bytes)
# 3. Better indexes - fewer bytes = faster comparisons

vehicle_type_enum = PG_ENUM(VehicleType, name="vehicle_type", create_type=True)
vehicle_status_enum = PG_ENUM(VehicleStatus, name="vehicle_status", create_type=True)
trailer_type_enum = PG_ENUM(TrailerType, name="trailer_type", create_type=True)
trailer_status_enum = PG_ENUM(TrailerStatus, name="trailer_status", create_type=True)
trip_status_enum = PG_ENUM(TripStatus, name="trip_status", create_type=True)
work_type_enum = PG_ENUM(WorkType, name="work_type", create_type=True)


class Vehicle(Base):
    """
    Vehicle model with GPS tracking support.
    Types: truck, van, other.
    
    Business rules enforced at DB level:
    - GPS coordinates must be valid (-90 to 90 for lat, -180 to 180 for long)
    - Year must be reasonable (1900 to current + 1)
    """

    __tablename__ = "vehicles"
    __table_args__ = (
        # Composite index for common query: available vehicles for a tenant
        Index("ix_vehicles_tenant_status", "tenant_id", "status"),
        # Partial index: only active/available vehicles (most common query)
        Index(
            "ix_vehicles_tenant_available",
            "tenant_id",
            "vehicle_type",
            postgresql_where="status = 'available'",
        ),
        # Unique plate number per tenant
        Index("ix_vehicles_tenant_plate_unique", "tenant_id", "plate_number", unique=True),
        # GPS coordinates validation
        CheckConstraint(
            "current_latitude IS NULL OR (current_latitude >= -90 AND current_latitude <= 90)",
            name="ck_vehicles_latitude_range"
        ),
        CheckConstraint(
            "current_longitude IS NULL OR (current_longitude >= -180 AND current_longitude <= 180)",
            name="ck_vehicles_longitude_range"
        ),
        # Year validation (reasonable range)
        CheckConstraint(
            "year IS NULL OR (year >= 1900 AND year <= EXTRACT(YEAR FROM CURRENT_DATE) + 1)",
            name="ck_vehicles_year_range"
        ),
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
    plate_number: Mapped[str] = mapped_column(
        "VARCHAR(20)",
        nullable=False,
    )
    brand: Mapped[str | None] = mapped_column("VARCHAR(100)", nullable=True)
    model: Mapped[str | None] = mapped_column("VARCHAR(100)", nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    vehicle_type: Mapped[VehicleType] = mapped_column(
        vehicle_type_enum,
        default=VehicleType.TRUCK,
        nullable=False,
    )
    status: Mapped[VehicleStatus] = mapped_column(
        vehicle_status_enum,
        default=VehicleStatus.AVAILABLE,
        nullable=False,
    )
    current_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_position_update: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        back_populates="vehicles",
    )
    trips: Mapped[list["Trip"]] = relationship(
        "Trip",
        back_populates="vehicle",
    )


class Trailer(Base):
    """
    Trailer model for cargo transport.
    Types: standard, refrigerated, flatbed, tanker.
    
    Business rules enforced at DB level:
    - Capacity must be positive if set
    """

    __tablename__ = "trailers"
    __table_args__ = (
        # Composite index for common query: available trailers by type
        Index("ix_trailers_tenant_status", "tenant_id", "status"),
        Index("ix_trailers_tenant_type_status", "tenant_id", "trailer_type", "status"),
        # Unique plate number per tenant
        Index("ix_trailers_tenant_plate_unique", "tenant_id", "plate_number", unique=True),
        # Capacity validation
        CheckConstraint(
            "capacity_kg IS NULL OR capacity_kg > 0",
            name="ck_trailers_capacity_kg_positive"
        ),
        CheckConstraint(
            "capacity_m3 IS NULL OR capacity_m3 > 0",
            name="ck_trailers_capacity_m3_positive"
        ),
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
    plate_number: Mapped[str] = mapped_column("VARCHAR(20)", nullable=False)
    trailer_type: Mapped[TrailerType] = mapped_column(
        trailer_type_enum,
        default=TrailerType.STANDARD,
        nullable=False,
    )
    capacity_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    capacity_m3: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[TrailerStatus] = mapped_column(
        trailer_status_enum,
        default=TrailerStatus.AVAILABLE,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        back_populates="trailers",
    )
    trips: Mapped[list["Trip"]] = relationship(
        "Trip",
        back_populates="trailer",
    )


class Trip(Base):
    """
    Trip model linking order, driver, vehicle, and trailer.
    Tracks planned vs actual departure/arrival times.
    
    Business rules enforced at DB level:
    - Planned arrival must be after planned departure
    - Actual arrival must be after actual departure (if both set)
    """

    __tablename__ = "trips"
    __table_args__ = (
        # Composite index for common queries
        Index("ix_trips_tenant_status", "tenant_id", "status"),
        Index("ix_trips_tenant_driver", "tenant_id", "driver_id"),
        Index("ix_trips_tenant_vehicle", "tenant_id", "vehicle_id"),
        # Partial index: only active trips (planned or in_progress)
        Index(
            "ix_trips_active",
            "tenant_id",
            "driver_id",
            "vehicle_id",
            postgresql_where="status IN ('planned', 'in_progress')",
        ),
        # Time validation: arrival must be after departure
        CheckConstraint(
            "planned_arrival > planned_departure",
            name="ck_trips_planned_times_order"
        ),
        CheckConstraint(
            "actual_arrival IS NULL OR actual_departure IS NULL OR actual_arrival > actual_departure",
            name="ck_trips_actual_times_order"
        ),
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
    order_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="RESTRICT"),
        unique=True,
        index=True,
        nullable=False,
    )
    driver_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    vehicle_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("vehicles.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    trailer_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("trailers.id", ondelete="RESTRICT"),
        index=True,
        nullable=True,
    )
    planned_departure: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    planned_arrival: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    actual_departure: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    actual_arrival: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[TripStatus] = mapped_column(
        trip_status_enum,
        default=TripStatus.PLANNED,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column("VARCHAR(1000)", nullable=True)
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
        back_populates="trips",
    )
    order: Mapped["Order"] = relationship(
        "Order",
        back_populates="trip",
    )
    driver: Mapped["User"] = relationship(
        "User",
        back_populates="trips",
        foreign_keys=[driver_id],
    )
    vehicle: Mapped["Vehicle"] = relationship(
        "Vehicle",
        back_populates="trips",
    )
    trailer: Mapped["Trailer | None"] = relationship(
        "Trailer",
        back_populates="trips",
    )
    work_times: Mapped[list["WorkTime"]] = relationship(
        "WorkTime",
        back_populates="trip",
    )


class WorkTime(Base):
    """
    Work time tracking for drivers.
    Types: driving, rest, loading, waiting, other.
    
    Important for EU driving regulations (EC 561/2006):
    - Max 9h driving per day (can be extended to 10h twice a week)
    - Min 11h daily rest (can be reduced to 9h three times between weekly rests)
    
    Business rules enforced at DB level:
    - ended_at must be after started_at (if set)
    """

    __tablename__ = "work_times"
    __table_args__ = (
        # Composite indexes for common queries
        Index("ix_work_times_tenant_driver", "tenant_id", "driver_id"),
        Index("ix_work_times_driver_started", "driver_id", "started_at"),
        # Partial index: only open work time entries (ended_at is null)
        Index(
            "ix_work_times_open",
            "tenant_id",
            "driver_id",
            postgresql_where="ended_at IS NULL",
        ),
        # Time validation: ended must be after started
        CheckConstraint(
            "ended_at IS NULL OR ended_at > started_at",
            name="ck_work_times_times_order"
        ),
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
    driver_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    trip_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("trips.id", ondelete="RESTRICT"),
        index=True,
        nullable=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    work_type: Mapped[WorkType] = mapped_column(
        work_type_enum,
        default=WorkType.DRIVING,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        back_populates="work_times",
    )
    driver: Mapped["User"] = relationship(
        "User",
        back_populates="work_times",
    )
    trip: Mapped["Trip | None"] = relationship(
        "Trip",
        back_populates="work_times",
    )
