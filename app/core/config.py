"""
Application configuration using Pydantic Settings.
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional
from urllib.parse import urlparse


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Logic NewsAct API"
    DEBUG: bool = False
    VERSION: str = "1.0.0"

    # Database - Supports both local PostgreSQL and Supabase
    # For Supabase: postgresql+asyncpg://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/logic_newsact"

    # Supabase Configuration (optional - for Supabase client features)
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_SERVICE_KEY: Optional[str] = None

    # Supabase Storage Configuration
    SUPABASE_STORAGE_BUCKET: str = "public"
    SUPABASE_STORAGE_PUBLIC: bool = True

    # Database Pool Settings (important for Supabase connection limits)
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800  # 30 minutes
    DB_STATEMENT_CACHE_SIZE: int = 0
    DB_PREPARED_STATEMENT_CACHE_SIZE: int = 0
    DB_NULL_POOL_FOR_SUPABASE: bool = True

    # JWT Authentication
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    TRUSTED_HOSTS: str = "localhost,127.0.0.1,*.onrender.com"

    # Security
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds

    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse ALLOWED_ORIGINS string into list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    @property
    def trusted_hosts_list(self) -> List[str]:
        """Parse TRUSTED_HOSTS string into hostnames accepted by TrustedHostMiddleware."""
        hosts: List[str] = []
        for raw in self.TRUSTED_HOSTS.split(","):
            value = raw.strip()
            if not value:
                continue
            if "://" in value:
                parsed = urlparse(value)
                value = parsed.hostname or ""
            if "/" in value:
                value = value.split("/", 1)[0]
            if ":" in value:
                value = value.split(":", 1)[0]
            if value:
                hosts.append(value)
        return hosts

    @property
    def is_supabase(self) -> bool:
        """Check if using Supabase database."""
        return "supabase.co" in self.DATABASE_URL

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        """
        Normalize database URL for SQLAlchemy async engine.

        Allows using provider-style `postgresql://...` URLs from Render/Supabase
        while internally requiring `postgresql+asyncpg://...`.
        """
        if isinstance(value, str) and value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
