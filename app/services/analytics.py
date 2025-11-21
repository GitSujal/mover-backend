"""Analytics and dashboard service."""

import logging
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.observability import tracer
from app.models.booking import Booking, BookingStatus
from app.models.driver import Driver
from app.models.invoice import Invoice, InvoiceStatus
from app.models.organization import Organization
from app.models.rating import Rating
from app.models.support import IssueStatus, SupportIssue
from app.models.truck import Truck
from app.models.verification import DocumentVerification, VerificationStatus
from app.schemas.analytics import (
    BookingMetrics,
    DriverMetrics,
    InvoiceMetrics,
    RatingMetrics,
    SupportMetrics,
    TimeSeriesDataPoint,
    TrendData,
    TruckMetrics,
    VerificationMetrics,
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for analytics and dashboard data."""

    @staticmethod
    async def get_booking_metrics(
        db: AsyncSession,
        org_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> BookingMetrics:
        """
        Get booking analytics metrics.

        Args:
            db: Database session
            org_id: Organization ID
            start_date: Period start
            end_date: Period end

        Returns:
            Booking metrics
        """
        with tracer.start_as_current_span("analytics.booking_metrics") as span:
            span.set_attribute("org_id", str(org_id))

            # Get all bookings in period
            result = await db.execute(
                select(Booking).where(
                    and_(
                        Booking.org_id == org_id,
                        Booking.created_at >= start_date,
                        Booking.created_at < end_date,
                    )
                )
            )
            bookings = result.scalars().all()

            total = len(bookings)
            pending = sum(1 for b in bookings if b.status == BookingStatus.PENDING)
            confirmed = sum(1 for b in bookings if b.status == BookingStatus.CONFIRMED)
            in_progress = sum(
                1 for b in bookings if b.status == BookingStatus.IN_PROGRESS
            )
            completed = sum(1 for b in bookings if b.status == BookingStatus.COMPLETED)
            cancelled = sum(1 for b in bookings if b.status == BookingStatus.CANCELLED)

            # Calculate revenue (completed bookings only)
            completed_bookings = [b for b in bookings if b.status == BookingStatus.COMPLETED]
            total_revenue = sum(
                float(b.final_amount or b.estimated_amount)
                for b in completed_bookings
            )
            average_booking_value = (
                total_revenue / len(completed_bookings) if completed_bookings else 0
            )

            # Calculate rates
            completion_rate = (completed / total * 100) if total > 0 else 0
            cancellation_rate = (cancelled / total * 100) if total > 0 else 0

            return BookingMetrics(
                total_bookings=total,
                pending_bookings=pending,
                confirmed_bookings=confirmed,
                in_progress_bookings=in_progress,
                completed_bookings=completed,
                cancelled_bookings=cancelled,
                total_revenue=total_revenue,
                average_booking_value=average_booking_value,
                completion_rate=completion_rate,
                cancellation_rate=cancellation_rate,
            )

    @staticmethod
    async def get_driver_metrics(
        db: AsyncSession,
        org_id: UUID,
    ) -> DriverMetrics:
        """
        Get driver analytics metrics.

        Args:
            db: Database session
            org_id: Organization ID

        Returns:
            Driver metrics
        """
        with tracer.start_as_current_span("analytics.driver_metrics") as span:
            span.set_attribute("org_id", str(org_id))

            # Get all drivers
            result = await db.execute(
                select(Driver).where(Driver.org_id == org_id)
            )
            drivers = result.scalars().all()

            total = len(drivers)
            active = sum(1 for d in drivers if d.is_active)
            inactive = total - active

            # Get booking counts per driver
            booking_counts = {}
            for driver in drivers:
                count_result = await db.execute(
                    select(func.count(Booking.id)).where(
                        and_(
                            Booking.assigned_driver_id == driver.id,
                            Booking.status == BookingStatus.COMPLETED,
                        )
                    )
                )
                booking_counts[driver.id] = count_result.scalar_one()

            average_bookings = (
                sum(booking_counts.values()) / len(drivers) if drivers else 0
            )

            # Get top performers (top 5 by booking count)
            top_performers = []
            sorted_drivers = sorted(
                booking_counts.items(), key=lambda x: x[1], reverse=True
            )[:5]

            for driver_id, count in sorted_drivers:
                driver = next(d for d in drivers if d.id == driver_id)
                # Get average rating
                rating_result = await db.execute(
                    select(func.avg(Rating.rating)).where(
                        Rating.driver_id == driver_id
                    )
                )
                avg_rating = rating_result.scalar_one() or 0

                top_performers.append(
                    {
                        "driver_id": str(driver_id),
                        "driver_name": driver.name,
                        "total_bookings": count,
                        "average_rating": float(avg_rating),
                    }
                )

            return DriverMetrics(
                total_drivers=total,
                active_drivers=active,
                inactive_drivers=inactive,
                average_bookings_per_driver=average_bookings,
                top_performers=top_performers,
            )

    @staticmethod
    async def get_truck_metrics(
        db: AsyncSession,
        org_id: UUID,
    ) -> TruckMetrics:
        """
        Get truck analytics metrics.

        Args:
            db: Database session
            org_id: Organization ID

        Returns:
            Truck metrics
        """
        with tracer.start_as_current_span("analytics.truck_metrics") as span:
            span.set_attribute("org_id", str(org_id))

            # Get all trucks
            result = await db.execute(
                select(Truck).where(Truck.org_id == org_id)
            )
            trucks = result.scalars().all()

            total = len(trucks)
            active = sum(1 for t in trucks if t.is_active)
            inactive = total - active

            # Calculate utilization (simplified - actual would need more complex logic)
            # This is a placeholder calculation
            average_utilization = 0.0
            if trucks:
                # Get total hours booked across all trucks in last 30 days
                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                booking_result = await db.execute(
                    select(
                        func.sum(Booking.estimated_duration_hours)
                    ).where(
                        and_(
                            Booking.org_id == org_id,
                            Booking.move_date >= thirty_days_ago,
                            Booking.status.in_(
                                [BookingStatus.COMPLETED, BookingStatus.IN_PROGRESS]
                            ),
                        )
                    )
                )
                total_hours_booked = booking_result.scalar_one() or 0

                # Assume 8 hours/day availability per truck
                available_hours = total * 8 * 30
                average_utilization = (
                    (float(total_hours_booked) / available_hours * 100)
                    if available_hours > 0
                    else 0
                )

            return TruckMetrics(
                total_trucks=total,
                active_trucks=active,
                inactive_trucks=inactive,
                average_utilization=average_utilization,
            )

    @staticmethod
    async def get_rating_metrics(
        db: AsyncSession,
        org_id: UUID,
    ) -> RatingMetrics:
        """
        Get rating and review analytics metrics.

        Args:
            db: Database session
            org_id: Organization ID

        Returns:
            Rating metrics
        """
        with tracer.start_as_current_span("analytics.rating_metrics") as span:
            span.set_attribute("org_id", str(org_id))

            # Get all ratings for organization
            result = await db.execute(
                select(Rating).where(Rating.org_id == org_id)
            )
            ratings = result.scalars().all()

            total = len(ratings)
            if total == 0:
                return RatingMetrics(
                    total_ratings=0,
                    average_rating=0.0,
                    five_star_count=0,
                    four_star_count=0,
                    three_star_count=0,
                    two_star_count=0,
                    one_star_count=0,
                    rating_distribution={1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
                    recent_reviews=[],
                )

            # Calculate distribution
            five_star = sum(1 for r in ratings if r.rating == 5)
            four_star = sum(1 for r in ratings if r.rating == 4)
            three_star = sum(1 for r in ratings if r.rating == 3)
            two_star = sum(1 for r in ratings if r.rating == 2)
            one_star = sum(1 for r in ratings if r.rating == 1)

            average_rating = sum(r.rating for r in ratings) / total

            # Get recent reviews (last 5 with comments)
            reviews_with_comments = [r for r in ratings if r.comment]
            reviews_with_comments.sort(key=lambda x: x.created_at, reverse=True)
            recent_reviews = [
                {
                    "rating": r.rating,
                    "comment": r.comment,
                    "created_at": r.created_at.isoformat(),
                    "booking_id": str(r.booking_id),
                }
                for r in reviews_with_comments[:5]
            ]

            return RatingMetrics(
                total_ratings=total,
                average_rating=average_rating,
                five_star_count=five_star,
                four_star_count=four_star,
                three_star_count=three_star,
                two_star_count=two_star,
                one_star_count=one_star,
                rating_distribution={
                    1: one_star,
                    2: two_star,
                    3: three_star,
                    4: four_star,
                    5: five_star,
                },
                recent_reviews=recent_reviews,
            )

    @staticmethod
    async def get_support_metrics(
        db: AsyncSession,
        org_id: UUID,
    ) -> SupportMetrics:
        """
        Get support ticket analytics metrics.

        Args:
            db: Database session
            org_id: Organization ID

        Returns:
            Support metrics
        """
        with tracer.start_as_current_span("analytics.support_metrics") as span:
            span.set_attribute("org_id", str(org_id))

            # Get all support tickets for organization's bookings
            result = await db.execute(
                select(SupportIssue)
                .join(Booking)
                .where(Booking.org_id == org_id)
            )
            tickets = result.scalars().all()

            total = len(tickets)
            open_count = sum(1 for t in tickets if t.status == IssueStatus.OPEN)
            in_progress = sum(
                1 for t in tickets if t.status == IssueStatus.IN_PROGRESS
            )
            resolved = sum(1 for t in tickets if t.status == IssueStatus.RESOLVED)
            escalated = sum(1 for t in tickets if t.is_escalated)

            # Calculate average resolution time
            resolved_tickets = [t for t in tickets if t.status == IssueStatus.RESOLVED and t.resolved_at]
            average_resolution_hours = 0.0
            if resolved_tickets:
                total_hours = sum(
                    (t.resolved_at - t.created_at).total_seconds() / 3600
                    for t in resolved_tickets
                )
                average_resolution_hours = total_hours / len(resolved_tickets)

            # Distribution by type
            ticket_by_type = {}
            for ticket in tickets:
                type_name = ticket.issue_type.value
                ticket_by_type[type_name] = ticket_by_type.get(type_name, 0) + 1

            # Distribution by priority
            ticket_by_priority = {}
            for ticket in tickets:
                priority_name = ticket.priority.value
                ticket_by_priority[priority_name] = (
                    ticket_by_priority.get(priority_name, 0) + 1
                )

            return SupportMetrics(
                total_tickets=total,
                open_tickets=open_count,
                in_progress_tickets=in_progress,
                resolved_tickets=resolved,
                escalated_tickets=escalated,
                average_resolution_hours=average_resolution_hours,
                ticket_by_type=ticket_by_type,
                ticket_by_priority=ticket_by_priority,
            )

    @staticmethod
    async def get_invoice_metrics(
        db: AsyncSession,
        org_id: UUID,
    ) -> InvoiceMetrics:
        """
        Get invoice analytics metrics.

        Args:
            db: Database session
            org_id: Organization ID

        Returns:
            Invoice metrics
        """
        with tracer.start_as_current_span("analytics.invoice_metrics") as span:
            span.set_attribute("org_id", str(org_id))

            # Get all invoices for organization
            result = await db.execute(
                select(Invoice)
                .join(Booking)
                .where(Booking.org_id == org_id)
            )
            invoices = result.scalars().all()

            total = len(invoices)
            draft = sum(1 for i in invoices if i.status == InvoiceStatus.DRAFT)
            issued = sum(1 for i in invoices if i.status == InvoiceStatus.ISSUED)
            paid = sum(1 for i in invoices if i.status == InvoiceStatus.PAID)
            overdue = sum(1 for i in invoices if i.status == InvoiceStatus.OVERDUE)

            # Calculate revenue
            total_revenue = sum(float(i.total_amount) for i in invoices if i.status == InvoiceStatus.PAID)
            total_outstanding = sum(
                float(i.total_amount)
                for i in invoices
                if i.status in [InvoiceStatus.ISSUED, InvoiceStatus.OVERDUE]
            )

            average_invoice_amount = (
                sum(float(i.total_amount) for i in invoices) / total if total > 0 else 0
            )

            payment_rate = (paid / total * 100) if total > 0 else 0

            return InvoiceMetrics(
                total_invoices=total,
                draft_invoices=draft,
                issued_invoices=issued,
                paid_invoices=paid,
                overdue_invoices=overdue,
                total_revenue=total_revenue,
                total_outstanding=total_outstanding,
                average_invoice_amount=average_invoice_amount,
                payment_rate=payment_rate,
            )

    @staticmethod
    async def get_verification_metrics(
        db: AsyncSession,
        org_id: UUID,
    ) -> VerificationMetrics:
        """
        Get verification analytics metrics.

        Args:
            db: Database session
            org_id: Organization ID

        Returns:
            Verification metrics
        """
        with tracer.start_as_current_span("analytics.verification_metrics") as span:
            span.set_attribute("org_id", str(org_id))

            # Get all verifications for organization
            result = await db.execute(
                select(DocumentVerification).where(
                    DocumentVerification.org_id == org_id
                )
            )
            verifications = result.scalars().all()

            pending = sum(
                1 for v in verifications if v.status == VerificationStatus.PENDING
            )
            under_review = sum(
                1 for v in verifications if v.status == VerificationStatus.UNDER_REVIEW
            )
            approved = sum(
                1 for v in verifications if v.status == VerificationStatus.APPROVED
            )
            rejected = sum(
                1
                for v in verifications
                if v.status
                in [
                    VerificationStatus.REJECTED,
                    VerificationStatus.RESUBMISSION_REQUIRED,
                ]
            )
            expired = sum(
                1 for v in verifications if v.status == VerificationStatus.EXPIRED
            )

            # Count expiring soon (30 days)
            thirty_days_from_now = datetime.utcnow() + timedelta(days=30)
            expiring_soon = sum(
                1
                for v in verifications
                if v.expiry_date
                and v.expiry_date < thirty_days_from_now
                and v.status == VerificationStatus.APPROVED
            )

            return VerificationMetrics(
                pending_verifications=pending,
                under_review_verifications=under_review,
                approved_verifications=approved,
                rejected_verifications=rejected,
                expired_verifications=expired,
                expiring_soon_count=expiring_soon,
            )

    @staticmethod
    async def get_trend_data(
        db: AsyncSession,
        org_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> TrendData:
        """
        Get trend data over time.

        Args:
            db: Database session
            org_id: Organization ID
            start_date: Period start
            end_date: Period end

        Returns:
            Trend data
        """
        with tracer.start_as_current_span("analytics.trend_data") as span:
            span.set_attribute("org_id", str(org_id))

            # Calculate daily booking trend
            bookings_trend = []
            revenue_trend = []
            rating_trend = []

            current_date = start_date
            while current_date < end_date:
                next_date = current_date + timedelta(days=1)

                # Bookings for this day
                booking_result = await db.execute(
                    select(func.count(Booking.id)).where(
                        and_(
                            Booking.org_id == org_id,
                            Booking.created_at >= current_date,
                            Booking.created_at < next_date,
                        )
                    )
                )
                booking_count = booking_result.scalar_one()

                bookings_trend.append(
                    TimeSeriesDataPoint(
                        date=current_date,
                        value=float(booking_count),
                        label=current_date.strftime("%Y-%m-%d"),
                    )
                )

                # Revenue for this day (completed bookings)
                revenue_result = await db.execute(
                    select(
                        func.sum(
                            func.coalesce(Booking.final_amount, Booking.estimated_amount)
                        )
                    ).where(
                        and_(
                            Booking.org_id == org_id,
                            Booking.status == BookingStatus.COMPLETED,
                            Booking.updated_at >= current_date,
                            Booking.updated_at < next_date,
                        )
                    )
                )
                revenue = revenue_result.scalar_one() or 0

                revenue_trend.append(
                    TimeSeriesDataPoint(
                        date=current_date,
                        value=float(revenue),
                        label=current_date.strftime("%Y-%m-%d"),
                    )
                )

                # Average rating for this day
                rating_result = await db.execute(
                    select(func.avg(Rating.rating)).where(
                        and_(
                            Rating.org_id == org_id,
                            Rating.created_at >= current_date,
                            Rating.created_at < next_date,
                        )
                    )
                )
                avg_rating = rating_result.scalar_one() or 0

                rating_trend.append(
                    TimeSeriesDataPoint(
                        date=current_date,
                        value=float(avg_rating),
                        label=current_date.strftime("%Y-%m-%d"),
                    )
                )

                current_date = next_date

            return TrendData(
                bookings_trend=bookings_trend,
                revenue_trend=revenue_trend,
                rating_trend=rating_trend,
            )
