"""Driver model."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.organization import Organization


class Driver(BaseModel):
    """
    Verified driver for moving companies.

    All drivers must have valid licenses and background checks.
    """

    __tablename__ = "drivers"

    # Foreign Keys
    org_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Personal Information
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)

    # License Information
    drivers_license_number: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    drivers_license_state: Mapped[str] = mapped_column(String(2), nullable=False)
    drivers_license_expiry: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD

    # Commercial Driver's License (CDL)
    has_cdl: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cdl_class: Mapped[str | None] = mapped_column(String(10), nullable=True)  # A, B, C

    # Verification
    is_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    background_check_completed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    # Documents
    photo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    license_front_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    license_back_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="drivers")

    __table_args__ = (
        CheckConstraint(
            "LENGTH(drivers_license_state) = 2",
            name="valid_state_code",
        ),
        CheckConstraint(
            "(has_cdl = false) OR (has_cdl = true AND cdl_class IS NOT NULL)",
            name="cdl_requires_class",
        ),
    )

    @property
    def full_name(self) -> str:
        """Get driver's full name."""
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return (
            f"<Driver(id={self.id}, name={self.full_name}, "
            f"verified={self.is_verified})>"
        )
