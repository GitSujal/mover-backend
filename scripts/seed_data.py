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
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import get_db_context
from app.models.driver import Driver
from app.models.insurance import InsurancePolicy, InsuranceType
from app.models.organization import Organization, OrganizationStatus
from app.models.pricing import PricingConfig
from app.models.truck import Truck


async def seed_insurance_policies(orgs: list[Organization]):
    """Create insurance policies for organizations."""
    print("Creating insurance policies...")
    from sqlalchemy import select

    async with get_db_context() as db:
        count = 0
        for org in orgs:
            # Check if liability insurance exists
            result = await db.execute(
                select(InsurancePolicy).where(
                    InsurancePolicy.org_id == org.id,
                    InsurancePolicy.policy_type == InsuranceType.LIABILITY
                )
            )
            existing_liability = result.scalar_one_or_none()

            if not existing_liability:
                # General liability
                liability = InsurancePolicy(
                    org_id=org.id,
                    policy_type=InsuranceType.LIABILITY,
                    provider="State Farm",
                    policy_number=f"GL-{org.business_license_number}-001",
                    coverage_amount=1000000,
                    effective_date=datetime.utcnow() - timedelta(days=30),
                    expiry_date=datetime.utcnow() + timedelta(days=335),
                    document_url="https://example.com/insurance/liability.pdf",
                )
                db.add(liability)
                count += 1

            # Check if cargo insurance exists
            result = await db.execute(
                select(InsurancePolicy).where(
                    InsurancePolicy.org_id == org.id,
                    InsurancePolicy.policy_type == InsuranceType.CARGO
                )
            )
            existing_cargo = result.scalar_one_or_none()

            if not existing_cargo:
                # Cargo insurance
                cargo = InsurancePolicy(
                    org_id=org.id,
                    policy_type=InsuranceType.CARGO,
                    provider="Allstate",
                    policy_number=f"CG-{org.business_license_number}-001",
                    coverage_amount=500000,
                    effective_date=datetime.utcnow() - timedelta(days=30),
                    expiry_date=datetime.utcnow() + timedelta(days=335),
                    document_url="https://example.com/insurance/cargo.pdf",
                )
                db.add(cargo)
                count += 1

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

    from sqlalchemy import select

    async with get_db_context() as db:
        trucks = []
        created_count = 0

        # Assign trucks to organizations (2 each)
        for i, truck_data in enumerate(trucks_data):
            org_index = i // 2

            # Check if truck already exists by license plate
            result = await db.execute(
                select(Truck).where(Truck.license_plate == truck_data["license_plate"])
            )
            existing_truck = result.scalar_one_or_none()

            if existing_truck:
                trucks.append(existing_truck)
            else:
                truck = Truck(org_id=orgs[org_index].id, **truck_data)
                db.add(truck)
                trucks.append(truck)
                created_count += 1

        await db.commit()

        for truck in trucks:
            await db.refresh(truck)

        print(f"✓ Created {created_count} trucks ({len(trucks)} total)")
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

    from sqlalchemy import select

    async with get_db_context() as db:
        drivers = []
        created_count = 0

        # Assign drivers to organizations (2 each)
        for i, driver_data in enumerate(drivers_data):
            org_index = i // 2

            # Check if driver already exists by license number
            result = await db.execute(
                select(Driver).where(
                    Driver.drivers_license_number == driver_data["drivers_license_number"]
                )
            )
            existing_driver = result.scalar_one_or_none()

            if existing_driver:
                drivers.append(existing_driver)
            else:
                driver = Driver(org_id=orgs[org_index].id, **driver_data)
                db.add(driver)
                drivers.append(driver)
                created_count += 1

        await db.commit()

        for driver in drivers:
            await db.refresh(driver)

        print(f"✓ Created {created_count} drivers ({len(drivers)} total)")
        return drivers


