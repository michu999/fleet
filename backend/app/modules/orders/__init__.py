"""
Orders module - Warehouse and order management.
"""

from app.modules.orders.models import Warehouse, Order
from app.modules.orders.schemas import (
    WarehouseCreate,
    WarehouseRead,
    WarehouseUpdate,
    OrderCreate,
    OrderRead,
    OrderUpdate,
    OrderList,
)
from app.modules.orders.service import WarehouseService, OrderService

__all__ = [
    # Models
    "Warehouse",
    "Order",
    # Schemas
    "WarehouseCreate",
    "WarehouseRead",
    "WarehouseUpdate",
    "OrderCreate",
    "OrderRead",
    "OrderUpdate",
    "OrderList",
    # Services
    "WarehouseService",
    "OrderService",
]
