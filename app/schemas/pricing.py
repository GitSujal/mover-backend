"""Pricing schemas."""

from typing import Any, Literal
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, ResourceResponse


class SurchargeRule(BaseSchema):
    """Surcharge rule for pricing calculations."""

    type: Literal[
        "stairs", "piano", "weekend", "holiday", "after_hours", "fragile", "distance", "custom"
    ]
    amount: float | None = Field(None, ge=0, description="Flat fee amount")
    multiplier: float | None = Field(None, gt=0, description="Price multiplier")
    per_flight: bool | None = Field(None, description="Apply per flight of stairs")
    min_time: str | None = Field(None, pattern=r"^\d{2}:\d{2}$", description="Start time (HH:MM)")
    max_time: str | None = Field(None, pattern=r"^\d{2}:\d{2}$", description="End time (HH:MM)")
    days: list[int] | None = Field(None, description="Days of week (0=Sunday, 6=Saturday)")
    description: str | None = Field(None, max_length=255)

    @field_validator("days")
    @classmethod
    def validate_days(cls, v: list[int] | None) -> list[int] | None:
        """Validate days are in range 0-6."""
        if v is not None:
            if not all(0 <= day <= 6 for day in v):
                raise ValueError("Days must be between 0 (Sunday) and 6 (Saturday)")
        return v


class PricingConfigBase(BaseSchema):
    """Base pricing configuration schema."""

    base_hourly_rate: float = Field(..., gt=0, description="Base hourly rate in USD")
    base_mileage_rate: float = Field(..., ge=0, description="Base mileage rate per mile in USD")
    minimum_charge: float = Field(..., ge=0, description="Minimum charge in USD")
    surcharge_rules: list[SurchargeRule] = Field(
        default_factory=list, description="List of surcharge rules"
    )


class PricingConfigCreate(PricingConfigBase):
    """Schema for creating pricing configuration."""

    pass


class PricingConfigResponse(PricingConfigBase, ResourceResponse):
    """Schema for pricing configuration response."""

    id: UUID
    org_id: UUID
    is_active: bool


class PriceBreakdown(BaseSchema):
    """Detailed price breakdown."""

    base_hourly_cost: float = Field(..., description="Cost from hourly rate")
    base_mileage_cost: float = Field(..., description="Cost from mileage")
    surcharges: list[dict[str, Any]] = Field(
        default_factory=list, description="Applied surcharges with details"
    )
    subtotal: float = Field(..., description="Subtotal before minimum")
    minimum_applied: bool = Field(..., description="Whether minimum charge was applied")
    total: float = Field(..., description="Final total amount")


class PriceEstimate(BaseSchema):
    """Price estimate for a booking."""

    estimated_amount: float = Field(..., ge=0, description="Total estimated amount")
    platform_fee: float = Field(..., ge=0, description="Platform fee (5%)")
    breakdown: PriceBreakdown = Field(..., description="Detailed price breakdown")
