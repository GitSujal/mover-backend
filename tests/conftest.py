"""Pytest configuration and fixtures."""

import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Import all models to ensure tables are created
from app import models  # noqa: F401
from app.core.database import Base, get_db
from app.main import app

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://movehub:test_password@localhost:5432/movehub_test"


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

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables
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

    move_date = datetime.utcnow() + timedelta(days=7)

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
