"""Booking cancellation API endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, get_current_customer_session
from app.core.database import get_db
from app.models.booking import Booking
from app.models.cancellation import BookingCancellation
from app.models.user import CustomerSession, User
from app.schemas.cancellation import CancellationRequest, CancellationResponse
from app.services.cancellation import (
    BookingAlreadyCancelledError,
    BookingNotCancellableError,
    CancellationError,
    CancellationService,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cancellations", tags=["Cancellations"])


@router.post("/bookings/{booking_id}/cancel", response_model=CancellationResponse)
async def cancel_booking_as_customer(
    booking_id: UUID,
    cancellation_request: CancellationRequest,
    db: AsyncSession = Depends(get_db),
    customer_session: CustomerSession = Depends(get_current_customer_session),
) -> CancellationResponse:
    """
    Cancel a booking as a customer.

    Requires customer session authentication.
    Refund amount calculated based on cancellation timing.
    """
    try:
        # Verify booking belongs to this customer session
        result = await db.execute(select(Booking).where(Booking.id == booking_id))
        booking = result.scalar_one_or_none()

        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking {booking_id} not found",
            )

        if booking.customer_email != customer_session.email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only cancel your own bookings",
            )

        # Cancel booking
        cancellation = await CancellationService.cancel_booking(
            db=db,
            booking_id=booking_id,
            reason=cancellation_request.reason,
            cancelled_by=cancellation_request.cancelled_by,
            cancelled_by_name=booking.customer_name,
        )

        # Calculate refund percentage for response
        refund_percentage = (
            (cancellation.refund_amount / cancellation.original_amount * 100)
            if cancellation.original_amount > 0
            else 0
        )

        logger.info(
            f"Booking {booking_id} cancelled by customer {customer_session.email}",
            extra={
                "booking_id": str(booking_id),
                "customer_email": customer_session.email,
                "refund_amount": cancellation.refund_amount,
            },
        )

        return CancellationResponse(
            id=cancellation.id,
            booking_id=cancellation.booking_id,
            cancelled_by=cancellation.cancelled_by,
            cancelled_at=cancellation.cancelled_at,
            cancellation_reason=cancellation.cancellation_reason,
            hours_before_move=cancellation.hours_before_move,
            original_amount=cancellation.original_amount,
            refund_amount=cancellation.refund_amount,
            refund_percentage=refund_percentage,
            refund_status=cancellation.refund_status,
            refund_reason=cancellation.refund_reason,
            stripe_refund_id=cancellation.stripe_refund_id,
            customer_email=cancellation.customer_email,
            rebook_offered=cancellation.rebook_offered,
        )

    except BookingAlreadyCancelledError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    except BookingNotCancellableError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    except CancellationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cancellation failed: {str(e)}",
        ) from e


@router.post("/bookings/{booking_id}/cancel-as-mover", response_model=CancellationResponse)
async def cancel_booking_as_mover(
    booking_id: UUID,
    cancellation_request: CancellationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CancellationResponse:
    """
    Cancel a booking as a mover/organization.

    Requires mover authentication.
    Typically results in full refund + rebook offer.
    """
    try:
        # Verify booking belongs to this organization
        result = await db.execute(select(Booking).where(Booking.id == booking_id))
        booking = result.scalar_one_or_none()

        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking {booking_id} not found",
            )

        if booking.org_id != current_user.org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only cancel bookings for your organization",
            )

        # Cancel booking
        cancellation = await CancellationService.cancel_booking(
            db=db,
            booking_id=booking_id,
            reason=cancellation_request.reason,
            cancelled_by=cancellation_request.cancelled_by,
            cancelled_by_name=current_user.name,
        )

        refund_percentage = (
            (cancellation.refund_amount / cancellation.original_amount * 100)
            if cancellation.original_amount > 0
            else 0
        )

        logger.info(
            f"Booking {booking_id} cancelled by mover {current_user.email}",
            extra={
                "booking_id": str(booking_id),
                "mover_email": current_user.email,
                "org_id": str(current_user.org_id),
            },
        )

        return CancellationResponse(
            id=cancellation.id,
            booking_id=cancellation.booking_id,
            cancelled_by=cancellation.cancelled_by,
            cancelled_at=cancellation.cancelled_at,
            cancellation_reason=cancellation.cancellation_reason,
            hours_before_move=cancellation.hours_before_move,
            original_amount=cancellation.original_amount,
            refund_amount=cancellation.refund_amount,
            refund_percentage=refund_percentage,
            refund_status=cancellation.refund_status,
            refund_reason=cancellation.refund_reason,
            stripe_refund_id=cancellation.stripe_refund_id,
            customer_email=cancellation.customer_email,
            rebook_offered=cancellation.rebook_offered,
        )

    except (
        BookingAlreadyCancelledError,
        BookingNotCancellableError,
        CancellationError,
    ) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/bookings/{booking_id}/refund-policy")
async def get_refund_policy(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get refund policy information for a booking.

    Shows current refund amount and policy tiers.
    Public endpoint - no authentication required.
    """
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking {booking_id} not found",
        )

    policy_info = await CancellationService.get_refund_policy_info(
        original_amount=float(booking.estimated_amount),
        move_date=booking.move_date,
    )

    return policy_info


