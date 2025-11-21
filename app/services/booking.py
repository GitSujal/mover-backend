"""
Booking service with conflict detection.

Handles booking creation, availability checking, and conflict prevention.
Uses PostgreSQL exclusion constraints for atomic conflict detection.
"""

import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.observability import availability_check_histogram, booking_counter, tracer
from app.models.booking import Booking, BookingStatus
from app.schemas.booking import (
    AvailabilityCheck,
    AvailabilityResponse,
    AvailabilitySlot,
    BookingCreate,
    BookingResponse,
    BookingUpdate,
)
from app.services.pricing import PricingService

logger = logging.getLogger(__name__)


class BookingConflictError(Exception):
    """Raised when a booking conflicts with existing bookings."""

    pass


class BookingService:
    """Service for managing bookings with conflict-free scheduling."""

    @staticmethod
    def _calculate_effective_window(
        move_date: datetime,
        duration_hours: float,
        buffer_minutes: int,
    ) -> tuple[datetime, datetime]:
        """
        Calculate effective time window including commute buffer.

        Args:
            move_date: Requested move date/time
            duration_hours: Estimated duration
            buffer_minutes: Commute buffer in minutes

        Returns:
            Tuple of (effective_start, effective_end)
        """
        buffer_delta = timedelta(minutes=buffer_minutes)
        duration_delta = timedelta(hours=duration_hours)

        effective_start = move_date - buffer_delta
        effective_end = move_date + duration_delta + buffer_delta

        return effective_start, effective_end

    @staticmethod
    async def check_availability(
        db: AsyncSession,
        availability_check: AvailabilityCheck,
    ) -> AvailabilityResponse:
        """
        Check if a truck is available for the requested time window.

        Args:
            db: Database session
            availability_check: Availability check parameters

        Returns:
            AvailabilityResponse with conflicts and suggested slots
        """
        with tracer.start_as_current_span("booking.check_availability") as span:
            start_time = datetime.now()

            truck_id = availability_check.truck_id
            move_date = availability_check.move_date
            duration_hours = availability_check.estimated_duration_hours
            buffer_minutes = availability_check.commute_buffer_minutes

            # Calculate effective window
            effective_start, effective_end = BookingService._calculate_effective_window(
                move_date, duration_hours, buffer_minutes
            )

            span.set_attribute("booking.truck_id", str(truck_id))
            span.set_attribute("booking.move_date", move_date.isoformat())
            span.set_attribute("booking.duration_hours", duration_hours)

            # Query for overlapping bookings
            stmt = select(Booking).where(
                and_(
                    Booking.truck_id == truck_id,
                    Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.IN_PROGRESS]),
                    or_(
                        # Requested window starts during existing booking
                        and_(
                            Booking.effective_start <= effective_start,
                            Booking.effective_end > effective_start,
                        ),
                        # Requested window ends during existing booking
                        and_(
                            Booking.effective_start < effective_end,
                            Booking.effective_end >= effective_end,
                        ),
                        # Requested window contains existing booking
                        and_(
                            Booking.effective_start >= effective_start,
                            Booking.effective_end <= effective_end,
                        ),
                    ),
                )
            )

            result = await db.execute(stmt)
            conflicts = result.scalars().all()

            is_available = len(conflicts) == 0

            # Convert conflicts to responses
            conflict_responses = [
                BookingResponse.model_validate(conflict) for conflict in conflicts
            ]

            # Generate suggested slots if not available
            suggested_slots: list[AvailabilitySlot] = []
            if not is_available and conflicts:
                # Suggest slot after last conflict
                latest_conflict = max(conflicts, key=lambda b: b.effective_end)
                suggested_start = latest_conflict.effective_end + timedelta(minutes=15)
                suggested_end = suggested_start + timedelta(hours=duration_hours)
                suggested_slots.append(AvailabilitySlot(start=suggested_start, end=suggested_end))

            # Record metrics
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            availability_check_histogram.record(duration_ms)

            span.set_attribute("booking.is_available", is_available)
            span.set_attribute("booking.conflicts_count", len(conflicts))

            logger.info(
                f"Availability check for truck {truck_id}: "
                f"{'available' if is_available else f'{len(conflicts)} conflicts'}",
                extra={
                    "truck_id": str(truck_id),
                    "is_available": is_available,
                    "conflicts": len(conflicts),
                },
            )

            return AvailabilityResponse(
                truck_id=truck_id,
                is_available=is_available,
                requested_start=effective_start,
                requested_end=effective_end,
                conflicts=conflict_responses,
                suggested_slots=suggested_slots,
            )

    @staticmethod
    async def create_booking(
        db: AsyncSession,
        booking_data: BookingCreate,
        pricing_config: Any,  # PricingConfigResponse
    ) -> Booking:
        """
        Create a new booking with conflict detection.

        Args:
            db: Database session
            booking_data: Booking creation data
            pricing_config: Organization's pricing configuration

        Returns:
            Created booking

        Raises:
            BookingConflictError: If booking conflicts with existing bookings
        """
        with tracer.start_as_current_span("booking.create") as span:
            # Calculate effective window
            buffer_minutes = settings.DEFAULT_COMMUTE_BUFFER_MINUTES
            effective_start, effective_end = BookingService._calculate_effective_window(
                booking_data.move_date,
                booking_data.estimated_duration_hours,
                buffer_minutes,
            )

            # Calculate pricing
            booking_details = {
                "estimated_duration_hours": booking_data.estimated_duration_hours,
                "estimated_distance_miles": booking_data.estimated_distance_miles,
                "special_items": booking_data.special_items,
                "pickup_floors": booking_data.pickup_floors,
                "dropoff_floors": booking_data.dropoff_floors,
                "has_elevator_pickup": booking_data.has_elevator_pickup,
                "has_elevator_dropoff": booking_data.has_elevator_dropoff,
                "move_date": booking_data.move_date,
            }

            price_estimate = PricingService.calculate_price(pricing_config, booking_details)

            # Create booking object
            booking = Booking(
                org_id=booking_data.org_id,
                truck_id=booking_data.truck_id,
                customer_name=booking_data.customer_name,
                customer_email=booking_data.customer_email,
                customer_phone=booking_data.customer_phone,
                move_date=booking_data.move_date,
                pickup_address=booking_data.pickup_address,
                pickup_city=booking_data.pickup_city,
                pickup_state=booking_data.pickup_state,
                pickup_zip=booking_data.pickup_zip,
                dropoff_address=booking_data.dropoff_address,
                dropoff_city=booking_data.dropoff_city,
                dropoff_state=booking_data.dropoff_state,
                dropoff_zip=booking_data.dropoff_zip,
                estimated_distance_miles=booking_data.estimated_distance_miles,
                estimated_duration_hours=booking_data.estimated_duration_hours,
                commute_buffer_minutes=buffer_minutes,
                effective_start=effective_start,
                effective_end=effective_end,
                special_items=booking_data.special_items,
                pickup_floors=booking_data.pickup_floors,
                dropoff_floors=booking_data.dropoff_floors,
                has_elevator_pickup=booking_data.has_elevator_pickup,
                has_elevator_dropoff=booking_data.has_elevator_dropoff,
                estimated_amount=price_estimate.estimated_amount,
                platform_fee=price_estimate.platform_fee,
                status=BookingStatus.CONFIRMED,
                customer_notes=booking_data.customer_notes,
            )

            db.add(booking)

            try:
                await db.flush()  # Trigger exclusion constraint check
                await db.commit()
                await db.refresh(booking)

                # Record metrics
                booking_counter.add(1, {"status": "success"})

                span.set_attribute("booking.id", str(booking.id))
                span.set_attribute("booking.truck_id", str(booking.truck_id))
                span.set_attribute("booking.amount", float(booking.estimated_amount))

                logger.info(
                    f"Booking created: {booking.id} for ${booking.estimated_amount:.2f}",
                    extra={
                        "booking_id": str(booking.id),
                        "customer_email": booking.customer_email,
                        "amount": float(booking.estimated_amount),
                    },
                )

                return booking

            except IntegrityError as e:
                await db.rollback()
                booking_counter.add(1, {"status": "conflict"})

                # Check if it's an exclusion constraint violation
                if "exclude_overlapping_bookings" in str(e):
                    logger.warning(
                        f"Booking conflict for truck {booking_data.truck_id}",
                        extra={"truck_id": str(booking_data.truck_id)},
                    )
                    raise BookingConflictError(
                        "This truck is not available for the requested time window. "
                        "Please choose a different time or truck."
                    ) from e
                raise

    @staticmethod
    async def get_booking(db: AsyncSession, booking_id: UUID) -> Booking | None:
        """
        Get booking by ID.

        Args:
            db: Database session
            booking_id: Booking ID

        Returns:
            Booking or None
        """
        stmt = select(Booking).where(Booking.id == booking_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_booking(
        db: AsyncSession,
        booking: Booking,
        update_data: BookingUpdate,
    ) -> Booking:
        """
        Update booking with state transition validation.

        Args:
            db: Database session
            booking: Existing booking
            update_data: Update data (BookingUpdate schema)

        Returns:
            Updated booking

        Raises:
            ValueError: If state transition is invalid
        """
        # Validate status transition
        if update_data.status and update_data.status != booking.status:
            BookingService._validate_status_transition(booking.status, update_data.status)
            booking.status = update_data.status

        # Update other fields
        if update_data.final_amount is not None:
            booking.final_amount = update_data.final_amount

        if update_data.internal_notes is not None:
            booking.internal_notes = update_data.internal_notes

        await db.commit()
        await db.refresh(booking)
        return booking

    @staticmethod
    def _validate_status_transition(
        current_status: BookingStatus, new_status: BookingStatus
    ) -> None:
        """
        Validate booking status transition.

        Args:
            current_status: Current status
            new_status: New status

        Raises:
            ValueError: If transition is invalid
        """
        valid_transitions = {
            BookingStatus.PENDING: {BookingStatus.CONFIRMED, BookingStatus.CANCELLED},
            BookingStatus.CONFIRMED: {BookingStatus.IN_PROGRESS, BookingStatus.CANCELLED},
            BookingStatus.IN_PROGRESS: {BookingStatus.COMPLETED},
            BookingStatus.COMPLETED: set(),
            BookingStatus.CANCELLED: set(),
        }

        if new_status not in valid_transitions.get(current_status, set()):
            raise ValueError(f"Invalid status transition from {current_status} to {new_status}")

    @staticmethod
    async def list_bookings(
        db: AsyncSession,
        org_id: UUID | None = None,
        truck_id: UUID | None = None,
        status: BookingStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Booking]:
        """
        List bookings with filters.

        Args:
            db: Database session
            org_id: Filter by organization
            truck_id: Filter by truck
            status: Filter by status
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of bookings
        """
        stmt = select(Booking)

        if org_id:
            stmt = stmt.where(Booking.org_id == org_id)
        if truck_id:
            stmt = stmt.where(Booking.truck_id == truck_id)
        if status:
            stmt = stmt.where(Booking.status == status)

        stmt = stmt.order_by(Booking.move_date.desc()).limit(limit).offset(offset)

        result = await db.execute(stmt)
        return list(result.scalars().all())
