"""Insurance policy model."""

import enum
from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.organization import Organization


class InsuranceType(str, enum.Enum):
    """Types of insurance coverage."""

    LIABILITY = "liability"
    CARGO = "cargo"
    WORKERS_COMP = "workers_comp"
    AUTO = "auto"


class InsurancePolicy(BaseModel):
    """
    Insurance policy for moving companies.

    Each organization must maintain valid insurance to operate.
    """

    __tablename__ = "insurance_policies"

    # Foreign Keys
    org_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Policy Details
    policy_type: Mapped[InsuranceType] = mapped_column(
        SQLEnum(InsuranceType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    policy_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    provider: Mapped[str] = mapped_column(String(255), nullable=False)

    # Coverage
    coverage_amount: Mapped[float] = mapped_column(Numeric(precision=12, scale=2), nullable=False)

    # Validity
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Documentation
    document_url: Mapped[str] = mapped_column(String(512), nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="insurance_policies"
    )

    __table_args__ = (
        CheckConstraint("coverage_amount > 0", name="positive_coverage"),
        CheckConstraint("expiry_date > effective_date", name="valid_date_range"),
        CheckConstraint(
            "policy_type IN ('liability', 'cargo', 'workers_comp', 'auto')",
            name="valid_policy_type",
        ),
        UniqueConstraint("org_id", "policy_type", name="uq_org_policy_type"),
    )

    @property
    def is_active(self) -> bool:
        """Check if policy is currently active."""
        from datetime import date

        return self.effective_date <= date.today() <= self.expiry_date

    def __repr__(self) -> str:
        return (
            f"<InsurancePolicy(id={self.id}, type={self.policy_type}, expiry={self.expiry_date})>"
        )
