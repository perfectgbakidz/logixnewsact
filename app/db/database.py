"""
Database configuration and session management.
Supports both local PostgreSQL and Supabase.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

from app.core.config import settings


def create_engine():
    """Create async engine with appropriate pool settings."""
    common_kwargs = {
        "echo": settings.DEBUG,
        "future": True,
        "pool_pre_ping": True,
    }

    # For Supabase, keep pool small and require SSL.
    if settings.is_supabase:
        connect_args = {"ssl": "require"}
        return create_async_engine(
            settings.DATABASE_URL,
            connect_args=connect_args,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_recycle=settings.DB_POOL_RECYCLE,
            **common_kwargs,
        )

    # For local development, disable pooling in debug mode.
    if settings.DEBUG:
        return create_async_engine(
            settings.DATABASE_URL,
            poolclass=NullPool,
            **common_kwargs,
        )

    return create_async_engine(
        settings.DATABASE_URL,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
        **common_kwargs,
    )


# Create async engine
engine = create_engine()

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
