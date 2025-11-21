"""Booking cancellation and refund tracking."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.organization import Organization


class CancellationSource(str, enum.Enum):
    """Who initiated the cancellation."""

    CUSTOMER = "customer"
    MOVER = "mover"
    PLATFORM = "platform"  # Platform-initiated (e.g., compliance issue)


class RefundStatus(str, enum.Enum):
    """Status of refund processing."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    NO_REFUND = "no_refund"


class BookingCancellation(BaseModel):
    """
    Track booking cancellations and refund processing.

    Stores cancellation reason, timing, and refund details.
    Used for analytics and refund automation.
    """

    __tablename__ = "booking_cancellations"

    # Foreign Keys
    booking_id: Mapped[UUID] = mapped_column(
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One cancellation per booking
        index=True,
    )
    org_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Cancellation Details
    cancelled_by: Mapped[CancellationSource] = mapped_column(
        SQLEnum(CancellationSource, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )
    cancelled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    cancellation_reason: Mapped[str] = mapped_column(Text, nullable=False)

    # Timing Analysis
    hours_before_move: Mapped[float] = mapped_column(
        nullable=False
    )  # Time between cancellation and scheduled move

    # Refund Calculation
    original_amount: Mapped[float] = mapped_column(nullable=False)
    platform_fee_paid: Mapped[float] = mapped_column(nullable=False)
    refund_amount: Mapped[float] = mapped_column(nullable=False)
    refund_reason: Mapped[str] = mapped_column(Text, nullable=True)

    # Refund Processing
    refund_status: Mapped[RefundStatus] = mapped_column(
        SQLEnum(RefundStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=RefundStatus.PENDING,
        index=True,
    )
    refund_processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    stripe_refund_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)

    # Customer Info (denormalized)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Rebook Option
    rebook_offered: Mapped[bool] = mapped_column(nullable=False, default=False)
    rebook_accepted: Mapped[bool] = mapped_column(nullable=False, default=False)
    new_booking_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("bookings.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    booking: Mapped["Booking"] = relationship("Booking", foreign_keys=[booking_id])
    organization: Mapped["Organization"] = relationship("Organization")
    new_booking: Mapped["Booking | None"] = relationship("Booking", foreign_keys=[new_booking_id])

    __table_args__ = (
        CheckConstraint(
            "cancelled_by IN ('customer', 'mover', 'platform')",
            name="valid_cancelled_by",
        ),
        CheckConstraint(
            "refund_status IN ('pending', 'processing', 'completed', 'failed', 'no_refund')",
            name="valid_refund_status",
        ),
        CheckConstraint("original_amount >= 0", name="non_negative_original_amount"),
        CheckConstraint("platform_fee_paid >= 0", name="non_negative_platform_fee"),
        CheckConstraint("refund_amount >= 0", name="non_negative_refund_amount"),
        CheckConstraint("hours_before_move >= 0", name="non_negative_hours_before"),
    )

    def __repr__(self) -> str:
        return (
            f"<BookingCancellation(id={self.id}, booking_id={self.booking_id}, "
            f"cancelled_by={self.cancelled_by}, refund_status={self.refund_status})>"
        )
