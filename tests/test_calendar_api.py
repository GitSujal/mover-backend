"""Tests for calendar and fleet management API endpoints."""

import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient

from app.models.booking import BookingStatus

pytestmark = pytest.mark.asyncio


class TestCalendarAPI:
    """Test calendar and fleet management endpoints."""

    async def test_get_calendar_bookings_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_organization_data: dict,
        sample_booking_data: dict,
    ):
        """Test retrieving calendar bookings."""
        # Create a booking
        booking_response = await client.post(
            "/api/v1/bookings",
            json=sample_booking_data,
        )
        assert booking_response.status_code == 201

        # Get calendar bookings
        start_date = datetime.utcnow().isoformat()
        end_date = (datetime.utcnow() + timedelta(days=30)).isoformat()

        response = await client.get(
            "/api/v1/calendar/bookings",
            params={
                "start_date": start_date,
                "end_date": end_date,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "bookings" in data
        assert "total_bookings" in data
        assert data["total_bookings"] >= 1

    async def test_get_calendar_bookings_with_status_filter(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_booking_data: dict,
    ):
        """Test calendar bookings with status filter."""
        # Create a booking
        await client.post("/api/v1/bookings", json=sample_booking_data)

        # Get only pending bookings
        start_date = datetime.utcnow().isoformat()
        end_date = (datetime.utcnow() + timedelta(days=30)).isoformat()

        response = await client.get(
            "/api/v1/calendar/bookings",
            params={
                "start_date": start_date,
                "end_date": end_date,
                "status_filter": [BookingStatus.PENDING.value],
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert all(
            booking["status"] == BookingStatus.PENDING.value
            for booking in data["bookings"]
        )

    async def test_get_calendar_bookings_invalid_date_range(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test calendar bookings with invalid date range."""
        start_date = datetime.utcnow().isoformat()
        end_date = (datetime.utcnow() - timedelta(days=1)).isoformat()  # Before start

        response = await client.get(
            "/api/v1/calendar/bookings",
            params={
                "start_date": start_date,
                "end_date": end_date,
            },
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "after start date" in response.json()["detail"].lower()

    async def test_get_calendar_bookings_exceeds_max_range(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test calendar bookings exceeding maximum range."""
        start_date = datetime.utcnow().isoformat()
        end_date = (datetime.utcnow() + timedelta(days=100)).isoformat()  # > 90 days

        response = await client.get(
            "/api/v1/calendar/bookings",
            params={
                "start_date": start_date,
                "end_date": end_date,
            },
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "90 days" in response.json()["detail"].lower()

    async def test_get_driver_schedule(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_driver_data: dict,
    ):
        """Test retrieving driver schedule."""
        # Create a driver
        driver_response = await client.post(
            "/api/v1/movers/drivers",
            json=sample_driver_data,
            headers=auth_headers,
        )
        assert driver_response.status_code == 201
        driver_id = driver_response.json()["id"]

        # Get driver schedule
        start_date = datetime.utcnow().isoformat()
        end_date = (datetime.utcnow() + timedelta(days=7)).isoformat()

        response = await client.get(
            f"/api/v1/calendar/driver/{driver_id}/schedule",
            params={
                "start_date": start_date,
                "end_date": end_date,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "driver_id" in data
        assert "driver_name" in data
        assert "schedule" in data
        assert "total_hours_booked" in data
        assert "total_bookings" in data
        assert data["driver_id"] == driver_id

    async def test_get_driver_schedule_wrong_org(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_driver_data: dict,
    ):
        """Test accessing driver schedule from different organization."""
        # This would require creating a driver for a different org
        # For now, test with non-existent driver
        fake_driver_id = "00000000-0000-0000-0000-000000000000"

        start_date = datetime.utcnow().isoformat()
        end_date = (datetime.utcnow() + timedelta(days=7)).isoformat()

        response = await client.get(
            f"/api/v1/calendar/driver/{fake_driver_id}/schedule",
            params={
                "start_date": start_date,
                "end_date": end_date,
            },
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_get_truck_schedule(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_truck_data: dict,
    ):
        """Test retrieving truck schedule."""
        # Create a truck
        truck_response = await client.post(
            "/api/v1/movers/trucks",
            json=sample_truck_data,
            headers=auth_headers,
        )
        assert truck_response.status_code == 201
        truck_id = truck_response.json()["id"]

        # Get truck schedule
        start_date = datetime.utcnow().isoformat()
        end_date = (datetime.utcnow() + timedelta(days=7)).isoformat()

        response = await client.get(
            f"/api/v1/calendar/truck/{truck_id}/schedule",
            params={
                "start_date": start_date,
                "end_date": end_date,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "truck_id" in data
        assert "truck_identifier" in data
        assert "schedule" in data
        assert "total_hours_booked" in data
        assert "total_bookings" in data
        assert data["truck_id"] == truck_id

    async def test_get_fleet_calendar(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test retrieving fleet-wide calendar."""
        start_date = datetime.utcnow().isoformat()
        end_date = (datetime.utcnow() + timedelta(days=7)).isoformat()

        response = await client.get(
            "/api/v1/calendar/fleet",
            params={
                "start_date": start_date,
                "end_date": end_date,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "org_id" in data
        assert "bookings" in data
        assert "driver_schedules" in data
        assert "truck_schedules" in data
        assert "total_bookings" in data
        assert "total_drivers" in data
        assert "total_trucks" in data

    async def test_get_fleet_calendar_exceeds_max_range(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test fleet calendar exceeding maximum range."""
        start_date = datetime.utcnow().isoformat()
        end_date = (datetime.utcnow() + timedelta(days=40)).isoformat()  # > 31 days

        response = await client.get(
            "/api/v1/calendar/fleet",
            params={
                "start_date": start_date,
                "end_date": end_date,
            },
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "31 days" in response.json()["detail"].lower()

    async def test_check_availability_available(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_organization_data: dict,
    ):
        """Test availability check when resources are available."""
        org_id = sample_organization_data["id"]
        move_date = (datetime.utcnow() + timedelta(days=7)).isoformat()

        response = await client.post(
            "/api/v1/calendar/availability",
            json={
                "org_id": org_id,
                "date": move_date,
                "estimated_duration_hours": 4.0,
                "require_driver": True,
                "require_truck": True,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "is_available" in data
        assert "available_slots" in data
        assert "total_available_drivers" in data
        assert "total_available_trucks" in data

    async def test_check_availability_wrong_org(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test availability check for different organization."""
        fake_org_id = "00000000-0000-0000-0000-000000000000"
        move_date = (datetime.utcnow() + timedelta(days=7)).isoformat()

        response = await client.post(
            "/api/v1/calendar/availability",
            json={
                "org_id": fake_org_id,
                "date": move_date,
                "estimated_duration_hours": 4.0,
            },
            headers=auth_headers,
        )

        assert response.status_code == 403
        assert "own organization" in response.json()["detail"].lower()

    async def test_check_availability_unauthenticated(
        self,
        client: AsyncClient,
        sample_organization_data: dict,
    ):
        """Test availability check without authentication."""
        org_id = sample_organization_data["id"]
        move_date = (datetime.utcnow() + timedelta(days=7)).isoformat()

        response = await client.post(
            "/api/v1/calendar/availability",
            json={
                "org_id": org_id,
                "date": move_date,
                "estimated_duration_hours": 4.0,
            },
        )

        assert response.status_code == 401
