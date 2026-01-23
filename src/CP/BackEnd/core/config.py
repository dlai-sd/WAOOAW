"""
Configuration settings for WAOOAW Customer Portal
Loads from environment variables and provides validated settings
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings from environment variables"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # App Info
    APP_NAME: str = "WAOOAW Customer Portal API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "codespace"

    # OpenAPI Schema Validation
    OPENAPI_SCHEMA_PATH: str = "openapi/schema.json"

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    OAUTH_REDIRECT_URI: str = ""

    # JWT Configuration
    JWT_SECRET: str = "dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Rate Limiting
    RATE_LIMIT: int = 100

    # URLs
    FRONTEND_URL: str = "http://localhost:3000"
    CORS_ORIGINS: str = "*"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/waooaw_cp"
    DEBUG: bool = True

    # Prometheus Metrics
    PROMETHEUS_METRICS_ENABLED: bool = True
    PROMETHEUS_METRICS_PORT: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )

    @property
    def cors_origins_list(self) -> List[str]:
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def access_token_expire_seconds(self) -> int:
        return self.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    @property
    def refresh_token_expire_seconds(self) -> int:
        return self.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

settings = Settings()

def get_settings() -> Settings:
    return settings
