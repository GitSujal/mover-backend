"""Invoice model for completed moves."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.booking import Booking


class InvoiceStatus(str, enum.Enum):
    """Invoice payment status."""

    DRAFT = "draft"
    ISSUED = "issued"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class Invoice(BaseModel):
    """
    Invoice for completed moves.

    Immutable once created to maintain financial audit trail.
    """

    __tablename__ = "invoices"

    # Foreign Keys
    booking_id: Mapped[UUID] = mapped_column(
        ForeignKey("bookings.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Invoice Details
    invoice_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
    )

    # Amounts
    subtotal: Mapped[float] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=False,
    )
    platform_fee: Mapped[float] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=False,
    )
    tax_amount: Mapped[float] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=False,
        default=0,
    )
    total_amount: Mapped[float] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=False,
    )

    # Payment
    status: Mapped[InvoiceStatus] = mapped_column(
        nullable=False,
        default=InvoiceStatus.DRAFT,
        index=True,
    )
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    payment_method: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # Stripe
    stripe_invoice_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
    )
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Dates
    due_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # PDF Document
    pdf_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Relationships
    booking: Mapped["Booking"] = relationship("Booking", back_populates="invoice")

    __table_args__ = (
        CheckConstraint("subtotal >= 0", name="non_negative_subtotal"),
        CheckConstraint("platform_fee >= 0", name="non_negative_platform_fee"),
        CheckConstraint("tax_amount >= 0", name="non_negative_tax"),
        CheckConstraint("total_amount >= 0", name="non_negative_total"),
        CheckConstraint(
            "total_amount = subtotal + tax_amount",
            name="valid_total_calculation",
        ),
        CheckConstraint(
            "status IN ('draft', 'issued', 'paid', 'overdue', 'cancelled')",
            name="valid_status",
        ),
        UniqueConstraint("booking_id", name="uq_invoice_booking"),
    )

    def __repr__(self) -> str:
        return (
            f"<Invoice(id={self.id}, number={self.invoice_number}, "
            f"total={self.total_amount}, status={self.status})>"
        )
