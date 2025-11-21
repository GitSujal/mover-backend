"""Booking status history tracking."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.booking import BookingStatus

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.user import User


class BookingStatusHistory(BaseModel):
    """
    Audit trail for booking status transitions.

    Tracks all status changes with timestamp and user information.
    Helps with debugging, customer support, and analytics.
    """

    __tablename__ = "booking_status_history"

    # Foreign Keys
    booking_id: Mapped[UUID] = mapped_column(
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    transitioned_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Status Transition
    from_status: Mapped[BookingStatus] = mapped_column(
        SQLEnum(BookingStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )
    to_status: Mapped[BookingStatus] = mapped_column(
        SQLEnum(BookingStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )

    # User Information (denormalized for audit trail)
    transitioned_by_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    transitioned_by_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # 'system', 'customer', 'mover', 'platform_admin'

    # Additional Context
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    transitioned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    # Relationships
    booking: Mapped["Booking"] = relationship("Booking")
    transitioned_by: Mapped["User | None"] = relationship("User")

    __table_args__ = (
        CheckConstraint(
            "from_status IN ('pending', 'confirmed', 'in_progress', 'completed', 'cancelled')",
            name="valid_from_status",
        ),
        CheckConstraint(
            "to_status IN ('pending', 'confirmed', 'in_progress', 'completed', 'cancelled')",
            name="valid_to_status",
        ),
        CheckConstraint(
            "transitioned_by_type IN ('system', 'customer', 'mover', 'platform_admin')",
            name="valid_transitioned_by_type",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<BookingStatusHistory(id={self.id}, booking_id={self.booking_id}, "
            f"{self.from_status} → {self.to_status}, at={self.transitioned_at})>"
        )
