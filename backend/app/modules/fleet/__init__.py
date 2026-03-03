"""
Fleet module - Vehicle, trailer, trip, and work time management.
"""

from app.modules.fleet.models import Vehicle, Trailer, Trip, WorkTime
from app.modules.fleet.schemas import (
    VehicleCreate,
    VehicleRead,
    VehicleUpdate,
    VehicleList,
    TrailerCreate,
    TrailerRead,
    TrailerUpdate,
    TripCreate,
    TripRead,
    TripUpdate,
    WorkTimeCreate,
    WorkTimeRead,
    WorkTimeUpdate,
)
from app.modules.fleet.service import (
    VehicleService,
    TrailerService,
    TripService,
    WorkTimeService,
)

__all__ = [
    # Models
    "Vehicle",
    "Trailer",
    "Trip",
    "WorkTime",
    # Schemas
    "VehicleCreate",
    "VehicleRead",
    "VehicleUpdate",
    "VehicleList",
    "TrailerCreate",
    "TrailerRead",
    "TrailerUpdate",
    "TripCreate",
    "TripRead",
    "TripUpdate",
    "WorkTimeCreate",
    "WorkTimeRead",
    "WorkTimeUpdate",
    # Services
    "VehicleService",
    "TrailerService",
    "TripService",
    "WorkTimeService",
]
