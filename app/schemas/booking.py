"""Booking schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from app.models.booking import BookingStatus
from app.schemas.base import BaseSchema, ResourceResponse


class BookingBase(BaseSchema):
    """Base booking schema."""

    customer_name: str = Field(..., min_length=1, max_length=255)
    customer_email: EmailStr
    customer_phone: str = Field(..., pattern=r"^\+?1?\d{9,15}$")
    move_date: datetime = Field(..., description="Requested move date and time")
    pickup_address: str = Field(..., min_length=1, max_length=512)
    pickup_city: str = Field(..., min_length=1, max_length=100)
    pickup_state: str = Field(..., min_length=2, max_length=50)
    pickup_zip: str = Field(..., pattern=r"^\d{5}(-\d{4})?$")
    dropoff_address: str = Field(..., min_length=1, max_length=512)
    dropoff_city: str = Field(..., min_length=1, max_length=100)
    dropoff_state: str = Field(..., min_length=2, max_length=50)
    dropoff_zip: str = Field(..., pattern=r"^\d{5}(-\d{4})?$")
    estimated_distance_miles: float = Field(..., gt=0)
    estimated_duration_hours: float = Field(..., gt=0, le=24)
    special_items: list[str] = Field(default_factory=list)
    pickup_floors: int = Field(default=0, ge=0, le=100)
    dropoff_floors: int = Field(default=0, ge=0, le=100)
    has_elevator_pickup: bool = False
    has_elevator_dropoff: bool = False
    customer_notes: str | None = Field(None, max_length=2000)

    @field_validator("move_date")
    @classmethod
    def validate_move_date(cls, v: datetime) -> datetime:
        """Validate move date is in the future."""
        if v < datetime.now():
            raise ValueError("Move date must be in the future")
        return v


class BookingCreate(BookingBase):
    """Schema for creating a booking."""

    truck_id: UUID
    org_id: UUID


class BookingUpdate(BaseSchema):
    """Schema for updating a booking."""

    move_date: datetime | None = None
    status: BookingStatus | None = None
    final_amount: float | None = Field(None, ge=0)
    internal_notes: str | None = Field(None, max_length=2000)


class BookingResponse(BookingBase, ResourceResponse):
    """Schema for booking response."""

    id: UUID
    org_id: UUID
    truck_id: UUID
    commute_buffer_minutes: int
    effective_start: datetime
    effective_end: datetime
    estimated_amount: float
    final_amount: float | None = None
    platform_fee: float
    stripe_payment_intent_id: str | None = None
    status: BookingStatus
    internal_notes: str | None = None


class AvailabilityCheck(BaseSchema):
    """Schema for checking truck availability."""

    truck_id: UUID
    move_date: datetime
    estimated_duration_hours: float = Field(..., gt=0, le=24)
    commute_buffer_minutes: int = Field(default=30, ge=0, le=120)


class AvailabilitySlot(BaseSchema):
    """Available time slot."""

    start: datetime
    end: datetime


class AvailabilityResponse(BaseSchema):
    """Schema for availability response."""

    truck_id: UUID
    is_available: bool
    requested_start: datetime
    requested_end: datetime
    conflicts: list[BookingResponse] = Field(default_factory=list)
    suggested_slots: list[AvailabilitySlot] = Field(default_factory=list)
