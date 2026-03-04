"""
Application configuration loaded from environment variables.
Uses pydantic-settings for type-safe configuration management.
"""

from functools import lru_cache
from typing import Literal

# EmailStr will be used when email validation is needed
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    All values can be overridden via .env file in backend directory.
    """

    # PostgreSQL
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "fleet"

    # Database URL - can be set directly or will be constructed from parts
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/fleet"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Google OAuth 2.0
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # SMTP / Email
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    EMAIL_FROM: str = "noreply@fleet.local"
    SUPER_ADMIN_EMAIL_LIST: str = ""

    def get_super_admin_emails(self) -> list[str]:
        if not self.SUPER_ADMIN_EMAIL_LIST:
            return []
        return [
            email.strip()
            for email in self.SUPER_ADMIN_EMAIL_LIST.split(",")
            if email.strip()
        ]

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    # Secret key Validation
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        if info.data.get("ENVIRONMENT") == "production":
            if not v or v == "change-me-in-production" or len(v) < 32:
                raise ValueError("SECRET_KEY must be at least 32 characters in production")
        return v


@lru_cache
def get_settings() -> Settings:
    """
    Create cached settings instance.
    Use this function to get settings throughout the application.
    """
    return Settings()


settings = get_settings()

