"""Booking model with conflict detection."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ExcludeConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.invoice import Invoice
    from app.models.organization import Organization
    from app.models.truck import Truck


class BookingStatus(str, enum.Enum):
    """Booking lifecycle status."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Booking(BaseModel):
    """
    Customer booking with conflict-free scheduling.

    Uses PostgreSQL exclusion constraints to prevent double-booking.
    Computed fields (effective_start, effective_end) include commute buffer.
    """

    __tablename__ = "bookings"

    # Foreign Keys
    org_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    truck_id: Mapped[UUID] = mapped_column(
        ForeignKey("trucks.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Customer Information (no account required)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    customer_phone: Mapped[str] = mapped_column(String(20), nullable=False)

    # Move Details
    move_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    # Locations
    pickup_address: Mapped[str] = mapped_column(String(512), nullable=False)
    pickup_city: Mapped[str] = mapped_column(String(100), nullable=False)
    pickup_state: Mapped[str] = mapped_column(String(50), nullable=False)
    pickup_zip: Mapped[str] = mapped_column(String(10), nullable=False)

    dropoff_address: Mapped[str] = mapped_column(String(512), nullable=False)
    dropoff_city: Mapped[str] = mapped_column(String(100), nullable=False)
    dropoff_state: Mapped[str] = mapped_column(String(50), nullable=False)
    dropoff_zip: Mapped[str] = mapped_column(String(10), nullable=False)

    # Estimated Metrics
    estimated_distance_miles: Mapped[float] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=False,
    )
    estimated_duration_hours: Mapped[float] = mapped_column(
        Numeric(precision=5, scale=2),
        nullable=False,
    )
    commute_buffer_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=30,
    )

    # Computed Time Windows (for conflict detection)
    # These are computed: effective_start = move_date - commute_buffer
    #                     effective_end = move_date + duration + commute_buffer
    effective_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    effective_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    # Special Items (JSONB for flexibility)
    # Example: ["piano", "antiques", "fragile_items"]
    special_items: Mapped[List[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    # Stairs/Floors
    pickup_floors: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    dropoff_floors: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    has_elevator_pickup: Mapped[bool] = mapped_column(nullable=False, default=False)
    has_elevator_dropoff: Mapped[bool] = mapped_column(nullable=False, default=False)

    # Pricing
    estimated_amount: Mapped[float] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=False,
    )
    final_amount: Mapped[Optional[float]] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=True,
    )

    # Payment
    platform_fee: Mapped[float] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=False,
    )
    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
    )

    # Status
    status: Mapped[BookingStatus] = mapped_column(
        nullable=False,
        default=BookingStatus.PENDING,
        index=True,
    )

    # Notes
    customer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    internal_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    truck: Mapped["Truck"] = relationship("Truck", back_populates="bookings")
    invoice: Mapped[Optional["Invoice"]] = relationship(
        "Invoice", back_populates="booking", uselist=False
    )

    __table_args__ = (
        # CRITICAL: Exclusion constraint prevents double-booking
        # No two bookings for the same truck can have overlapping time windows
        ExcludeConstraint(
            (text("truck_id"), "="),
            (text("tsrange(effective_start, effective_end)"), "&&"),
            name="exclude_overlapping_bookings",
            using="gist",
        ),
        CheckConstraint("estimated_distance_miles > 0", name="positive_distance"),
        CheckConstraint("estimated_duration_hours > 0", name="positive_duration"),
        CheckConstraint("commute_buffer_minutes >= 0", name="non_negative_buffer"),
        CheckConstraint("estimated_amount >= 0", name="non_negative_amount"),
        CheckConstraint(
            "effective_end > effective_start",
            name="valid_time_window",
        ),
        CheckConstraint(
            "status IN ('pending', 'confirmed', 'in_progress', 'completed', 'cancelled')",
            name="valid_status",
        ),
        CheckConstraint("pickup_floors >= 0", name="non_negative_pickup_floors"),
        CheckConstraint("dropoff_floors >= 0", name="non_negative_dropoff_floors"),
        # Composite index for availability queries
        Index("idx_booking_availability", "truck_id", "effective_start", "effective_end"),
    )

    def __repr__(self) -> str:
        return (
            f"<Booking(id={self.id}, customer={self.customer_name}, "
            f"date={self.move_date}, status={self.status})>"
        )
