"""Support ticket and issue reporting models."""

import enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.organization import Organization
    from app.models.user import User


class IssueType(str, enum.Enum):
    """Types of support issues."""

    LATE_NO_SHOW = "late_no_show"
    DAMAGE = "damage"
    PRICING_DISPUTE = "pricing_dispute"
    RUDE_BEHAVIOR = "rude_behavior"
    QUALITY_CONCERN = "quality_concern"
    PAYMENT_ISSUE = "payment_issue"
    CANCELLATION_REQUEST = "cancellation_request"
    OTHER = "other"


class IssueStatus(str, enum.Enum):
    """Support ticket status."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"


class IssuePriority(str, enum.Enum):
    """Issue priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class SupportIssue(BaseModel):
    """
    Customer support ticket for issue tracking and resolution.

    Issues can be created by customers or system automatically.
    Platform team handles resolution and may escalate.
    """

    __tablename__ = "support_issues"

    # Foreign Keys
    booking_id: Mapped[UUID] = mapped_column(
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    org_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Assigned agent (platform user)
    assigned_to: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Issue Details
    issue_type: Mapped[IssueType] = mapped_column(
        SQLEnum(IssueType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )
    priority: Mapped[IssuePriority] = mapped_column(
        SQLEnum(IssuePriority, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=IssuePriority.MEDIUM,
        index=True,
    )
    status: Mapped[IssueStatus] = mapped_column(
        SQLEnum(IssueStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=IssueStatus.OPEN,
        index=True,
    )

    # Content
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Evidence
    evidence_urls: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )  # Photos/documents

    # Reporter Info (denormalized)
    reporter_name: Mapped[str] = mapped_column(String(255), nullable=False)
    reporter_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    reporter_phone: Mapped[str] = mapped_column(String(20), nullable=True)

    # Resolution
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[str | None] = mapped_column(String(30), nullable=True)
    resolved_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Refund/Compensation
    refund_amount: Mapped[float | None] = mapped_column(nullable=True)
    refund_issued_at: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Relationships
    booking: Mapped["Booking"] = relationship("Booking")
    organization: Mapped["Organization"] = relationship("Organization")
    assigned_user: Mapped["User | None"] = relationship(
        "User", foreign_keys=[assigned_to], back_populates=None
    )
    resolved_user: Mapped["User | None"] = relationship(
        "User", foreign_keys=[resolved_by], back_populates=None
    )

    __table_args__ = (
        CheckConstraint(
            "issue_type IN ('late_no_show', 'damage', 'pricing_dispute', 'rude_behavior', 'quality_concern', 'payment_issue', 'cancellation_request', 'other')",
            name="valid_issue_type",
        ),
        CheckConstraint(
            "status IN ('open', 'in_progress', 'resolved', 'closed', 'escalated')",
            name="valid_status",
        ),
        CheckConstraint(
            "priority IN ('low', 'medium', 'high', 'urgent')",
            name="valid_priority",
        ),
        CheckConstraint("refund_amount IS NULL OR refund_amount >= 0", name="non_negative_refund"),
    )

    def __repr__(self) -> str:
        return (
            f"<SupportIssue(id={self.id}, type={self.issue_type}, "
            f"status={self.status}, priority={self.priority})>"
        )


class IssueComment(BaseModel):
    """
    Comments/updates on support issues.

    Track conversation history between customer, mover, and platform team.
    """

    __tablename__ = "issue_comments"

    # Foreign Key
    issue_id: Mapped[UUID] = mapped_column(
        ForeignKey("support_issues.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Author
    author_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    author_name: Mapped[str] = mapped_column(String(255), nullable=False)
    author_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # 'customer', 'mover', 'platform'

    # Content
    comment_text: Mapped[str] = mapped_column(Text, nullable=False)
    attachment_urls: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    # Internal vs External
    is_internal: Mapped[bool] = mapped_column(
        nullable=False, default=False
    )  # Only visible to platform team

    # Relationships
    issue: Mapped["SupportIssue"] = relationship("SupportIssue")
    author: Mapped["User | None"] = relationship("User")

    __table_args__ = (
        CheckConstraint(
            "author_type IN ('customer', 'mover', 'platform')",
            name="valid_author_type",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<IssueComment(id={self.id}, issue_id={self.issue_id}, " f"author={self.author_name})>"
        )
