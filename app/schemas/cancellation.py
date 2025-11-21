"""Booking cancellation schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.cancellation import CancellationSource, RefundStatus


class CancellationRequest(BaseModel):
    """Request to cancel a booking."""

    reason: str = Field(
        description="Reason for cancellation",
        min_length=10,
        max_length=1000,
    )
    cancelled_by: CancellationSource = Field(description="Who is initiating the cancellation")


class CancellationResponse(BaseModel):
    """Response after cancellation."""

    id: UUID
    booking_id: UUID
    cancelled_by: CancellationSource
    cancelled_at: datetime
    cancellation_reason: str
    hours_before_move: float
    original_amount: float
    refund_amount: float
    refund_percentage: float
    refund_status: RefundStatus
    refund_reason: str | None
    stripe_refund_id: str | None
    customer_email: str
    rebook_offered: bool

    class Config:
        from_attributes = True

    @property
    def is_full_refund(self) -> bool:
        """Check if this is a full refund."""
        return self.refund_amount == self.original_amount

    @property
    def is_partial_refund(self) -> bool:
        """Check if this is a partial refund."""
        return 0 < self.refund_amount < self.original_amount

    @property
    def is_no_refund(self) -> bool:
        """Check if no refund is given."""
        return self.refund_amount == 0


class RefundPolicyInfo(BaseModel):
    """Information about refund policy for given timing."""

    hours_before_move: float
    refund_percentage: int
    refund_amount: float
    policy_tier: str  # 'full', 'partial_75', 'partial_50', 'none'
    cancellation_fee: float


class CancellationListResponse(BaseModel):
    """List of cancellations."""

    cancellations: list[CancellationResponse]
    total: int
    page: int
    page_size: int
