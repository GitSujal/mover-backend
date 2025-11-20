"""
Security utilities for authentication and authorization.
Handles JWT tokens, password hashing, and API key validation.
"""

import secrets
from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password
        hashed_password: Bcrypt hashed password

    Returns:
        bool: True if password matches
    """
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)


def create_access_token(
    subject: str,
    additional_claims: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        subject: Token subject (usually user_id)
        additional_claims: Additional claims to include
        expires_delta: Token expiration time (defaults to settings)

    Returns:
        str: Encoded JWT token
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.utcnow() + expires_delta

    to_encode = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
    }

    if additional_claims:
        to_encode.update(additional_claims)

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    return encoded_jwt


def create_refresh_token(subject: str) -> str:
    """
    Create a JWT refresh token.

    Args:
        subject: Token subject (usually user_id)

    Returns:
        str: Encoded JWT token
    """
    expires_delta = timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    expire = datetime.utcnow() + expires_delta

    to_encode = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    return encoded_jwt


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        Dict[str, Any]: Decoded token payload

    Raises:
        JWTError: If token is invalid or expired
    """
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )

    return payload


def verify_token(token: str, token_type: str = "access") -> str | None:
    """
    Verify a JWT token and return the subject.

    Args:
        token: JWT token string
        token_type: Expected token type ("access" or "refresh")

    Returns:
        Optional[str]: Token subject (user_id) if valid, None otherwise
    """
    try:
        payload = decode_token(token)

        # Verify token type
        if payload.get("type") != token_type:
            return None

        # Get subject
        subject: str = payload.get("sub")
        if subject is None:
            return None

        return subject

    except JWTError:
        return None


def generate_otp() -> str:
    """
    Generate a secure 6-digit OTP for customer authentication.

    Returns:
        str: 6-digit OTP
    """
    return f"{secrets.randbelow(1000000):06d}"


def generate_api_key() -> str:
    """
    Generate a secure API key.

    Returns:
        str: 32-character API key
    """
    return secrets.token_urlsafe(32)


def generate_session_token() -> str:
    """
    Generate a secure session token for customer sessions.

    Returns:
        str: Session token
    """
    return secrets.token_urlsafe(64)
