"""Pydantic schemas for rating and review system."""

from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema


class RatingCreate(BaseSchema):
    """Schema for creating a new rating."""

    booking_id: UUID
    overall_rating: int = Field(ge=1, le=5, description="Overall rating from 1-5 stars")

    # Optional category ratings
    professionalism_rating: int | None = Field(None, ge=1, le=5)
    punctuality_rating: int | None = Field(None, ge=1, le=5)
    care_of_items_rating: int | None = Field(None, ge=1, le=5)
    communication_rating: int | None = Field(None, ge=1, le=5)
    value_for_money_rating: int | None = Field(None, ge=1, le=5)

    # Review content
    review_text: str | None = Field(None, max_length=2000)
    review_title: str | None = Field(None, max_length=200)

    @field_validator("review_text")
    @classmethod
    def validate_review_text(cls, v: str | None) -> str | None:
        """Validate review text is not just whitespace."""
        if v and not v.strip():
            raise ValueError("Review text cannot be empty or just whitespace")
        return v.strip() if v else None


class RatingUpdate(BaseSchema):
    """Schema for mover response to rating."""

    mover_response: str = Field(max_length=1000, description="Mover's response to the review")

    @field_validator("mover_response")
    @classmethod
    def validate_response(cls, v: str) -> str:
        """Validate response is not empty."""
        if not v.strip():
            raise ValueError("Response cannot be empty")
        return v.strip()


class RatingResponse(BaseSchema):
    """Schema for rating response."""

    id: UUID
    booking_id: UUID
    org_id: UUID

    overall_rating: int
    professionalism_rating: int | None
    punctuality_rating: int | None
    care_of_items_rating: int | None
    communication_rating: int | None
    value_for_money_rating: int | None

    review_text: str | None
    review_title: str | None
    customer_name: str

    mover_response: str | None
    mover_responded_at: str | None

    is_published: bool
    is_verified_booking: bool

    created_at: datetime
    updated_at: datetime


class RatingSummaryResponse(BaseSchema):
    """Schema for rating summary statistics."""

    org_id: UUID
    total_ratings: int
    average_overall_rating: float

    # Category averages
    average_professionalism: float | None
    average_punctuality: float | None
    average_care_of_items: float | None
    average_communication: float | None
    average_value_for_money: float | None

    # Star distribution
    five_star_count: int
    four_star_count: int
    three_star_count: int
    two_star_count: int
    one_star_count: int

    created_at: datetime
    updated_at: datetime


class RatingListResponse(BaseSchema):
    """Schema for paginated rating list."""

    ratings: list[RatingResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class RatingStatsResponse(BaseSchema):
    """Schema for detailed rating statistics for an organization."""

    org_id: UUID
    summary: RatingSummaryResponse
    recent_ratings: list[RatingResponse]

    # Additional computed stats
    rating_trend: str  # "improving", "stable", "declining"
    response_rate: float  # Percentage of ratings with mover responses
    average_response_time_hours: float | None  # Average time to respond
