"""
Seed database with sample data for testing.

Run this script to populate the database with:
- Sample moving companies (organizations)
- Trucks
- Drivers
- Insurance policies
- Pricing configurations

Usage:
    python scripts/seed_data.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import select

from app.core.database import get_db_context
from app.models.organization import Organization, OrganizationStatus
from app.models.truck import Truck
from app.models.driver import Driver
from app.models.insurance import InsurancePolicy, InsuranceType
from app.models.pricing import PricingConfig
from app.core.security import get_password_hash


async def seed_organizations():
    """Create sample moving companies."""
    print("Creating organizations...")

    orgs_data = [
        {
            "name": "Bay Area Movers",
            "email": "contact@bayareamovers.com",
            "phone": "+14155551234",
            "business_license_number": "BL-2024-001",
            "tax_id": "12-3456789",
            "address_line1": "123 Mission St",
            "city": "San Francisco",
            "state": "CA",
            "zip_code": "94105",
            "status": OrganizationStatus.APPROVED,
        },
        {
            "name": "Golden Gate Moving Co",
            "email": "info@goldengatemove.com",
            "phone": "+14155552345",
            "business_license_number": "BL-2024-002",
            "tax_id": "98-7654321",
            "address_line1": "456 Market St",
            "city": "San Francisco",
            "state": "CA",
            "zip_code": "94103",
            "status": OrganizationStatus.APPROVED,
        },
        {
            "name": "Oakland Express Movers",
            "email": "hello@oaklandmovers.com",
            "phone": "+15105553456",
            "business_license_number": "BL-2024-003",
            "tax_id": "45-6789012",
            "address_line1": "789 Broadway",
            "city": "Oakland",
            "state": "CA",
            "zip_code": "94607",
            "status": OrganizationStatus.APPROVED,
        },
    ]

    async with get_db_context() as db:
        orgs = []
        for org_data in orgs_data:
            org = Organization(**org_data)
            db.add(org)
            orgs.append(org)

        await db.commit()

        # Refresh to get IDs
        for org in orgs:
            await db.refresh(org)

        print(f"✓ Created {len(orgs)} organizations")
        return orgs


async def seed_insurance_policies(orgs: list[Organization]):
    """Create insurance policies for organizations."""
    print("Creating insurance policies...")

    async with get_db_context() as db:
        count = 0
        for org in orgs:
            # General liability
            liability = InsurancePolicy(
                org_id=org.id,
                insurance_type=InsuranceType.GENERAL_LIABILITY,
                provider="State Farm",
                policy_number=f"GL-{org.business_license_number}-001",
                coverage_amount=1000000,
                effective_date=datetime.utcnow() - timedelta(days=30),
                expiry_date=datetime.utcnow() + timedelta(days=335),
            )
            db.add(liability)

            # Cargo insurance
            cargo = InsurancePolicy(
                org_id=org.id,
                insurance_type=InsuranceType.CARGO,
                provider="Allstate",
                policy_number=f"CG-{org.business_license_number}-001",
                coverage_amount=500000,
                effective_date=datetime.utcnow() - timedelta(days=30),
                expiry_date=datetime.utcnow() + timedelta(days=335),
            )
            db.add(cargo)
            count += 2

        await db.commit()
        print(f"✓ Created {count} insurance policies")


async def seed_trucks(orgs: list[Organization]):
    """Create sample trucks."""
    print("Creating trucks...")

    trucks_data = [
        # Bay Area Movers trucks
        {
            "license_plate": "CA-1234AB",
            "make": "Ford",
            "model": "F-650",
            "year": 2022,
            "capacity_cubic_feet": 1200,
            "current_latitude": 37.7749,
            "current_longitude": -122.4194,
        },
        {
            "license_plate": "CA-5678CD",
            "make": "Freightliner",
            "model": "M2",
            "year": 2021,
            "capacity_cubic_feet": 1500,
            "current_latitude": 37.7849,
            "current_longitude": -122.4294,
        },
        # Golden Gate Moving Co trucks
        {
            "license_plate": "CA-9012EF",
            "make": "International",
            "model": "DuraStar",
            "year": 2023,
            "capacity_cubic_feet": 1300,
            "current_latitude": 37.7649,
            "current_longitude": -122.4094,
        },
        {
            "license_plate": "CA-3456GH",
            "make": "Isuzu",
            "model": "NPR",
            "year": 2022,
            "capacity_cubic_feet": 1000,
            "current_latitude": 37.7549,
            "current_longitude": -122.3994,
        },
        # Oakland Express Movers trucks
        {
            "license_plate": "CA-7890IJ",
            "make": "Mercedes-Benz",
            "model": "Sprinter",
            "year": 2023,
            "capacity_cubic_feet": 800,
            "current_latitude": 37.8044,
            "current_longitude": -122.2711,
        },
        {
            "license_plate": "CA-2345KL",
            "make": "Ford",
            "model": "Transit",
            "year": 2022,
            "capacity_cubic_feet": 900,
            "current_latitude": 37.8144,
            "current_longitude": -122.2811,
        },
    ]

    async with get_db_context() as db:
        trucks = []
        # Assign trucks to organizations (2 each)
        for i, truck_data in enumerate(trucks_data):
            org_index = i // 2
            truck = Truck(
                org_id=orgs[org_index].id,
                **truck_data
            )
            db.add(truck)
            trucks.append(truck)

        await db.commit()

        for truck in trucks:
            await db.refresh(truck)

        print(f"✓ Created {len(trucks)} trucks")
        return trucks


async def seed_drivers(orgs: list[Organization]):
    """Create sample drivers."""
    print("Creating drivers...")

    drivers_data = [
        # Bay Area Movers drivers
        {
            "first_name": "John",
            "last_name": "Smith",
            "email": "john.smith@bayareamovers.com",
            "phone": "+14155551111",
            "drivers_license_number": "D1234567",
            "drivers_license_state": "CA",
            "drivers_license_expiry": "2026-12-31",
            "has_cdl": True,
            "cdl_class": "B",
            "is_verified": True,
            "background_check_completed": True,
        },
        {
            "first_name": "Maria",
            "last_name": "Garcia",
            "email": "maria.garcia@bayareamovers.com",
            "phone": "+14155552222",
            "drivers_license_number": "D2345678",
            "drivers_license_state": "CA",
            "drivers_license_expiry": "2027-06-30",
            "has_cdl": True,
            "cdl_class": "B",
            "is_verified": True,
            "background_check_completed": True,
        },
        # Golden Gate Moving Co drivers
        {
            "first_name": "David",
            "last_name": "Chen",
            "email": "david.chen@goldengatemove.com",
            "phone": "+14155553333",
            "drivers_license_number": "D3456789",
            "drivers_license_state": "CA",
            "drivers_license_expiry": "2026-03-31",
            "has_cdl": True,
            "cdl_class": "B",
            "is_verified": True,
            "background_check_completed": True,
        },
        {
            "first_name": "Sarah",
            "last_name": "Johnson",
            "email": "sarah.johnson@goldengatemove.com",
            "phone": "+14155554444",
            "drivers_license_number": "D4567890",
            "drivers_license_state": "CA",
            "drivers_license_expiry": "2027-09-30",
            "has_cdl": True,
            "cdl_class": "B",
            "is_verified": True,
            "background_check_completed": True,
        },
        # Oakland Express Movers drivers
        {
            "first_name": "Michael",
            "last_name": "Brown",
            "email": "michael.brown@oaklandmovers.com",
            "phone": "+15105555555",
            "drivers_license_number": "D5678901",
            "drivers_license_state": "CA",
            "drivers_license_expiry": "2026-08-31",
            "has_cdl": False,
            "is_verified": True,
            "background_check_completed": True,
        },
        {
            "first_name": "Emily",
            "last_name": "Davis",
            "email": "emily.davis@oaklandmovers.com",
            "phone": "+15105556666",
            "drivers_license_number": "D6789012",
            "drivers_license_state": "CA",
            "drivers_license_expiry": "2027-11-30",
            "has_cdl": False,
            "is_verified": True,
            "background_check_completed": True,
        },
    ]

    async with get_db_context() as db:
        drivers = []
        # Assign drivers to organizations (2 each)
        for i, driver_data in enumerate(drivers_data):
            org_index = i // 2
            driver = Driver(
                org_id=orgs[org_index].id,
                **driver_data
            )
            db.add(driver)
            drivers.append(driver)

        await db.commit()

        for driver in drivers:
            await db.refresh(driver)

        print(f"✓ Created {len(drivers)} drivers")
        return drivers


async def seed_pricing_configs(orgs: list[Organization]):
    """Create pricing configurations."""
    print("Creating pricing configurations...")

    async with get_db_context() as db:
        count = 0
        for org in orgs:
            pricing = PricingConfig(
                org_id=org.id,
                base_hourly_rate=150.0,
                base_mileage_rate=2.50,
                minimum_charge=200.0,
                surcharge_rules=[
                    {
                        "type": "stairs",
                        "amount": 50.0,
                        "per_flight": True,
                        "description": "Stairs surcharge (per flight)"
                    },
                    {
                        "type": "piano",
                        "amount": 150.0,
                        "description": "Piano moving surcharge"
                    },
                    {
                        "type": "weekend",
                        "multiplier": 1.25,
                        "days": [0, 6],  # Sunday and Saturday
                        "description": "Weekend surcharge (25% extra)"
                    },
                    {
                        "type": "after_hours",
                        "multiplier": 1.20,
                        "min_time": "18:00",
                        "max_time": "08:00",
                        "description": "After hours surcharge (20% extra)"
                    }
                ],
                is_active=True,
            )
            db.add(pricing)
            count += 1

        await db.commit()
        print(f"✓ Created {count} pricing configurations")


async def main():
    """Run all seed functions."""
    print("\n=== Seeding Database ===\n")

    try:
        # Create organizations first
        orgs = await seed_organizations()

        # Create dependent data
        await seed_insurance_policies(orgs)
        await seed_trucks(orgs)
        await seed_drivers(orgs)
        await seed_pricing_configs(orgs)

        print("\n=== ✓ Database seeded successfully! ===\n")
        print("Sample Organizations:")
        for org in orgs:
            print(f"  - {org.name} ({org.id})")

    except Exception as e:
        print(f"\n✗ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
