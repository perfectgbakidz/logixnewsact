"""
Database configuration and session management.
Supports both local PostgreSQL and Supabase.
"""
from uuid import uuid4

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
    asyncpg_connect_args = {
        "statement_cache_size": settings.DB_STATEMENT_CACHE_SIZE,
        "prepared_statement_cache_size": settings.DB_PREPARED_STATEMENT_CACHE_SIZE,
        "prepared_statement_name_func": lambda: f"__asyncpg_{uuid4()}__",
    }

    # For Supabase/PgBouncer, force SSL and prefer no app-side pooling.
    if settings.is_supabase:
        connect_args = {**asyncpg_connect_args, "ssl": "require"}
        if settings.DB_NULL_POOL_FOR_SUPABASE:
            return create_async_engine(
                settings.DATABASE_URL,
                connect_args=connect_args,
                poolclass=NullPool,
                **common_kwargs,
            )
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
            connect_args=asyncpg_connect_args,
            poolclass=NullPool,
            **common_kwargs,
        )

    return create_async_engine(
        settings.DATABASE_URL,
        connect_args=asyncpg_connect_args,
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
