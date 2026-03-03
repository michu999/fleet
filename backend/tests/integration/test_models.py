import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import Tenant, User
from app.modules.fleet.models import Vehicle
from app.modules.orders.models import Order
from app.core.enums import UserRole, VehicleStatus, VehicleType


@pytest.mark.asyncio
class TestTenantModel:
    async def test_create_tenant(self, db_session: AsyncSession):
        tenant = Tenant(
            name="Test Company",
            slug="test-company"
        )
        db_session.add(tenant)
        await db_session.commit()

        assert tenant.id is not None
        assert tenant.name == "Test Company"
        assert tenant.is_active is True

    async def test_tenant_slug_unique(self, db_session: AsyncSession):
        tenant1 = Tenant(name="Company 1", slug="same-slug")
        tenant2 = Tenant(name="Company 2", slug="same-slug")

        db_session.add(tenant1)
        await db_session.commit()

        db_session.add(tenant2)
        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()


@pytest.mark.asyncio
class TestUserModel:
    async def test_create_user(self, db_session: AsyncSession):
        tenant = Tenant(name="Test", slug="test")
        db_session.add(tenant)
        await db_session.commit()

        user = User(
            tenant_id=tenant.id,
            email="test@example.com",
            name="Jan Kowalski",
            google_id="google_123456",
            role=UserRole.DRIVER
        )
        db_session.add(user)
        await db_session.commit()

        assert user.id is not None
        assert user.role == UserRole.DRIVER
        assert user.is_active is True


@pytest.mark.asyncio
class TestVehicleModel:
    async def test_create_vehicle(self, db_session: AsyncSession):
        tenant = Tenant(name="Test", slug="test-vehicle")
        db_session.add(tenant)
        await db_session.commit()

        vehicle = Vehicle(
            tenant_id=tenant.id,
            plate_number="WA12345",
            brand="Volvo",
            model="FH",
            year=2023,
            vehicle_type=VehicleType.TRUCK,
            status=VehicleStatus.AVAILABLE
        )
        db_session.add(vehicle)
        await db_session.commit()

        assert vehicle.id is not None
        assert vehicle.status == VehicleStatus.AVAILABLE

    async def test_vehicle_year_constraint(self, db_session: AsyncSession):
        tenant = Tenant(name="Test", slug="test-year")
        db_session.add(tenant)
        await db_session.commit()

        vehicle = Vehicle(
            tenant_id=tenant.id,
            plate_number="WA99999",
            brand="Invalid",
            model="Invalid",
            year=1800,  # Nieprawidłowy rok (< 1900)
            vehicle_type=VehicleType.TRUCK
        )
        db_session.add(vehicle)

        with pytest.raises(Exception):  # CheckConstraint violation
            await db_session.commit()
