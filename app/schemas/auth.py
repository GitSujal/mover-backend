"""Authentication schemas."""

from pydantic import EmailStr, Field

from app.models.user import UserRole
from app.schemas.base import BaseSchema


class UserCreate(BaseSchema):
    """Schema for creating a user."""

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str | None = Field(None, pattern=r"^\+?1?\d{9,15}$")
    password: str = Field(..., min_length=8, max_length=100)
    role: UserRole = UserRole.ORG_STAFF


class UserLogin(BaseSchema):
    """Schema for user login."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseSchema):
    """Schema for JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token expiry in seconds")


class CustomerOTPRequest(BaseSchema):
    """Schema for requesting customer OTP."""

    identifier: str = Field(..., description="Email or phone number")
    identifier_type: str = Field(..., pattern=r"^(email|phone)$")


class CustomerOTPVerify(BaseSchema):
    """Schema for verifying customer OTP."""

    session_token: str = Field(..., min_length=1)
    otp_code: str = Field(..., pattern=r"^\d{6}$", description="6-digit OTP code")
