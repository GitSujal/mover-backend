"""
FastAPI dependencies for authentication and authorization.

Provides JWT validation for movers and session validation for customers.
"""

import logging
from uuid import UUID

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, set_rls_context
from app.core.security import verify_token
from app.models.organization import Organization, OrganizationStatus
from app.models.user import CustomerSession, User, UserRole
from app.services.redis_cache import RedisCache

logger = logging.getLogger(__name__)

# Security schemes
security = HTTPBearer()
redis_cache = RedisCache()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency to get current authenticated user (mover).

    Validates JWT token and returns user object.
    Sets RLS context for multi-tenant isolation.
    """
    token = credentials.credentials
    user_id = verify_token(token, token_type="access")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    stmt = select(User).where(User.id == UUID(user_id))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Set RLS context for this request
    await set_rls_context(db, org_id=str(user.org_id), user_id=str(user.id))

    logger.info(f"User authenticated: {user.email}", extra={"user_id": str(user.id)})

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency to ensure user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """
    Optional dependency to get current authenticated user.

    Returns None if no credentials provided instead of raising an error.
    """
    if not credentials:
        return None

    token = credentials.credentials
    user_id = verify_token(token, token_type="access")

    if not user_id:
        return None

    # Get user from database
    stmt = select(User).where(User.id == UUID(user_id))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        return None

    # Set RLS context for this request
    await set_rls_context(db, org_id=str(user.org_id), user_id=str(user.id))

    return user


async def require_role(
    required_role: UserRole,
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Dependency factory to require specific user role.

    Args:
        required_role: Minimum required role

    Returns:
        Dependency function
    """
    # Role hierarchy: admin > org_owner > org_manager > org_staff
    role_hierarchy = {
        UserRole.ADMIN: 4,
        UserRole.ORG_OWNER: 3,
        UserRole.ORG_MANAGER: 2,
        UserRole.ORG_STAFF: 1,
    }

    user_level = role_hierarchy.get(current_user.role, 0)
    required_level = role_hierarchy.get(required_role, 0)

    if user_level < required_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required role: {required_role}",
        )

    return current_user


async def get_current_customer_session(
    session_token: str | None = Cookie(None),
    db: AsyncSession = Depends(get_db),
) -> CustomerSession | None:
    """
    Dependency to get current customer session.

    Validates session token from cookie and returns customer session.
    Returns None if no session token provided (for optional authentication).
    """
    if not session_token:
        return None

    # Check Redis cache first
    cached_session = await redis_cache.get_customer_session(session_token)
    if cached_session:
        return cached_session

    # Fallback to database
    stmt = select(CustomerSession).where(
        CustomerSession.session_token == session_token,
        CustomerSession.is_verified == True,  # noqa: E712
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    if session.is_expired:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired",
        )

    # Cache session in Redis
    await redis_cache.cache_customer_session(session)

    logger.info(
        f"Customer session validated: {session.identifier}",
        extra={"session_id": str(session.id)},
    )

    return session


async def get_organization(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Organization:
    """
    Dependency to get organization with access check.

    Ensures user has access to the requested organization.
    """
    # Verify user belongs to the organization
    if current_user.org_id != org_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this organization",
        )

    stmt = select(Organization).where(Organization.id == org_id)
    result = await db.execute(stmt)
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    return org


async def require_approved_organization(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Organization:
    """
    Dependency to ensure organization is approved.

    Only approved organizations can perform booking operations.
    """
    org = await get_organization(org_id, db, current_user)

    if org.status != OrganizationStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Organization must be approved. Current status: {org.status}",
        )

    return org
