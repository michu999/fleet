"""
Orders module schemas for request/response validation.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import WarehouseType, OrderStatus


# =============================================================================
# Warehouse Schemas
# =============================================================================

class WarehouseBase(BaseModel):
    """Base schema for Warehouse."""
    name: str = Field(..., min_length=1, max_length=255)
    address: str = Field(..., min_length=1, max_length=255)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    warehouse_type: WarehouseType = WarehouseType.WAREHOUSE


class WarehouseCreate(WarehouseBase):
    """Schema for creating a new warehouse."""
    pass


class WarehouseUpdate(BaseModel):
    """Schema for updating a warehouse."""
    name: str | None = Field(None, min_length=1, max_length=255)
    address: str | None = Field(None, min_length=1, max_length=255)
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    warehouse_type: WarehouseType | None = None
    is_active: bool | None = None


class WarehouseRead(WarehouseBase):
    """Schema for reading a warehouse."""
    id: UUID
    tenant_id: UUID
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Order Schemas
# =============================================================================

class OrderBase(BaseModel):
    """Base schema for Order."""
    order_number: str = Field(..., min_length=1, max_length=50)
    origin_warehouse_id: UUID
    destination_warehouse_id: UUID
    client_name: str = Field(..., min_length=1, max_length=255)
    client_contact: str | None = Field(None, max_length=255)
    cargo_description: str | None = Field(None, max_length=500)
    weight_kg: float | None = Field(None, gt=0)
    volume_m3: float | None = Field(None, gt=0)
    deadline_at: datetime | None = None
    notes: str | None = Field(None, max_length=1000)


class OrderCreate(OrderBase):
    """Schema for creating a new order."""
    pass


class OrderUpdate(BaseModel):
    """Schema for updating an order."""
    client_name: str | None = Field(None, min_length=1, max_length=255)
    client_contact: str | None = Field(None, max_length=255)
    cargo_description: str | None = Field(None, max_length=500)
    weight_kg: float | None = Field(None, gt=0)
    volume_m3: float | None = Field(None, gt=0)
    status: OrderStatus | None = None
    deadline_at: datetime | None = None
    notes: str | None = Field(None, max_length=1000)


class OrderRead(OrderBase):
    """Schema for reading an order."""
    id: UUID
    tenant_id: UUID
    status: OrderStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderList(BaseModel):
    """Schema for listing orders."""
    items: list[OrderRead]
    total: int
    page: int
    per_page: int
