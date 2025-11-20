"""Pydantic schemas for API requests and responses."""

from app.schemas.booking import (
    BookingCreate,
    BookingResponse,
    BookingUpdate,
    AvailabilityCheck,
    AvailabilityResponse,
)
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)
from app.schemas.pricing import PricingConfigCreate, PricingConfigResponse, PriceEstimate
from app.schemas.truck import TruckCreate, TruckResponse, TruckUpdate
from app.schemas.driver import DriverCreate, DriverResponse, DriverUpdate
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    TokenResponse,
    CustomerOTPRequest,
    CustomerOTPVerify,
)

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
