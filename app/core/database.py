"""
Database connection and session management.
Provides async SQLAlchemy engine with connection pooling and RLS support.
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
from sqlalchemy.pool import NullPool, QueuePool

from app.core.config import settings

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
    Get or create the global async database engine.

    Returns:
        AsyncEngine: SQLAlchemy async engine
    """
    global _engine

    if _engine is None:
        # Determine pool class based on environment
        pool_class = QueuePool if not settings.DEBUG else NullPool

        _engine = create_async_engine(
            str(settings.DATABASE_URL),
            echo=settings.DATABASE_ECHO,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_recycle=settings.DATABASE_POOL_RECYCLE,
            pool_pre_ping=True,  # Verify connections before using
            poolclass=pool_class,
        )

        logger.info(
            f"Database engine created: pool_size={settings.DATABASE_POOL_SIZE}, "
            f"max_overflow={settings.DATABASE_MAX_OVERFLOW}"
        )

    return _engine


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

    Yields:
        AsyncSession: Database session
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
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
