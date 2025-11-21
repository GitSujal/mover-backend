"""Document verification and compliance tracking models."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.driver import Driver
    from app.models.organization import Organization
    from app.models.user import User


class DocumentType(str, enum.Enum):
    """Types of documents for verification."""

    BUSINESS_LICENSE = "business_license"
    LIABILITY_INSURANCE = "liability_insurance"
    WORKERS_COMP_INSURANCE = "workers_comp_insurance"
    DRIVERS_LICENSE = "drivers_license"
    CDL_LICENSE = "cdl_license"
    VEHICLE_REGISTRATION = "vehicle_registration"
    VEHICLE_INSURANCE = "vehicle_insurance"
    BACKGROUND_CHECK = "background_check"
    DOT_MEDICAL_CARD = "dot_medical_card"
    OTHER = "other"


class VerificationStatus(str, enum.Enum):
    """Document verification status."""

    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    RESUBMISSION_REQUIRED = "resubmission_required"


class DocumentVerification(BaseModel):
    """
    Track document verification for organizations and drivers.

    Platform team reviews and approves/rejects documents.
    Tracks expiration and sends renewal reminders.
    """

    __tablename__ = "document_verifications"

    # Foreign Keys (either org or driver)
    org_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    driver_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("drivers.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Document Details
    document_type: Mapped[DocumentType] = mapped_column(
        SQLEnum(DocumentType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )
    document_url: Mapped[str] = mapped_column(String(512), nullable=False)
    document_number: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Verification
    status: Mapped[VerificationStatus] = mapped_column(
        SQLEnum(VerificationStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=VerificationStatus.PENDING,
        index=True,
    )

    # Review Details
    reviewed_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Expiration
    expiry_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    expiry_reminder_sent: Mapped[bool] = mapped_column(nullable=False, default=False)

    # Additional Data
    additional_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )  # Store additional info (e.g., extracted data)

    # Relationships
    organization: Mapped["Organization | None"] = relationship("Organization")
    driver: Mapped["Driver | None"] = relationship("Driver")
    reviewer: Mapped["User | None"] = relationship("User")

    __table_args__ = (
        CheckConstraint(
            "(org_id IS NOT NULL AND driver_id IS NULL) OR (org_id IS NULL AND driver_id IS NOT NULL)",
            name="one_entity_required",
        ),
        CheckConstraint(
            "document_type IN ('business_license', 'liability_insurance', 'workers_comp_insurance', 'drivers_license', 'cdl_license', 'vehicle_registration', 'vehicle_insurance', 'background_check', 'dot_medical_card', 'other')",
            name="valid_document_type",
        ),
        CheckConstraint(
            "status IN ('pending', 'under_review', 'approved', 'rejected', 'expired', 'resubmission_required')",
            name="valid_verification_status",
        ),
    )

    @property
    def is_expired(self) -> bool:
        """Check if document has expired."""
        if not self.expiry_date:
            return False
        return datetime.now() > self.expiry_date

    @property
    def days_until_expiry(self) -> int | None:
        """Calculate days until document expires."""
        if not self.expiry_date:
            return None
        delta = self.expiry_date - datetime.now()
        return max(0, delta.days)

    def __repr__(self) -> str:
        entity_type = "org" if self.org_id else "driver"
        entity_id = self.org_id or self.driver_id
        return (
            f"<DocumentVerification(id={self.id}, {entity_type}={entity_id}, "
            f"type={self.document_type}, status={self.status})>"
        )


class ComplianceAlert(BaseModel):
    """
    Automated alerts for compliance issues.

    Tracks insurance expiration, license renewal, etc.
    Triggers email/SMS notifications at configured thresholds.
    """

    __tablename__ = "compliance_alerts"

    # Foreign Keys
    org_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    driver_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("drivers.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    document_verification_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("document_verifications.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Alert Details
    alert_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # e.g., 'insurance_expiring', 'license_expired'
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # 'info', 'warning', 'critical'
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # Notification
    notification_sent: Mapped[bool] = mapped_column(nullable=False, default=False)
    notification_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Resolution
    is_resolved: Mapped[bool] = mapped_column(nullable=False, default=False, index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    organization: Mapped["Organization | None"] = relationship("Organization")
    driver: Mapped["Driver | None"] = relationship("Driver")
    document_verification: Mapped["DocumentVerification | None"] = relationship(
        "DocumentVerification"
    )

    __table_args__ = (
        CheckConstraint(
            "severity IN ('info', 'warning', 'critical')",
            name="valid_severity",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<ComplianceAlert(id={self.id}, type={self.alert_type}, "
            f"severity={self.severity}, resolved={self.is_resolved})>"
        )
