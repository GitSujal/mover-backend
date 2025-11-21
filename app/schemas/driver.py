"""Driver schemas."""

from uuid import UUID

from pydantic import EmailStr, Field

from app.schemas.base import BaseSchema, ResourceResponse


class DriverBase(BaseSchema):
    """Base driver schema."""

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str = Field(..., pattern=r"^\+?1?\d{9,15}$")
    drivers_license_number: str = Field(..., min_length=1, max_length=50)
    drivers_license_state: str = Field(..., min_length=2, max_length=2)
    drivers_license_expiry: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    has_cdl: bool = False
    cdl_class: str | None = Field(None, pattern=r"^[ABC]$")


class DriverCreate(DriverBase):
    """Schema for creating a driver."""

    photo_url: str | None = Field(None, max_length=512)
    license_front_url: str | None = Field(None, max_length=512)
    license_back_url: str | None = Field(None, max_length=512)


class DriverUpdate(BaseSchema):
    """Schema for updating a driver."""

    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(None, pattern=r"^\+?1?\d{9,15}$")
    drivers_license_expiry: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    photo_url: str | None = Field(None, max_length=512)
    license_front_url: str | None = Field(None, max_length=512)
    license_back_url: str | None = Field(None, max_length=512)


class DriverResponse(DriverBase, ResourceResponse):
    """Schema for driver response."""

    id: UUID
    org_id: UUID
    is_verified: bool
    background_check_completed: bool
    photo_url: str | None = None
    license_front_url: str | None = None
    license_back_url: str | None = None
    full_name: str
