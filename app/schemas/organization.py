"""Organization schemas."""

from typing import Optional
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

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
    address_line2: Optional[str] = Field(None, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=2, max_length=50)
    zip_code: str = Field(..., pattern=r"^\d{5}(-\d{4})?$")


class OrganizationCreate(OrganizationBase):
    """Schema for creating an organization."""

    pass


class OrganizationUpdate(BaseSchema):
    """Schema for updating an organization."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r"^\+?1?\d{9,15}$")
    address_line1: Optional[str] = Field(None, min_length=1, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    state: Optional[str] = Field(None, min_length=2, max_length=50)
    zip_code: Optional[str] = Field(None, pattern=r"^\d{5}(-\d{4})?$")


class OrganizationResponse(OrganizationBase, ResourceResponse):
    """Schema for organization response."""

    id: UUID
    status: OrganizationStatus
    stripe_account_id: Optional[str] = None
