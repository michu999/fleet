"""
Test factories using factory_boy for generating test data.
"""

import factory
from factory import fuzzy
from uuid import uuid4
from datetime import datetime, timedelta

from app.modules.auth.models import Tenant, User, DriverProfile
from app.modules.fleet.models import Vehicle, Trailer, Trip, WorkTime
from app.modules.orders.models import Warehouse, Order
from app.core.enums import (
    UserRole,
    VehicleType,
    VehicleStatus,
    TrailerType,
    TrailerStatus,
    WarehouseType,
    OrderStatus,
    TripStatus,
    WorkType,
)


class TenantFactory(factory.Factory):
    """Factory for creating Tenant instances."""

    class Meta:
        model = Tenant

    id = factory.LazyFunction(uuid4)
    name = factory.Faker("company")
    slug = factory.LazyAttribute(lambda o: o.name.lower().replace(" ", "-").replace(",", "")[:50])
    domain = factory.LazyAttribute(lambda o: f"{o.slug}.fleet.dev")
    is_active = True
    created_at = factory.LazyFunction(datetime.now)


class UserFactory(factory.Factory):
    """Factory for creating User instances."""

    class Meta:
        model = User

    id = factory.LazyFunction(uuid4)
    tenant_id = factory.LazyFunction(uuid4)
    email = factory.Faker("email")
    name = factory.Faker("name")
    picture = factory.Faker("image_url")
    google_id = factory.LazyFunction(lambda: f"google_{uuid4().hex[:16]}")
    role = UserRole.DRIVER
    is_active = True
    created_at = factory.LazyFunction(datetime.now)
    updated_at = factory.LazyFunction(datetime.now)


class DriverProfileFactory(factory.Factory):
    """Factory for creating DriverProfile instances."""

    class Meta:
        model = DriverProfile

    id = factory.LazyFunction(uuid4)
    user_id = factory.LazyFunction(uuid4)
    tenant_id = factory.LazyFunction(uuid4)
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    phone = factory.Faker("phone_number")
    date_of_birth = factory.Faker("date_of_birth", minimum_age=21, maximum_age=65)
    hire_date = factory.LazyFunction(lambda: datetime.now() - timedelta(days=365))
    license_number = factory.LazyFunction(lambda: f"DL{uuid4().hex[:8].upper()}")
    license_expiry = factory.LazyFunction(lambda: datetime.now() + timedelta(days=365 * 3))
    card_number = factory.LazyFunction(lambda: f"TC{uuid4().hex[:10].upper()}")


class VehicleFactory(factory.Factory):
    """Factory for creating Vehicle instances."""

    class Meta:
        model = Vehicle

    id = factory.LazyFunction(uuid4)
    tenant_id = factory.LazyFunction(uuid4)
    plate_number = factory.LazyFunction(lambda: f"WA{uuid4().hex[:5].upper()}")
    brand = factory.Faker("random_element", elements=["Volvo", "Scania", "MAN", "Mercedes", "DAF"])
    model = factory.Faker("random_element", elements=["FH16", "R500", "TGX", "Actros", "XF"])
    year = factory.Faker("random_int", min=2015, max=2024)
    vehicle_type = VehicleType.TRUCK
    status = VehicleStatus.AVAILABLE
    current_latitude = factory.Faker("latitude")
    current_longitude = factory.Faker("longitude")
    last_position_update = factory.LazyFunction(datetime.now)
    created_at = factory.LazyFunction(datetime.now)


class TrailerFactory(factory.Factory):
    """Factory for creating Trailer instances."""

    class Meta:
        model = Trailer

    id = factory.LazyFunction(uuid4)
    tenant_id = factory.LazyFunction(uuid4)
    plate_number = factory.LazyFunction(lambda: f"WT{uuid4().hex[:5].upper()}")
    trailer_type = TrailerType.STANDARD
    capacity_kg = factory.Faker("random_int", min=10000, max=30000)
    capacity_m3 = factory.Faker("random_int", min=60, max=100)
    status = TrailerStatus.AVAILABLE
    created_at = factory.LazyFunction(datetime.now)


class WarehouseFactory(factory.Factory):
    """Factory for creating Warehouse instances."""

    class Meta:
        model = Warehouse

    id = factory.LazyFunction(uuid4)
    tenant_id = factory.LazyFunction(uuid4)
    name = factory.Faker("company")
    address = factory.Faker("address")
    latitude = factory.Faker("latitude")
    longitude = factory.Faker("longitude")
    warehouse_type = WarehouseType.WAREHOUSE
    is_active = True
    created_at = factory.LazyFunction(datetime.now)


class OrderFactory(factory.Factory):
    """Factory for creating Order instances."""

    class Meta:
        model = Order

    id = factory.LazyFunction(uuid4)
    tenant_id = factory.LazyFunction(uuid4)
    order_number = factory.LazyFunction(lambda: f"ORD-{uuid4().hex[:8].upper()}")
    origin_warehouse_id = factory.LazyFunction(uuid4)
    destination_warehouse_id = factory.LazyFunction(uuid4)
    client_name = factory.Faker("company")
    client_contact = factory.Faker("email")
    cargo_description = factory.Faker("sentence")
    weight_kg = factory.Faker("random_int", min=100, max=20000)
    volume_m3 = factory.Faker("random_int", min=1, max=80)
    status = OrderStatus.PENDING
    created_at = factory.LazyFunction(datetime.now)
    deadline_at = factory.LazyFunction(lambda: datetime.now() + timedelta(days=7))
    notes = factory.Faker("text", max_nb_chars=200)


class TripFactory(factory.Factory):
    """Factory for creating Trip instances."""

    class Meta:
        model = Trip

    id = factory.LazyFunction(uuid4)
    tenant_id = factory.LazyFunction(uuid4)
    order_id = factory.LazyFunction(uuid4)
    driver_id = factory.LazyFunction(uuid4)
    vehicle_id = factory.LazyFunction(uuid4)
    trailer_id = factory.LazyFunction(uuid4)
    planned_departure = factory.LazyFunction(lambda: datetime.now() + timedelta(hours=2))
    planned_arrival = factory.LazyFunction(lambda: datetime.now() + timedelta(hours=8))
    actual_departure = None
    actual_arrival = None
    status = TripStatus.PLANNED
    notes = factory.Faker("text", max_nb_chars=200)
    created_at = factory.LazyFunction(datetime.now)
    updated_at = factory.LazyFunction(datetime.now)


class WorkTimeFactory(factory.Factory):
    """Factory for creating WorkTime instances."""

    class Meta:
        model = WorkTime

    id = factory.LazyFunction(uuid4)
    tenant_id = factory.LazyFunction(uuid4)
    driver_id = factory.LazyFunction(uuid4)
    trip_id = None
    started_at = factory.LazyFunction(datetime.now)
    ended_at = None
    work_type = WorkType.DRIVING
    created_at = factory.LazyFunction(datetime.now)
