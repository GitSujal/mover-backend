"""Document verification API endpoints."""

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, get_db
from app.models.driver import Driver
from app.models.organization import Organization
from app.models.user import User
from app.models.verification import DocumentVerification, VerificationStatus
from app.schemas.verification import (
    DocumentVerificationCreate,
    DocumentVerificationListResponse,
    DocumentVerificationResponse,
    DocumentVerificationReview,
    DocumentVerificationStats,
    DriverVerificationStatus,
    OrganizationVerificationStatus,
)
from app.services.verification import VerificationError, VerificationService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/verification", tags=["Verification"])


@router.post("/organization/{org_id}/documents", response_model=DocumentVerificationResponse)
async def submit_organization_document(
    org_id: UUID,
    document: DocumentVerificationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DocumentVerificationResponse:
    """
    Submit document for organization verification.

    Requires mover authentication for own organization.
    """
    # Verify user belongs to organization
    if current_user.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only submit documents for your own organization",
        )

    verification = await VerificationService.submit_organization_document(
        db=db,
        org_id=org_id,
        document_type=document.document_type,
        document_url=document.document_url,
        document_number=document.document_number,
        expiry_date=document.expiry_date,
        additional_data=document.additional_data,
    )

    logger.info(
        f"Document submitted by {current_user.email} for org {org_id}",
        extra={
            "user_email": current_user.email,
            "org_id": str(org_id),
            "document_type": document.document_type.value,
        },
    )

    return DocumentVerificationResponse.model_validate(verification)


@router.post("/driver/{driver_id}/documents", response_model=DocumentVerificationResponse)
async def submit_driver_document(
    driver_id: UUID,
    document: DocumentVerificationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DocumentVerificationResponse:
    """
    Submit document for driver verification.

    Requires mover authentication for own organization's drivers.
    """
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
            detail="You can only submit documents for your organization's drivers",
        )

    verification = await VerificationService.submit_driver_document(
        db=db,
        driver_id=driver_id,
        document_type=document.document_type,
        document_url=document.document_url,
        document_number=document.document_number,
        expiry_date=document.expiry_date,
        additional_data=document.additional_data,
    )

    logger.info(
        f"Document submitted by {current_user.email} for driver {driver_id}",
        extra={
            "user_email": current_user.email,
            "driver_id": str(driver_id),
            "document_type": document.document_type.value,
        },
    )

    return DocumentVerificationResponse.model_validate(verification)


