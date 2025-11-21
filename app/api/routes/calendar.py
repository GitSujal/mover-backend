"""Calendar and fleet management API endpoints."""

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, get_db
from app.models.booking import BookingStatus
from app.models.driver import Driver
from app.models.truck import Truck
from app.models.user import User
from app.schemas.calendar import (
    AvailabilityCheckRequest,
    AvailabilityCheckResponse,
    CalendarViewResponse,
    DriverScheduleResponse,
    FleetCalendarResponse,
    TruckScheduleResponse,
)
from app.services.calendar import CalendarService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/calendar", tags=["Calendar"])


@router.get("/bookings", response_model=CalendarViewResponse)
async def get_calendar_bookings(
    start_date: datetime = Query(..., description="Start date (ISO format)"),
    end_date: datetime = Query(..., description="End date (ISO format)"),
    status_filter: list[BookingStatus] | None = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CalendarViewResponse:
    """
    Get bookings for calendar view.

    Requires mover authentication.
    Returns all bookings for the organization in the specified date range.
    """
    if not current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not associated with an organization",
        )

    # Validate date range
    if end_date <= start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after start date",
        )

    # Limit range to 3 months
    if (end_date - start_date).days > 90:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Date range cannot exceed 90 days",
        )

    bookings = await CalendarService.get_bookings_for_date_range(
        db=db,
        org_id=current_user.org_id,
        start_date=start_date,
        end_date=end_date,
        status_filter=status_filter,
    )

    logger.info(
        f"Calendar bookings retrieved by {current_user.email}",
        extra={
            "user_email": current_user.email,
            "org_id": str(current_user.org_id),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "count": len(bookings),
        },
    )

    return CalendarViewResponse(
        start_date=start_date,
        end_date=end_date,
        bookings=bookings,
        total_bookings=len(bookings),
    )


@router.get("/driver/{driver_id}/schedule", response_model=DriverScheduleResponse)
async def get_driver_schedule(
    driver_id: UUID,
    start_date: datetime = Query(..., description="Start date (ISO format)"),
    end_date: datetime = Query(..., description="End date (ISO format)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DriverScheduleResponse:
    """
    Get schedule for a specific driver.

    Requires mover authentication.
    Shows all confirmed and in-progress bookings for the driver.
    """
    if not current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not associated with an organization",
        )

    # Get driver and verify organization
    result = await db.execute(select(Driver).where(Driver.id == driver_id))
    driver = result.scalar_one_or_none()

    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver {driver_id} not found",
        )

    if driver.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    schedule = await CalendarService.get_driver_schedule(
        db=db,
        driver_id=driver_id,
        start_date=start_date,
        end_date=end_date,
    )

    # Calculate total hours
    total_hours = sum((item.end_time - item.start_time).total_seconds() / 3600 for item in schedule)

    logger.info(
        f"Driver schedule retrieved by {current_user.email}",
        extra={
            "user_email": current_user.email,
            "driver_id": str(driver_id),
            "total_bookings": len(schedule),
            "total_hours": total_hours,
        },
    )

    return DriverScheduleResponse(
        driver_id=driver.id,
        driver_name=driver.name,
        start_date=start_date,
        end_date=end_date,
        schedule=schedule,
        total_hours_booked=total_hours,
        total_bookings=len(schedule),
    )


@router.get("/truck/{truck_id}/schedule", response_model=TruckScheduleResponse)
async def get_truck_schedule(
    truck_id: UUID,
    start_date: datetime = Query(..., description="Start date (ISO format)"),
    end_date: datetime = Query(..., description="End date (ISO format)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TruckScheduleResponse:
    """
    Get schedule for a specific truck.

    Requires mover authentication.
    Shows all confirmed and in-progress bookings for the truck.
    """
    if not current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not associated with an organization",
        )

    # Get truck and verify organization
    result = await db.execute(select(Truck).where(Truck.id == truck_id))
    truck = result.scalar_one_or_none()

    if not truck:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Truck {truck_id} not found",
        )

    if truck.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    schedule = await CalendarService.get_truck_schedule(
        db=db,
        truck_id=truck_id,
        start_date=start_date,
        end_date=end_date,
    )

    # Calculate total hours
    total_hours = sum((item.end_time - item.start_time).total_seconds() / 3600 for item in schedule)

    logger.info(
        f"Truck schedule retrieved by {current_user.email}",
        extra={
            "user_email": current_user.email,
            "truck_id": str(truck_id),
            "total_bookings": len(schedule),
            "total_hours": total_hours,
        },
    )

    return TruckScheduleResponse(
        truck_id=truck.id,
        truck_identifier=truck.license_plate,
        start_date=start_date,
        end_date=end_date,
        schedule=schedule,
        total_hours_booked=total_hours,
        total_bookings=len(schedule),
    )


