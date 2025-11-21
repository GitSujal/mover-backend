"""Truck schemas."""

from uuid import UUID

from pydantic import Field

from app.models.truck import TruckSize, TruckStatus
from app.schemas.base import BaseSchema, ResourceResponse


class LocationInput(BaseSchema):
    """Geographic location input."""

    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class TruckBase(BaseSchema):
    """Base truck schema."""

    license_plate: str = Field(..., min_length=1, max_length=20, description="License plate number")
    make: str = Field(..., min_length=1, max_length=50)
    model: str = Field(..., min_length=1, max_length=50)
    year: int = Field(..., ge=1990, le=2030)
    size: TruckSize
    capacity_cubic_feet: int = Field(..., gt=0)
    max_weight_lbs: int = Field(..., gt=0)
    registration_number: str = Field(..., min_length=1, max_length=50)
    registration_expiry: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")


class TruckCreate(TruckBase):
    """Schema for creating a truck."""

    base_location: LocationInput = Field(..., description="Base location (lat, long)")
    insurance_document_url: str | None = Field(None, max_length=512)
    photo_front: str | None = Field(None, max_length=512)
    photo_back: str | None = Field(None, max_length=512)
    photo_left: str | None = Field(None, max_length=512)
    photo_right: str | None = Field(None, max_length=512)


class TruckUpdate(BaseSchema):
    """Schema for updating a truck."""

    license_plate: str | None = Field(None, min_length=1, max_length=20)
    status: TruckStatus | None = None
    base_location: LocationInput | None = None
    registration_expiry: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    insurance_document_url: str | None = Field(None, max_length=512)
    photo_front: str | None = Field(None, max_length=512)
    photo_back: str | None = Field(None, max_length=512)
    photo_left: str | None = Field(None, max_length=512)
    photo_right: str | None = Field(None, max_length=512)


class TruckResponse(TruckBase, ResourceResponse):
    """Schema for truck response."""

    id: UUID
    org_id: UUID
    status: TruckStatus
    base_location_lat: float = Field(..., description="Base latitude")
    base_location_lng: float = Field(..., description="Base longitude")
    insurance_document_url: str | None = None
    photo_front: str | None = None
    photo_back: str | None = None
    photo_left: str | None = None
    photo_right: str | None = None
