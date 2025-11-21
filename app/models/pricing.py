"""Pricing configuration model."""

from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.organization import Organization


class PricingConfig(BaseModel):
    """
    Extensible pricing configuration per organization.

    Uses JSONB for flexible surcharge rules that can evolve without schema changes.
    Rules are validated at the application layer using Pydantic schemas.
    """

    __tablename__ = "pricing_configs"

    # Foreign Keys
    org_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Base Rates
    base_hourly_rate: Mapped[float] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=False,
    )
    base_mileage_rate: Mapped[float] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=False,
    )
    minimum_charge: Mapped[float] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=False,
    )

    # Surcharge Rules (JSONB for flexibility)
    # Example structure:
    # [
    #   {
    #     "type": "stairs",
    #     "amount": 50.00,
    #     "per_flight": true
    #   },
    #   {
    #     "type": "weekend",
    #     "multiplier": 1.25,
    #     "days": [0, 6]
    #   }
    # ]
    surcharge_rules: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    # Active Status (only one active config per org)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="pricing_configs"
    )

    __table_args__ = (
        CheckConstraint("base_hourly_rate > 0", name="positive_hourly_rate"),
        CheckConstraint("base_mileage_rate >= 0", name="non_negative_mileage_rate"),
        CheckConstraint("minimum_charge >= 0", name="non_negative_minimum"),
    )

    def __repr__(self) -> str:
        return f"<PricingConfig(id={self.id}, org_id={self.org_id}, active={self.is_active})>"
