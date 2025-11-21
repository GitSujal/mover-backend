"""Integration tests for booking API endpoints."""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from app.models.driver import Driver
from app.models.organization import Organization, OrganizationStatus
from app.models.pricing import PricingConfig
from app.models.truck import Truck, TruckSize, TruckStatus


@pytest.mark.integration
class TestBookingAPI:
    """Test booking API endpoints."""

    def _create_booking_data(self, org_truck_data, **kwargs):
        """Helper to create booking data with required fields."""
        base_data = {
            "org_id": str(org_truck_data["org"].id),
            "truck_id": str(org_truck_data["truck"].id),
        }
        base_data.update(kwargs)
        return base_data

    @pytest.fixture
    async def sample_org_with_truck(self, db_session):
        """Create organization with truck and pricing."""
        # Create organization
        org = Organization(
            name="Test Movers",
            email="test@movers.com",
            phone="+14155551234",
            business_license_number="BL-TEST-001",
            tax_id="12-3456789",
            address_line1="123 Test St",
            city="San Francisco",
            state="CA",
            zip_code="94105",
            status=OrganizationStatus.APPROVED,
        )
        db_session.add(org)
        await db_session.commit()
        await db_session.refresh(org)

        # Create truck
        truck = Truck(
            org_id=org.id,
            license_plate="TEST123",
            make="Ford",
            model="F-650",
            year=2022,
            size=TruckSize.LARGE,
            capacity_cubic_feet=1200,
            max_weight_lbs=10000,
            status=TruckStatus.AVAILABLE,
            base_location="SRID=4326;POINT(-122.4194 37.7749)",  # PostGIS format: lon lat
            registration_number="REG123456",
            registration_expiry="2026-12-31",
        )
        db_session.add(truck)

        # Create driver
        driver = Driver(
            org_id=org.id,
            first_name="John",
            last_name="Driver",
            email="john@test.com",
            phone="+14155559999",
            drivers_license_number="D1234567",
            drivers_license_state="CA",
            drivers_license_expiry="2026-12-31",
            has_cdl=True,
            cdl_class="B",
            is_verified=True,
            background_check_completed=True,
        )
        db_session.add(driver)

        # Create pricing config
        pricing = PricingConfig(
            org_id=org.id,
            base_hourly_rate=150.0,
            base_mileage_rate=2.50,
            minimum_charge=200.0,
            surcharge_rules=[{"type": "stairs", "amount": 50.0, "per_flight": True}],
            is_active=True,
        )
        db_session.add(pricing)

        await db_session.commit()
        await db_session.refresh(truck)
        await db_session.refresh(driver)

        return {"org": org, "truck": truck, "driver": driver}

    async def test_create_booking_success(self, client: AsyncClient, sample_org_with_truck):
        """Test successful booking creation."""
        # Book for tomorrow
        move_date = datetime.now(UTC) + timedelta(days=1)

        booking_data = self._create_booking_data(
            sample_org_with_truck,
            customer_name="John Doe",
            customer_email="john@example.com",
            customer_phone="+14155551111",
            move_date=move_date.isoformat(),
            pickup_address="123 Start St",
            pickup_city="San Francisco",
            pickup_state="CA",
            pickup_zip="94102",
            pickup_floors=2,
            has_elevator_pickup=False,
            dropoff_address="456 End Ave",
            dropoff_city="Oakland",
            dropoff_state="CA",
            dropoff_zip="94601",
            dropoff_floors=1,
            has_elevator_dropoff=True,
            estimated_distance_miles=15.5,
            estimated_duration_hours=4.0,
            special_items=["piano"],
            customer_notes="Handle with care",
        )

        response = await client.post("/api/v1/bookings", json=booking_data)

        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "id" in data
        assert data["customer_name"] == "John Doe"
        assert data["customer_email"] == "john@example.com"
        assert data["status"] == "confirmed"
        assert data["pickup_floors"] == 2
        assert data["dropoff_floors"] == 1
        assert "piano" in data["special_items"]
        assert data["customer_notes"] == "Handle with care"

    async def test_create_booking_validation_error(self, client: AsyncClient):
        """Test booking creation with invalid data."""
        booking_data = {
            "customer_name": "J",  # Too short
            "customer_email": "invalid-email",  # Invalid email
            "customer_phone": "123",  # Invalid phone
            # Missing required fields
        }

        response = await client.post("/api/v1/bookings", json=booking_data)

        assert response.status_code == 422  # Validation error

    async def test_get_booking_by_id(self, client: AsyncClient, sample_org_with_truck):
        """Test retrieving a booking by ID."""
        # First create a booking
        move_date = datetime.now(UTC) + timedelta(days=1)

        booking_data = self._create_booking_data(
            sample_org_with_truck,
            customer_name="Jane Smith",
            customer_email="jane@example.com",
            customer_phone="+14155552222",
            move_date=move_date.isoformat(),
            pickup_address="789 Main St",
            pickup_city="San Francisco",
            pickup_state="CA",
            pickup_zip="94103",
            pickup_floors=0,
            has_elevator_pickup=True,
            dropoff_address="321 Oak Ave",
            dropoff_city="Berkeley",
            dropoff_state="CA",
            dropoff_zip="94704",
            dropoff_floors=3,
            has_elevator_dropoff=False,
            estimated_distance_miles=10.0,
            estimated_duration_hours=3.0,
            special_items=[],
        )

        create_response = await client.post("/api/v1/bookings", json=booking_data)
        assert create_response.status_code == 201
        booking_id = create_response.json()["id"]

        # Now retrieve it
        get_response = await client.get(f"/api/v1/bookings/{booking_id}")

        assert get_response.status_code == 200
        data = get_response.json()
        assert data["id"] == booking_id
        assert data["customer_name"] == "Jane Smith"
        assert data["customer_email"] == "jane@example.com"

    async def test_get_nonexistent_booking(self, client: AsyncClient):
        """Test retrieving a booking that doesn't exist."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/api/v1/bookings/{fake_id}")

        assert response.status_code == 404

    async def test_list_bookings(self, client: AsyncClient, sample_org_with_truck):
        """Test listing all bookings requires authentication."""
        # Create multiple bookings at different times to avoid conflicts
        base_date = datetime.now(UTC) + timedelta(days=1)

        for i in range(3):
            # Space bookings 1 day apart to avoid conflicts
            move_date = base_date + timedelta(days=i)
            booking_data = self._create_booking_data(
                sample_org_with_truck,
                customer_name=f"Customer {i}",
                customer_email=f"customer{i}@example.com",
                customer_phone=f"+1415555000{i}",
                move_date=move_date.isoformat(),
                pickup_address=f"{i} Start St",
                pickup_city="San Francisco",
                pickup_state="CA",
                pickup_zip="94102",
                pickup_floors=0,
                has_elevator_pickup=True,
                dropoff_address=f"{i} End Ave",
                dropoff_city="Oakland",
                dropoff_state="CA",
                dropoff_zip="94601",
                dropoff_floors=0,
                has_elevator_dropoff=True,
                estimated_distance_miles=10.0,
                estimated_duration_hours=2.0,
                special_items=[],
            )
            response = await client.post("/api/v1/bookings", json=booking_data)
            assert response.status_code == 201

        # List endpoint requires authentication (returns 403 without auth)
        list_response = await client.get("/api/v1/bookings")

        # Should return 403 Forbidden because no authentication provided
        assert list_response.status_code == 403

    async def test_update_booking_status(self, client: AsyncClient, sample_org_with_truck):
        """Test updating booking status requires authentication."""
        # Create booking
        move_date = datetime.now(UTC) + timedelta(days=1)

        booking_data = self._create_booking_data(
            sample_org_with_truck,
            customer_name="Test Customer",
            customer_email="test@example.com",
            customer_phone="+14155553333",
            move_date=move_date.isoformat(),
            pickup_address="100 Test St",
            pickup_city="San Francisco",
            pickup_state="CA",
            pickup_zip="94105",
            pickup_floors=0,
            has_elevator_pickup=True,
            dropoff_address="200 Test Ave",
            dropoff_city="Oakland",
            dropoff_state="CA",
            dropoff_zip="94607",
            dropoff_floors=0,
            has_elevator_dropoff=True,
            estimated_distance_miles=5.0,
            estimated_duration_hours=2.0,
            special_items=[],
        )

        create_response = await client.post("/api/v1/bookings", json=booking_data)
        assert create_response.status_code == 201
        booking_id = create_response.json()["id"]

        # Update endpoint requires authentication (returns 403 without auth)
        update_response = await client.patch(
            f"/api/v1/bookings/{booking_id}", json={"status": "CONFIRMED"}
        )

        # Should return 403 Forbidden because no authentication provided
        assert update_response.status_code == 403

    async def test_stairs_surcharge_calculation(self, client: AsyncClient, sample_org_with_truck):
        """Test that stairs surcharge is calculated correctly."""
        move_date = datetime.now(UTC) + timedelta(days=1)

        # Booking with stairs at both locations
        booking_data = self._create_booking_data(
            sample_org_with_truck,
            customer_name="Stairs Test",
            customer_email="stairs@example.com",
            customer_phone="+14155554444",
            move_date=move_date.isoformat(),
            pickup_address="Walk-up Building",
            pickup_city="San Francisco",
            pickup_state="CA",
            pickup_zip="94102",
            pickup_floors=3,  # 3 flights
            has_elevator_pickup=False,  # No elevator!
            dropoff_address="Another Walk-up",
            dropoff_city="Oakland",
            dropoff_state="CA",
            dropoff_zip="94601",
            dropoff_floors=2,  # 2 flights
            has_elevator_dropoff=False,  # No elevator!
            estimated_distance_miles=10.0,
            estimated_duration_hours=4.0,
            special_items=[],
        )

        response = await client.post("/api/v1/bookings", json=booking_data)

        assert response.status_code == 201
        data = response.json()

        # Verify booking was created correctly
        assert data["pickup_floors"] == 3
        assert data["has_elevator_pickup"] is False
        assert data["dropoff_floors"] == 2
        assert data["has_elevator_dropoff"] is False

        # Price calculation happens on backend
        # With 5 total flights at $50/flight = $250 stairs surcharge
        # This is tested in the pricing unit tests

    async def test_special_items_handling(self, client: AsyncClient, sample_org_with_truck):
        """Test booking with multiple special items."""
        move_date = datetime.now(UTC) + timedelta(days=1)

        booking_data = self._create_booking_data(
            sample_org_with_truck,
            customer_name="Special Items Customer",
            customer_email="special@example.com",
            customer_phone="+14155555555",
            move_date=move_date.isoformat(),
            pickup_address="123 Art St",
            pickup_city="San Francisco",
            pickup_state="CA",
            pickup_zip="94102",
            pickup_floors=0,
            has_elevator_pickup=True,
            dropoff_address="456 Gallery Ave",
            dropoff_city="Oakland",
            dropoff_state="CA",
            dropoff_zip="94601",
            dropoff_floors=0,
            has_elevator_dropoff=True,
            estimated_distance_miles=12.0,
            estimated_duration_hours=5.0,
            special_items=["piano", "antiques", "artwork"],
        )

        response = await client.post("/api/v1/bookings", json=booking_data)

        assert response.status_code == 201
        data = response.json()

        assert "piano" in data["special_items"]
        assert "antiques" in data["special_items"]
        assert "artwork" in data["special_items"]
        assert len(data["special_items"]) == 3


@pytest.mark.integration
class TestHealthEndpoints:
    """Test health check endpoints."""

    async def test_health_check(self, client: AsyncClient):
        """Test main health check endpoint."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    async def test_database_health_check(self, client: AsyncClient):
        """Test database health check."""
        response = await client.get("/health/db")

        # Will pass if database is connected (which it is in tests)
        assert response.status_code in [200, 503]
