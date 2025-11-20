"""
Redis caching service.

Provides caching for sessions, availability windows, and frequently accessed data.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

import redis.asyncio as redis
from pydantic import BaseModel

from app.core.config import settings
from app.core.observability import tracer
from app.models.user import CustomerSession

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis caching service for high-performance data access."""

    def __init__(self) -> None:
        """Initialize Redis connection pools."""
        self.session_pool = redis.ConnectionPool.from_url(
            str(settings.REDIS_URL),
            db=settings.REDIS_SESSION_DB,
            max_connections=settings.REDIS_POOL_SIZE,
            decode_responses=True,
        )

        self.cache_pool = redis.ConnectionPool.from_url(
            str(settings.REDIS_URL),
            db=settings.REDIS_CACHE_DB,
            max_connections=settings.REDIS_POOL_SIZE,
            decode_responses=True,
        )

    async def _get_session_client(self) -> redis.Redis:
        """Get Redis client for sessions."""
        return redis.Redis(connection_pool=self.session_pool)

    async def _get_cache_client(self) -> redis.Redis:
        """Get Redis client for general caching."""
        return redis.Redis(connection_pool=self.cache_pool)

    # Customer Session Management

    async def cache_customer_session(
        self,
        session: CustomerSession,
        ttl_seconds: int = 86400,  # 24 hours
    ) -> bool:
        """
        Cache customer session in Redis.

        Args:
            session: Customer session object
            ttl_seconds: Time to live in seconds

        Returns:
            True if cached successfully
        """
        with tracer.start_as_current_span("redis.cache_customer_session"):
            try:
                client = await self._get_session_client()

                key = f"customer_session:{session.session_token}"
                value = {
                    "id": str(session.id),
                    "session_token": session.session_token,
                    "identifier": session.identifier,
                    "identifier_type": session.identifier_type,
                    "is_verified": session.is_verified,
                    "expires_at": session.expires_at.isoformat(),
                }

                await client.setex(key, ttl_seconds, json.dumps(value))
                await client.close()

                logger.debug(f"Cached customer session: {session.session_token}")
                return True

            except Exception as e:
                logger.error(f"Failed to cache session: {e}", exc_info=True)
                return False

    async def get_customer_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Get customer session from cache.

        Args:
            session_token: Session token

        Returns:
            Session data or None
        """
        with tracer.start_as_current_span("redis.get_customer_session"):
            try:
                client = await self._get_session_client()
                key = f"customer_session:{session_token}"

                value = await client.get(key)
                await client.close()

                if value:
                    return json.loads(value)
                return None

            except Exception as e:
                logger.error(f"Failed to get session: {e}", exc_info=True)
                return None

    async def invalidate_customer_session(self, session_token: str) -> bool:
        """
        Invalidate (delete) customer session from cache.

        Args:
            session_token: Session token

        Returns:
            True if deleted
        """
        with tracer.start_as_current_span("redis.invalidate_session"):
            try:
                client = await self._get_session_client()
                key = f"customer_session:{session_token}"

                await client.delete(key)
                await client.close()

                logger.debug(f"Invalidated session: {session_token}")
                return True

            except Exception as e:
                logger.error(f"Failed to invalidate session: {e}", exc_info=True)
                return False

    # OTP Management

    async def store_otp(
        self,
        identifier: str,
        otp_code: str,
        ttl_seconds: int = 600,  # 10 minutes
    ) -> bool:
        """
        Store OTP code in Redis.

        Args:
            identifier: Email or phone
            otp_code: 6-digit OTP
            ttl_seconds: Time to live

        Returns:
            True if stored
        """
        with tracer.start_as_current_span("redis.store_otp"):
            try:
                client = await self._get_session_client()
                key = f"otp:{identifier}"

                await client.setex(key, ttl_seconds, otp_code)
                await client.close()

                logger.debug(f"Stored OTP for: {identifier}")
                return True

            except Exception as e:
                logger.error(f"Failed to store OTP: {e}", exc_info=True)
                return False

    async def verify_otp(self, identifier: str, otp_code: str) -> bool:
        """
        Verify OTP code.

        Args:
            identifier: Email or phone
            otp_code: OTP to verify

        Returns:
            True if valid
        """
        with tracer.start_as_current_span("redis.verify_otp"):
            try:
                client = await self._get_session_client()
                key = f"otp:{identifier}"

                stored_otp = await client.get(key)

                if stored_otp == otp_code:
                    # Delete OTP after successful verification
                    await client.delete(key)
                    await client.close()
                    logger.debug(f"OTP verified for: {identifier}")
                    return True

                await client.close()
                return False

            except Exception as e:
                logger.error(f"Failed to verify OTP: {e}", exc_info=True)
                return False

    # Rate Limiting

    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> bool:
        """
        Check if rate limit is exceeded.

        Args:
            key: Rate limit key (e.g., IP address, user ID)
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            True if within limit, False if exceeded
        """
        with tracer.start_as_current_span("redis.check_rate_limit"):
            try:
                client = await self._get_cache_client()
                rate_key = f"rate_limit:{key}"

                # Increment counter
                count = await client.incr(rate_key)

                # Set expiry on first request
                if count == 1:
                    await client.expire(rate_key, window_seconds)

                await client.close()

                is_within_limit = count <= max_requests

                if not is_within_limit:
                    logger.warning(
                        f"Rate limit exceeded for {key}: {count}/{max_requests}",
                        extra={"key": key, "count": count, "limit": max_requests},
                    )

                return is_within_limit

            except Exception as e:
                logger.error(f"Failed to check rate limit: {e}", exc_info=True)
                # Fail open - allow request on Redis error
                return True

    # Availability Caching

    async def cache_availability(
        self,
        truck_id: UUID,
        date: datetime,
        is_available: bool,
        ttl_seconds: int = 300,  # 5 minutes
    ) -> bool:
        """
        Cache truck availability status.

        Args:
            truck_id: Truck ID
            date: Date to check
            is_available: Availability status
            ttl_seconds: Cache TTL

        Returns:
            True if cached
        """
        with tracer.start_as_current_span("redis.cache_availability"):
            try:
                client = await self._get_cache_client()
                key = f"availability:{truck_id}:{date.date()}"

                await client.setex(key, ttl_seconds, "1" if is_available else "0")
                await client.close()

                return True

            except Exception as e:
                logger.error(f"Failed to cache availability: {e}", exc_info=True)
                return False

    async def get_cached_availability(
        self,
        truck_id: UUID,
        date: datetime,
    ) -> Optional[bool]:
        """
        Get cached availability status.

        Args:
            truck_id: Truck ID
            date: Date to check

        Returns:
            True/False if cached, None if not in cache
        """
        with tracer.start_as_current_span("redis.get_availability"):
            try:
                client = await self._get_cache_client()
                key = f"availability:{truck_id}:{date.date()}"

                value = await client.get(key)
                await client.close()

                if value is not None:
                    return value == "1"
                return None

            except Exception as e:
                logger.error(f"Failed to get availability: {e}", exc_info=True)
                return None

    async def close(self) -> None:
        """Close all Redis connections."""
        await self.session_pool.disconnect()
        await self.cache_pool.disconnect()
        logger.info("Redis connections closed")