async def seed_pricing_configs(orgs: list[Organization]):
    """Create pricing configurations."""
    print("Creating pricing configurations...")
    from sqlalchemy import select

    async with get_db_context() as db:
        count = 0
        for org in orgs:
            # Check if pricing config already exists for this org
            result = await db.execute(
                select(PricingConfig).where(
                    PricingConfig.org_id == org.id,
                    PricingConfig.is_active == True
                )
            )
            existing_pricing = result.scalar_one_or_none()

            if not existing_pricing:
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
                            "description": "Stairs surcharge (per flight)",
                        },
                        {"type": "piano", "amount": 150.0, "description": "Piano moving surcharge"},
                        {
                            "type": "weekend",
                            "multiplier": 1.25,
                            "days": [0, 6],  # Sunday and Saturday
                            "description": "Weekend surcharge (25% extra)",
                        },
                        {
                            "type": "after_hours",
                            "multiplier": 1.20,
                            "min_time": "18:00",
                            "max_time": "08:00",
                            "description": "After hours surcharge (20% extra)",
                        },
                    ],
                    is_active=True,
                )
                db.add(pricing)
                count += 1

        await db.commit()
        print(f"✓ Created {count} pricing configurations")


async def seed_bookings(orgs: list[Organization]):
    """Create sample bookings."""
    print("Creating bookings...")
    from app.models.booking import Booking, BookingStatus
    from app.models.truck import Truck
    from sqlalchemy import select

    async with get_db_context() as db:
        count = 0
        for org in orgs:
            # Get a truck for this org
            result = await db.execute(select(Truck).where(Truck.org_id == org.id).limit(1))
            truck = result.scalar_one_or_none()

            if not truck:
                continue

            # Check if past booking exists
            past_date = datetime.utcnow() - timedelta(days=2)
            result = await db.execute(
                select(Booking).where(
                    Booking.org_id == org.id,
                    Booking.customer_email == "olivia.martin@email.com"
                )
            )
            existing_booking1 = result.scalar_one_or_none()

            if not existing_booking1:
                # Past booking (Completed)
                booking1 = Booking(
                    org_id=org.id,
                    truck_id=truck.id,
                    customer_name="Olivia Martin",
                    customer_email="olivia.martin@email.com",
                    customer_phone="+15551234567",
                    pickup_address="123 Start St, San Francisco, CA 94102",
                    dropoff_address="456 End Ave, Oakland, CA 94601",
                    pickup_date=past_date,
                    move_date=past_date,
                    status=BookingStatus.COMPLETED,
                    estimated_amount=1999.00,
                    actual_amount=1999.00,
                    distance_miles=15.5,
                    estimated_duration_hours=4,
                )
                db.add(booking1)
                count += 1

            # Check if upcoming booking exists
            result = await db.execute(
                select(Booking).where(
                    Booking.org_id == org.id,
                    Booking.customer_email == "jackson.lee@email.com"
                )
            )
            existing_booking2 = result.scalar_one_or_none()

            if not existing_booking2:
                # Upcoming booking (Confirmed)
                future_date = datetime.utcnow() + timedelta(days=1)
                booking2 = Booking(
                    org_id=org.id,
                    truck_id=truck.id,
                    customer_name="Jackson Lee",
                    customer_email="jackson.lee@email.com",
                    customer_phone="+15559876543",
                    pickup_address="789 Main St, San Francisco, CA 94103",
                    dropoff_address="321 Oak Ave, Berkeley, CA 94704",
                    pickup_date=future_date,
                    move_date=future_date,
                    status=BookingStatus.CONFIRMED,
                    estimated_amount=1250.00,
                    distance_miles=12.0,
                    estimated_duration_hours=3,
                )
                db.add(booking2)
                count += 1

        await db.commit()
        print(f"✓ Created {count} bookings")


async def seed_invoices(orgs: list[Organization]):
    """Create sample invoices."""
    print("Creating invoices...")
    from app.models.invoice import Invoice, InvoiceStatus
    from app.models.booking import Booking
    from sqlalchemy import select

    async with get_db_context() as db:
        count = 0
        for org in orgs:
            # Get bookings for this org
            result = await db.execute(select(Booking).where(Booking.org_id == org.id))
            bookings = result.scalars().all()

            for booking in bookings:
                # Check if invoice already exists for this booking
                result = await db.execute(
                    select(Invoice).where(Invoice.booking_id == booking.id)
                )
                existing_invoice = result.scalar_one_or_none()

                if not existing_invoice:
                    status = (
                        InvoiceStatus.PAID if booking.status == "COMPLETED" else InvoiceStatus.ISSUED
                    )
                    amount = (
                        booking.actual_amount if booking.actual_amount else booking.estimated_amount
                    )

                    invoice = Invoice(
                        org_id=org.id,
                        booking_id=booking.id,
                        invoice_number=f"INV-{booking.id.hex[:8].upper()}",
                        status=status,
                        subtotal=amount * 0.9,
                        tax_amount=amount * 0.1,
                        total_amount=amount,
                        issued_at=datetime.utcnow(),
                        due_date=datetime.utcnow() + timedelta(days=30),
                        paid_at=datetime.utcnow() if status == InvoiceStatus.PAID else None,
                        payment_method="credit_card" if status == InvoiceStatus.PAID else None,
                    )
                    db.add(invoice)
                    count += 1

        await db.commit()
        print(f"✓ Created {count} invoices")


