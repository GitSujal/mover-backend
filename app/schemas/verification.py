"""Document verification schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.verification import DocumentType, VerificationStatus


class DocumentVerificationCreate(BaseModel):
    """Request to submit document for verification."""

    document_type: DocumentType = Field(description="Type of document")
    document_url: str = Field(description="S3 URL of uploaded document")
    document_number: str | None = Field(
        None, description="Document number (license #, policy #, etc.)"
    )
    expiry_date: datetime | None = Field(None, description="Document expiration date")
    additional_data: dict = Field(default_factory=dict, description="Additional document metadata")


class DocumentVerificationResponse(BaseModel):
    """Document verification details."""

    id: UUID
    org_id: UUID | None
    driver_id: UUID | None
    document_type: DocumentType
    document_url: str
    document_number: str | None
    status: VerificationStatus
    reviewed_by: UUID | None
    reviewed_at: datetime | None
    review_notes: str | None
    rejection_reason: str | None
    expiry_date: datetime | None
    expiry_reminder_sent: bool
    additional_data: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentVerificationReview(BaseModel):
    """Admin review of document verification."""

    status: VerificationStatus = Field(description="New verification status")
    review_notes: str | None = Field(None, description="Admin review notes", max_length=1000)
    rejection_reason: str | None = Field(
        None, description="Reason for rejection if rejected", max_length=1000
    )


class DocumentVerificationListResponse(BaseModel):
    """Paginated list of document verifications."""

    verifications: list[DocumentVerificationResponse]
    total: int
    page: int
    page_size: int
    pages: int


class DocumentVerificationStats(BaseModel):
    """Verification statistics."""

    total_pending: int
    total_under_review: int
    total_approved: int
    total_rejected: int
    total_expired: int
    documents_expiring_soon: int  # Expiring within 30 days


class OrganizationVerificationStatus(BaseModel):
    """Overall verification status for an organization."""

    org_id: UUID
    business_name: str
    is_fully_verified: bool
    required_documents: list[DocumentType]
    submitted_documents: list[DocumentType]
    approved_documents: list[DocumentType]
    pending_documents: list[DocumentType]
    rejected_documents: list[DocumentType]
    missing_documents: list[DocumentType]
    verification_progress_percentage: int


class DriverVerificationStatus(BaseModel):
    """Overall verification status for a driver."""

    driver_id: UUID
    driver_name: str
    is_fully_verified: bool
    required_documents: list[DocumentType]
    submitted_documents: list[DocumentType]
    approved_documents: list[DocumentType]
    pending_documents: list[DocumentType]
    rejected_documents: list[DocumentType]
    missing_documents: list[DocumentType]
    verification_progress_percentage: int
