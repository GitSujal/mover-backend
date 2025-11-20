"""Authentication routes for movers and customers."""

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_otp,
    generate_session_token,
    hash_password,
    verify_password,
)
from app.models.user import CustomerSession, User
from app.schemas.auth import (
    CustomerOTPRequest,
    CustomerOTPVerify,
    TokenResponse,
    UserCreate,
    UserLogin,
)
from app.services.notifications import NotificationService
from app.services.redis_cache import RedisCache

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

notification_service = NotificationService()
redis_cache = RedisCache()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Register a new user (mover organization staff).

    Requires organization to be created first.
    """
    # Check if email already exists
    stmt = select(User).where(User.email == user_data.email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    user = User(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        email=user_data.email,
        phone=user_data.phone,
        hashed_password=hash_password(user_data.password),
        role=user_data.role,
        org_id=user_data.org_id,  # type: ignore
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Generate tokens
    access_token = create_access_token(
        str(user.id),
        additional_claims={"org_id": str(user.org_id), "role": user.role},
    )
    refresh_token = create_refresh_token(str(user.id))

    logger.info(f"User registered: {user.email}", extra={"user_id": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=15 * 60,  # 15 minutes
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Login for mover organization users.

    Returns JWT access and refresh tokens.
    """
    # Get user by email
    stmt = select(User).where(User.email == credentials.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    # Update last login
    user.last_login_at = datetime.utcnow()
    await db.commit()

    # Generate tokens
    access_token = create_access_token(
        str(user.id),
        additional_claims={"org_id": str(user.org_id), "role": user.role},
    )
    refresh_token = create_refresh_token(str(user.id))

    logger.info(f"User logged in: {user.email}", extra={"user_id": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=15 * 60,
    )


@router.post("/customer/request-otp", status_code=status.HTTP_200_OK)
async def request_customer_otp(
    request: CustomerOTPRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Request OTP for customer authentication (no account needed).

    Sends OTP via email or SMS.
    """
    # Generate OTP
    otp_code = generate_otp()

    # Create or update customer session
    stmt = select(CustomerSession).where(
        CustomerSession.identifier == request.identifier,
        CustomerSession.identifier_type == request.identifier_type,
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    session_token = generate_session_token()
    otp_expires_at = datetime.utcnow() + timedelta(minutes=10)
    expires_at = datetime.utcnow() + timedelta(hours=24)

    if session:
        # Update existing session
        session.session_token = session_token
        session.otp_code = otp_code
        session.otp_expires_at = otp_expires_at
        session.expires_at = expires_at
        session.is_verified = False
    else:
        # Create new session
        session = CustomerSession(
            session_token=session_token,
            identifier=request.identifier,
            identifier_type=request.identifier_type,
            otp_code=otp_code,
            otp_expires_at=otp_expires_at,
            expires_at=expires_at,
            is_verified=False,
        )
        db.add(session)

    await db.commit()

    # Store OTP in Redis
    await redis_cache.store_otp(request.identifier, otp_code)

    # Send OTP
    if request.identifier_type == "email":
        await notification_service.send_otp_email(request.identifier, otp_code)
    else:
        await notification_service.send_otp_sms(request.identifier, otp_code)

    logger.info(
        f"OTP requested for customer: {request.identifier}",
        extra={"identifier": request.identifier, "type": request.identifier_type},
    )

    return {
        "message": "OTP sent successfully",
        "session_token": session_token,
        "expires_in": 600,  # 10 minutes
    }


@router.post("/customer/verify-otp", status_code=status.HTTP_200_OK)
async def verify_customer_otp(
    verification: CustomerOTPVerify,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Verify OTP and establish customer session.

    Sets session cookie for subsequent requests.
    """
    # Get session
    stmt = select(CustomerSession).where(
        CustomerSession.session_token == verification.session_token
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    # Verify OTP from Redis first (faster)
    redis_valid = await redis_cache.verify_otp(session.identifier, verification.otp_code)

    # Fallback to database OTP
    db_valid = session.otp_code == verification.otp_code and session.is_otp_valid

    if not (redis_valid or db_valid):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OTP",
        )

    # Mark session as verified
    session.is_verified = True
    session.otp_code = None  # Clear OTP
    session.otp_expires_at = None
    await db.commit()

    # Cache session in Redis
    await redis_cache.cache_customer_session(session)

    # Set session cookie
    response.set_cookie(
        key="session_token",
        value=session.session_token,
        httponly=True,
        secure=True,  # HTTPS only in production
        samesite="lax",
        max_age=86400,  # 24 hours
    )

    logger.info(
        f"Customer session verified: {session.identifier}",
        extra={"session_id": str(session.id)},
    )

    return {
        "message": "OTP verified successfully",
        "session_token": session.session_token,
    }
