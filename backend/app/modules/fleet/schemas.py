"""
Fleet module schemas for request/response validation.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import VehicleType, VehicleStatus, TrailerType, TrailerStatus, TripStatus, WorkType


# =============================================================================
# Vehicle Schemas
# =============================================================================

class VehicleBase(BaseModel):
    """Base schema for Vehicle."""
    plate_number: str = Field(..., min_length=1, max_length=20)
    brand: str | None = Field(None, max_length=100)
    model: str | None = Field(None, max_length=100)
    year: int | None = Field(None, ge=1900, le=2100)
    vehicle_type: VehicleType = VehicleType.TRUCK


class VehicleCreate(VehicleBase):
    """Schema for creating a new vehicle."""
    pass


class VehicleUpdate(BaseModel):
    """Schema for updating a vehicle."""
    plate_number: str | None = Field(None, min_length=1, max_length=20)
    brand: str | None = Field(None, max_length=100)
    model: str | None = Field(None, max_length=100)
    year: int | None = Field(None, ge=1900, le=2100)
    vehicle_type: VehicleType | None = None
    status: VehicleStatus | None = None
    current_latitude: float | None = Field(None, ge=-90, le=90)
    current_longitude: float | None = Field(None, ge=-180, le=180)


class VehicleRead(VehicleBase):
    """Schema for reading a vehicle."""
    id: UUID
    tenant_id: UUID
    status: VehicleStatus
    current_latitude: float | None
    current_longitude: float | None
    last_position_update: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VehicleList(BaseModel):
    """Schema for listing vehicles."""
    items: list[VehicleRead]
    total: int
    page: int
    per_page: int


# =============================================================================
# Trailer Schemas
# =============================================================================

class TrailerBase(BaseModel):
    """Base schema for Trailer."""
    plate_number: str = Field(..., min_length=1, max_length=20)
    trailer_type: TrailerType = TrailerType.STANDARD
    capacity_kg: float | None = Field(None, gt=0)
    capacity_m3: float | None = Field(None, gt=0)


class TrailerCreate(TrailerBase):
    """Schema for creating a new trailer."""
    pass


class TrailerUpdate(BaseModel):
    """Schema for updating a trailer."""
    plate_number: str | None = Field(None, min_length=1, max_length=20)
    trailer_type: TrailerType | None = None
    capacity_kg: float | None = Field(None, gt=0)
    capacity_m3: float | None = Field(None, gt=0)
    status: TrailerStatus | None = None


class TrailerRead(TrailerBase):
    """Schema for reading a trailer."""
    id: UUID
    tenant_id: UUID
    status: TrailerStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Trip Schemas
# =============================================================================

class TripBase(BaseModel):
    """Base schema for Trip."""
    order_id: UUID
    driver_id: UUID
    vehicle_id: UUID
    trailer_id: UUID | None = None
    planned_departure: datetime
    planned_arrival: datetime
    notes: str | None = Field(None, max_length=1000)


class TripCreate(TripBase):
    """Schema for creating a new trip."""
    pass


class TripUpdate(BaseModel):
    """Schema for updating a trip."""
    driver_id: UUID | None = None
    vehicle_id: UUID | None = None
    trailer_id: UUID | None = None
    planned_departure: datetime | None = None
    planned_arrival: datetime | None = None
    actual_departure: datetime | None = None
    actual_arrival: datetime | None = None
    status: TripStatus | None = None
    notes: str | None = Field(None, max_length=1000)


class TripRead(TripBase):
    """Schema for reading a trip."""
    id: UUID
    tenant_id: UUID
    status: TripStatus
    actual_departure: datetime | None
    actual_arrival: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# WorkTime Schemas
# =============================================================================

class WorkTimeBase(BaseModel):
    """Base schema for WorkTime."""
    driver_id: UUID
    trip_id: UUID | None = None
    started_at: datetime
    work_type: WorkType = WorkType.DRIVING


class WorkTimeCreate(WorkTimeBase):
    """Schema for creating a work time entry."""
    pass


class WorkTimeUpdate(BaseModel):
    """Schema for updating a work time entry."""
    ended_at: datetime | None = None
    work_type: WorkType | None = None


class WorkTimeRead(WorkTimeBase):
    """Schema for reading a work time entry."""
    id: UUID
    tenant_id: UUID
    ended_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
