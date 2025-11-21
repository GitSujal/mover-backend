"""Booking routes for customers and movers."""

import logging
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_current_active_user,
    get_current_customer_session,
    get_current_user_optional,
)
from app.core.database import get_db
from app.models.booking import BookingStatus
from app.models.user import CustomerSession, User
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
    customer: CustomerSession | None = Depends(get_current_customer_session),
) -> BookingResponse:
    """
    Create a new booking (customer endpoint).

    Validates availability and creates confirmed booking with pricing.
    For customer bookings without org_id/truck_id, a default org and available
    truck will be assigned.
    """
    # If org_id or truck_id not provided (customer booking), assign defaults
    # TODO: Implement proper truck/org matching algorithm based on location, availability, etc.
    if not booking_data.org_id or not booking_data.truck_id:
        from sqlalchemy import select

        from app.models.organization import Organization, OrganizationStatus
        from app.models.truck import Truck

        # Get first approved organization
        result = await db.execute(
            select(Organization).where(Organization.status == OrganizationStatus.APPROVED).limit(1)
        )
        org = result.scalar_one_or_none()

        if not org:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No moving companies available at this time. Please try again later.",
            )

        # Get an available truck from this organization
        result = await db.execute(select(Truck).where(Truck.org_id == org.id).limit(1))
        truck = result.scalar_one_or_none()

        if not truck:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No trucks available at this time. Please try again later.",
            )

        # Assign to booking data
        booking_data.org_id = org.id
        booking_data.truck_id = truck.id

    # Get organization's pricing config
    # TODO: Fetch from database - simplified for now
    pricing_config = PricingConfigResponse(
        id=UUID("00000000-0000-0000-0000-000000000000"),
        org_id=booking_data.org_id,
        base_hourly_rate=150.0,
        base_mileage_rate=2.50,
        minimum_charge=200.0,
        surcharge_rules=[],
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
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
        ) from e


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> BookingResponse:
    """
    Get booking details by ID.

    Optional mover authentication for access control.
    """
    booking = await BookingService.get_booking(db, booking_id)

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    # Verify access if authenticated (user must belong to booking's organization)
    if current_user and booking.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return BookingResponse.model_validate(booking)


@router.get("", response_model=list[BookingResponse])
async def list_bookings(
    truck_id: UUID | None = Query(None),
    status_filter: BookingStatus | None = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[BookingResponse]:
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

    # Update booking via service
    try:
        booking = await BookingService.update_booking(db, booking, update_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    logger.info(
        f"Booking updated: {booking_id}",
        extra={"booking_id": str(booking_id), "user": current_user.email},
    )

    return BookingResponse.model_validate(booking)
