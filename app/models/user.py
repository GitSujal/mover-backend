"""User and authentication models."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.organization import Organization


class UserRole(str, enum.Enum):
    """User roles for authorization."""

    ADMIN = "admin"  # Platform admin
    ORG_OWNER = "org_owner"  # Organization owner
    ORG_MANAGER = "org_manager"  # Can manage org resources
    ORG_STAFF = "org_staff"  # Read-only access


class User(BaseModel):
    """
    User account for mover organizations.

    Uses JWT authentication with email/password.
    """

    __tablename__ = "users"

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
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Authentication
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # Role
    role: Mapped[UserRole] = mapped_column(
        nullable=False,
        default=UserRole.ORG_STAFF,
        index=True,
    )

    # 2FA (optional)
    has_2fa_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    totp_secret: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    # Last Login
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="users")

    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'org_owner', 'org_manager', 'org_staff')",
            name="valid_role",
        ),
        UniqueConstraint("email", name="uq_user_email"),
    )

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"


class CustomerSession(BaseModel):
    """
    Customer session for OTP-based authentication.

    Customers don't need accounts - they authenticate via email/phone OTP.
    Sessions are stored in Redis with TTL for performance.
    """

    __tablename__ = "customer_sessions"

    # Session Token (used in cookies)
    session_token: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        unique=True,
        index=True,
    )

    # Customer Identifier (email or phone)
    identifier: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    identifier_type: Mapped[str] = mapped_column(String(10), nullable=False)  # 'email' or 'phone'

    # OTP for verification
    otp_code: Mapped[Optional[str]] = mapped_column(String(6), nullable=True)
    otp_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Session Status
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    # Expiry
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    # Last Activity
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="NOW()",
    )

    __table_args__ = (
        CheckConstraint(
            "identifier_type IN ('email', 'phone')",
            name="valid_identifier_type",
        ),
        CheckConstraint(
            "expires_at > created_at",
            name="valid_expiry",
        ),
    )

    @property
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.utcnow() > self.expires_at

    @property
    def is_otp_valid(self) -> bool:
        """Check if OTP is still valid."""
        if not self.otp_expires_at:
            return False
        return datetime.utcnow() < self.otp_expires_at

    def __repr__(self) -> str:
        return (
            f"<CustomerSession(id={self.id}, identifier={self.identifier}, "
            f"verified={self.is_verified})>"
        )
