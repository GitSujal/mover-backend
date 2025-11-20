"""
Base model classes with common fields and mixins.
All models inherit from these to ensure consistency.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDMixin:
    """Mixin for UUID primary key."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )


class BaseModel(Base, UUIDMixin, TimestampMixin):
    """
    Base model class with UUID primary key and timestamps.
    All application models should inherit from this.
    """

    __abstract__ = True

    def __repr__(self) -> str:
        """String representation of the model."""
        columns = ", ".join(
            [f"{col.name}={getattr(self, col.name)!r}" for col in self.__table__.columns]
        )
        return f"{self.__class__.__name__}({columns})"

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}
