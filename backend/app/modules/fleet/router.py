"""
Fleet module router.
API endpoints for vehicle, trailer, trip, and work time management.

All endpoints require authentication via JWT cookie.
Tenant isolation is enforced by extracting tenant_id from authenticated user.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_dispatcher, require_driver, require_dispatcher_tenant, require_driver_tenant
from app.core.enums import VehicleStatus, TrailerStatus, TripStatus
from app.modules.auth.models import User
from app.modules.fleet.service import VehicleService, TrailerService, TripService
from app.modules.fleet.schemas import (
    VehicleCreate,
    VehicleUpdate,
    VehicleRead,
    VehicleList,
    TrailerCreate,
    TrailerUpdate,
    TrailerRead,
    TrailerList,
    TripCreate,
    TripUpdate,
    TripRead,
    TripList,
)

router = APIRouter()


# =============================================================================
# Vehicle Endpoints
# =============================================================================

@router.get("/vehicles", response_model=VehicleList)
async def list_vehicles(
    current_user: User = Depends(require_dispatcher),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: VehicleStatus | None = None,
):
    """List all vehicles with pagination and optional filtering."""
    service = VehicleService(db, current_user.tenant_id)
    skip = (page - 1) * per_page
    vehicles, total = await service.list_all(skip=skip, limit=per_page, status=status)
    return VehicleList(
        items=[VehicleRead.model_validate(v) for v in vehicles],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/vehicles/{vehicle_id}", response_model=VehicleRead)
async def get_vehicle(
    vehicle_id: UUID,
    current_user: User = Depends(require_driver),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific vehicle by ID."""
    service = VehicleService(db, current_user.tenant_id)
    vehicle = await service.get_by_id(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle


@router.post("/vehicles", response_model=VehicleRead, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    data: VehicleCreate,
    current_user: User = Depends(require_dispatcher_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Create a new vehicle."""
    service = VehicleService(db, current_user.tenant_id)
    
    # Check if plate number already exists
    existing = await service.get_by_plate_number(data.plate_number)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Vehicle with this plate number already exists",
        )
    
    vehicle = await service.create(data)
    return vehicle


@router.patch("/vehicles/{vehicle_id}", response_model=VehicleRead)
async def update_vehicle(
    vehicle_id: UUID,
    data: VehicleUpdate,
    current_user: User = Depends(require_dispatcher_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing vehicle."""
    service = VehicleService(db, current_user.tenant_id)
    vehicle = await service.get_by_id(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    # Check plate number uniqueness if being updated
    if data.plate_number and data.plate_number != vehicle.plate_number:
        existing = await service.get_by_plate_number(data.plate_number)
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Vehicle with this plate number already exists",
            )
    
    updated = await service.update(vehicle, data)
    return updated


@router.delete("/vehicles/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle(
    vehicle_id: UUID,
    current_user: User = Depends(require_dispatcher_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a vehicle (set status to inactive)."""
    service = VehicleService(db, current_user.tenant_id)
    vehicle = await service.get_by_id(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    await service.delete(vehicle)


# =============================================================================
# Trailer Endpoints
# =============================================================================

@router.get("/trailers", response_model=TrailerList)
async def list_trailers(
    current_user: User = Depends(require_dispatcher),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: TrailerStatus | None = None,
):
    """List all trailers with pagination."""
    service = TrailerService(db, current_user.tenant_id)
    skip = (page - 1) * per_page
    trailers, _ = await service.list_all(skip=skip, limit=per_page, status=status)
    return [TrailerRead.model_validate(t) for t in trailers]


@router.get("/trailers/{trailer_id}", response_model=TrailerRead)
async def get_trailer(
    trailer_id: UUID,
    current_user: User = Depends(require_driver),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific trailer by ID."""
    service = TrailerService(db, current_user.tenant_id)
    trailer = await service.get_by_id(trailer_id)
    if not trailer:
        raise HTTPException(status_code=404, detail="Trailer not found")
    return trailer


@router.post("/trailers", response_model=TrailerRead, status_code=status.HTTP_201_CREATED)
async def create_trailer(
    data: TrailerCreate,
    current_user: User = Depends(require_dispatcher_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Create a new trailer."""
    service = TrailerService(db, current_user.tenant_id)
    trailer = await service.create(data)
    return trailer


@router.patch("/trailers/{trailer_id}", response_model=TrailerRead)
async def update_trailer(
    trailer_id: UUID,
    data: TrailerUpdate,
    current_user: User = Depends(require_dispatcher_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing trailer."""
    service = TrailerService(db, current_user.tenant_id)
    trailer = await service.get_by_id(trailer_id)
    if not trailer:
        raise HTTPException(status_code=404, detail="Trailer not found")
    updated = await service.update(trailer, data)
    return updated


# =============================================================================
# Trip Endpoints
# =============================================================================

@router.get("/trips", response_model=TripList)
async def list_trips(
    current_user: User = Depends(require_driver),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: TripStatus | None = None,
    driver_id: UUID | None = None,
):
    """List all trips with pagination and filtering."""
    service = TripService(db, current_user.tenant_id)
    skip = (page - 1) * per_page
    trips, _ = await service.list_all(
        skip=skip, limit=per_page, status=status, driver_id=driver_id
    )
    return [TripRead.model_validate(t) for t in trips]


@router.get("/trips/{trip_id}", response_model=TripRead)
async def get_trip(
    trip_id: UUID,
    current_user: User = Depends(require_driver),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific trip by ID."""
    service = TripService(db, current_user.tenant_id)
    trip = await service.get_by_id(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@router.post("/trips", response_model=TripRead, status_code=status.HTTP_201_CREATED)
async def create_trip(
    data: TripCreate,
    current_user: User = Depends(require_dispatcher_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Create a new trip."""
    service = TripService(db, current_user.tenant_id)
    trip = await service.create(data)
    return trip


@router.patch("/trips/{trip_id}", response_model=TripRead)
async def update_trip(
    trip_id: UUID,
    data: TripUpdate,
    current_user: User = Depends(require_dispatcher_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing trip."""
    service = TripService(db, current_user.tenant_id)
    trip = await service.get_by_id(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    updated = await service.update(trip, data)
    return updated


@router.post("/trips/{trip_id}/start", response_model=TripRead)
async def start_trip(
    trip_id: UUID,
    current_user: User = Depends(require_driver_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Start a trip (set actual departure time)."""
    service = TripService(db, current_user.tenant_id)
    trip = await service.get_by_id(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    if trip.status != TripStatus.PLANNED:
        raise HTTPException(status_code=400, detail="Trip cannot be started")
    updated = await service.start_trip(trip)
    return updated


@router.post("/trips/{trip_id}/complete", response_model=TripRead)
async def complete_trip(
    trip_id: UUID,
    current_user: User = Depends(require_driver_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Complete a trip (set actual arrival time)."""
    service = TripService(db, current_user.tenant_id)
    trip = await service.get_by_id(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    if trip.status != TripStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Trip cannot be completed")
    updated = await service.complete_trip(trip)
    return updated
