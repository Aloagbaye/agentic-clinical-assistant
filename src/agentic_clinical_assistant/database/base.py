"""Database base configuration and session management."""

from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

from agentic_clinical_assistant.config import settings

# Create base class for models
Base = declarative_base()

# Engine will be created lazily to avoid issues with Alembic imports
_engine: Optional[AsyncEngine] = None
_async_session_local: Optional[async_sessionmaker[AsyncSession]] = None


def get_engine() -> AsyncEngine:
    """Get or create the async engine."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            poolclass=NullPool if settings.DATABASE_POOL_SIZE == 0 else None,
            pool_size=settings.DATABASE_POOL_SIZE if settings.DATABASE_POOL_SIZE > 0 else None,
            max_overflow=settings.DATABASE_MAX_OVERFLOW if settings.DATABASE_POOL_SIZE > 0 else None,
            pool_pre_ping=True,  # Verify connections before using
        )
    return _engine


def get_async_session_local() -> async_sessionmaker[AsyncSession]:
    """Get or create the async session factory."""
    global _async_session_local
    if _async_session_local is None:
        _async_session_local = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _async_session_local


# For backward compatibility, create engine and session factory
# But only if not being imported by Alembic (which will handle its own engine)
engine = get_engine()
AsyncSessionLocal = get_async_session_local()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database session.
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_db():
    """
    Dependency for getting database session (for compatibility).
    
    Returns:
        AsyncGenerator[AsyncSession, None]: Database session generator
    """
    return get_async_session()

