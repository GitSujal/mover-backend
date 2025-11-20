"""
Application configuration using Pydantic Settings.
All settings are type-safe and validated at startup.
"""

from functools import lru_cache
from typing import Any

from pydantic import (
    EmailStr,
    Field,
    PostgresDsn,
    RedisDsn,
    field_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Production-grade application settings with comprehensive validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "MoveHub"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(
        default="development", pattern="^(development|staging|production|test)$"
    )
    DEBUG: bool = False
    LOG_LEVEL: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = Field(default=8000, ge=1, le=65535)
    WORKERS: int = Field(default=4, ge=1)

    # Database (PostgreSQL with PostGIS)
    DATABASE_URL: PostgresDsn
    DATABASE_POOL_SIZE: int = Field(default=20, ge=5, le=100)
    DATABASE_MAX_OVERFLOW: int = Field(default=10, ge=0, le=50)
    DATABASE_ECHO: bool = False
    DATABASE_POOL_RECYCLE: int = Field(default=3600, ge=300)  # Prevent stale connections
    DATABASE_POOL_TIMEOUT: int = Field(default=30, ge=5, le=60)  # Connection timeout
    DATABASE_POOL_PRE_PING: bool = True  # Verify connections before use
    DATABASE_STATEMENT_TIMEOUT: int = Field(default=30000, ge=1000)  # Statement timeout (ms)

    # Redis
    REDIS_URL: RedisDsn
    REDIS_SESSION_DB: int = Field(default=1, ge=0, le=15)
    REDIS_CACHE_DB: int = Field(default=2, ge=0, le=15)
    REDIS_POOL_SIZE: int = Field(default=10, ge=1)

    # JWT & Security
    JWT_SECRET_KEY: str = Field(min_length=32)
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, ge=1)
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, ge=1)
    BCRYPT_ROUNDS: int = Field(default=12, ge=10, le=15)

    # AWS
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    S3_BUCKET_NAME: str = "test-bucket"  # Default for testing
    S3_PRESIGNED_URL_EXPIRE_SECONDS: int = Field(default=300, ge=60, le=3600)
    SQS_QUEUE_URL: str | None = None

    # Stripe
    STRIPE_SECRET_KEY: str = "sk_test_dummy"  # Default for testing
    STRIPE_PUBLISHABLE_KEY: str = "pk_test_dummy"  # Default for testing
    STRIPE_WEBHOOK_SECRET: str = "whsec_dummy"  # Default for testing
    PLATFORM_FEE_PERCENTAGE: float = Field(default=5.0, ge=0, le=100)

    # Twilio (SMS)
    TWILIO_ACCOUNT_SID: str | None = None
    TWILIO_AUTH_TOKEN: str | None = None
    TWILIO_PHONE_NUMBER: str | None = None

    # SendGrid (Email)
    SENDGRID_API_KEY: str | None = None
    SENDGRID_FROM_EMAIL: EmailStr = "noreply@movehub.com"
    SENDGRID_FROM_NAME: str = "MoveHub"

    # OpenTelemetry
    OTEL_SERVICE_NAME: str = "movehub-api"
    OTEL_EXPORTER_OTLP_ENDPOINT: str | None = "http://localhost:4317"
    OTEL_TRACES_SAMPLER: str = "parentbased_traceidratio"
    OTEL_TRACES_SAMPLER_ARG: float = Field(default=1.0, ge=0.0, le=1.0)
    OTEL_METRICS_EXPORTER: str = "prometheus"
    OTEL_LOGS_EXPORTER: str = "otlp"

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, ge=1)

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    CORS_CREDENTIALS: bool = True

    # Booking Configuration
    DEFAULT_COMMUTE_BUFFER_MINUTES: int = Field(default=30, ge=0)
    BOOKING_CANCELLATION_HOURS: int = Field(default=24, ge=1)

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = Field(default=10, ge=1, le=100)
    ALLOWED_UPLOAD_EXTENSIONS: list[str] = [".jpg", ".jpeg", ".png", ".pdf"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            import json

            return json.loads(v)
        return v

    @field_validator("ALLOWED_UPLOAD_EXTENSIONS", mode="before")
    @classmethod
    def parse_upload_extensions(cls, v: Any) -> list[str]:
        """Parse upload extensions from string or list."""
        if isinstance(v, str):
            import json

            return json.loads(v)
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"

    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for Alembic migrations."""
        return str(self.DATABASE_URL).replace("+asyncpg", "")


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.
    Settings are validated once and cached for performance.
    """
    return Settings()


# Global settings instance
settings = get_settings()
