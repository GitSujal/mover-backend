"""Pydantic schemas for API requests and responses."""

from app.schemas.auth import (
    CustomerOTPRequest,
    CustomerOTPVerify,
    TokenResponse,
    UserCreate,
    UserLogin,
)
from app.schemas.booking import (
    AvailabilityCheck,
    AvailabilityResponse,
    BookingCreate,
    BookingResponse,
    BookingUpdate,
)
from app.schemas.driver import DriverCreate, DriverResponse, DriverUpdate
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)
from app.schemas.pricing import PriceEstimate, PricingConfigCreate, PricingConfigResponse
from app.schemas.truck import TruckCreate, TruckResponse, TruckUpdate

__all__ = [
    # Booking
    "BookingCreate",
    "BookingResponse",
    "BookingUpdate",
    "AvailabilityCheck",
    "AvailabilityResponse",
    # Organization
    "OrganizationCreate",
    "OrganizationResponse",
    "OrganizationUpdate",
    # Pricing
    "PricingConfigCreate",
    "PricingConfigResponse",
    "PriceEstimate",
    # Truck
    "TruckCreate",
    "TruckResponse",
    "TruckUpdate",
    # Driver
    "DriverCreate",
    "DriverResponse",
    "DriverUpdate",
    # Auth
    "UserCreate",
    "UserLogin",
    "TokenResponse",
    "CustomerOTPRequest",
    "CustomerOTPVerify",
]
