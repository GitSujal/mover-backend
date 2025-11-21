"""Rating and Review models for quality tracking."""

import enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.organization import Organization


class RatingCategory(str, enum.Enum):
    """Rating categories for detailed feedback."""

    PROFESSIONALISM = "professionalism"
    PUNCTUALITY = "punctuality"
    CARE_OF_ITEMS = "care_of_items"
    COMMUNICATION = "communication"
    VALUE_FOR_MONEY = "value_for_money"


class Rating(BaseModel):
    """
    Customer rating and review for completed bookings.

    Ratings are immutable once submitted (no edits allowed).
    Used for mover quality tracking and customer decision-making.
    """

    __tablename__ = "ratings"

    # Foreign Keys
    booking_id: Mapped[UUID] = mapped_column(
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One rating per booking
        index=True,
    )
    org_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Overall Rating (1-5 stars)
    overall_rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Category Ratings (1-5 stars each)
    professionalism_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    punctuality_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    care_of_items_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    communication_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    value_for_money_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Review
    review_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_title: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Customer Info (denormalized for display)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Response from Mover
    mover_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    mover_responded_at: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Moderation
    is_published: Mapped[bool] = mapped_column(nullable=False, default=True)
    is_verified_booking: Mapped[bool] = mapped_column(nullable=False, default=True)

    # Relationships
    booking: Mapped["Booking"] = relationship("Booking")
    organization: Mapped["Organization"] = relationship("Organization")

    __table_args__ = (
        CheckConstraint("overall_rating >= 1 AND overall_rating <= 5", name="valid_overall_rating"),
        CheckConstraint(
            "professionalism_rating IS NULL OR (professionalism_rating >= 1 AND professionalism_rating <= 5)",
            name="valid_professionalism_rating",
        ),
        CheckConstraint(
            "punctuality_rating IS NULL OR (punctuality_rating >= 1 AND punctuality_rating <= 5)",
            name="valid_punctuality_rating",
        ),
        CheckConstraint(
            "care_of_items_rating IS NULL OR (care_of_items_rating >= 1 AND care_of_items_rating <= 5)",
            name="valid_care_rating",
        ),
        CheckConstraint(
            "communication_rating IS NULL OR (communication_rating >= 1 AND communication_rating <= 5)",
            name="valid_communication_rating",
        ),
        CheckConstraint(
            "value_for_money_rating IS NULL OR (value_for_money_rating >= 1 AND value_for_money_rating <= 5)",
            name="valid_value_rating",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Rating(id={self.id}, booking_id={self.booking_id}, "
            f"overall={self.overall_rating})>"
        )


class RatingSummary(BaseModel):
    """
    Aggregated rating statistics for an organization.

    Updated via background job after each new rating.
    Denormalized for fast read performance.
    """

    __tablename__ = "rating_summaries"

    # Foreign Key
    org_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Summary Statistics
    total_ratings: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    average_overall_rating: Mapped[float] = mapped_column(nullable=False, default=0.0)

    # Category Averages
    average_professionalism: Mapped[float | None] = mapped_column(nullable=True)
    average_punctuality: Mapped[float | None] = mapped_column(nullable=True)
    average_care_of_items: Mapped[float | None] = mapped_column(nullable=True)
    average_communication: Mapped[float | None] = mapped_column(nullable=True)
    average_value_for_money: Mapped[float | None] = mapped_column(nullable=True)

    # Distribution (count by star rating)
    five_star_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    four_star_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    three_star_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    two_star_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    one_star_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")

    __table_args__ = (
        CheckConstraint("total_ratings >= 0", name="non_negative_total"),
        CheckConstraint(
            "average_overall_rating >= 0 AND average_overall_rating <= 5",
            name="valid_average_rating",
        ),
        CheckConstraint("five_star_count >= 0", name="non_negative_five_star"),
        CheckConstraint("four_star_count >= 0", name="non_negative_four_star"),
        CheckConstraint("three_star_count >= 0", name="non_negative_three_star"),
        CheckConstraint("two_star_count >= 0", name="non_negative_two_star"),
        CheckConstraint("one_star_count >= 0", name="non_negative_one_star"),
    )

    def __repr__(self) -> str:
        return (
            f"<RatingSummary(org_id={self.org_id}, avg={self.average_overall_rating:.2f}, "
            f"count={self.total_ratings})>"
        )
