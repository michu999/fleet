"""
Orders module models: Warehouse, Order.
Logistics management with origin/destination warehouses.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Index, String, func, Time
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ENUM as PG_ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import WarehouseType, OrderStatus

if TYPE_CHECKING:
    from app.modules.auth.models import Tenant
    from app.modules.fleet.models import Trip


# ============================================================================
# PostgreSQL ENUM types
# ============================================================================
warehouse_type_enum = PG_ENUM(WarehouseType, name="warehouse_type", create_type=True)
order_status_enum = PG_ENUM(OrderStatus, name="order_status", create_type=True)


class Warehouse(Base):
    """
    Warehouse/location model.
    Can be warehouse, client location, or pickup point.
    """

    __tablename__ = "warehouses"
    __table_args__ = (
        Index("ix_warehouses_tenant_type", "tenant_id", "warehouse_type"),
        Index("ix_warehouses_tenant_active", "tenant_id", "is_active"),
        Index(
            "ix_warehouses_active",
            "tenant_id",
            "warehouse_type",
            postgresql_where="is_active = true",
        ),
        CheckConstraint("latitude >= -90 AND latitude <= 90", name="ck_warehouses_latitude_range"),
        CheckConstraint("longitude >= -180 AND longitude <= 180", name="ck_warehouses_longitude_range"),
        CheckConstraint("length(trim(name)) > 0", name="ck_warehouses_name_not_empty"),
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
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    warehouse_type: Mapped[WarehouseType] = mapped_column(
        warehouse_type_enum,
        default=WarehouseType.WAREHOUSE,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="warehouses")
    orders_as_origin: Mapped[list["Order"]] = relationship(
        "Order",
        back_populates="origin_warehouse",
        foreign_keys="[Order.origin_warehouse_id]",
    )
    orders_as_destination: Mapped[list["Order"]] = relationship(
        "Order",
        back_populates="destination_warehouse",
        foreign_keys="[Order.destination_warehouse_id]",
    )

class WarehouseOperatingHours(Base):
    __tablename__ = "warehouses_operating_hours"
    __table_args__ = (

    )
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    warehouse_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False)
    day_of_the_week: Mapped[int]
    is_open: Mapped[bool]
    open_time: Mapped[datetime | None]
    close_time: Mapped[datetime | None]


class Order(Base):
    """
    Order model for cargo transport.
    Links origin and destination warehouses with trip assignment.
    """

    __tablename__ = "orders"
    __table_args__ = (
        Index("ix_orders_tenant_status", "tenant_id", "status"),
        Index("ix_orders_tenant_created", "tenant_id", "created_at"),
        Index("ix_orders_tenant_number_unique", "tenant_id", "order_number", unique=True),
        Index(
            "ix_orders_active",
            "tenant_id",
            "status",
            postgresql_where="status IN ('PENDING', 'ASSIGNED', 'IN_TRANSIT')",
        ),
        CheckConstraint("weight_kg IS NULL OR weight_kg > 0", name="ck_orders_weight_positive"),
        CheckConstraint("volume_m3 IS NULL OR volume_m3 > 0", name="ck_orders_volume_positive"),
        CheckConstraint("origin_warehouse_id != destination_warehouse_id", name="ck_orders_different_warehouses"),
        CheckConstraint("length(trim(order_number)) > 0", name="ck_orders_number_not_empty"),
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
    order_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    origin_warehouse_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    destination_warehouse_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cargo_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume_m3: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[OrderStatus] = mapped_column(
        order_status_enum,
        default=OrderStatus.PENDING,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="orders")
    origin_warehouse: Mapped["Warehouse"] = relationship(
        "Warehouse",
        back_populates="orders_as_origin",
        foreign_keys=[origin_warehouse_id],
    )
    destination_warehouse: Mapped["Warehouse"] = relationship(
        "Warehouse",
        back_populates="orders_as_destination",
        foreign_keys=[destination_warehouse_id],
    )
    trip: Mapped["Trip | None"] = relationship("Trip", back_populates="order", uselist=False)
