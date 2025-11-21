"""Pytest configuration and fixtures."""

import asyncio
import os
from collections.abc import AsyncGenerator, Generator
from datetime import UTC

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Import all models to ensure tables are created
from app import models  # noqa: F401
from app.core.database import get_db
from app.main import app
from app.models.base import Base

# Test database URL
TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://movehub:movehub_dev_password@localhost:5432/movehub_test",
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    # Drop all tables and recreate
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        # Ensure required PostgreSQL extensions are enabled
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Clean up after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def sample_organization_data() -> dict:
    """Sample organization data for testing."""
    return {
        "name": "Test Moving Company",
        "email": "test@movingcompany.com",
        "phone": "+15551234567",
        "business_license_number": "BL123456",
        "tax_id": "12-3456789",
        "address_line1": "123 Main St",
        "address_line2": "Suite 100",
        "city": "San Francisco",
        "state": "CA",
        "zip_code": "94102",
    }


@pytest.fixture
def sample_booking_data() -> dict:
    """Sample booking data for testing."""
    from datetime import datetime, timedelta

    move_date = datetime.now(UTC) + timedelta(days=7)

    return {
        "customer_name": "John Doe",
        "customer_email": "john@example.com",
        "customer_phone": "+15559876543",
        "move_date": move_date.isoformat(),
        "pickup_address": "123 Start St",
        "pickup_city": "San Francisco",
        "pickup_state": "CA",
        "pickup_zip": "94102",
        "dropoff_address": "456 End Ave",
        "dropoff_city": "Oakland",
        "dropoff_state": "CA",
        "dropoff_zip": "94601",
        "estimated_distance_miles": 15.5,
        "estimated_duration_hours": 4.0,
        "special_items": ["piano"],
        "pickup_floors": 2,
        "dropoff_floors": 1,
        "has_elevator_pickup": False,
        "has_elevator_dropoff": True,
        "customer_notes": "Handle piano with care",
    }


@pytest.fixture
def auth_headers() -> dict:
    """Return authentication headers for testing."""
    return {"Authorization": "Bearer test_token"}


@pytest_asyncio.fixture
async def organization(db_session: AsyncSession, sample_organization_data: dict):
    """Create an organization in the database."""
    from app.models.organization import Organization, OrganizationStatus

    org = Organization(**sample_organization_data)
    org.status = OrganizationStatus.APPROVED
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest.fixture
def sample_driver_data(organization) -> dict:
    """Sample driver data for testing."""
    return {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane@example.com",
        "phone": "+15551112222",
        "drivers_license_number": "DL123456",
        "drivers_license_state": "CA",
        "drivers_license_expiry": "2030-01-01",
        "org_id": str(organization.id),
        "is_verified": True,
    }


@pytest.fixture
def sample_truck_data(organization) -> dict:
    """Sample truck data for testing."""
    return {
        "license_plate": "TRUCK1",
        "make": "Ford",
        "model": "F-150",
        "year": 2023,
        "capacity_cubic_feet": 1000,
        "max_weight_lbs": 5000,
        "size": "medium",
        "base_location": {"latitude": 37.7749, "longitude": -122.4194},
        "registration_number": "REG123456",
        "registration_expiry": "2030-01-01",
        "org_id": str(organization.id),
        "status": "available",
    }


@pytest_asyncio.fixture
async def driver(db_session: AsyncSession, sample_driver_data: dict):
    """Create a driver in the database."""
    from app.models.driver import Driver

    driver = Driver(**sample_driver_data)
    db_session.add(driver)
    await db_session.commit()
    await db_session.refresh(driver)
    return driver


@pytest_asyncio.fixture
async def truck(db_session: AsyncSession, sample_truck_data: dict):
    """Create a truck in the database."""
    from app.models.truck import Truck

    # Create a copy to avoid modifying the fixture data
    truck_data = sample_truck_data.copy()

    # Convert base_location dict to WKT for DB
    if isinstance(truck_data["base_location"], dict):
        lat = truck_data["base_location"]["latitude"]
        lng = truck_data["base_location"]["longitude"]
        truck_data["base_location"] = f"POINT({lng} {lat})"

    truck = Truck(**truck_data)
    db_session.add(truck)
    await db_session.commit()
    await db_session.refresh(truck)
    return truck


@pytest.fixture
def sample_user_data(organization) -> dict:
    """Sample user data for testing."""
    from app.models.user import UserRole

    return {
        "email": "mover@example.com",
        "hashed_password": "hashed_secret",
        "first_name": "Mover",
        "last_name": "Admin",
        "role": UserRole.ORG_OWNER,
        "org_id": organization.id,
        "is_active": True,
        "is_verified": True,
    }


@pytest_asyncio.fixture
async def user(db_session: AsyncSession, sample_user_data: dict):
    """Create a user in the database."""
    from app.models.user import User

    user = User(**sample_user_data)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def authed_client(client: AsyncClient, user):
    """Create an authenticated client."""
    from app.api.dependencies import get_current_user
    from app.main import app

    app.dependency_overrides[get_current_user] = lambda: user
    yield client
    app.dependency_overrides.pop(get_current_user, None)
