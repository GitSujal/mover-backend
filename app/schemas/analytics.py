"""Analytics dashboard schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class BookingMetrics(BaseModel):
    """Booking analytics metrics."""

    total_bookings: int
    pending_bookings: int
    confirmed_bookings: int
    in_progress_bookings: int
    completed_bookings: int
    cancelled_bookings: int
    total_revenue: float
    average_booking_value: float
    completion_rate: float  # Percentage of completed vs total
    cancellation_rate: float  # Percentage of cancelled vs total


class DriverMetrics(BaseModel):
    """Driver analytics metrics."""

    total_drivers: int
    active_drivers: int
    inactive_drivers: int
    average_bookings_per_driver: float
    top_performers: list[dict]  # Top 5 drivers by bookings/ratings


class TruckMetrics(BaseModel):
    """Truck analytics metrics."""

    total_trucks: int
    active_trucks: int
    inactive_trucks: int
    average_utilization: float  # Percentage of time trucks are booked


class RatingMetrics(BaseModel):
    """Rating and review analytics metrics."""

    total_ratings: int
    average_rating: float
    five_star_count: int
    four_star_count: int
    three_star_count: int
    two_star_count: int
    one_star_count: int
    rating_distribution: dict[int, int]  # {1: count, 2: count, ...}
    recent_reviews: list[dict]  # Last 5 reviews


class SupportMetrics(BaseModel):
    """Support ticket analytics metrics."""

    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    escalated_tickets: int
    average_resolution_hours: float
    ticket_by_type: dict[str, int]  # Issue type distribution
    ticket_by_priority: dict[str, int]  # Priority distribution


class InvoiceMetrics(BaseModel):
    """Invoice analytics metrics."""

    total_invoices: int
    draft_invoices: int
    issued_invoices: int
    paid_invoices: int
    overdue_invoices: int
    total_revenue: float
    total_outstanding: float  # Unpaid invoice amount
    average_invoice_amount: float
    payment_rate: float  # Percentage of paid invoices


class VerificationMetrics(BaseModel):
    """Verification analytics metrics."""

    pending_verifications: int
    under_review_verifications: int
    approved_verifications: int
    rejected_verifications: int
    expired_verifications: int
    expiring_soon_count: int  # Expiring in next 30 days


class TimeSeriesDataPoint(BaseModel):
    """Single data point in time series."""

    date: datetime
    value: float
    label: str | None = None


class TrendData(BaseModel):
    """Trend data over time."""

    bookings_trend: list[TimeSeriesDataPoint]  # Bookings over time
    revenue_trend: list[TimeSeriesDataPoint]  # Revenue over time
    rating_trend: list[TimeSeriesDataPoint]  # Average rating over time


class OrganizationDashboard(BaseModel):
    """Comprehensive organization dashboard."""

    org_id: UUID
    org_name: str
    period_start: datetime
    period_end: datetime
    booking_metrics: BookingMetrics
    driver_metrics: DriverMetrics
    truck_metrics: TruckMetrics
    rating_metrics: RatingMetrics
    support_metrics: SupportMetrics
    invoice_metrics: InvoiceMetrics
    verification_metrics: VerificationMetrics
    trends: TrendData


class PlatformDashboard(BaseModel):
    """Platform-wide analytics dashboard."""

    period_start: datetime
    period_end: datetime
    total_organizations: int
    verified_organizations: int
    pending_organizations: int
    total_bookings: int
    total_revenue: float
    average_rating: float
    total_support_tickets: int
    top_organizations: list[dict]  # Top 10 by revenue/bookings
    booking_metrics: BookingMetrics
    support_metrics: SupportMetrics


class RevenueBreakdown(BaseModel):
    """Revenue breakdown by category."""

    total_revenue: float
    service_revenue: float
    platform_fees: float
    tax_collected: float
    refunds_issued: float
    net_revenue: float


class PerformanceMetrics(BaseModel):
    """Performance and efficiency metrics."""

    average_booking_lead_time_hours: float  # Time from booking to move
    average_assignment_time_hours: float  # Time to assign driver/truck
    on_time_completion_rate: float  # Percentage completed on time
    customer_satisfaction_score: float  # Based on ratings
    driver_efficiency_score: float  # Bookings per driver per week
    truck_utilization_rate: float  # Hours booked / total available hours
