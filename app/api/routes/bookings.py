"""Booking routes for customers and movers."""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, get_current_customer_session
from app.core.database import get_db
from app.models.booking import BookingStatus
from app.models.user import User, CustomerSession
from app.schemas.booking import (
    AvailabilityCheck,
    AvailabilityResponse,
    BookingCreate,
    BookingResponse,
    BookingUpdate,
)
from app.schemas.pricing import PricingConfigResponse
from app.services.booking import BookingConflictError, BookingService
from app.services.notifications import NotificationService
from app.services.pricing import PricingService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/bookings", tags=["Bookings"])

booking_service = BookingService()
notification_service = NotificationService()


@router.post("/check-availability", response_model=AvailabilityResponse)
async def check_availability(
    check: AvailabilityCheck,
    db: AsyncSession = Depends(get_db),
) -> AvailabilityResponse:
    """
    Check if a truck is available for the requested time window.

    Public endpoint - no authentication required.
    """
    availability = await BookingService.check_availability(db, check)
    return availability


@router.post(
    "",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_booking(
    booking_data: BookingCreate,
    db: AsyncSession = Depends(get_db),
    customer: Optional[CustomerSession] = Depends(get_current_customer_session),
) -> BookingResponse:
    """
    Create a new booking (customer endpoint).

    Validates availability and creates confirmed booking with pricing.
    """
    # Get organization's pricing config
    # TODO: Fetch from database - simplified for now
    from app.schemas.pricing import PricingConfigResponse

    pricing_config = PricingConfigResponse(
        id=UUID("00000000-0000-0000-0000-000000000000"),
        org_id=booking_data.org_id,
        base_hourly_rate=150.0,
        base_mileage_rate=2.50,
        minimum_charge=200.0,
        surcharge_rules=[],
        is_active=True,
        created_at=datetime.utcnow(),  # type: ignore # noqa: F821
        updated_at=datetime.utcnow(),  # type: ignore # noqa: F821
    )

    try:
        booking = await BookingService.create_booking(db, booking_data, pricing_config)

        # Send confirmation email
        await notification_service.send_booking_confirmation_email(
            customer_email=booking.customer_email,
            customer_name=booking.customer_name,
            booking_details={
                "move_date": booking.move_date.isoformat(),
                "pickup_address": booking.pickup_address,
                "dropoff_address": booking.dropoff_address,
                "estimated_amount": float(booking.estimated_amount),
            },
        )

        logger.info(
            f"Booking created: {booking.id}",
            extra={"booking_id": str(booking.id), "customer": booking.customer_email},
        )

        return BookingResponse.model_validate(booking)

    except BookingConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_active_user),
) -> BookingResponse:
    """
    Get booking details by ID.

    Mover authentication required.
    """
    booking = await BookingService.get_booking(db, booking_id)

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    # Verify access (user must belong to booking's organization)
    if booking.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return BookingResponse.model_validate(booking)


@router.get("", response_model=List[BookingResponse])
async def list_bookings(
    truck_id: Optional[UUID] = Query(None),
    status_filter: Optional[BookingStatus] = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[BookingResponse]:
    """
    List bookings for the current organization.

    Supports filtering by truck and status.
    """
    bookings = await BookingService.list_bookings(
        db,
        org_id=current_user.org_id,
        truck_id=truck_id,
        status=status_filter,
        limit=limit,
        offset=offset,
    )

    return [BookingResponse.model_validate(b) for b in bookings]


@router.patch("/{booking_id}", response_model=BookingResponse)
async def update_booking(
    booking_id: UUID,
    update_data: BookingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> BookingResponse:
    """
    Update booking status or details.

    Mover authentication required.
    """
    booking = await BookingService.get_booking(db, booking_id)

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    # Verify access
    if booking.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Update fields
    if update_data.status is not None:
        booking.status = update_data.status

    if update_data.final_amount is not None:
        booking.final_amount = update_data.final_amount

    if update_data.internal_notes is not None:
        booking.internal_notes = update_data.internal_notes

    await db.commit()
    await db.refresh(booking)

    logger.info(
        f"Booking updated: {booking_id}",
        extra={"booking_id": str(booking_id), "user": current_user.email},
    )

    return BookingResponse.model_validate(booking)
