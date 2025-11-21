"""Booking status transition schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.booking import BookingStatus


class StatusTransitionRequest(BaseModel):
    """Request to transition booking to new status."""

    new_status: BookingStatus = Field(description="Target status")
    notes: str | None = Field(
        None,
        description="Optional notes about status change",
        max_length=1000,
    )


class StatusTransitionResponse(BaseModel):
    """Response after status transition."""

    booking_id: UUID
    old_status: BookingStatus
    new_status: BookingStatus
    transitioned_at: datetime
    transitioned_by: str
    notes: str | None

    class Config:
        from_attributes = True


class StatusHistoryEntry(BaseModel):
    """Single status transition history entry."""

    id: UUID
    booking_id: UUID
    from_status: BookingStatus
    to_status: BookingStatus
    transitioned_at: datetime
    transitioned_by_id: UUID | None
    transitioned_by_name: str
    notes: str | None

    class Config:
        from_attributes = True


class StatusHistoryResponse(BaseModel):
    """Complete status history for a booking."""

    booking_id: UUID
    current_status: BookingStatus
    history: list[StatusHistoryEntry]
