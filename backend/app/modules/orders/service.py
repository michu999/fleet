"""
Orders module service layer.
Business logic for warehouse and order management.
"""

from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.orders.models import Warehouse, Order
from app.modules.orders.schemas import (
    WarehouseCreate,
    WarehouseUpdate,
    OrderCreate,
    OrderUpdate,
)
from app.core.enums import OrderStatus


class WarehouseService:
    """Service for warehouse operations."""

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def get_by_id(self, warehouse_id: UUID) -> Warehouse | None:
        """Get warehouse by ID within tenant."""
        result = await self.db.execute(
            select(Warehouse).where(
                Warehouse.id == warehouse_id,
                Warehouse.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: bool | None = None,
    ) -> tuple[list[Warehouse], int]:
        """List all warehouses in tenant."""
        query = select(Warehouse).where(Warehouse.tenant_id == self.tenant_id)
        count_query = select(func.count(Warehouse.id)).where(
            Warehouse.tenant_id == self.tenant_id
        )

        if is_active is not None:
            query = query.where(Warehouse.is_active == is_active)
            count_query = count_query.where(Warehouse.is_active == is_active)

        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        warehouses = list(result.scalars().all())

        return warehouses, total

    async def create(self, data: WarehouseCreate) -> Warehouse:
        """Create a new warehouse."""
        warehouse = Warehouse(
            **data.model_dump(),
            tenant_id=self.tenant_id,
        )
        self.db.add(warehouse)
        await self.db.flush()
        return warehouse

    async def update(self, warehouse: Warehouse, data: WarehouseUpdate) -> Warehouse:
        """Update an existing warehouse."""
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(warehouse, field, value)
        await self.db.flush()
        return warehouse

    async def deactivate(self, warehouse: Warehouse) -> Warehouse:
        """Deactivate a warehouse."""
        warehouse.is_active = False
        await self.db.flush()
        return warehouse


class OrderService:
    """Service for order operations."""

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def get_by_id(self, order_id: UUID) -> Order | None:
        """Get order by ID within tenant."""
        result = await self.db.execute(
            select(Order).where(
                Order.id == order_id,
                Order.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_order_number(self, order_number: str) -> Order | None:
        """Get order by order number within tenant."""
        result = await self.db.execute(
            select(Order).where(
                Order.order_number == order_number,
                Order.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: OrderStatus | None = None,
    ) -> tuple[list[Order], int]:
        """List all orders in tenant with optional filtering."""
        query = select(Order).where(Order.tenant_id == self.tenant_id)
        count_query = select(func.count(Order.id)).where(
            Order.tenant_id == self.tenant_id
        )

        if status:
            query = query.where(Order.status == status)
            count_query = count_query.where(Order.status == status)

        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        query = query.offset(skip).limit(limit).order_by(Order.created_at.desc())
        result = await self.db.execute(query)
        orders = list(result.scalars().all())

        return orders, total

    async def create(self, data: OrderCreate) -> Order:
        """Create a new order."""
        order = Order(
            **data.model_dump(),
            tenant_id=self.tenant_id,
        )
        self.db.add(order)
        await self.db.flush()
        return order

    async def update(self, order: Order, data: OrderUpdate) -> Order:
        """Update an existing order."""
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(order, field, value)
        await self.db.flush()
        return order

    async def cancel(self, order: Order) -> Order:
        """Cancel an order."""
        if order.status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
            raise ValueError("Cannot cancel a delivered or already cancelled order")
        order.status = OrderStatus.CANCELLED
        await self.db.flush()
        return order