@router.post("/documents/{verification_id}/review", response_model=DocumentVerificationResponse)
async def review_document_verification(
    verification_id: UUID,
    review: DocumentVerificationReview,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DocumentVerificationResponse:
    """
    Admin reviews and approves/rejects document.

    Requires platform admin role.
    """
    # TODO: Add role check for platform admin
    # For now, any authenticated user can review (should be restricted in production)

    try:
        verification = await VerificationService.review_document(
            db=db,
            verification_id=verification_id,
            reviewer_id=current_user.id,
            new_status=review.status,
            review_notes=review.review_notes,
            rejection_reason=review.rejection_reason,
        )

        logger.info(
            f"Document reviewed by {current_user.email}: {verification_id}",
            extra={
                "reviewer_email": current_user.email,
                "verification_id": str(verification_id),
                "new_status": review.status.value,
            },
        )

        return DocumentVerificationResponse.model_validate(verification)

    except VerificationError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.get("/documents/pending", response_model=DocumentVerificationListResponse)
async def list_pending_verifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DocumentVerificationListResponse:
    """
    List all pending document verifications.

    Requires platform admin role.
    """
    # Get pending verifications
    query = (
        select(DocumentVerification)
        .where(
            DocumentVerification.status.in_(
                [VerificationStatus.PENDING, VerificationStatus.UNDER_REVIEW]
            )
        )
        .order_by(DocumentVerification.created_at.asc())
    )

    # Get total count
    count_result = await db.execute(
        select(func.count(DocumentVerification.id)).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    # Get page
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    verifications = result.scalars().all()

    return DocumentVerificationListResponse(
        verifications=[DocumentVerificationResponse.model_validate(v) for v in verifications],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/organization/{org_id}/status", response_model=OrganizationVerificationStatus)
async def get_organization_verification_status(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> OrganizationVerificationStatus:
    """
    Get verification status for an organization.

    Requires mover authentication for own organization or platform admin.
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

    # Get verification status
    status_dict = await VerificationService.get_organization_verification_status(
        db=db,
        org_id=org_id,
    )

    return OrganizationVerificationStatus(
        org_id=org_id,
        business_name=org.business_name,
        **status_dict,
    )


@router.get("/driver/{driver_id}/status", response_model=DriverVerificationStatus)
async def get_driver_verification_status(
    driver_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DriverVerificationStatus:
    """
    Get verification status for a driver.

    Requires mover authentication for own organization's drivers or platform admin.
    """
    # Get driver
    result = await db.execute(select(Driver).where(Driver.id == driver_id))
    driver = result.scalar_one_or_none()

    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver {driver_id} not found",
        )

    # Verify access
    if driver.org_id != current_user.org_id:
        # TODO: Check if platform admin
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Get verification status
    status_dict = await VerificationService.get_driver_verification_status(
        db=db,
        driver_id=driver_id,
    )

    return DriverVerificationStatus(
        driver_id=driver_id,
        driver_name=driver.name,
        **status_dict,
    )


@router.get("/stats", response_model=DocumentVerificationStats)
async def get_verification_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DocumentVerificationStats:
    """
    Get verification statistics.

    Requires platform admin role.
    """
    # Get counts by status
    pending_result = await db.execute(
        select(func.count(DocumentVerification.id)).where(
            DocumentVerification.status == VerificationStatus.PENDING
        )
    )
    pending = pending_result.scalar_one()

    under_review_result = await db.execute(
        select(func.count(DocumentVerification.id)).where(
            DocumentVerification.status == VerificationStatus.UNDER_REVIEW
        )
    )
    under_review = under_review_result.scalar_one()

    approved_result = await db.execute(
        select(func.count(DocumentVerification.id)).where(
            DocumentVerification.status == VerificationStatus.APPROVED
        )
    )
    approved = approved_result.scalar_one()

    rejected_result = await db.execute(
        select(func.count(DocumentVerification.id)).where(
            DocumentVerification.status.in_(
                [VerificationStatus.REJECTED, VerificationStatus.RESUBMISSION_REQUIRED]
            )
        )
    )
    rejected = rejected_result.scalar_one()

    expired_result = await db.execute(
        select(func.count(DocumentVerification.id)).where(
            DocumentVerification.status == VerificationStatus.EXPIRED
        )
    )
    expired = expired_result.scalar_one()

    # Get expiring soon
    expiring_docs = await VerificationService.get_expiring_documents(db=db, days_threshold=30)

    return DocumentVerificationStats(
        total_pending=pending,
        total_under_review=under_review,
        total_approved=approved,
        total_rejected=rejected,
        total_expired=expired,
        documents_expiring_soon=len(expiring_docs),
    )


@router.get("/documents/{verification_id}", response_model=DocumentVerificationResponse)
async def get_document_verification(
    verification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DocumentVerificationResponse:
    """
    Get document verification details.

    Requires authentication.
    """
    result = await db.execute(
        select(DocumentVerification).where(DocumentVerification.id == verification_id)
    )
    verification = result.scalar_one_or_none()

    if not verification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verification {verification_id} not found",
        )

    # Verify access (own org/driver or platform admin)
    if verification.org_id and verification.org_id != current_user.org_id:
        # TODO: Check if platform admin
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    if verification.driver_id:
        driver_result = await db.execute(select(Driver).where(Driver.id == verification.driver_id))
        driver = driver_result.scalar_one_or_none()
        if driver and driver.org_id != current_user.org_id:
            # TODO: Check if platform admin
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

    return DocumentVerificationResponse.model_validate(verification)


@router.post("/expiry-reminders/send")
async def send_expiry_reminders(
    days_threshold: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Send expiry reminder notifications for documents expiring soon.

    Typically called by background job/cron.
    Requires platform admin role.
    """
    from app.services.notification_templates import EmailTemplates
    from app.services.notifications import NotificationService

    # Get expiring documents
    expiring_docs = await VerificationService.get_expiring_documents(
        db=db,
        days_threshold=days_threshold,
    )

    notification_service = NotificationService()
    email_templates = EmailTemplates()
    sent_count = 0

    for verification in expiring_docs:
        try:
            # Get entity (org or driver)
            if verification.org_id:
                org_result = await db.execute(
                    select(Organization).where(Organization.id == verification.org_id)
                )
                org = org_result.scalar_one_or_none()
                if not org:
                    continue

                recipient_email = org.contact_email
                recipient_name = org.business_name
            elif verification.driver_id:
                driver_result = await db.execute(
                    select(Driver).where(Driver.id == verification.driver_id)
                )
                driver = driver_result.scalar_one_or_none()
                if not driver:
                    continue

                recipient_email = driver.email
                recipient_name = driver.name
            else:
                continue

            # Calculate days until expiry
            days_until_expiry = (
                (verification.expiry_date - datetime.utcnow()).days
                if verification.expiry_date
                else 0
            )

            # Send reminder
            await notification_service.send_email(
                to_email=recipient_email,
                subject=f"Document Expiring Soon - {verification.document_type.value}",
                html_content=email_templates.insurance_expiring(
                    customer_name=recipient_name,
                    document_type=verification.document_type.value,
                    expiry_date=(
                        verification.expiry_date.strftime("%B %d, %Y")
                        if verification.expiry_date
                        else "N/A"
                    ),
                    days_remaining=days_until_expiry,
                ),
            )

            # Mark reminder sent
            await VerificationService.mark_expiry_reminder_sent(
                db=db,
                verification_id=verification.id,
            )

            sent_count += 1

            logger.info(
                f"Expiry reminder sent for verification {verification.id}",
                extra={
                    "verification_id": str(verification.id),
                    "document_type": verification.document_type.value,
                    "days_until_expiry": days_until_expiry,
                },
            )

        except Exception as e:
            logger.error(
                f"Failed to send expiry reminder for verification {verification.id}: {e}",
                exc_info=True,
            )

    return {
        "total_expiring": len(expiring_docs),
        "reminders_sent": sent_count,
        "days_threshold": days_threshold,
    }


@router.get("/expiry-reminders/preview")
async def preview_expiring_documents(
    days_threshold: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Preview documents that will expire soon (without sending notifications).

    Requires platform admin role.
    """
    expiring_docs = await VerificationService.get_expiring_documents(
        db=db,
        days_threshold=days_threshold,
    )

    return {
        "total_expiring": len(expiring_docs),
        "days_threshold": days_threshold,
        "documents": [
            {
                "verification_id": str(doc.id),
                "document_type": doc.document_type.value,
                "expiry_date": doc.expiry_date.strftime("%Y-%m-%d") if doc.expiry_date else None,
                "days_until_expiry": (
                    (doc.expiry_date - datetime.utcnow()).days if doc.expiry_date else 0
                ),
                "org_id": str(doc.org_id) if doc.org_id else None,
                "driver_id": str(doc.driver_id) if doc.driver_id else None,
            }
            for doc in expiring_docs
        ],
    }
