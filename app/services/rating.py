"""
Rating service for managing customer reviews and ratings.

Handles rating creation, aggregation, and statistics calculation.
"""

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.observability import tracer
from app.models.booking import Booking, BookingStatus
from app.models.rating import Rating, RatingSummary
from app.schemas.rating import RatingCreate, RatingUpdate

logger = logging.getLogger(__name__)


class RatingAlreadyExistsError(Exception):
    """Raised when trying to create a duplicate rating for a booking."""

    pass


class BookingNotEligibleError(Exception):
    """Raised when booking is not eligible for rating."""

    pass


class RatingService:
    """Service for managing ratings and reviews."""

    @staticmethod
    async def create_rating(
        db: AsyncSession,
        rating_data: RatingCreate,
        customer_name: str,
        customer_email: str,
    ) -> Rating:
        """
        Create a new rating for a completed booking.

        Args:
            db: Database session
            rating_data: Rating data from customer
            customer_name: Customer name
            customer_email: Customer email for verification

        Returns:
            Created Rating instance

        Raises:
            RatingAlreadyExistsError: If rating already exists for booking
            BookingNotEligibleError: If booking is not completed or customer doesn't match
        """
        with tracer.start_as_current_span("rating.create") as span:
            span.set_attribute("booking_id", str(rating_data.booking_id))
            span.set_attribute("overall_rating", rating_data.overall_rating)

            # Get booking
            stmt = select(Booking).where(Booking.id == rating_data.booking_id)
            result = await db.execute(stmt)
            booking = result.scalar_one_or_none()

            if not booking:
                raise BookingNotEligibleError("Booking not found")

            # Verify booking is completed
            if booking.status != BookingStatus.COMPLETED:
                raise BookingNotEligibleError("Can only rate completed bookings")

            # Verify customer
            if booking.customer_email != customer_email:
                raise BookingNotEligibleError("Customer email does not match booking")

            # Check if rating already exists
            stmt = select(Rating).where(Rating.booking_id == rating_data.booking_id)
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                raise RatingAlreadyExistsError("Rating already exists for this booking")

            # Create rating
            rating = Rating(
                booking_id=rating_data.booking_id,
                org_id=booking.org_id,
                overall_rating=rating_data.overall_rating,
                professionalism_rating=rating_data.professionalism_rating,
                punctuality_rating=rating_data.punctuality_rating,
                care_of_items_rating=rating_data.care_of_items_rating,
                communication_rating=rating_data.communication_rating,
                value_for_money_rating=rating_data.value_for_money_rating,
                review_text=rating_data.review_text,
                review_title=rating_data.review_title,
                customer_name=customer_name,
                is_published=True,
                is_verified_booking=True,
            )

            try:
                db.add(rating)
                await db.commit()
                await db.refresh(rating)

                # Update rating summary asynchronously
                await RatingService._update_rating_summary(db, booking.org_id)

                logger.info(
                    f"Rating created: {rating.id}",
                    extra={
                        "rating_id": str(rating.id),
                        "booking_id": str(booking.id),
                        "org_id": str(booking.org_id),
                        "overall_rating": rating.overall_rating,
                    },
                )

                return rating

            except IntegrityError as e:
                await db.rollback()
                logger.error(f"Failed to create rating: {e}")
                raise RatingAlreadyExistsError("Rating already exists for this booking") from e

    @staticmethod
    async def add_mover_response(
        db: AsyncSession,
        rating_id: UUID,
        org_id: UUID,
        response_data: RatingUpdate,
    ) -> Rating:
        """
        Add mover's response to a rating.

        Args:
            db: Database session
            rating_id: Rating ID
            org_id: Organization ID (for verification)
            response_data: Mover's response

        Returns:
            Updated Rating instance
        """
        with tracer.start_as_current_span("rating.add_response") as span:
            span.set_attribute("rating_id", str(rating_id))

            stmt = select(Rating).where(Rating.id == rating_id, Rating.org_id == org_id)
            result = await db.execute(stmt)
            rating = result.scalar_one_or_none()

            if not rating:
                raise ValueError("Rating not found")

            rating.mover_response = response_data.mover_response
            rating.mover_responded_at = datetime.now(UTC).isoformat()

            await db.commit()
            await db.refresh(rating)

            logger.info(
                f"Mover response added to rating: {rating_id}",
                extra={"rating_id": str(rating_id), "org_id": str(org_id)},
            )

            return rating

    @staticmethod
    async def get_rating(db: AsyncSession, rating_id: UUID) -> Rating | None:
        """Get rating by ID."""
        stmt = select(Rating).where(Rating.id == rating_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_rating_by_booking(db: AsyncSession, booking_id: UUID) -> Rating | None:
        """Get rating for a specific booking."""
        stmt = select(Rating).where(Rating.booking_id == booking_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_ratings_for_org(
        db: AsyncSession,
        org_id: UUID,
        limit: int = 50,
        offset: int = 0,
        published_only: bool = True,
    ) -> tuple[list[Rating], int]:
        """
        List ratings for an organization.

        Args:
            db: Database session
            org_id: Organization ID
            limit: Max number of results
            offset: Pagination offset
            published_only: Only return published ratings

        Returns:
            Tuple of (ratings list, total count)
        """
        with tracer.start_as_current_span("rating.list") as span:
            span.set_attribute("org_id", str(org_id))

            # Build query
            stmt = select(Rating).where(Rating.org_id == org_id)
            if published_only:
                stmt = stmt.where(Rating.is_published == True)  # noqa: E712

            # Get total count
            count_stmt = select(func.count()).select_from(stmt.subquery())
            result = await db.execute(count_stmt)
            total = result.scalar() or 0

            # Get paginated results
            stmt = stmt.order_by(Rating.created_at.desc()).limit(limit).offset(offset)
            result = await db.execute(stmt)
            ratings = list(result.scalars().all())

            span.set_attribute("total_ratings", total)
            span.set_attribute("returned_count", len(ratings))

            return ratings, total

    @staticmethod
    async def get_rating_summary(db: AsyncSession, org_id: UUID) -> RatingSummary | None:
        """Get rating summary for an organization."""
        stmt = select(RatingSummary).where(RatingSummary.org_id == org_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def _update_rating_summary(db: AsyncSession, org_id: UUID) -> None:
        """
        Update or create rating summary for an organization.

        Calculates all aggregate statistics from existing ratings.
        """
        with tracer.start_as_current_span("rating.update_summary") as span:
            span.set_attribute("org_id", str(org_id))

            # Get all published ratings
            stmt = select(Rating).where(
                Rating.org_id == org_id, Rating.is_published == True  # noqa: E712
            )
            result = await db.execute(stmt)
            ratings = list(result.scalars().all())

            if not ratings:
                logger.info(f"No ratings found for org {org_id}, skipping summary update")
                return

            # Calculate statistics
            total_ratings = len(ratings)
            overall_sum = sum(r.overall_rating for r in ratings)
            average_overall = overall_sum / total_ratings

            # Category averages
            def calc_category_avg(ratings: list[Rating], attr: str) -> float | None:
                values = [getattr(r, attr) for r in ratings if getattr(r, attr) is not None]
                return sum(values) / len(values) if values else None

            avg_professionalism = calc_category_avg(ratings, "professionalism_rating")
            avg_punctuality = calc_category_avg(ratings, "punctuality_rating")
            avg_care = calc_category_avg(ratings, "care_of_items_rating")
            avg_communication = calc_category_avg(ratings, "communication_rating")
            avg_value = calc_category_avg(ratings, "value_for_money_rating")

            # Star distribution
            star_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            for rating in ratings:
                star_counts[rating.overall_rating] += 1

            # Get or create summary
            stmt = select(RatingSummary).where(RatingSummary.org_id == org_id)
            result = await db.execute(stmt)
            summary = result.scalar_one_or_none()

            if summary:
                # Update existing
                summary.total_ratings = total_ratings
                summary.average_overall_rating = average_overall
                summary.average_professionalism = avg_professionalism
                summary.average_punctuality = avg_punctuality
                summary.average_care_of_items = avg_care
                summary.average_communication = avg_communication
                summary.average_value_for_money = avg_value
                summary.five_star_count = star_counts[5]
                summary.four_star_count = star_counts[4]
                summary.three_star_count = star_counts[3]
                summary.two_star_count = star_counts[2]
                summary.one_star_count = star_counts[1]
            else:
                # Create new
                summary = RatingSummary(
                    org_id=org_id,
                    total_ratings=total_ratings,
                    average_overall_rating=average_overall,
                    average_professionalism=avg_professionalism,
                    average_punctuality=avg_punctuality,
                    average_care_of_items=avg_care,
                    average_communication=avg_communication,
                    average_value_for_money=avg_value,
                    five_star_count=star_counts[5],
                    four_star_count=star_counts[4],
                    three_star_count=star_counts[3],
                    two_star_count=star_counts[2],
                    one_star_count=star_counts[1],
                )
                db.add(summary)

            await db.commit()

            logger.info(
                f"Rating summary updated for org {org_id}",
                extra={
                    "org_id": str(org_id),
                    "total_ratings": total_ratings,
                    "average_rating": average_overall,
                },
            )

    @staticmethod
    async def calculate_rating_trend(db: AsyncSession, org_id: UUID, days: int = 30) -> str:
        """
        Calculate rating trend over time.

        Args:
            db: Database session
            org_id: Organization ID
            days: Number of days to analyze

        Returns:
            Trend string: "improving", "stable", or "declining"
        """
        cutoff_date = datetime.now(UTC) - timedelta(days=days)

        # Get recent ratings
        stmt = (
            select(Rating)
            .where(
                Rating.org_id == org_id,
                Rating.is_published == True,  # noqa: E712
                Rating.created_at >= cutoff_date,
            )
            .order_by(Rating.created_at.asc())
        )
        result = await db.execute(stmt)
        ratings = list(result.scalars().all())

        if len(ratings) < 5:
            return "stable"  # Not enough data

        # Split into first half and second half
        mid = len(ratings) // 2
        first_half = ratings[:mid]
        second_half = ratings[mid:]

        avg_first = sum(r.overall_rating for r in first_half) / len(first_half)
        avg_second = sum(r.overall_rating for r in second_half) / len(second_half)

        diff = avg_second - avg_first

        if diff > 0.3:
            return "improving"
        elif diff < -0.3:
            return "declining"
        else:
            return "stable"

    @staticmethod
    async def calculate_response_rate(db: AsyncSession, org_id: UUID) -> float:
        """Calculate percentage of ratings with mover responses."""
        stmt = select(Rating).where(Rating.org_id == org_id, Rating.is_published == True)  # noqa
        result = await db.execute(stmt)
        ratings = list(result.scalars().all())

        if not ratings:
            return 0.0

        with_response = sum(1 for r in ratings if r.mover_response is not None)
        return (with_response / len(ratings)) * 100