@router.get("/{cancellation_id}", response_model=CancellationResponse)
async def get_cancellation(
    cancellation_id: UUID,
    db: AsyncSession = Depends(get_db),
    customer_session: CustomerSession = Depends(get_current_customer_session),
) -> CancellationResponse:
    """
    Get cancellation details.

    Requires customer session authentication.
    """
    result = await db.execute(
        select(BookingCancellation).where(BookingCancellation.id == cancellation_id)
    )
    cancellation = result.scalar_one_or_none()

    if not cancellation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cancellation {cancellation_id} not found",
        )

    # Verify customer owns this cancellation
    if cancellation.customer_email != customer_session.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    refund_percentage = (
        (cancellation.refund_amount / cancellation.original_amount * 100)
        if cancellation.original_amount > 0
        else 0
    )

    return CancellationResponse(
        id=cancellation.id,
        booking_id=cancellation.booking_id,
        cancelled_by=cancellation.cancelled_by,
        cancelled_at=cancellation.cancelled_at,
        cancellation_reason=cancellation.cancellation_reason,
        hours_before_move=cancellation.hours_before_move,
        original_amount=cancellation.original_amount,
        refund_amount=cancellation.refund_amount,
        refund_percentage=refund_percentage,
        refund_status=cancellation.refund_status,
        refund_reason=cancellation.refund_reason,
        stripe_refund_id=cancellation.stripe_refund_id,
        customer_email=cancellation.customer_email,
        rebook_offered=cancellation.rebook_offered,
    )


@router.get("/booking/{booking_id}", response_model=CancellationResponse | None)
async def get_cancellation_by_booking(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
    customer_session: CustomerSession = Depends(get_current_customer_session),
) -> CancellationResponse | None:
    """
    Get cancellation for a specific booking.

    Returns null if booking not cancelled.
    """
    result = await db.execute(
        select(BookingCancellation).where(BookingCancellation.booking_id == booking_id)
    )
    cancellation = result.scalar_one_or_none()

    if not cancellation:
        return None

    # Verify customer owns this booking
    if cancellation.customer_email != customer_session.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    refund_percentage = (
        (cancellation.refund_amount / cancellation.original_amount * 100)
        if cancellation.original_amount > 0
        else 0
    )

    return CancellationResponse(
        id=cancellation.id,
        booking_id=cancellation.booking_id,
        cancelled_by=cancellation.cancelled_by,
        cancelled_at=cancellation.cancelled_at,
        cancellation_reason=cancellation.cancellation_reason,
        hours_before_move=cancellation.hours_before_move,
        original_amount=cancellation.original_amount,
        refund_amount=cancellation.refund_amount,
        refund_percentage=refund_percentage,
        refund_status=cancellation.refund_status,
        refund_reason=cancellation.refund_reason,
        stripe_refund_id=cancellation.stripe_refund_id,
        customer_email=cancellation.customer_email,
        rebook_offered=cancellation.rebook_offered,
    )


@router.get("/organization/{org_id}/cancellations")
async def list_organization_cancellations(
    org_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    List all cancellations for an organization.

    Requires mover authentication.
    """
    # Verify user belongs to organization
    if current_user.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Get cancellations
    offset = (page - 1) * page_size

    result = await db.execute(
        select(BookingCancellation)
        .where(BookingCancellation.org_id == org_id)
        .order_by(BookingCancellation.cancelled_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    cancellations = result.scalars().all()

    # Get total count
    from sqlalchemy import func

    count_result = await db.execute(
        select(func.count(BookingCancellation.id)).where(BookingCancellation.org_id == org_id)
    )
    total = count_result.scalar_one()

    return {
        "cancellations": [
            CancellationResponse(
                id=c.id,
                booking_id=c.booking_id,
                cancelled_by=c.cancelled_by,
                cancelled_at=c.cancelled_at,
                cancellation_reason=c.cancellation_reason,
                hours_before_move=c.hours_before_move,
                original_amount=c.original_amount,
                refund_amount=c.refund_amount,
                refund_percentage=(
                    (c.refund_amount / c.original_amount * 100) if c.original_amount > 0 else 0
                ),
                refund_status=c.refund_status,
                refund_reason=c.refund_reason,
                stripe_refund_id=c.stripe_refund_id,
                customer_email=c.customer_email,
                rebook_offered=c.rebook_offered,
            )
            for c in cancellations
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }
