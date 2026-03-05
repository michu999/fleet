"""
Orders module router.
API endpoints for warehouse and order management.

All endpoints require authentication via JWT cookie.
Tenant isolation is enforced by extracting tenant_id from authenticated user.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_dispatcher, require_driver
from app.core.enums import OrderStatus
from app.modules.auth.models import User
from app.modules.orders.service import WarehouseService, OrderService
from app.modules.orders.schemas import (
    WarehouseCreate,
    WarehouseUpdate,
    WarehouseRead,
    WarehouseList,
    OrderCreate,
    OrderUpdate,
    OrderRead,
    OrderList,
)

router = APIRouter()


# =============================================================================
# Warehouse Endpoints
# =============================================================================

@router.get("/warehouses", response_model=WarehouseList)
async def list_warehouses(
    current_user: User = Depends(require_dispatcher),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    is_active: bool | None = None,
):
    """List all warehouses with pagination."""
    service = WarehouseService(db, current_user.tenant_id)
    skip = (page - 1) * per_page
    warehouses, _ = await service.list_all(skip=skip, limit=per_page, is_active=is_active)
    return [WarehouseRead.model_validate(w) for w in warehouses]


@router.get("/warehouses/{warehouse_id}", response_model=WarehouseRead)
async def get_warehouse(
    warehouse_id: UUID,
    current_user: User = Depends(require_driver),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific warehouse by ID."""
    service = WarehouseService(db, current_user.tenant_id)
    warehouse = await service.get_by_id(warehouse_id)
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return warehouse


@router.post("/warehouses", response_model=WarehouseRead, status_code=status.HTTP_201_CREATED)
async def create_warehouse(
    data: WarehouseCreate,
    current_user: User = Depends(require_dispatcher),
    db: AsyncSession = Depends(get_db),
):
    """Create a new warehouse."""
    service = WarehouseService(db, current_user.tenant_id)
    warehouse = await service.create(data)
    return warehouse


@router.patch("/warehouses/{warehouse_id}", response_model=WarehouseRead)
async def update_warehouse(
    warehouse_id: UUID,
    data: WarehouseUpdate,
    current_user: User = Depends(require_dispatcher),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing warehouse."""
    service = WarehouseService(db, current_user.tenant_id)
    warehouse = await service.get_by_id(warehouse_id)
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    updated = await service.update(warehouse, data)
    return updated


@router.delete("/warehouses/{warehouse_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_warehouse(
    warehouse_id: UUID,
    current_user: User = Depends(require_dispatcher),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a warehouse (soft delete)."""
    service = WarehouseService(db, current_user.tenant_id)
    warehouse = await service.get_by_id(warehouse_id)
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    await service.deactivate(warehouse)


# =============================================================================
# Order Endpoints
# =============================================================================

@router.get("", response_model=OrderList)
async def list_orders(
    current_user: User = Depends(require_dispatcher),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: OrderStatus | None = None,
):
    """List all orders with pagination and filtering."""
    service = OrderService(db, current_user.tenant_id)
    skip = (page - 1) * per_page
    orders, total = await service.list_all(skip=skip, limit=per_page, status=status)
    return OrderList(
        items=[OrderRead.model_validate(o) for o in orders],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: UUID,
    current_user: User = Depends(require_driver),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific order by ID."""
    service = OrderService(db, current_user.tenant_id)
    order = await service.get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: OrderCreate,
    current_user: User = Depends(require_dispatcher),
    db: AsyncSession = Depends(get_db),
):
    """Create a new order."""
    service = OrderService(db, current_user.tenant_id)
    
    # Check if order number already exists
    existing = await service.get_by_order_number(data.order_number)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Order with this order number already exists",
        )
    
    # Validate warehouses are different
    if data.origin_warehouse_id == data.destination_warehouse_id:
        raise HTTPException(
            status_code=400,
            detail="Origin and destination warehouses must be different",
        )
    
    order = await service.create(data)
    return order


@router.patch("/{order_id}", response_model=OrderRead)
async def update_order(
    order_id: UUID,
    data: OrderUpdate,
    current_user: User = Depends(require_dispatcher),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing order."""
    service = OrderService(db, current_user.tenant_id)
    order = await service.get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    updated = await service.update(order, data)
    return updated


@router.post("/{order_id}/cancel", response_model=OrderRead)
async def cancel_order(
    order_id: UUID,
    current_user: User = Depends(require_dispatcher),
    db: AsyncSession = Depends(get_db),
):
    """Cancel an order."""
    service = OrderService(db, current_user.tenant_id)
    order = await service.get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    try:
        cancelled = await service.cancel(order)
        return cancelled
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
