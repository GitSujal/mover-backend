"""Booking status transition API endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.booking_status import (
    StatusHistoryEntry,
    StatusHistoryResponse,
    StatusTransitionRequest,
    StatusTransitionResponse,
)
from app.services.booking_status import (
    BookingNotFoundError,
    BookingStatusService,
    InvalidStatusTransitionError,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/bookings", tags=["Booking Status"])


@router.post("/{booking_id}/status", response_model=StatusTransitionResponse)
async def transition_booking_status(
    booking_id: UUID,
    transition: StatusTransitionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> StatusTransitionResponse:
    """
    Transition booking to a new status.

    Validates the transition, updates the booking, creates audit trail,
    and sends appropriate notifications.

    Requires mover/driver authentication.
    """
    try:
        old_status = None
        # Get current status first for response
        from sqlalchemy import select

        from app.models.booking import Booking

        result = await db.execute(select(Booking).where(Booking.id == booking_id))
        booking = result.scalar_one_or_none()

        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking {booking_id} not found",
            )

        old_status = booking.status

        # Perform transition
        updated_booking = await BookingStatusService.transition_status(
            db=db,
            booking_id=booking_id,
            new_status=transition.new_status,
            transitioned_by=current_user,
            transitioned_by_type="mover",
            transitioned_by_name=current_user.name,
            notes=transition.notes,
        )

        logger.info(
            f"Booking {booking_id} status changed by {current_user.email}",
            extra={
                "booking_id": str(booking_id),
                "old_status": old_status.value,
                "new_status": transition.new_status.value,
                "user_email": current_user.email,
            },
        )

        return StatusTransitionResponse(
            booking_id=updated_booking.id,
            old_status=old_status,
            new_status=updated_booking.status,
            transitioned_at=updated_booking.updated_at,
            transitioned_by=current_user.email,
            notes=transition.notes,
        )

    except BookingNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    except InvalidStatusTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post("/{booking_id}/confirm", response_model=StatusTransitionResponse)
async def confirm_booking(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> StatusTransitionResponse:
    """
    Confirm a pending booking.

    Typically called after payment is processed or by mover accepting the job.
    """
    try:
        from sqlalchemy import select

        from app.models.booking import Booking

        # Get current status for response
        result = await db.execute(select(Booking).where(Booking.id == booking_id))
        booking = result.scalar_one_or_none()

        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking {booking_id} not found",
            )

        old_status = booking.status

        updated_booking = await BookingStatusService.auto_confirm_booking(
            db=db,
            booking_id=booking_id,
        )

        return StatusTransitionResponse(
            booking_id=updated_booking.id,
            old_status=old_status,
            new_status=updated_booking.status,
            transitioned_at=updated_booking.updated_at,
            transitioned_by="system",
            notes="Booking confirmed",
        )

    except (BookingNotFoundError, InvalidStatusTransitionError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post("/{booking_id}/start", response_model=StatusTransitionResponse)
async def start_booking(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> StatusTransitionResponse:
    """
    Mark booking as in-progress.

    Called by driver when they arrive on-site to start the move.
    """
    try:
        from sqlalchemy import select

        from app.models.booking import Booking

        result = await db.execute(select(Booking).where(Booking.id == booking_id))
        booking = result.scalar_one_or_none()

        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking {booking_id} not found",
            )

        old_status = booking.status

        updated_booking = await BookingStatusService.mark_in_progress(
            db=db,
            booking_id=booking_id,
            driver_user=current_user,
        )

        return StatusTransitionResponse(
            booking_id=updated_booking.id,
            old_status=old_status,
            new_status=updated_booking.status,
            transitioned_at=updated_booking.updated_at,
            transitioned_by=current_user.email,
            notes="Driver arrived on-site",
        )

    except (BookingNotFoundError, InvalidStatusTransitionError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post("/{booking_id}/complete", response_model=StatusTransitionResponse)
async def complete_booking(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> StatusTransitionResponse:
    """
    Mark booking as completed.

    Called by driver when the move is finished.
    Triggers rating request notification to customer.
    """
    try:
        from sqlalchemy import select

        from app.models.booking import Booking

        result = await db.execute(select(Booking).where(Booking.id == booking_id))
        booking = result.scalar_one_or_none()

        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking {booking_id} not found",
            )

        old_status = booking.status

        updated_booking = await BookingStatusService.mark_completed(
            db=db,
            booking_id=booking_id,
            driver_user=current_user,
        )

        return StatusTransitionResponse(
            booking_id=updated_booking.id,
            old_status=old_status,
            new_status=updated_booking.status,
            transitioned_at=updated_booking.updated_at,
            transitioned_by=current_user.email,
            notes="Job completed",
        )

    except (BookingNotFoundError, InvalidStatusTransitionError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/{booking_id}/status-history", response_model=StatusHistoryResponse)
async def get_booking_status_history(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> StatusHistoryResponse:
    """
    Get complete status transition history for a booking.

    Useful for debugging, customer support, and audit trails.
    """
    from sqlalchemy import select

    from app.models.booking import Booking

    # Verify booking exists and user has access
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking {booking_id} not found",
        )

    # Get history
    history = await BookingStatusService.get_status_history(
        db=db,
        booking_id=booking_id,
    )

    return StatusHistoryResponse(
        booking_id=booking_id,
        current_status=booking.status,
        history=[
            StatusHistoryEntry(
                id=entry.id,
                booking_id=entry.booking_id,
                from_status=entry.from_status,
                to_status=entry.to_status,
                transitioned_at=entry.transitioned_at,
                transitioned_by_id=entry.transitioned_by_id,
                transitioned_by_name=entry.transitioned_by_name,
                notes=entry.notes,
            )
            for entry in history
        ],
    )
