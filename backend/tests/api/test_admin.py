"""
Tests for Admin module - Ops Panel endpoints.
"""

from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.core.enums import TenantPlan, UserRole
from app.core.security import create_access_token
from app.modules.auth.models import Tenant, User


@pytest.fixture
async def super_admin_user(db_session) -> User:
    """Create a super admin user (no tenant)."""
    user = User(
        id=uuid4(),
        email="superadmin@fleet.local",
        name="Super Admin",
        role=UserRole.SUPER_ADMIN,
        tenant_id=None,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def regular_tenant(db_session) -> Tenant:
    """Create a regular tenant."""
    tenant = Tenant(
        id=uuid4(),
        name="Test Company",
        slug="test-company",
        domain="testcompany.com",
        plan=TenantPlan.TRIAL.value,
        max_users=10,
        is_active=True,
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest.fixture
async def regular_admin_user(db_session, regular_tenant) -> User:
    """Create a regular admin user in a tenant."""
    user = User(
        id=uuid4(),
        email="admin@testcompany.com",
        name="Regular Admin",
        role=UserRole.ADMIN,
        tenant_id=regular_tenant.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def super_admin_token(super_admin_user: User) -> str:
    """Create JWT token for super admin."""
    return create_access_token({
        "sub": str(super_admin_user.id),
        "tenant_id": None,
        "role": super_admin_user.role.value,
    })


@pytest.fixture
def regular_admin_token(regular_admin_user: User) -> str:
    """Create JWT token for regular admin."""
    return create_access_token({
        "sub": str(regular_admin_user.id),
        "tenant_id": str(regular_admin_user.tenant_id),
        "role": regular_admin_user.role.value,
    })


class TestSuperAdminTenants:
    """Tests for tenant management by super admin."""

    @pytest.mark.asyncio
    async def test_super_admin_can_list_tenants(
        self,
        client: AsyncClient,
        super_admin_token: str,
        regular_tenant: Tenant,
    ):
        """Super admin can list all tenants."""
        client.cookies.set("access_token", super_admin_token)
        
        response = await client.get("/api/v1/admin/tenants")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        # Check our tenant is in the list
        tenant_ids = [t["id"] for t in data]
        assert str(regular_tenant.id) in tenant_ids

    @pytest.mark.asyncio
    async def test_super_admin_can_create_tenant(
        self,
        client: AsyncClient,
        super_admin_token: str,
    ):
        """Super admin can create a new tenant."""
        client.cookies.set("access_token", super_admin_token)
        
        response = await client.post(
            "/api/v1/admin/tenants",
            json={
                "name": "New Company",
                "slug": "new-company",
                "domain": "newcompany.com",
                "plan": "basic",
                "max_users": 20,
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Company"
        assert data["slug"] == "new-company"
        assert data["plan"] == "basic"
        assert data["max_users"] == 20
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_cannot_create_duplicate_slug(
        self,
        client: AsyncClient,
        super_admin_token: str,
        regular_tenant: Tenant,
    ):
        """Cannot create tenant with existing slug."""
        client.cookies.set("access_token", super_admin_token)
        
        response = await client.post(
            "/api/v1/admin/tenants",
            json={
                "name": "Another Company",
                "slug": regular_tenant.slug,  # Duplicate slug
            },
        )
        
        assert response.status_code == 409
        assert "slug" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_super_admin_can_get_tenant(
        self,
        client: AsyncClient,
        super_admin_token: str,
        regular_tenant: Tenant,
    ):
        """Super admin can get a specific tenant."""
        client.cookies.set("access_token", super_admin_token)
        
        response = await client.get(f"/api/v1/admin/tenants/{regular_tenant.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(regular_tenant.id)
        assert data["name"] == regular_tenant.name

    @pytest.mark.asyncio
    async def test_super_admin_can_get_tenant_stats(
        self,
        client: AsyncClient,
        super_admin_token: str,
        regular_tenant: Tenant,
        regular_admin_user: User,  # Creates a user for the tenant
    ):
        """Super admin can get tenant statistics."""
        client.cookies.set("access_token", super_admin_token)
        
        response = await client.get(f"/api/v1/admin/tenants/{regular_tenant.id}/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["tenant_id"] == str(regular_tenant.id)
        assert data["tenant_name"] == regular_tenant.name
        assert data["users_count"] >= 1  # At least the admin user


class TestSuperAdminUsers:
    """Tests for user management by super admin."""

    @pytest.mark.asyncio
    async def test_super_admin_can_list_tenant_users(
        self,
        client: AsyncClient,
        super_admin_token: str,
        regular_tenant: Tenant,
        regular_admin_user: User,
    ):
        """Super admin can list users for a tenant."""
        client.cookies.set("access_token", super_admin_token)
        
        response = await client.get(f"/api/v1/admin/tenants/{regular_tenant.id}/users")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        user_emails = [u["email"] for u in data]
        assert regular_admin_user.email in user_emails

    @pytest.mark.asyncio
    async def test_super_admin_can_create_user(
        self,
        client: AsyncClient,
        super_admin_token: str,
        regular_tenant: Tenant,
    ):
        """Super admin can create a user for a tenant."""
        client.cookies.set("access_token", super_admin_token)
        
        response = await client.post(
            f"/api/v1/admin/tenants/{regular_tenant.id}/users",
            json={
                "email": "newuser@testcompany.com",
                "name": "New User",
                "role": "manager",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@testcompany.com"
        assert data["role"] == "manager"
        assert data["tenant_id"] == str(regular_tenant.id)

    @pytest.mark.asyncio
    async def test_cannot_create_duplicate_email(
        self,
        client: AsyncClient,
        super_admin_token: str,
        regular_tenant: Tenant,
        regular_admin_user: User,
    ):
        """Cannot create user with existing email."""
        client.cookies.set("access_token", super_admin_token)
        
        response = await client.post(
            f"/api/v1/admin/tenants/{regular_tenant.id}/users",
            json={
                "email": regular_admin_user.email,  # Duplicate email
                "name": "Duplicate User",
            },
        )
        
        assert response.status_code == 409
        assert "email" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_cannot_create_super_admin_via_api(
        self,
        client: AsyncClient,
        super_admin_token: str,
        regular_tenant: Tenant,
    ):
        """Cannot create SUPER_ADMIN user via this endpoint."""
        client.cookies.set("access_token", super_admin_token)
        
        response = await client.post(
            f"/api/v1/admin/tenants/{regular_tenant.id}/users",
            json={
                "email": "fakesuperadmin@test.com",
                "name": "Fake Super Admin",
                "role": "super_admin",
            },
        )
        
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_cannot_exceed_user_limit(
        self,
        client: AsyncClient,
        super_admin_token: str,
        db_session,
    ):
        """Cannot create users beyond tenant's max_users limit."""
        # Create tenant with max_users=1
        tenant = Tenant(
            id=uuid4(),
            name="Small Company",
            slug="small-company",
            plan=TenantPlan.TRIAL.value,
            max_users=1,
            is_active=True,
        )
        db_session.add(tenant)
        
        # Create one user (reaches limit)
        user = User(
            id=uuid4(),
            email="only@smallcompany.com",
            name="Only User",
            role=UserRole.ADMIN,
            tenant_id=tenant.id,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        
        client.cookies.set("access_token", super_admin_token)
        
        # Try to create another user
        response = await client.post(
            f"/api/v1/admin/tenants/{tenant.id}/users",
            json={
                "email": "second@smallcompany.com",
                "name": "Second User",
            },
        )
        
        assert response.status_code == 409
        assert "limit" in response.json()["detail"].lower()


class TestNonSuperAdminAccess:
    """Tests that non-super-admin users cannot access admin endpoints."""

    @pytest.mark.asyncio
    async def test_regular_admin_cannot_access_admin_endpoints(
        self,
        client: AsyncClient,
        regular_admin_token: str,
    ):
        """Regular admin cannot access admin endpoints."""
        client.cookies.set("access_token", regular_admin_token)
        
        response = await client.get("/api/v1/admin/tenants")
        
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_manager_cannot_access_admin_endpoints(
        self,
        client: AsyncClient,
        db_session,
        regular_tenant: Tenant,
    ):
        """Manager cannot access admin endpoints."""
        manager = User(
            id=uuid4(),
            email="manager@testcompany.com",
            name="Manager",
            role=UserRole.MANAGER,
            tenant_id=regular_tenant.id,
            is_active=True,
        )
        db_session.add(manager)
        await db_session.commit()
        
        token = create_access_token({
            "sub": str(manager.id),
            "tenant_id": str(manager.tenant_id),
            "role": manager.role.value,
        })
        client.cookies.set("access_token", token)
        
        response = await client.get("/api/v1/admin/tenants")
        
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_dispatcher_cannot_access_admin_endpoints(
        self,
        client: AsyncClient,
        db_session,
        regular_tenant: Tenant,
    ):
        """Dispatcher cannot access admin endpoints."""
        dispatcher = User(
            id=uuid4(),
            email="dispatcher@testcompany.com",
            name="Dispatcher",
            role=UserRole.DISPATCHER,
            tenant_id=regular_tenant.id,
            is_active=True,
        )
        db_session.add(dispatcher)
        await db_session.commit()
        
        token = create_access_token({
            "sub": str(dispatcher.id),
            "tenant_id": str(dispatcher.tenant_id),
            "role": dispatcher.role.value,
        })
        client.cookies.set("access_token", token)
        
        response = await client.get("/api/v1/admin/tenants")
        
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_driver_cannot_access_admin_endpoints(
        self,
        client: AsyncClient,
        db_session,
        regular_tenant: Tenant,
    ):
        """Driver cannot access admin endpoints."""
        driver = User(
            id=uuid4(),
            email="driver@testcompany.com",
            name="Driver",
            role=UserRole.DRIVER,
            tenant_id=regular_tenant.id,
            is_active=True,
        )
        db_session.add(driver)
        await db_session.commit()
        
        token = create_access_token({
            "sub": str(driver.id),
            "tenant_id": str(driver.tenant_id),
            "role": driver.role.value,
        })
        client.cookies.set("access_token", token)
        
        response = await client.get("/api/v1/admin/tenants")
        
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_access_admin_endpoints(
        self,
        client: AsyncClient,
    ):
        """Unauthenticated users cannot access admin endpoints."""
        response = await client.get("/api/v1/admin/tenants")
        
        assert response.status_code == 401
