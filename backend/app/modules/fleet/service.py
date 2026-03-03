"""
Fleet module service layer.
Business logic for vehicle, trailer, trip, and work time management.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.fleet.models import Vehicle, Trailer, Trip, WorkTime
from app.modules.fleet.schemas import (
    VehicleCreate,
    VehicleUpdate,
    TrailerCreate,
    TrailerUpdate,
    TripCreate,
    TripUpdate,
    WorkTimeCreate,
    WorkTimeUpdate,
)
from app.core.enums import VehicleStatus, TrailerStatus, TripStatus


class VehicleService:
    """Service for vehicle operations."""

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def get_by_id(self, vehicle_id: UUID) -> Vehicle | None:
        """Get vehicle by ID within tenant."""
        result = await self.db.execute(
            select(Vehicle).where(
                Vehicle.id == vehicle_id,
                Vehicle.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_plate_number(self, plate_number: str) -> Vehicle | None:
        """Get vehicle by plate number within tenant."""
        result = await self.db.execute(
            select(Vehicle).where(
                Vehicle.plate_number == plate_number,
                Vehicle.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: VehicleStatus | None = None,
    ) -> tuple[list[Vehicle], int]:
        """List all vehicles in tenant with optional filtering."""
        query = select(Vehicle).where(Vehicle.tenant_id == self.tenant_id)
        count_query = select(func.count(Vehicle.id)).where(
            Vehicle.tenant_id == self.tenant_id
        )

        if status:
            query = query.where(Vehicle.status == status)
            count_query = count_query.where(Vehicle.status == status)

        # Get total count
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        # Get paginated results
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        vehicles = list(result.scalars().all())

        return vehicles, total

    async def create(self, data: VehicleCreate) -> Vehicle:
        """Create a new vehicle."""
        vehicle = Vehicle(
            **data.model_dump(),
            tenant_id=self.tenant_id,
        )
        self.db.add(vehicle)
        await self.db.flush()
        return vehicle

    async def update(self, vehicle: Vehicle, data: VehicleUpdate) -> Vehicle:
        """Update an existing vehicle."""
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(vehicle, field, value)

        # Update last_position_update if coordinates changed
        if "current_latitude" in update_data or "current_longitude" in update_data:
            vehicle.last_position_update = datetime.now()

        await self.db.flush()
        return vehicle

    async def delete(self, vehicle: Vehicle) -> None:
        """Soft delete a vehicle by setting status to inactive."""
        vehicle.status = VehicleStatus.INACTIVE
        await self.db.flush()


class TrailerService:
    """Service for trailer operations."""

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def get_by_id(self, trailer_id: UUID) -> Trailer | None:
        """Get trailer by ID within tenant."""
        result = await self.db.execute(
            select(Trailer).where(
                Trailer.id == trailer_id,
                Trailer.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: TrailerStatus | None = None,
    ) -> tuple[list[Trailer], int]:
        """List all trailers in tenant with optional filtering."""
        query = select(Trailer).where(Trailer.tenant_id == self.tenant_id)
        count_query = select(func.count(Trailer.id)).where(
            Trailer.tenant_id == self.tenant_id
        )

        if status:
            query = query.where(Trailer.status == status)
            count_query = count_query.where(Trailer.status == status)

        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        trailers = list(result.scalars().all())

        return trailers, total

    async def create(self, data: TrailerCreate) -> Trailer:
        """Create a new trailer."""
        trailer = Trailer(
            **data.model_dump(),
            tenant_id=self.tenant_id,
        )
        self.db.add(trailer)
        await self.db.flush()
        return trailer

    async def update(self, trailer: Trailer, data: TrailerUpdate) -> Trailer:
        """Update an existing trailer."""
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(trailer, field, value)
        await self.db.flush()
        return trailer


class TripService:
    """Service for trip operations."""

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def get_by_id(self, trip_id: UUID) -> Trip | None:
        """Get trip by ID within tenant."""
        result = await self.db.execute(
            select(Trip).where(
                Trip.id == trip_id,
                Trip.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: TripStatus | None = None,
        driver_id: UUID | None = None,
    ) -> tuple[list[Trip], int]:
        """List all trips in tenant with optional filtering."""
        query = select(Trip).where(Trip.tenant_id == self.tenant_id)
        count_query = select(func.count(Trip.id)).where(
            Trip.tenant_id == self.tenant_id
        )

        if status:
            query = query.where(Trip.status == status)
            count_query = count_query.where(Trip.status == status)

        if driver_id:
            query = query.where(Trip.driver_id == driver_id)
            count_query = count_query.where(Trip.driver_id == driver_id)

        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        query = query.offset(skip).limit(limit).order_by(Trip.planned_departure.desc())
        result = await self.db.execute(query)
        trips = list(result.scalars().all())

        return trips, total

    async def create(self, data: TripCreate) -> Trip:
        """Create a new trip."""
        trip = Trip(
            **data.model_dump(),
            tenant_id=self.tenant_id,
        )
        self.db.add(trip)
        await self.db.flush()
        return trip

    async def update(self, trip: Trip, data: TripUpdate) -> Trip:
        """Update an existing trip."""
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(trip, field, value)
        await self.db.flush()
        return trip

    async def start_trip(self, trip: Trip) -> Trip:
        """Start a trip by setting actual departure time."""
        trip.status = TripStatus.IN_PROGRESS
        trip.actual_departure = datetime.now()
        await self.db.flush()
        return trip

    async def complete_trip(self, trip: Trip) -> Trip:
        """Complete a trip by setting actual arrival time."""
        trip.status = TripStatus.COMPLETED
        trip.actual_arrival = datetime.now()
        await self.db.flush()
        return trip


class WorkTimeService:
    """Service for work time operations."""

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def get_by_id(self, work_time_id: UUID) -> WorkTime | None:
        """Get work time by ID within tenant."""
        result = await self.db.execute(
            select(WorkTime).where(
                WorkTime.id == work_time_id,
                WorkTime.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_active_for_driver(self, driver_id: UUID) -> WorkTime | None:
        """Get currently active (not ended) work time for a driver."""
        result = await self.db.execute(
            select(WorkTime).where(
                WorkTime.driver_id == driver_id,
                WorkTime.tenant_id == self.tenant_id,
                WorkTime.ended_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def create(self, data: WorkTimeCreate) -> WorkTime:
        """Create a new work time entry."""
        work_time = WorkTime(
            **data.model_dump(),
            tenant_id=self.tenant_id,
        )
        self.db.add(work_time)
        await self.db.flush()
        return work_time

    async def end_work_time(self, work_time: WorkTime) -> WorkTime:
        """End a work time entry."""
        work_time.ended_at = datetime.now()
        await self.db.flush()
        return work_time
