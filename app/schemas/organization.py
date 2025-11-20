"""Organization schemas."""

from uuid import UUID

from pydantic import EmailStr, Field

from app.models.organization import OrganizationStatus
from app.schemas.base import BaseSchema, ResourceResponse


class OrganizationBase(BaseSchema):
    """Base organization schema."""

    name: str = Field(..., min_length=1, max_length=255, description="Company name")
    email: EmailStr = Field(..., description="Company email")
    phone: str = Field(..., pattern=r"^\+?1?\d{9,15}$", description="Company phone number")
    business_license_number: str = Field(..., min_length=1, max_length=100)
    tax_id: str = Field(..., min_length=1, max_length=50)
    address_line1: str = Field(..., min_length=1, max_length=255)
    address_line2: str | None = Field(None, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=2, max_length=50)
    zip_code: str = Field(..., pattern=r"^\d{5}(-\d{4})?$")


class OrganizationCreate(OrganizationBase):
    """Schema for creating an organization."""

    pass


class OrganizationUpdate(BaseSchema):
    """Schema for updating an organization."""

    name: str | None = Field(None, min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(None, pattern=r"^\+?1?\d{9,15}$")
    address_line1: str | None = Field(None, min_length=1, max_length=255)
    address_line2: str | None = Field(None, max_length=255)
    city: str | None = Field(None, min_length=1, max_length=100)
    state: str | None = Field(None, min_length=2, max_length=50)
    zip_code: str | None = Field(None, pattern=r"^\d{5}(-\d{4})?$")


class OrganizationResponse(OrganizationBase, ResourceResponse):
    """Schema for organization response."""

    id: UUID
    status: OrganizationStatus
    stripe_account_id: str | None = None
