"""
Database connection and session management.
Provides async SQLAlchemy engine with optimized connection pooling and RLS support.

Connection Pooling Strategy:
- Global engine and session factory (singleton pattern)
- QueuePool for production (configurable size and overflow)
- NullPool for testing (no pooling overhead)
- Pool recycling to prevent stale connections
- Pre-ping health checks before each connection use
- Connection timeout and statement timeout for reliability
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool, Pool, QueuePool

from app.core.config import settings
from app.core.observability import tracer

logger = logging.getLogger(__name__)


# Base class for all models
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


# Global engine and session factory
_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def get_engine() -> AsyncEngine:
    """
    Get or create the global async database engine with optimized connection pooling.

    Singleton pattern ensures only one engine is created per application lifecycle.
    Connections are reused from the pool instead of creating new ones.

    Pool Configuration:
    - pool_size: Base number of connections to maintain
    - max_overflow: Additional connections when pool is exhausted
    - pool_timeout: Max time to wait for available connection
    - pool_recycle: Recycle connections after N seconds (prevents stale connections)
    - pool_pre_ping: Test connection validity before using (prevents broken connections)

    Returns:
        AsyncEngine: SQLAlchemy async engine with connection pool
    """
    global _engine

    if _engine is None:
        # Use NullPool only for testing (no pooling overhead)
        # QueuePool for all other environments (dev, staging, production)
        pool_class = NullPool if settings.ENVIRONMENT == "test" else QueuePool

        # Create engine with optimized pool settings
        _engine = create_async_engine(
            str(settings.DATABASE_URL),
            echo=settings.DATABASE_ECHO,
            # Connection Pool Settings
            poolclass=pool_class,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_timeout=settings.DATABASE_POOL_TIMEOUT,
            pool_recycle=settings.DATABASE_POOL_RECYCLE,
            pool_pre_ping=settings.DATABASE_POOL_PRE_PING,
            # Connection Settings
            connect_args={
                "server_settings": {
                    # Statement timeout (prevent long-running queries)
                    "statement_timeout": str(settings.DATABASE_STATEMENT_TIMEOUT),
                    # Application name for connection tracking
                    "application_name": f"{settings.APP_NAME}-{settings.ENVIRONMENT}",
                },
                # Command timeout at driver level
                "command_timeout": settings.DATABASE_POOL_TIMEOUT,
            },
        )

        # Register connection pool event listeners for monitoring
        _setup_pool_listeners(_engine)

        logger.info(
            f"✓ Database engine created with connection pooling: "
            f"pool_class={pool_class.__name__}, "
            f"pool_size={settings.DATABASE_POOL_SIZE}, "
            f"max_overflow={settings.DATABASE_MAX_OVERFLOW}, "
            f"total_capacity={settings.DATABASE_POOL_SIZE + settings.DATABASE_MAX_OVERFLOW}, "
            f"pool_timeout={settings.DATABASE_POOL_TIMEOUT}s, "
            f"pool_recycle={settings.DATABASE_POOL_RECYCLE}s"
        )

    return _engine


def _setup_pool_listeners(engine: AsyncEngine) -> None:
    """
    Set up event listeners for connection pool monitoring.

    Tracks pool usage metrics for observability and debugging.

    Args:
        engine: SQLAlchemy engine to attach listeners to
    """

    @event.listens_for(engine.sync_engine.pool, "connect")
    def receive_connect(dbapi_conn, connection_record):  # type: ignore
        """Log new database connections."""
        logger.debug("New database connection established")

    @event.listens_for(engine.sync_engine.pool, "checkout")
    def receive_checkout(dbapi_conn, connection_record, connection_proxy):  # type: ignore
        """Log connection checkout from pool."""
        pool = connection_proxy._pool
        logger.debug(
            f"Connection checked out from pool: "
            f"size={pool.size()}, "
            f"checked_in={pool.checkedin()}, "
            f"checked_out={pool.checkedout()}, "
            f"overflow={pool.overflow()}"
        )

    @event.listens_for(engine.sync_engine.pool, "checkin")
    def receive_checkin(dbapi_conn, connection_record):  # type: ignore
        """Log connection return to pool."""
        logger.debug("Connection returned to pool")

    @event.listens_for(engine.sync_engine.pool, "invalidate")
    def receive_invalidate(dbapi_conn, connection_record, exception):  # type: ignore
        """Log connection invalidation (usually due to errors)."""
        logger.warning(
            f"Database connection invalidated: {exception}",
            extra={"exception": str(exception)},
        )

    logger.debug("Connection pool event listeners registered")


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Get or create the global session factory.

    Returns:
        async_sessionmaker: Session factory
    """
    global _session_factory

    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        logger.info("Session factory created")

    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session for FastAPI endpoints.

    This function properly manages the session lifecycle:
    1. Get session from the pool (reuses existing connection)
    2. Yield session to endpoint
    3. Rollback on error
    4. Always close session (returns connection to pool)

    The connection is NOT closed - it's returned to the pool for reuse.
    This is critical for performance: connection pooling means we reuse
    connections instead of opening/closing them for every request.

    Yields:
        AsyncSession: Database session backed by pooled connection
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            # Close session (returns connection to pool, does NOT close connection)
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager to get database session outside of FastAPI.

    Yields:
        AsyncSession: Database session
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def set_rls_context(
    session: AsyncSession,
    org_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> None:
    """
    Set Row-Level Security (RLS) context for the current session.

    This sets PostgreSQL session variables that RLS policies use to filter data.

    Args:
        session: Database session
        org_id: Organization ID for multi-tenant isolation
        user_id: User ID for user-specific data
    """
    if org_id:
        await session.execute(text(f"SET app.current_org_id = '{org_id}'"))
        logger.debug(f"RLS context set: org_id={org_id}")

    if user_id:
        await session.execute(text(f"SET app.current_user_id = '{user_id}'"))
        logger.debug(f"RLS context set: user_id={user_id}")


async def clear_rls_context(session: AsyncSession) -> None:
    """
    Clear Row-Level Security context.

    Args:
        session: Database session
    """
    await session.execute(text("RESET app.current_org_id"))
    await session.execute(text("RESET app.current_user_id"))
    logger.debug("RLS context cleared")


class RLSSession:
    """
    Context manager for database sessions with automatic RLS setup.

    Usage:
        async with RLSSession(org_id="uuid") as session:
            # All queries automatically filtered by org_id
            results = await session.execute(select(Organization))
    """

    def __init__(
        self,
        org_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        self.org_id = org_id
        self.user_id = user_id
        self.session: Optional[AsyncSession] = None

    async def __aenter__(self) -> AsyncSession:
        """Enter context and set RLS."""
        session_factory = get_session_factory()
        self.session = session_factory()

        # Set RLS context
        await set_rls_context(self.session, self.org_id, self.user_id)

        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        """Exit context and cleanup."""
        if self.session:
            try:
                if exc_type is None:
                    await self.session.commit()
                else:
                    await self.session.rollback()
            finally:
                await clear_rls_context(self.session)
                await self.session.close()


async def init_db() -> None:
    """
    Initialize database: create tables and extensions.

    Note: In production, use Alembic migrations instead.
    """
    engine = get_engine()

    async with engine.begin() as conn:
        # Enable PostGIS extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist"))

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database initialized")


async def close_db() -> None:
    """Close database connections and cleanup."""
    global _engine, _session_factory

    if _engine:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("Database connections closed")
