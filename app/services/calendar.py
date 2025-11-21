"""Calendar and fleet management service."""

import logging
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.observability import tracer
from app.models.booking import Booking, BookingStatus
from app.models.driver import Driver
from app.models.truck import Truck
from app.schemas.calendar import (
    AvailabilitySlot,
    BookingCalendarItem,
    DriverScheduleItem,
    TruckScheduleItem,
)

logger = logging.getLogger(__name__)


class CalendarService:
    """Service for calendar and fleet management."""

    @staticmethod
    async def get_bookings_for_date_range(
        db: AsyncSession,
        org_id: UUID,
        start_date: datetime,
        end_date: datetime,
        status_filter: list[BookingStatus] | None = None,
    ) -> list[BookingCalendarItem]:
        """
        Get all bookings for a date range.

        Args:
            db: Database session
            org_id: Organization ID
            start_date: Start of date range
            end_date: End of date range
            status_filter: Optional status filter

        Returns:
            List of booking calendar items
        """
        with tracer.start_as_current_span("calendar.get_bookings") as span:
            span.set_attribute("org_id", str(org_id))
            span.set_attribute("start_date", start_date.isoformat())
            span.set_attribute("end_date", end_date.isoformat())

            # Build query
            query = (
                select(Booking)
                .where(
                    and_(
                        Booking.org_id == org_id,
                        Booking.move_date >= start_date,
                        Booking.move_date < end_date,
                    )
                )
                .order_by(Booking.move_date.asc())
            )

            # Apply status filter
            if status_filter:
                query = query.where(Booking.status.in_(status_filter))

            result = await db.execute(query)
            bookings = result.scalars().all()

            # Convert to calendar items
            calendar_items = []
            for booking in bookings:
                # Get driver info if assigned
                driver_name = None
                if booking.assigned_driver_id:
                    driver_result = await db.execute(
                        select(Driver).where(Driver.id == booking.assigned_driver_id)
                    )
                    driver = driver_result.scalar_one_or_none()
                    if driver:
                        driver_name = driver.name

                # Get truck info if assigned
                truck_identifier = None
                if booking.assigned_truck_id:
                    truck_result = await db.execute(
                        select(Truck).where(Truck.id == booking.assigned_truck_id)
                    )
                    truck = truck_result.scalar_one_or_none()
                    if truck:
                        truck_identifier = truck.license_plate

                calendar_items.append(
                    BookingCalendarItem(
                        id=booking.id,
                        booking_number=booking.booking_number,
                        customer_name=booking.customer_name,
                        customer_phone=booking.customer_phone,
                        move_date=booking.move_date,
                        pickup_address=booking.pickup_address,
                        dropoff_address=booking.dropoff_address,
                        estimated_duration_hours=float(booking.estimated_duration_hours),
                        status=booking.status,
                        assigned_driver_id=booking.assigned_driver_id,
                        assigned_driver_name=driver_name,
                        assigned_truck_id=booking.assigned_truck_id,
                        assigned_truck_identifier=truck_identifier,
                        notes=booking.notes,
                    )
                )

            logger.info(
                f"Retrieved {len(calendar_items)} bookings for calendar",
                extra={
                    "org_id": str(org_id),
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "count": len(calendar_items),
                },
            )

            return calendar_items

    @staticmethod
    async def get_driver_schedule(
        db: AsyncSession,
        driver_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> list[DriverScheduleItem]:
        """
        Get schedule for a specific driver.

        Args:
            db: Database session
            driver_id: Driver ID
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of schedule items
        """
        with tracer.start_as_current_span("calendar.get_driver_schedule") as span:
            span.set_attribute("driver_id", str(driver_id))

            # Get driver
            driver_result = await db.execute(select(Driver).where(Driver.id == driver_id))
            driver = driver_result.scalar_one_or_none()
            if not driver:
                return []

            # Get bookings for this driver
            query = (
                select(Booking)
                .where(
                    and_(
                        Booking.assigned_driver_id == driver_id,
                        Booking.move_date >= start_date,
                        Booking.move_date < end_date,
                        Booking.status.in_(
                            [
                                BookingStatus.CONFIRMED,
                                BookingStatus.IN_PROGRESS,
                            ]
                        ),
                    )
                )
                .order_by(Booking.move_date.asc())
            )

            result = await db.execute(query)
            bookings = result.scalars().all()

            # Build schedule items
            schedule = []
            for booking in bookings:
                end_time = booking.move_date + timedelta(
                    hours=float(booking.estimated_duration_hours)
                )

                schedule.append(
                    DriverScheduleItem(
                        driver_id=driver.id,
                        driver_name=driver.name,
                        driver_phone=driver.phone,
                        booking_id=booking.id,
                        booking_number=booking.booking_number,
                        start_time=booking.move_date,
                        end_time=end_time,
                        status="booked",
                        customer_name=booking.customer_name,
                        pickup_address=booking.pickup_address,
                        dropoff_address=booking.dropoff_address,
                    )
                )

            return schedule

    @staticmethod
    async def get_truck_schedule(
        db: AsyncSession,
        truck_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> list[TruckScheduleItem]:
        """
        Get schedule for a specific truck.

        Args:
            db: Database session
            truck_id: Truck ID
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of schedule items
        """
        with tracer.start_as_current_span("calendar.get_truck_schedule") as span:
            span.set_attribute("truck_id", str(truck_id))

            # Get truck
            truck_result = await db.execute(select(Truck).where(Truck.id == truck_id))
            truck = truck_result.scalar_one_or_none()
            if not truck:
                return []

            # Get bookings for this truck
            query = (
                select(Booking)
                .where(
                    and_(
                        Booking.assigned_truck_id == truck_id,
                        Booking.move_date >= start_date,
                        Booking.move_date < end_date,
                        Booking.status.in_(
                            [
                                BookingStatus.CONFIRMED,
                                BookingStatus.IN_PROGRESS,
                            ]
                        ),
                    )
                )
                .order_by(Booking.move_date.asc())
            )

            result = await db.execute(query)
            bookings = result.scalars().all()

            # Build schedule items
            schedule = []
            for booking in bookings:
                end_time = booking.move_date + timedelta(
                    hours=float(booking.estimated_duration_hours)
                )

                schedule.append(
                    TruckScheduleItem(
                        truck_id=truck.id,
                        truck_identifier=truck.license_plate,
                        booking_id=booking.id,
                        booking_number=booking.booking_number,
                        start_time=booking.move_date,
                        end_time=end_time,
                        status="booked",
                        customer_name=booking.customer_name,
                        pickup_address=booking.pickup_address,
                        dropoff_address=booking.dropoff_address,
                    )
                )

            return schedule

    @staticmethod
    async def find_available_resources(
        db: AsyncSession,
        org_id: UUID,
        requested_start: datetime,
        requested_end: datetime,
    ) -> tuple[list[UUID], list[UUID]]:
        """
        Find available drivers and trucks for a time range.

        Args:
            db: Database session
            org_id: Organization ID
            requested_start: Requested start time
            requested_end: Requested end time

        Returns:
            Tuple of (available_driver_ids, available_truck_ids)
        """
        with tracer.start_as_current_span("calendar.find_available_resources") as span:
            span.set_attribute("org_id", str(org_id))

            # Get all active drivers for organization
            driver_result = await db.execute(
                select(Driver).where(
                    and_(
                        Driver.org_id == org_id,
                        Driver.is_active == True,  # noqa: E712
                    )
                )
            )
            all_drivers = driver_result.scalars().all()

            # Get all active trucks for organization
            truck_result = await db.execute(
                select(Truck).where(
                    and_(
                        Truck.org_id == org_id,
                        Truck.is_active == True,  # noqa: E712
                    )
                )
            )
            all_trucks = truck_result.scalars().all()

            # Find conflicting bookings
            conflict_query = select(Booking).where(
                and_(
                    Booking.org_id == org_id,
                    Booking.status.in_(
                        [
                            BookingStatus.CONFIRMED,
                            BookingStatus.IN_PROGRESS,
                        ]
                    ),
                    # Check for time overlap
                    or_(
                        # Booking starts during requested time
                        and_(
                            Booking.move_date >= requested_start,
                            Booking.move_date < requested_end,
                        ),
                        # Booking ends during requested time
                        and_(
                            Booking.move_date < requested_start,
                            # End time calculation
                            Booking.move_date
                            + (Booking.estimated_duration_hours * timedelta(hours=1))
                            > requested_start,
                        ),
                    ),
                )
            )

            conflict_result = await db.execute(conflict_query)
            conflicting_bookings = conflict_result.scalars().all()

            # Get busy driver and truck IDs
            busy_driver_ids = {
                b.assigned_driver_id for b in conflicting_bookings if b.assigned_driver_id
            }
            busy_truck_ids = {
                b.assigned_truck_id for b in conflicting_bookings if b.assigned_truck_id
            }

            # Find available resources
            available_driver_ids = [d.id for d in all_drivers if d.id not in busy_driver_ids]
            available_truck_ids = [t.id for t in all_trucks if t.id not in busy_truck_ids]

            logger.info(
                f"Found {len(available_driver_ids)} available drivers, {len(available_truck_ids)} available trucks",
                extra={
                    "org_id": str(org_id),
                    "available_drivers": len(available_driver_ids),
                    "available_trucks": len(available_truck_ids),
                },
            )

            return available_driver_ids, available_truck_ids

    @staticmethod
    async def check_availability(
        db: AsyncSession,
        org_id: UUID,
        date: datetime,
        estimated_duration_hours: float,
    ) -> tuple[bool, list[AvailabilitySlot]]:
        """
        Check if resources are available for a booking.

        Args:
            db: Database session
            org_id: Organization ID
            date: Requested move date
            estimated_duration_hours: Estimated duration

        Returns:
            Tuple of (is_available, available_slots)
        """
        with tracer.start_as_current_span("calendar.check_availability") as span:
            span.set_attribute("org_id", str(org_id))
            span.set_attribute("date", date.isoformat())

            requested_end = date + timedelta(hours=estimated_duration_hours)

            available_drivers, available_trucks = await CalendarService.find_available_resources(
                db=db,
                org_id=org_id,
                requested_start=date,
                requested_end=requested_end,
            )

            is_available = len(available_drivers) > 0 and len(available_trucks) > 0

            slots = []
            if is_available:
                slots.append(
                    AvailabilitySlot(
                        start_time=date,
                        end_time=requested_end,
                        available_drivers=available_drivers,
                        available_trucks=available_trucks,
                    )
                )

            return is_available, slots
