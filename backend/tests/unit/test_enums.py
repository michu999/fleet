import pytest
from app.core.enums import (
    UserRole, VehicleStatus, OrderStatus,
    WorkType, TrailerType, #OrderPriority
)


class TestUserRole:
    def test_all_roles_exist(self):
        assert UserRole.ADMIN == "admin"
        assert UserRole.DISPATCHER == "dispatcher"
        assert UserRole.DRIVER == "driver"

    def test_role_is_string(self):
        assert isinstance(UserRole.ADMIN.value, str)

    def test_role_from_string(self):
        assert UserRole("admin") == UserRole.ADMIN


class TestVehicleStatus:
    def test_all_statuses_exist(self):
        statuses = [s.value for s in VehicleStatus]
        assert "available" in statuses
        assert "on_route" in statuses
        assert "maintenance" in statuses
        assert "inactive" in statuses

    def test_invalid_status_raises(self):
        with pytest.raises(ValueError):
            VehicleStatus("invalid_status")


class TestOrderStatus:
    def test_order_flow_statuses(self):
        flow = ["pending", "assigned", "in_transit", "delivered"]
        for status in flow:
            assert OrderStatus(status) is not None

    def test_cancelled_status(self):
        assert OrderStatus.CANCELLED == "cancelled"


class TestWorkType:
    def test_driving_work_types(self):
        assert WorkType.DRIVING.value == "driving"
        assert WorkType.REST.value == "rest"
        assert WorkType.BREAK.value == "break"
        assert WorkType.AVAILABILITY.value == "availability"
        assert WorkType.OTHER.value == "other"