@router.get("/fleet", response_model=FleetCalendarResponse)
async def get_fleet_calendar(
    start_date: datetime = Query(..., description="Start date (ISO format)"),
    end_date: datetime = Query(..., description="End date (ISO format)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FleetCalendarResponse:
    """
    Get fleet-wide calendar view.

    Requires mover authentication.
    Returns comprehensive view of all bookings, drivers, and trucks.
    """
    if not current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not associated with an organization",
        )

    # Validate date range
    if end_date <= start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after start date",
        )

    # Limit range to 1 month for fleet view
    if (end_date - start_date).days > 31:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Date range cannot exceed 31 days for fleet view",
        )

    # Get all bookings
    bookings = await CalendarService.get_bookings_for_date_range(
        db=db,
        org_id=current_user.org_id,
        start_date=start_date,
        end_date=end_date,
    )

    # Get all drivers
    driver_result = await db.execute(select(Driver).where(Driver.org_id == current_user.org_id))
    drivers = driver_result.scalars().all()

    # Get all trucks
    truck_result = await db.execute(select(Truck).where(Truck.org_id == current_user.org_id))
    trucks = truck_result.scalars().all()

    # Get schedules for all drivers
    driver_schedules = []
    for driver in drivers:
        schedule = await CalendarService.get_driver_schedule(
            db=db,
            driver_id=driver.id,
            start_date=start_date,
            end_date=end_date,
        )
        total_hours = sum(
            (item.end_time - item.start_time).total_seconds() / 3600 for item in schedule
        )
        driver_schedules.append(
            DriverScheduleResponse(
                driver_id=driver.id,
                driver_name=driver.name,
                start_date=start_date,
                end_date=end_date,
                schedule=schedule,
                total_hours_booked=total_hours,
                total_bookings=len(schedule),
            )
        )

    # Get schedules for all trucks
    truck_schedules = []
    for truck in trucks:
        schedule = await CalendarService.get_truck_schedule(
            db=db,
            truck_id=truck.id,
            start_date=start_date,
            end_date=end_date,
        )
        total_hours = sum(
            (item.end_time - item.start_time).total_seconds() / 3600 for item in schedule
        )
        truck_schedules.append(
            TruckScheduleResponse(
                truck_id=truck.id,
                truck_identifier=truck.license_plate,
                start_date=start_date,
                end_date=end_date,
                schedule=schedule,
                total_hours_booked=total_hours,
                total_bookings=len(schedule),
            )
        )

    logger.info(
        f"Fleet calendar retrieved by {current_user.email}",
        extra={
            "user_email": current_user.email,
            "org_id": str(current_user.org_id),
            "total_bookings": len(bookings),
            "total_drivers": len(drivers),
            "total_trucks": len(trucks),
        },
    )

    return FleetCalendarResponse(
        org_id=current_user.org_id,
        start_date=start_date,
        end_date=end_date,
        bookings=bookings,
        driver_schedules=driver_schedules,
        truck_schedules=truck_schedules,
        total_bookings=len(bookings),
        total_drivers=len(drivers),
        total_trucks=len(trucks),
    )


@router.post("/availability", response_model=AvailabilityCheckResponse)
async def check_availability(
    request: AvailabilityCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AvailabilityCheckResponse:
    """
    Check availability for a requested time slot.

    Requires mover authentication.
    Returns available drivers and trucks for the requested time.
    """
    if not current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not associated with an organization",
        )

    # Verify organization match
    if request.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only check availability for own organization",
        )

    is_available, slots = await CalendarService.check_availability(
        db=db,
        org_id=request.org_id,
        date=request.date,
        estimated_duration_hours=request.estimated_duration_hours,
    )

    total_drivers = len(slots[0].available_drivers) if slots else 0
    total_trucks = len(slots[0].available_trucks) if slots else 0

    message = None
    if not is_available:
        if total_drivers == 0 and total_trucks == 0:
            message = "No drivers or trucks available for this time slot"
        elif total_drivers == 0:
            message = "No drivers available for this time slot"
        elif total_trucks == 0:
            message = "No trucks available for this time slot"

    logger.info(
        f"Availability checked by {current_user.email}",
        extra={
            "user_email": current_user.email,
            "org_id": str(current_user.org_id),
            "is_available": is_available,
            "available_drivers": total_drivers,
            "available_trucks": total_trucks,
        },
    )

    return AvailabilityCheckResponse(
        is_available=is_available,
        available_slots=slots,
        total_available_drivers=total_drivers,
        total_available_trucks=total_trucks,
        message=message,
    )
