"""Rating and review API endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, get_current_customer_session
from app.core.database import get_db
from app.models.user import CustomerSession, User
from app.schemas.rating import (
    RatingCreate,
    RatingListResponse,
    RatingResponse,
    RatingStatsResponse,
    RatingSummaryResponse,
    RatingUpdate,
)
from app.services.notifications import NotificationService
from app.services.rating import (
    BookingNotEligibleError,
    RatingAlreadyExistsError,
    RatingService,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ratings", tags=["Ratings"])

notification_service = NotificationService()


@router.post(
    "",
    response_model=RatingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_rating(
    rating_data: RatingCreate,
    db: AsyncSession = Depends(get_db),
    customer: CustomerSession | None = Depends(get_current_customer_session),
) -> RatingResponse:
    """
    Create a new rating for a completed booking.

    Customer must have a verified session (OTP authenticated).
    Can only rate bookings that belong to them and are completed.
    """
    if not customer or not customer.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Customer authentication required to submit ratings",
        )

    try:
        rating = await RatingService.create_rating(
            db=db,
            rating_data=rating_data,
            customer_name=customer.identifier,  # Use email/phone as name for now
            customer_email=customer.identifier if "@" in customer.identifier else "",
        )

        # Send notification to mover
        # TODO: Implement notification to mover about new rating

        logger.info(
            f"Rating submitted: {rating.id}",
            extra={
                "rating_id": str(rating.id),
                "booking_id": str(rating.booking_id),
                "overall_rating": rating.overall_rating,
            },
        )

        return RatingResponse.model_validate(rating)

    except RatingAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e
    except BookingNotEligibleError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/{rating_id}", response_model=RatingResponse)
async def get_rating(
    rating_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> RatingResponse:
    """
    Get a specific rating by ID.

    Public endpoint - no authentication required.
    """
    rating = await RatingService.get_rating(db, rating_id)

    if not rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rating not found",
        )

    return RatingResponse.model_validate(rating)


@router.get("/booking/{booking_id}", response_model=RatingResponse)
async def get_rating_by_booking(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> RatingResponse:
    """
    Get rating for a specific booking.

    Public endpoint - useful for checking if booking has been rated.
    """
    rating = await RatingService.get_rating_by_booking(db, booking_id)

    if not rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No rating found for this booking",
        )

    return RatingResponse.model_validate(rating)


@router.get("/organization/{org_id}", response_model=RatingListResponse)
async def list_organization_ratings(
    org_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
) -> RatingListResponse:
    """
    List all ratings for an organization.

    Public endpoint - displays published ratings only.
    Used for mover profile pages.
    """
    offset = (page - 1) * limit

    ratings, total = await RatingService.list_ratings_for_org(
        db=db,
        org_id=org_id,
        limit=limit,
        offset=offset,
        published_only=True,
    )

    return RatingListResponse(
        ratings=[RatingResponse.model_validate(r) for r in ratings],
        total=total,
        page=page,
        page_size=limit,
        has_more=(offset + limit) < total,
    )


@router.get("/organization/{org_id}/summary", response_model=RatingSummaryResponse)
async def get_organization_rating_summary(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> RatingSummaryResponse:
    """
    Get aggregate rating statistics for an organization.

    Public endpoint - displays on mover profile cards and search results.
    """
    summary = await RatingService.get_rating_summary(db, org_id)

    if not summary:
        # Return default empty summary
        return RatingSummaryResponse(
            org_id=org_id,
            total_ratings=0,
            average_overall_rating=0.0,
            average_professionalism=None,
            average_punctuality=None,
            average_care_of_items=None,
            average_communication=None,
            average_value_for_money=None,
            five_star_count=0,
            four_star_count=0,
            three_star_count=0,
            two_star_count=0,
            one_star_count=0,
            created_at=None,  # type: ignore
            updated_at=None,  # type: ignore
        )

    return RatingSummaryResponse.model_validate(summary)


@router.get("/organization/{org_id}/stats", response_model=RatingStatsResponse)
async def get_organization_rating_stats(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> RatingStatsResponse:
    """
    Get detailed rating statistics for an organization.

    Includes summary, recent ratings, trends, and response metrics.
    Public endpoint.
    """
    # Get summary
    summary = await RatingService.get_rating_summary(db, org_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No ratings found for this organization",
        )

    # Get recent ratings (last 10)
    recent_ratings, _ = await RatingService.list_ratings_for_org(
        db=db,
        org_id=org_id,
        limit=10,
        offset=0,
        published_only=True,
    )

    # Calculate trend
    trend = await RatingService.calculate_rating_trend(db, org_id, days=30)

    # Calculate response rate
    response_rate = await RatingService.calculate_response_rate(db, org_id)

    return RatingStatsResponse(
        org_id=org_id,
        summary=RatingSummaryResponse.model_validate(summary),
        recent_ratings=[RatingResponse.model_validate(r) for r in recent_ratings],
        rating_trend=trend,
        response_rate=response_rate,
        average_response_time_hours=None,  # TODO: Implement if needed
    )


@router.patch("/{rating_id}/response", response_model=RatingResponse)
async def add_mover_response(
    rating_id: UUID,
    response_data: RatingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RatingResponse:
    """
    Add mover's response to a rating.

    Requires mover authentication.
    Only the organization that received the rating can respond.
    """
    try:
        rating = await RatingService.add_mover_response(
            db=db,
            rating_id=rating_id,
            org_id=current_user.org_id,
            response_data=response_data,
        )

        logger.info(
            f"Mover response added: {rating_id}",
            extra={"rating_id": str(rating_id), "org_id": str(current_user.org_id)},
        )

        return RatingResponse.model_validate(rating)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
