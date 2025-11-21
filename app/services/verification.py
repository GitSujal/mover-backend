"""Document verification service for admin workflows."""

import logging
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.observability import tracer
from app.models.driver import Driver
from app.models.organization import Organization
from app.models.verification import DocumentType, DocumentVerification, VerificationStatus
from app.services.notifications import NotificationService

logger = logging.getLogger(__name__)


class VerificationError(Exception):
    """Base exception for verification errors."""

    pass


class VerificationService:
    """Service for document verification workflows."""

    # Required documents for organization onboarding
    REQUIRED_ORG_DOCUMENTS = [
        DocumentType.BUSINESS_LICENSE,
        DocumentType.LIABILITY_INSURANCE,
        DocumentType.WORKERS_COMP_INSURANCE,
    ]

    # Required documents for driver verification
    REQUIRED_DRIVER_DOCUMENTS = [
        DocumentType.DRIVERS_LICENSE,
        DocumentType.BACKGROUND_CHECK,
    ]

    @staticmethod
    async def submit_organization_document(
        db: AsyncSession,
        org_id: UUID,
        document_type: DocumentType,
        document_url: str,
        document_number: str | None = None,
        expiry_date: datetime | None = None,
        additional_data: dict | None = None,
    ) -> DocumentVerification:
        """
        Submit document for organization verification.

        Args:
            db: Database session
            org_id: Organization ID
            document_type: Type of document
            document_url: S3 URL
            document_number: Optional document number
            expiry_date: Optional expiration date
            additional_data: Optional metadata

        Returns:
            Created verification record
        """
        with tracer.start_as_current_span("verification.submit_org_document"):
            verification = DocumentVerification(
                org_id=org_id,
                driver_id=None,
                document_type=document_type,
                document_url=document_url,
                document_number=document_number,
                status=VerificationStatus.PENDING,
                expiry_date=expiry_date,
                additional_data=additional_data or {},
            )

            db.add(verification)
            await db.commit()
            await db.refresh(verification)

            logger.info(
                f"Document submitted for org {org_id}: {document_type.value}",
                extra={
                    "org_id": str(org_id),
                    "document_type": document_type.value,
                    "verification_id": str(verification.id),
                },
            )

            return verification

    @staticmethod
    async def submit_driver_document(
        db: AsyncSession,
        driver_id: UUID,
        document_type: DocumentType,
        document_url: str,
        document_number: str | None = None,
        expiry_date: datetime | None = None,
        additional_data: dict | None = None,
    ) -> DocumentVerification:
        """
        Submit document for driver verification.

        Args:
            db: Database session
            driver_id: Driver ID
            document_type: Type of document
            document_url: S3 URL
            document_number: Optional document number
            expiry_date: Optional expiration date
            additional_data: Optional metadata

        Returns:
            Created verification record
        """
        with tracer.start_as_current_span("verification.submit_driver_document"):
            verification = DocumentVerification(
                org_id=None,
                driver_id=driver_id,
                document_type=document_type,
                document_url=document_url,
                document_number=document_number,
                status=VerificationStatus.PENDING,
                expiry_date=expiry_date,
                additional_data=additional_data or {},
            )

            db.add(verification)
            await db.commit()
            await db.refresh(verification)

            logger.info(
                f"Document submitted for driver {driver_id}: {document_type.value}",
                extra={
                    "driver_id": str(driver_id),
                    "document_type": document_type.value,
                    "verification_id": str(verification.id),
                },
            )

            return verification

    @staticmethod
    async def review_document(
        db: AsyncSession,
        verification_id: UUID,
        reviewer_id: UUID,
        new_status: VerificationStatus,
        review_notes: str | None = None,
        rejection_reason: str | None = None,
    ) -> DocumentVerification:
        """
        Admin reviews and approves/rejects document.

        Args:
            db: Database session
            verification_id: Verification record ID
            reviewer_id: Admin user ID
            new_status: New verification status
            review_notes: Optional review notes
            rejection_reason: Required if rejected

        Returns:
            Updated verification record
        """
        with tracer.start_as_current_span("verification.review_document") as span:
            span.set_attribute("verification_id", str(verification_id))
            span.set_attribute("new_status", new_status.value)

            # Get verification
            result = await db.execute(
                select(DocumentVerification).where(DocumentVerification.id == verification_id)
            )
            verification = result.scalar_one_or_none()

            if not verification:
                raise VerificationError(f"Verification {verification_id} not found")

            # Update verification
            old_status = verification.status
            verification.status = new_status
            verification.reviewed_by = reviewer_id
            verification.reviewed_at = datetime.utcnow()
            verification.review_notes = review_notes
            verification.rejection_reason = rejection_reason

            await db.commit()
            await db.refresh(verification)

            logger.info(
                f"Document verification reviewed: {verification_id} from {old_status.value} to {new_status.value}",
                extra={
                    "verification_id": str(verification_id),
                    "old_status": old_status.value,
                    "new_status": new_status.value,
                    "reviewer_id": str(reviewer_id),
                },
            )

            # Send notification
            try:
                await VerificationService._send_verification_notification(
                    db=db,
                    verification=verification,
                )
            except Exception as e:
                logger.error(f"Failed to send verification notification: {e}")

            return verification

    @staticmethod
    async def _send_verification_notification(
        db: AsyncSession,
        verification: DocumentVerification,
    ) -> None:
        """Send notification about verification status change."""
        notification_service = NotificationService()

        # Get entity (org or driver)
        if verification.org_id:
            result = await db.execute(
                select(Organization).where(Organization.id == verification.org_id)
            )
            org = result.scalar_one_or_none()
            if not org:
                return

            recipient_email = org.contact_email
            recipient_name = org.business_name
        elif verification.driver_id:
            result = await db.execute(select(Driver).where(Driver.id == verification.driver_id))
            driver = result.scalar_one_or_none()
            if not driver:
                return

            recipient_email = driver.email
            recipient_name = driver.name
        else:
            return

        # Send notification based on status
        if verification.status == VerificationStatus.APPROVED:
            subject = f"Document Approved - {verification.document_type.value}"
            message = f"Your {verification.document_type.value} has been approved."
        elif verification.status == VerificationStatus.REJECTED:
            subject = f"Document Rejected - {verification.document_type.value}"
            message = f"Your {verification.document_type.value} was rejected. Reason: {verification.rejection_reason}"
        elif verification.status == VerificationStatus.RESUBMISSION_REQUIRED:
            subject = f"Resubmission Required - {verification.document_type.value}"
            message = f"Please resubmit your {verification.document_type.value}. {verification.review_notes}"
        else:
            return  # No notification for other statuses

        # Simple text email (would use template in production)
        html_content = f"""
        <html>
        <body>
            <h2>Document Verification Update</h2>
            <p>Dear {recipient_name},</p>
            <p>{message}</p>
            <p>Document Type: {verification.document_type.value}</p>
            {f'<p>Review Notes: {verification.review_notes}</p>' if verification.review_notes else ''}
            <p>Thank you,<br>MoveHub Platform Team</p>
        </body>
        </html>
        """

        await notification_service.send_email(
            to_email=recipient_email,
            subject=subject,
            html_content=html_content,
        )

    @staticmethod
    async def get_organization_verification_status(
        db: AsyncSession,
        org_id: UUID,
    ) -> dict:
        """
        Get comprehensive verification status for organization.

        Args:
            db: Database session
            org_id: Organization ID

        Returns:
            Dict with verification status details
        """
        with tracer.start_as_current_span("verification.get_org_status"):
            # Get all verifications for org
            result = await db.execute(
                select(DocumentVerification).where(DocumentVerification.org_id == org_id)
            )
            verifications = result.scalars().all()

            # Group by document type (latest submission)
            doc_status = {}
            for v in verifications:
                if v.document_type not in doc_status:
                    doc_status[v.document_type] = v
                else:
                    # Keep most recent
                    if v.created_at > doc_status[v.document_type].created_at:
                        doc_status[v.document_type] = v

            # Calculate status
            required_docs = set(VerificationService.REQUIRED_ORG_DOCUMENTS)
            submitted_docs = set(doc_status.keys())
            approved_docs = {
                doc for doc, v in doc_status.items() if v.status == VerificationStatus.APPROVED
            }
            pending_docs = {
                doc
                for doc, v in doc_status.items()
                if v.status in [VerificationStatus.PENDING, VerificationStatus.UNDER_REVIEW]
            }
            rejected_docs = {
                doc
                for doc, v in doc_status.items()
                if v.status
                in [VerificationStatus.REJECTED, VerificationStatus.RESUBMISSION_REQUIRED]
            }
            missing_docs = required_docs - submitted_docs

            # Check if fully verified
            is_fully_verified = required_docs.issubset(approved_docs)

            # Calculate progress
            progress = int((len(approved_docs) / len(required_docs)) * 100) if required_docs else 0

            return {
                "is_fully_verified": is_fully_verified,
                "required_documents": list(required_docs),
                "submitted_documents": list(submitted_docs),
                "approved_documents": list(approved_docs),
                "pending_documents": list(pending_docs),
                "rejected_documents": list(rejected_docs),
                "missing_documents": list(missing_docs),
                "verification_progress_percentage": progress,
            }

    @staticmethod
    async def get_driver_verification_status(
        db: AsyncSession,
        driver_id: UUID,
    ) -> dict:
        """
        Get comprehensive verification status for driver.

        Args:
            db: Database session
            driver_id: Driver ID

        Returns:
            Dict with verification status details
        """
        with tracer.start_as_current_span("verification.get_driver_status"):
            # Get all verifications for driver
            result = await db.execute(
                select(DocumentVerification).where(DocumentVerification.driver_id == driver_id)
            )
            verifications = result.scalars().all()

            # Group by document type (latest submission)
            doc_status = {}
            for v in verifications:
                if v.document_type not in doc_status:
                    doc_status[v.document_type] = v
                else:
                    if v.created_at > doc_status[v.document_type].created_at:
                        doc_status[v.document_type] = v

            # Calculate status
            required_docs = set(VerificationService.REQUIRED_DRIVER_DOCUMENTS)
            submitted_docs = set(doc_status.keys())
            approved_docs = {
                doc for doc, v in doc_status.items() if v.status == VerificationStatus.APPROVED
            }
            pending_docs = {
                doc
                for doc, v in doc_status.items()
                if v.status in [VerificationStatus.PENDING, VerificationStatus.UNDER_REVIEW]
            }
            rejected_docs = {
                doc
                for doc, v in doc_status.items()
                if v.status
                in [VerificationStatus.REJECTED, VerificationStatus.RESUBMISSION_REQUIRED]
            }
            missing_docs = required_docs - submitted_docs

            is_fully_verified = required_docs.issubset(approved_docs)
            progress = int((len(approved_docs) / len(required_docs)) * 100) if required_docs else 0

            return {
                "is_fully_verified": is_fully_verified,
                "required_documents": list(required_docs),
                "submitted_documents": list(submitted_docs),
                "approved_documents": list(approved_docs),
                "pending_documents": list(pending_docs),
                "rejected_documents": list(rejected_docs),
                "missing_documents": list(missing_docs),
                "verification_progress_percentage": progress,
            }

    @staticmethod
    async def get_expiring_documents(
        db: AsyncSession,
        days_threshold: int = 30,
    ) -> list[DocumentVerification]:
        """
        Get documents expiring within threshold.

        Args:
            db: Database session
            days_threshold: Days until expiry

        Returns:
            List of expiring document verifications
        """
        with tracer.start_as_current_span("verification.get_expiring"):
            threshold_date = datetime.utcnow() + timedelta(days=days_threshold)

            result = await db.execute(
                select(DocumentVerification)
                .where(DocumentVerification.status == VerificationStatus.APPROVED)
                .where(DocumentVerification.expiry_date.isnot(None))
                .where(DocumentVerification.expiry_date <= threshold_date)
                .where(DocumentVerification.expiry_reminder_sent == False)  # noqa: E712
            )

            return list(result.scalars().all())

    @staticmethod
    async def mark_expiry_reminder_sent(
        db: AsyncSession,
        verification_id: UUID,
    ) -> None:
        """Mark that expiry reminder was sent."""
        result = await db.execute(
            select(DocumentVerification).where(DocumentVerification.id == verification_id)
        )
        verification = result.scalar_one_or_none()

        if verification:
            verification.expiry_reminder_sent = True
            await db.commit()
