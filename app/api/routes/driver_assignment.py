"""Driver assignment API endpoints."""

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.core.database import get_db
from app.models.booking import Booking
from app.models.driver import Driver
from app.models.user import User
from app.schemas.booking import BookingResponse
from app.schemas.driver import DriverResponse
from app.services.driver_assignment import DriverAssignmentError, DriverAssignmentService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/driver-assignment", tags=["Driver Assignment"])


class DriverAssignmentRequest(BaseModel):
    """Request to assign driver to booking."""

    driver_id: UUID = Field(description="Driver ID to assign")


class DriverReassignmentRequest(BaseModel):
    """Request to reassign booking to different driver."""

    new_driver_id: UUID = Field(description="New driver ID")
    reason: str | None = Field(None, description="Reason for reassignment")


class DriverUnassignRequest(BaseModel):
    """Request to unassign driver from booking."""

    reason: str | None = Field(None, description="Reason for unassignment")


class AvailableDriversQuery(BaseModel):
    """Query parameters for available drivers."""

    start_time: datetime
    end_time: datetime


@router.post("/bookings/{booking_id}/assign", response_model=BookingResponse)
async def assign_driver(
    booking_id: UUID,
    assignment: DriverAssignmentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> BookingResponse:
    """
    Manually assign a driver to a booking.

    Requires manager or owner role.
    """
    try:
        booking = await DriverAssignmentService.assign_driver_to_booking(
            db=db,
            booking_id=booking_id,
            driver_id=assignment.driver_id,
            assigned_by="manual",
        )

        logger.info(
            f"Driver manually assigned to booking {booking_id}",
            extra={
                "booking_id": str(booking_id),
                "driver_id": str(assignment.driver_id),
                "assigned_by": current_user.email,
            },
        )

        return BookingResponse.model_validate(booking)

    except DriverAssignmentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post("/bookings/{booking_id}/auto-assign", response_model=BookingResponse)
async def auto_assign_driver(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> BookingResponse:
    """
    Automatically assign best available driver to booking.

    Uses intelligent selection based on availability and workload.
    """
    try:
        booking = await DriverAssignmentService.auto_assign_driver(
            db=db,
            booking_id=booking_id,
        )

        logger.info(
            f"Driver auto-assigned to booking {booking_id}",
            extra={
                "booking_id": str(booking_id),
                "driver_id": str(booking.driver_id) if booking.driver_id else None,
                "requested_by": current_user.email,
            },
        )

        return BookingResponse.model_validate(booking)

    except DriverAssignmentError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.delete("/bookings/{booking_id}/unassign", response_model=BookingResponse)
async def unassign_driver(
    booking_id: UUID,
    unassign: DriverUnassignRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> BookingResponse:
    """
    Remove driver assignment from booking.
    """
    try:
        booking = await DriverAssignmentService.unassign_driver(
            db=db,
            booking_id=booking_id,
            reason=unassign.reason,
        )

        logger.info(
            f"Driver unassigned from booking {booking_id}",
            extra={
                "booking_id": str(booking_id),
                "reason": unassign.reason,
                "unassigned_by": current_user.email,
            },
        )

        return BookingResponse.model_validate(booking)

    except DriverAssignmentError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.put("/bookings/{booking_id}/reassign", response_model=BookingResponse)
async def reassign_driver(
    booking_id: UUID,
    reassignment: DriverReassignmentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> BookingResponse:
    """
    Reassign booking to a different driver.
    """
    try:
        booking = await DriverAssignmentService.reassign_driver(
            db=db,
            booking_id=booking_id,
            new_driver_id=reassignment.new_driver_id,
            reason=reassignment.reason,
        )

        logger.info(
            f"Booking {booking_id} reassigned to new driver",
            extra={
                "booking_id": str(booking_id),
                "new_driver_id": str(reassignment.new_driver_id),
                "reason": reassignment.reason,
                "reassigned_by": current_user.email,
            },
        )

        return BookingResponse.model_validate(booking)

    except DriverAssignmentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/drivers/{driver_id}/schedule", response_model=list[BookingResponse])
async def get_driver_schedule(
    driver_id: UUID,
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[BookingResponse]:
    """
    Get all bookings assigned to a driver within a date range.

    Useful for viewing driver's schedule/calendar.
    """
    bookings = await DriverAssignmentService.get_driver_schedule(
        db=db,
        driver_id=driver_id,
        start_date=start_date,
        end_date=end_date,
    )

    return [BookingResponse.model_validate(b) for b in bookings]


@router.get("/available-drivers", response_model=list[DriverResponse])
async def get_available_drivers(
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[DriverResponse]:
    """
    Get all drivers available during a specific time window.

    Useful for manual assignment - shows which drivers are free.
    """
    drivers = await DriverAssignmentService.get_available_drivers(
        db=db,
        org_id=current_user.org_id,
        start_time=start_time,
        end_time=end_time,
    )

    return [DriverResponse.model_validate(d) for d in drivers]
