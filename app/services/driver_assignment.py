"""
Driver Assignment Service

Handles automatic and manual driver assignment to bookings.
Considers availability, proximity, and qualifications.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.observability import tracer
from app.models.booking import Booking
from app.models.driver import Driver
from app.models.truck import Truck

logger = logging.getLogger(__name__)


class DriverAssignmentError(Exception):
    """Raised when driver assignment fails."""

    pass


class DriverAssignmentService:
    """Service for managing driver assignments."""

    @staticmethod
    async def assign_driver_to_booking(
        db: AsyncSession,
        booking_id: UUID,
        driver_id: UUID,
        assigned_by: str = "manual",
    ) -> Booking:
        """
        Assign a driver to a booking.

        Args:
            db: Database session
            booking_id: Booking ID
            driver_id: Driver ID to assign
            assigned_by: How assignment was made ("auto" or "manual")

        Returns:
            Updated Booking instance

        Raises:
            DriverAssignmentError: If assignment is not possible
        """
        with tracer.start_as_current_span("driver_assignment.assign") as span:
            span.set_attribute("booking_id", str(booking_id))
            span.set_attribute("driver_id", str(driver_id))
            span.set_attribute("assigned_by", assigned_by)

            # Get booking
            stmt = select(Booking).where(Booking.id == booking_id)
            result = await db.execute(stmt)
            booking = result.scalar_one_or_none()

            if not booking:
                raise DriverAssignmentError("Booking not found")

            # Get driver
            stmt = select(Driver).where(Driver.id == driver_id)
            result = await db.execute(stmt)
            driver = result.scalar_one_or_none()

            if not driver:
                raise DriverAssignmentError("Driver not found")

            # Verify driver belongs to same organization
            if driver.org_id != booking.org_id:
                raise DriverAssignmentError("Driver does not belong to booking's organization")

            # Verify driver is verified
            if not driver.is_verified:
                raise DriverAssignmentError("Driver is not verified")

            # Check driver availability (no overlapping assignments)
            overlapping = await DriverAssignmentService._check_driver_availability(
                db, driver_id, booking.effective_start, booking.effective_end, exclude_booking_id=booking_id
            )

            if overlapping:
                raise DriverAssignmentError(
                    f"Driver already assigned to another booking during this time window"
                )

            # Assign driver
            booking.driver_id = driver_id
            await db.commit()
            await db.refresh(booking)

            logger.info(
                f"Driver assigned to booking",
                extra={
                    "booking_id": str(booking_id),
                    "driver_id": str(driver_id),
                    "driver_name": driver.full_name,
                    "assigned_by": assigned_by,
                },
            )

            return booking

    @staticmethod
    async def auto_assign_driver(
        db: AsyncSession,
        booking_id: UUID,
    ) -> Booking:
        """
        Automatically assign best available driver to a booking.

        Selection criteria:
        1. Driver must be verified
        2. Driver must be available (no conflicts)
        3. Driver from same organization
        4. Prefer drivers with fewer upcoming assignments
        5. Prefer drivers with higher completion rates (future enhancement)

        Args:
            db: Database session
            booking_id: Booking ID

        Returns:
            Updated Booking instance with assigned driver

        Raises:
            DriverAssignmentError: If no suitable driver found
        """
        with tracer.start_as_current_span("driver_assignment.auto_assign") as span:
            span.set_attribute("booking_id", str(booking_id))

            # Get booking
            stmt = select(Booking).where(Booking.id == booking_id)
            result = await db.execute(stmt)
            booking = result.scalar_one_or_none()

            if not booking:
                raise DriverAssignmentError("Booking not found")

            if booking.driver_id:
                logger.info(f"Booking {booking_id} already has driver assigned")
                return booking

            # Get all verified drivers from organization
            stmt = select(Driver).where(
                and_(
                    Driver.org_id == booking.org_id,
                    Driver.is_verified == True,  # noqa: E712
                )
            )
            result = await db.execute(stmt)
            drivers = list(result.scalars().all())

            if not drivers:
                raise DriverAssignmentError("No verified drivers available in organization")

            # Filter available drivers (no conflicts)
            available_drivers = []
            for driver in drivers:
                overlapping = await DriverAssignmentService._check_driver_availability(
                    db,
                    driver.id,
                    booking.effective_start,
                    booking.effective_end,
                    exclude_booking_id=booking_id,
                )
                if not overlapping:
                    available_drivers.append(driver)

            if not available_drivers:
                raise DriverAssignmentError("No available drivers for this time slot")

            # Select driver with fewest upcoming assignments
            # (Simple heuristic - can be enhanced with more sophisticated logic)
            best_driver = available_drivers[0]
            min_assignments = await DriverAssignmentService._count_upcoming_assignments(
                db, best_driver.id
            )

            for driver in available_drivers[1:]:
                count = await DriverAssignmentService._count_upcoming_assignments(db, driver.id)
                if count < min_assignments:
                    best_driver = driver
                    min_assignments = count

            # Assign the selected driver
            booking = await DriverAssignmentService.assign_driver_to_booking(
                db, booking_id, best_driver.id, assigned_by="auto"
            )

            span.set_attribute("assigned_driver_id", str(best_driver.id))
            span.set_attribute("driver_name", best_driver.full_name)

            return booking

    @staticmethod
    async def unassign_driver(
        db: AsyncSession,
        booking_id: UUID,
        reason: str | None = None,
    ) -> Booking:
        """
        Remove driver assignment from booking.

        Args:
            db: Database session
            booking_id: Booking ID
            reason: Optional reason for unassignment

        Returns:
            Updated Booking instance
        """
        with tracer.start_as_current_span("driver_assignment.unassign") as span:
            span.set_attribute("booking_id", str(booking_id))

            stmt = select(Booking).where(Booking.id == booking_id)
            result = await db.execute(stmt)
            booking = result.scalar_one_or_none()

            if not booking:
                raise DriverAssignmentError("Booking not found")

            previous_driver_id = booking.driver_id
            booking.driver_id = None
            await db.commit()
            await db.refresh(booking)

            logger.info(
                f"Driver unassigned from booking",
                extra={
                    "booking_id": str(booking_id),
                    "previous_driver_id": str(previous_driver_id) if previous_driver_id else None,
                    "reason": reason,
                },
            )

            return booking

    @staticmethod
    async def reassign_driver(
        db: AsyncSession,
        booking_id: UUID,
        new_driver_id: UUID,
        reason: str | None = None,
    ) -> Booking:
        """
        Reassign booking to a different driver.

        Args:
            db: Database session
            booking_id: Booking ID
            new_driver_id: New driver ID
            reason: Optional reason for reassignment

        Returns:
            Updated Booking instance
        """
        with tracer.start_as_current_span("driver_assignment.reassign") as span:
            span.set_attribute("booking_id", str(booking_id))
            span.set_attribute("new_driver_id", str(new_driver_id))

            # Get current booking
            stmt = select(Booking).where(Booking.id == booking_id)
            result = await db.execute(stmt)
            booking = result.scalar_one_or_none()

            if not booking:
                raise DriverAssignmentError("Booking not found")

            old_driver_id = booking.driver_id

            # Assign new driver
            booking = await DriverAssignmentService.assign_driver_to_booking(
                db, booking_id, new_driver_id, assigned_by="manual"
            )

            logger.info(
                f"Driver reassigned",
                extra={
                    "booking_id": str(booking_id),
                    "old_driver_id": str(old_driver_id) if old_driver_id else None,
                    "new_driver_id": str(new_driver_id),
                    "reason": reason,
                },
            )

            return booking

    @staticmethod
    async def _check_driver_availability(
        db: AsyncSession,
        driver_id: UUID,
        start_time: datetime,
        end_time: datetime,
        exclude_booking_id: UUID | None = None,
    ) -> bool:
        """
        Check if driver has any conflicting assignments.

        Args:
            db: Database session
            driver_id: Driver ID to check
            start_time: Start of time window
            end_time: End of time window
            exclude_booking_id: Booking ID to exclude from check (for updates)

        Returns:
            True if driver has conflicts, False if available
        """
        stmt = select(Booking).where(
            and_(
                Booking.driver_id == driver_id,
                Booking.effective_start < end_time,
                Booking.effective_end > start_time,
            )
        )

        if exclude_booking_id:
            stmt = stmt.where(Booking.id != exclude_booking_id)

        result = await db.execute(stmt)
        conflicts = result.scalars().all()

        return len(conflicts) > 0

    @staticmethod
    async def _count_upcoming_assignments(db: AsyncSession, driver_id: UUID) -> int:
        """
        Count upcoming bookings for a driver.

        Args:
            db: Database session
            driver_id: Driver ID

        Returns:
            Count of upcoming bookings
        """
        now = datetime.now(UTC)
        stmt = select(Booking).where(
            and_(
                Booking.driver_id == driver_id,
                Booking.effective_start > now,
            )
        )
        result = await db.execute(stmt)
        bookings = result.scalars().all()
        return len(bookings)

    @staticmethod
    async def get_driver_schedule(
        db: AsyncSession,
        driver_id: UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[Booking]:
        """
        Get all bookings assigned to a driver within a date range.

        Args:
            db: Database session
            driver_id: Driver ID
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of bookings
        """
        stmt = select(Booking).where(Booking.driver_id == driver_id)

        if start_date:
            stmt = stmt.where(Booking.effective_start >= start_date)
        if end_date:
            stmt = stmt.where(Booking.effective_start <= end_date)

        stmt = stmt.order_by(Booking.effective_start.asc())

        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_available_drivers(
        db: AsyncSession,
        org_id: UUID,
        start_time: datetime,
        end_time: datetime,
    ) -> list[Driver]:
        """
        Get all drivers available during a specific time window.

        Args:
            db: Database session
            org_id: Organization ID
            start_time: Start of time window
            end_time: End of time window

        Returns:
            List of available drivers
        """
        # Get all verified drivers
        stmt = select(Driver).where(
            and_(
                Driver.org_id == org_id,
                Driver.is_verified == True,  # noqa: E712
            )
        )
        result = await db.execute(stmt)
        all_drivers = list(result.scalars().all())

        # Filter for availability
        available = []
        for driver in all_drivers:
            has_conflict = await DriverAssignmentService._check_driver_availability(
                db, driver.id, start_time, end_time
            )
            if not has_conflict:
                available.append(driver)

        return available
