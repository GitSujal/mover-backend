"""Support ticket schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.support import IssuePriority, IssueStatus, IssueType


class SupportIssueCreate(BaseModel):
    """Request to create a support ticket."""

    booking_id: UUID = Field(description="Related booking ID")
    issue_type: IssueType = Field(description="Type of issue")
    title: str = Field(description="Issue title", min_length=5, max_length=200)
    description: str = Field(description="Detailed description", min_length=10, max_length=5000)
    evidence_urls: list[str] = Field(default_factory=list, description="Photo/document URLs")
    reporter_name: str = Field(description="Reporter name")
    reporter_email: str = Field(description="Reporter email")
    reporter_phone: str | None = Field(None, description="Reporter phone")


class IssueCommentCreate(BaseModel):
    """Request to add comment to support ticket."""

    comment_text: str = Field(description="Comment text", min_length=1, max_length=5000)
    attachment_urls: list[str] = Field(default_factory=list, description="Attachment URLs")
    is_internal: bool = Field(default=False, description="Internal comment (platform only)")


class IssueCommentResponse(BaseModel):
    """Support issue comment."""

    id: UUID
    issue_id: UUID
    author_id: UUID | None
    author_name: str
    author_type: str  # 'customer', 'mover', 'platform'
    comment_text: str
    attachment_urls: list[str]
    is_internal: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SupportIssueResponse(BaseModel):
    """Support ticket details."""

    id: UUID
    booking_id: UUID
    org_id: UUID
    assigned_to: UUID | None
    issue_type: IssueType
    priority: IssuePriority
    status: IssueStatus
    title: str
    description: str
    evidence_urls: list[str]
    reporter_name: str
    reporter_email: str
    reporter_phone: str | None
    resolution_notes: str | None
    resolved_at: str | None
    resolved_by: UUID | None
    refund_amount: float | None
    refund_issued_at: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SupportIssueWithComments(SupportIssueResponse):
    """Support ticket with full comment history."""

    comments: list[IssueCommentResponse]


class SupportIssueUpdate(BaseModel):
    """Update support ticket."""

    status: IssueStatus | None = None
    priority: IssuePriority | None = None
    assigned_to: UUID | None = None
    resolution_notes: str | None = Field(None, max_length=5000)
    refund_amount: float | None = Field(None, ge=0)


class SupportIssueListResponse(BaseModel):
    """Paginated list of support tickets."""

    issues: list[SupportIssueResponse]
    total: int
    page: int
    page_size: int
    pages: int


class SupportStats(BaseModel):
    """Support ticket statistics."""

    total_open: int
    total_in_progress: int
    total_resolved: int
    total_escalated: int
    average_resolution_time_hours: float | None
    total_refunds_issued: float
