"""Tests for analytics dashboard API endpoints."""

import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestAnalyticsAPI:
    """Test analytics dashboard endpoints."""

    async def test_get_organization_dashboard(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_organization_data: dict,
    ):
        """Test retrieving complete organization dashboard."""
        org_id = sample_organization_data["id"]

        response = await client.get(
            f"/api/v1/analytics/organization/{org_id}/dashboard",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify all required sections
        assert "org_id" in data
        assert "org_name" in data
        assert "period_start" in data
        assert "period_end" in data
        assert "booking_metrics" in data
        assert "driver_metrics" in data
        assert "truck_metrics" in data
        assert "rating_metrics" in data
        assert "support_metrics" in data
        assert "invoice_metrics" in data
        assert "verification_metrics" in data
        assert "trends" in data

        # Verify booking metrics structure
        booking_metrics = data["booking_metrics"]
        assert "total_bookings" in booking_metrics
        assert "pending_bookings" in booking_metrics
        assert "confirmed_bookings" in booking_metrics
        assert "completed_bookings" in booking_metrics
        assert "cancelled_bookings" in booking_metrics
        assert "total_revenue" in booking_metrics
        assert "average_booking_value" in booking_metrics
        assert "completion_rate" in booking_metrics
        assert "cancellation_rate" in booking_metrics

    async def test_get_organization_dashboard_custom_date_range(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_organization_data: dict,
    ):
        """Test dashboard with custom date range."""
        org_id = sample_organization_data["id"]
        start_date = (datetime.utcnow() - timedelta(days=60)).isoformat()
        end_date = datetime.utcnow().isoformat()

        response = await client.get(
            f"/api/v1/analytics/organization/{org_id}/dashboard",
            params={
                "start_date": start_date,
                "end_date": end_date,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["period_start"] == start_date
        assert data["period_end"] == end_date

    async def test_get_organization_dashboard_invalid_date_range(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_organization_data: dict,
    ):
        """Test dashboard with invalid date range."""
        org_id = sample_organization_data["id"]
        start_date = datetime.utcnow().isoformat()
        end_date = (datetime.utcnow() - timedelta(days=1)).isoformat()  # Before start

        response = await client.get(
            f"/api/v1/analytics/organization/{org_id}/dashboard",
            params={
                "start_date": start_date,
                "end_date": end_date,
            },
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "after start date" in response.json()["detail"].lower()

    async def test_get_organization_dashboard_wrong_org(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test accessing dashboard for different organization."""
        fake_org_id = "00000000-0000-0000-0000-000000000000"

        response = await client.get(
            f"/api/v1/analytics/organization/{fake_org_id}/dashboard",
            headers=auth_headers,
        )

        assert response.status_code == 403
        assert "access denied" in response.json()["detail"].lower()

    async def test_get_booking_metrics(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_organization_data: dict,
        sample_booking_data: dict,
    ):
        """Test retrieving booking metrics."""
        org_id = sample_organization_data["id"]

        # Create a booking first
        await client.post("/api/v1/bookings", json=sample_booking_data)

        response = await client.get(
            f"/api/v1/analytics/organization/{org_id}/bookings",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert "total_bookings" in data
        assert "pending_bookings" in data
        assert "confirmed_bookings" in data
        assert "in_progress_bookings" in data
        assert "completed_bookings" in data
        assert "cancelled_bookings" in data
        assert "total_revenue" in data
        assert "average_booking_value" in data
        assert "completion_rate" in data
        assert "cancellation_rate" in data

        # Verify at least one booking counted
        assert data["total_bookings"] >= 1

    async def test_get_driver_metrics(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_organization_data: dict,
        sample_driver_data: dict,
    ):
        """Test retrieving driver metrics."""
        org_id = sample_organization_data["id"]

        # Create a driver first
        await client.post(
            "/api/v1/movers/drivers",
            json=sample_driver_data,
            headers=auth_headers,
        )

        response = await client.get(
            f"/api/v1/analytics/organization/{org_id}/drivers",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert "total_drivers" in data
        assert "active_drivers" in data
        assert "inactive_drivers" in data
        assert "average_bookings_per_driver" in data
        assert "top_performers" in data
        assert isinstance(data["top_performers"], list)

        # Verify at least one driver counted
        assert data["total_drivers"] >= 1

    async def test_get_truck_metrics(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_organization_data: dict,
        sample_truck_data: dict,
    ):
        """Test retrieving truck metrics."""
        org_id = sample_organization_data["id"]

        # Create a truck first
        await client.post(
            "/api/v1/movers/trucks",
            json=sample_truck_data,
            headers=auth_headers,
        )

        response = await client.get(
            f"/api/v1/analytics/organization/{org_id}/trucks",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert "total_trucks" in data
        assert "active_trucks" in data
        assert "inactive_trucks" in data
        assert "average_utilization" in data

        # Verify at least one truck counted
        assert data["total_trucks"] >= 1

    async def test_get_rating_metrics(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_organization_data: dict,
    ):
        """Test retrieving rating metrics."""
        org_id = sample_organization_data["id"]

        response = await client.get(
            f"/api/v1/analytics/organization/{org_id}/ratings",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert "total_ratings" in data
        assert "average_rating" in data
        assert "five_star_count" in data
        assert "four_star_count" in data
        assert "three_star_count" in data
        assert "two_star_count" in data
        assert "one_star_count" in data
        assert "rating_distribution" in data
        assert "recent_reviews" in data

        # Verify distribution is a dict
        assert isinstance(data["rating_distribution"], dict)
        assert isinstance(data["recent_reviews"], list)

    async def test_get_support_metrics(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_organization_data: dict,
    ):
        """Test retrieving support metrics."""
        org_id = sample_organization_data["id"]

        response = await client.get(
            f"/api/v1/analytics/organization/{org_id}/support",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert "total_tickets" in data
        assert "open_tickets" in data
        assert "in_progress_tickets" in data
        assert "resolved_tickets" in data
        assert "escalated_tickets" in data
        assert "average_resolution_hours" in data
        assert "ticket_by_type" in data
        assert "ticket_by_priority" in data

        # Verify distributions are dicts
        assert isinstance(data["ticket_by_type"], dict)
        assert isinstance(data["ticket_by_priority"], dict)

    async def test_get_invoice_metrics(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_organization_data: dict,
    ):
        """Test retrieving invoice metrics."""
        org_id = sample_organization_data["id"]

        response = await client.get(
            f"/api/v1/analytics/organization/{org_id}/invoices",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert "total_invoices" in data
        assert "draft_invoices" in data
        assert "issued_invoices" in data
        assert "paid_invoices" in data
        assert "overdue_invoices" in data
        assert "total_revenue" in data
        assert "total_outstanding" in data
        assert "average_invoice_amount" in data
        assert "payment_rate" in data

    async def test_get_verification_metrics(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_organization_data: dict,
    ):
        """Test retrieving verification metrics."""
        org_id = sample_organization_data["id"]

        response = await client.get(
            f"/api/v1/analytics/organization/{org_id}/verification",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert "pending_verifications" in data
        assert "under_review_verifications" in data
        assert "approved_verifications" in data
        assert "rejected_verifications" in data
        assert "expired_verifications" in data
        assert "expiring_soon_count" in data

    async def test_get_trend_data(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_organization_data: dict,
    ):
        """Test retrieving trend data."""
        org_id = sample_organization_data["id"]

        response = await client.get(
            f"/api/v1/analytics/organization/{org_id}/trends",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert "bookings_trend" in data
        assert "revenue_trend" in data
        assert "rating_trend" in data

        # Verify trends are lists of time series data
        assert isinstance(data["bookings_trend"], list)
        assert isinstance(data["revenue_trend"], list)
        assert isinstance(data["rating_trend"], list)

        # Verify time series data points have correct structure
        if len(data["bookings_trend"]) > 0:
            point = data["bookings_trend"][0]
            assert "date" in point
            assert "value" in point
            assert "label" in point

    async def test_get_trend_data_custom_range(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_organization_data: dict,
    ):
        """Test trend data with custom date range."""
        org_id = sample_organization_data["id"]
        start_date = (datetime.utcnow() - timedelta(days=14)).isoformat()
        end_date = datetime.utcnow().isoformat()

        response = await client.get(
            f"/api/v1/analytics/organization/{org_id}/trends",
            params={
                "start_date": start_date,
                "end_date": end_date,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should have 14 days of data
        assert len(data["bookings_trend"]) == 14
        assert len(data["revenue_trend"]) == 14
        assert len(data["rating_trend"]) == 14

    async def test_get_trend_data_exceeds_max_range(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_organization_data: dict,
    ):
        """Test trend data exceeding maximum range."""
        org_id = sample_organization_data["id"]
        start_date = (datetime.utcnow() - timedelta(days=100)).isoformat()
        end_date = datetime.utcnow().isoformat()

        response = await client.get(
            f"/api/v1/analytics/organization/{org_id}/trends",
            params={
                "start_date": start_date,
                "end_date": end_date,
            },
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "90 days" in response.json()["detail"].lower()

    async def test_analytics_unauthenticated(
        self,
        client: AsyncClient,
        sample_organization_data: dict,
    ):
        """Test analytics endpoints without authentication."""
        org_id = sample_organization_data["id"]

        # Dashboard
        response = await client.get(
            f"/api/v1/analytics/organization/{org_id}/dashboard",
        )
        assert response.status_code == 401

        # Booking metrics
        response = await client.get(
            f"/api/v1/analytics/organization/{org_id}/bookings",
        )
        assert response.status_code == 401

        # Driver metrics
        response = await client.get(
            f"/api/v1/analytics/organization/{org_id}/drivers",
        )
        assert response.status_code == 401

    async def test_analytics_wrong_organization(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test accessing analytics for different organization."""
        fake_org_id = "00000000-0000-0000-0000-000000000000"

        endpoints = [
            f"/api/v1/analytics/organization/{fake_org_id}/dashboard",
            f"/api/v1/analytics/organization/{fake_org_id}/bookings",
            f"/api/v1/analytics/organization/{fake_org_id}/drivers",
            f"/api/v1/analytics/organization/{fake_org_id}/trucks",
            f"/api/v1/analytics/organization/{fake_org_id}/ratings",
            f"/api/v1/analytics/organization/{fake_org_id}/support",
            f"/api/v1/analytics/organization/{fake_org_id}/invoices",
            f"/api/v1/analytics/organization/{fake_org_id}/verification",
            f"/api/v1/analytics/organization/{fake_org_id}/trends",
        ]

        for endpoint in endpoints:
            response = await client.get(endpoint, headers=auth_headers)
            assert response.status_code == 403, f"Failed for {endpoint}"
