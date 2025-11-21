"""Analytics dashboard API endpoints."""

import logging
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, get_db
from app.models.organization import Organization
from app.models.user import User
from app.schemas.analytics import (
    BookingMetrics,
    DriverMetrics,
    InvoiceMetrics,
    OrganizationDashboard,
    RatingMetrics,
    SupportMetrics,
    TrendData,
    TruckMetrics,
    VerificationMetrics,
)
from app.services.analytics import AnalyticsService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/organization/{org_id}/dashboard", response_model=OrganizationDashboard)
async def get_organization_dashboard(
    org_id: UUID,
    start_date: datetime = Query(default=None, description="Period start (default: 30 days ago)"),
    end_date: datetime = Query(default=None, description="Period end (default: now)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> OrganizationDashboard:
    """
    Get comprehensive analytics dashboard for organization.

    Requires mover authentication for own organization.
    Returns all metrics, trends, and insights.
    """
    # Verify access
    if current_user.org_id != org_id:
        # TODO: Check if platform admin
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Get organization
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {org_id} not found",
        )

    # Set default date range (last 30 days)
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()

    # Validate date range
    if end_date <= start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after start date",
        )

    # Get all metrics
    booking_metrics = await AnalyticsService.get_booking_metrics(
        db=db,
        org_id=org_id,
        start_date=start_date,
        end_date=end_date,
    )

    driver_metrics = await AnalyticsService.get_driver_metrics(
        db=db,
        org_id=org_id,
    )

    truck_metrics = await AnalyticsService.get_truck_metrics(
        db=db,
        org_id=org_id,
    )

    rating_metrics = await AnalyticsService.get_rating_metrics(
        db=db,
        org_id=org_id,
    )

    support_metrics = await AnalyticsService.get_support_metrics(
        db=db,
        org_id=org_id,
    )

    invoice_metrics = await AnalyticsService.get_invoice_metrics(
        db=db,
        org_id=org_id,
    )

    verification_metrics = await AnalyticsService.get_verification_metrics(
        db=db,
        org_id=org_id,
    )

    trends = await AnalyticsService.get_trend_data(
        db=db,
        org_id=org_id,
        start_date=start_date,
        end_date=end_date,
    )

    logger.info(
        f"Dashboard retrieved by {current_user.email} for org {org_id}",
        extra={
            "user_email": current_user.email,
            "org_id": str(org_id),
            "period_days": (end_date - start_date).days,
        },
    )

    return OrganizationDashboard(
        org_id=org_id,
        org_name=org.business_name,
        period_start=start_date,
        period_end=end_date,
        booking_metrics=booking_metrics,
        driver_metrics=driver_metrics,
        truck_metrics=truck_metrics,
        rating_metrics=rating_metrics,
        support_metrics=support_metrics,
        invoice_metrics=invoice_metrics,
        verification_metrics=verification_metrics,
        trends=trends,
    )


@router.get("/organization/{org_id}/bookings", response_model=BookingMetrics)
async def get_booking_metrics(
    org_id: UUID,
    start_date: datetime = Query(default=None, description="Period start (default: 30 days ago)"),
    end_date: datetime = Query(default=None, description="Period end (default: now)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> BookingMetrics:
    """
    Get booking analytics metrics.

    Requires mover authentication for own organization.
    """
    if current_user.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Set default date range
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()

    metrics = await AnalyticsService.get_booking_metrics(
        db=db,
        org_id=org_id,
        start_date=start_date,
        end_date=end_date,
    )

    logger.info(
        f"Booking metrics retrieved by {current_user.email}",
        extra={
            "user_email": current_user.email,
            "org_id": str(org_id),
        },
    )

    return metrics


@router.get("/organization/{org_id}/drivers", response_model=DriverMetrics)
async def get_driver_metrics(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DriverMetrics:
    """
    Get driver analytics metrics.

    Requires mover authentication for own organization.
    """
    if current_user.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    metrics = await AnalyticsService.get_driver_metrics(
        db=db,
        org_id=org_id,
    )

    logger.info(
        f"Driver metrics retrieved by {current_user.email}",
        extra={
            "user_email": current_user.email,
            "org_id": str(org_id),
        },
    )

    return metrics


@router.get("/organization/{org_id}/trucks", response_model=TruckMetrics)
async def get_truck_metrics(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TruckMetrics:
    """
    Get truck analytics metrics.

    Requires mover authentication for own organization.
    """
    if current_user.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    metrics = await AnalyticsService.get_truck_metrics(
        db=db,
        org_id=org_id,
    )

    logger.info(
        f"Truck metrics retrieved by {current_user.email}",
        extra={
            "user_email": current_user.email,
            "org_id": str(org_id),
        },
    )

    return metrics


@router.get("/organization/{org_id}/ratings", response_model=RatingMetrics)
async def get_rating_metrics(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RatingMetrics:
    """
    Get rating and review analytics metrics.

    Requires mover authentication for own organization.
    """
    if current_user.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    metrics = await AnalyticsService.get_rating_metrics(
        db=db,
        org_id=org_id,
    )

    logger.info(
        f"Rating metrics retrieved by {current_user.email}",
        extra={
            "user_email": current_user.email,
            "org_id": str(org_id),
        },
    )

    return metrics


@router.get("/organization/{org_id}/support", response_model=SupportMetrics)
async def get_support_metrics(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SupportMetrics:
    """
    Get support ticket analytics metrics.

    Requires mover authentication for own organization.
    """
    if current_user.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    metrics = await AnalyticsService.get_support_metrics(
        db=db,
        org_id=org_id,
    )

    logger.info(
        f"Support metrics retrieved by {current_user.email}",
        extra={
            "user_email": current_user.email,
            "org_id": str(org_id),
        },
    )

    return metrics


@router.get("/organization/{org_id}/invoices", response_model=InvoiceMetrics)
async def get_invoice_metrics(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> InvoiceMetrics:
    """
    Get invoice analytics metrics.

    Requires mover authentication for own organization.
    """
    if current_user.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    metrics = await AnalyticsService.get_invoice_metrics(
        db=db,
        org_id=org_id,
    )

    logger.info(
        f"Invoice metrics retrieved by {current_user.email}",
        extra={
            "user_email": current_user.email,
            "org_id": str(org_id),
        },
    )

    return metrics


@router.get("/organization/{org_id}/verification", response_model=VerificationMetrics)
async def get_verification_metrics(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> VerificationMetrics:
    """
    Get verification analytics metrics.

    Requires mover authentication for own organization.
    """
    if current_user.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    metrics = await AnalyticsService.get_verification_metrics(
        db=db,
        org_id=org_id,
    )

    logger.info(
        f"Verification metrics retrieved by {current_user.email}",
        extra={
            "user_email": current_user.email,
            "org_id": str(org_id),
        },
    )

    return metrics


@router.get("/organization/{org_id}/trends", response_model=TrendData)
async def get_trend_data(
    org_id: UUID,
    start_date: datetime = Query(default=None, description="Period start (default: 30 days ago)"),
    end_date: datetime = Query(default=None, description="Period end (default: now)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TrendData:
    """
    Get trend data over time.

    Requires mover authentication for own organization.
    """
    if current_user.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Set default date range
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()

    # Limit to 90 days
    if (end_date - start_date).days > 90:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Date range cannot exceed 90 days for trend data",
        )

    trends = await AnalyticsService.get_trend_data(
        db=db,
        org_id=org_id,
        start_date=start_date,
        end_date=end_date,
    )

    logger.info(
        f"Trend data retrieved by {current_user.email}",
        extra={
            "user_email": current_user.email,
            "org_id": str(org_id),
        },
    )

    return trends
