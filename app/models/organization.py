"""Organization model for moving companies."""

import enum
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.driver import Driver
    from app.models.insurance import InsurancePolicy
    from app.models.pricing import PricingConfig
    from app.models.truck import Truck
    from app.models.user import User


class OrganizationStatus(str, enum.Enum):
    """Organization verification status."""

    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    SUSPENDED = "suspended"
    REJECTED = "rejected"


class Organization(BaseModel):
    """
    Moving company organization.

    Multi-tenant isolation: All org-scoped data references this table.
    RLS Policy: Users can only access orgs they belong to.
    """

    __tablename__ = "organizations"

    # Basic Information
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)

    # Business Information
    business_license_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    tax_id: Mapped[str] = mapped_column(String(50), nullable=False)

    # Address
    address_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(50), nullable=False)
    zip_code: Mapped[str] = mapped_column(String(10), nullable=False)

    # Verification
    status: Mapped[OrganizationStatus] = mapped_column(
        nullable=False,
        default=OrganizationStatus.PENDING_REVIEW,
        index=True,
    )

    # Stripe Connect for payments
    stripe_account_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)

    # Relationships
    users: Mapped[list["User"]] = relationship("User", back_populates="organization")
    trucks: Mapped[list["Truck"]] = relationship(
        "Truck", back_populates="organization", cascade="all, delete-orphan"
    )
    drivers: Mapped[list["Driver"]] = relationship(
        "Driver", back_populates="organization", cascade="all, delete-orphan"
    )
    insurance_policies: Mapped[list["InsurancePolicy"]] = relationship(
        "InsurancePolicy", back_populates="organization", cascade="all, delete-orphan"
    )
    pricing_configs: Mapped[list["PricingConfig"]] = relationship(
        "PricingConfig", back_populates="organization", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending_review', 'approved', 'suspended', 'rejected')",
            name="valid_status",
        ),
        UniqueConstraint("email", name="uq_organization_email"),
        UniqueConstraint("business_license_number", name="uq_business_license"),
    )

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name={self.name}, status={self.status})>"
