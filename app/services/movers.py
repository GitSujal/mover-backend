"""Service for mover operations."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.driver import Driver
from app.models.organization import Organization
from app.models.truck import Truck
from app.schemas.driver import DriverCreate, DriverUpdate
from app.schemas.organization import OrganizationCreate, OrganizationUpdate
from app.schemas.truck import TruckCreate, TruckUpdate


class MoverService:
    """Service for managing mover organizations and fleet."""

    @staticmethod
    async def get_organization(db: AsyncSession, org_id: UUID) -> Organization | None:
        """Get organization by ID."""
        result = await db.execute(select(Organization).where(Organization.id == org_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_organization(db: AsyncSession, org_data: OrganizationCreate) -> Organization:
        """Create a new organization."""
        org = Organization(**org_data.model_dump())
        db.add(org)
        await db.commit()
        await db.refresh(org)
        return org

    @staticmethod
    async def update_organization(
        db: AsyncSession, org: Organization, update_data: OrganizationUpdate
    ) -> Organization:
        """Update an organization."""
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(org, field, value)

        await db.commit()
        await db.refresh(org)
        return org

    @staticmethod
    async def list_trucks(
        db: AsyncSession, org_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[Truck]:
        """List trucks for an organization."""
        result = await db.execute(
            select(Truck).where(Truck.org_id == org_id).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_truck(db: AsyncSession, truck_id: UUID) -> Truck | None:
        """Get truck by ID."""
        result = await db.execute(select(Truck).where(Truck.id == truck_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_truck(db: AsyncSession, org_id: UUID, truck_data: TruckCreate) -> Truck:
        """Create a new truck."""
        # Convert location input to PostGIS point
        location = (
            f"POINT({truck_data.base_location.longitude} {truck_data.base_location.latitude})"
        )

        data = truck_data.model_dump(exclude={"base_location"})
        truck = Truck(org_id=org_id, base_location=location, **data)
        db.add(truck)
        await db.commit()
        await db.refresh(truck)
        return truck

    @staticmethod
    async def update_truck(db: AsyncSession, truck: Truck, update_data: TruckUpdate) -> Truck:
        """Update a truck."""
        data = update_data.model_dump(exclude_unset=True)

        if "base_location" in data:
            loc = data.pop("base_location")
            truck.base_location = f"POINT({loc['longitude']} {loc['latitude']})"

        for field, value in data.items():
            setattr(truck, field, value)

        await db.commit()
        await db.refresh(truck)
        return truck

    @staticmethod
    async def list_drivers(
        db: AsyncSession, org_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[Driver]:
        """List drivers for an organization."""
        result = await db.execute(
            select(Driver).where(Driver.org_id == org_id).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_driver(db: AsyncSession, driver_id: UUID) -> Driver | None:
        """Get driver by ID."""
        result = await db.execute(select(Driver).where(Driver.id == driver_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_driver(db: AsyncSession, org_id: UUID, driver_data: DriverCreate) -> Driver:
        """Create a new driver."""
        driver = Driver(org_id=org_id, **driver_data.model_dump())
        db.add(driver)
        await db.commit()
        await db.refresh(driver)
        return driver

    @staticmethod
    async def update_driver(db: AsyncSession, driver: Driver, update_data: DriverUpdate) -> Driver:
        """Update a driver."""
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(driver, field, value)

        await db.commit()
        await db.refresh(driver)
        return driver