async def seed_support_tickets(orgs: list[Organization]):
    """Create sample support tickets."""
    print("Creating support tickets...")
    from app.models.support import SupportTicket, IssueStatus, IssueType, IssuePriority
    from sqlalchemy import select

    async with get_db_context() as db:
        count = 0
        for org in orgs:
            # Check if ticket from Alice exists
            result = await db.execute(
                select(SupportTicket).where(
                    SupportTicket.org_id == org.id,
                    SupportTicket.customer_email == "alice@example.com"
                )
            )
            existing_ticket1 = result.scalar_one_or_none()

            if not existing_ticket1:
                ticket1 = SupportTicket(
                    org_id=org.id,
                    customer_name="Alice Johnson",
                    customer_email="alice@example.com",
                    subject="Late Arrival",
                    description="The movers arrived 2 hours late.",
                    issue_type=IssueType.LATE_ARRIVAL,
                    priority=IssuePriority.MEDIUM,
                    status=IssueStatus.OPEN,
                )
                db.add(ticket1)
                count += 1

            # Check if ticket from Bob exists
            result = await db.execute(
                select(SupportTicket).where(
                    SupportTicket.org_id == org.id,
                    SupportTicket.customer_email == "bob@example.com"
                )
            )
            existing_ticket2 = result.scalar_one_or_none()

            if not existing_ticket2:
                ticket2 = SupportTicket(
                    org_id=org.id,
                    customer_name="Bob Smith",
                    customer_email="bob@example.com",
                    subject="Damaged Item",
                    description="My lamp was broken during the move.",
                    issue_type=IssueType.DAMAGE,
                    priority=IssuePriority.HIGH,
                    status=IssueStatus.IN_PROGRESS,
                )
                db.add(ticket2)
                count += 1

        await db.commit()
        print(f"✓ Created {count} support tickets")


async def seed_organizations():
    """Create sample organizations."""
    print("Creating organizations...")
    from app.models.organization import Organization, OrganizationStatus
    from sqlalchemy import select

    organizations_data = [
        {
            "name": "Oakland Movers",
            "email": "info@oaklandmovers.com",
            "phone": "+15101234567",
            "business_license_number": "BLN-OAK-001",
            "tax_id": "TID-OAK-001",
            "address_line1": "123 Main St",
            "city": "Oakland",
            "state": "CA",
            "zip_code": "94607",
        },
        {
            "name": "San Francisco Haulers",
            "email": "contact@sfhaulers.com",
            "phone": "+14159876543",
            "business_license_number": "BLN-SFH-002",
            "tax_id": "TID-SFH-002",
            "address_line1": "456 Market St",
            "city": "San Francisco",
            "state": "CA",
            "zip_code": "94105",
        },
    ]

    created_orgs = []
    count = 0
    async with get_db_context() as db:
        for org_data in organizations_data:
            # Check if org exists
            result = await db.execute(
                select(Organization).where(Organization.email == org_data["email"])
            )
            existing_org = result.scalar_one_or_none()

            if existing_org:
                print(f"  - Organization {org_data['name']} already exists")
                created_orgs.append(existing_org)
                continue

            org = Organization(
                name=org_data["name"],
                email=org_data["email"],
                phone=org_data["phone"],
                business_license_number=org_data["business_license_number"],
                tax_id=org_data["tax_id"],
                address_line1=org_data["address_line1"],
                city=org_data["city"],
                state=org_data["state"],
                zip_code=org_data["zip_code"],
                status=OrganizationStatus.APPROVED,
            )
            db.add(org)
            created_orgs.append(org)
            count += 1

        await db.commit()

        # Refresh all orgs to ensure they are bound to the session
        for i, org in enumerate(created_orgs):
            if org not in db:
                result = await db.execute(select(Organization).where(Organization.id == org.id))
                created_orgs[i] = result.scalar_one()

        print(f"✓ Created {count} organizations")
        return created_orgs


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
        await seed_bookings(orgs)
        await seed_invoices(orgs)
        await seed_support_tickets(orgs)

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
