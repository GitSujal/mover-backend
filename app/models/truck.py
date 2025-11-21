"""Truck model with PostGIS support."""

import enum
from typing import TYPE_CHECKING
from uuid import UUID

from geoalchemy2 import Geography
from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.organization import Organization


class TruckStatus(str, enum.Enum):
    """Truck availability status."""

    AVAILABLE = "available"
    IN_USE = "in_use"
    MAINTENANCE = "maintenance"
    INACTIVE = "inactive"


class TruckSize(str, enum.Enum):
    """Standard truck sizes."""

    SMALL = "small"  # 10-14 ft
    MEDIUM = "medium"  # 15-17 ft
    LARGE = "large"  # 20-24 ft
    XLARGE = "xlarge"  # 26+ ft


class Truck(BaseModel):
    """
    Truck/vehicle for moving services.

    Includes PostGIS geography for location-based queries.
    """

    __tablename__ = "trucks"

    # Foreign Keys
    org_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Vehicle Information
    license_plate: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    make: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(50), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)

    # Capacity
    size: Mapped[TruckSize] = mapped_column(
        SQLEnum(TruckSize, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    capacity_cubic_feet: Mapped[int] = mapped_column(Integer, nullable=False)
    max_weight_lbs: Mapped[int] = mapped_column(Integer, nullable=False)

    # Status
    status: Mapped[TruckStatus] = mapped_column(
        SQLEnum(TruckStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=TruckStatus.AVAILABLE,
        index=True,
    )

    # Location (PostGIS)
    # Stored as geography (lat/long) for accurate distance calculations
    base_location: Mapped[str] = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=False,
    )

    # Registration & Insurance
    registration_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    registration_expiry: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD
    insurance_document_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Photos (4 sides)
    photo_front: Mapped[str | None] = mapped_column(String(512), nullable=True)
    photo_back: Mapped[str | None] = mapped_column(String(512), nullable=True)
    photo_left: Mapped[str | None] = mapped_column(String(512), nullable=True)
    photo_right: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="trucks")
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="truck")

    __table_args__ = (
        CheckConstraint("year >= 1990 AND year <= 2030", name="valid_year"),
        CheckConstraint("capacity_cubic_feet > 0", name="positive_capacity"),
        CheckConstraint("max_weight_lbs > 0", name="positive_weight"),
        CheckConstraint(
            "status IN ('available', 'in_use', 'maintenance', 'inactive')",
            name="valid_status",
        ),
        CheckConstraint(
            "size IN ('small', 'medium', 'large', 'xlarge')",
            name="valid_size",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Truck(id={self.id}, license_plate={self.license_plate}, "
            f"size={self.size}, status={self.status})>"
        )
