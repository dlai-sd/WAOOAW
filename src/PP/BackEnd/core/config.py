"""
Configuration settings for WAOOAW Platform Portal
Loads from environment variables and provides validated settings
"""

from typing import List

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )

    # App Info
    APP_NAME: str = "WAOOAW Platform Portal API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "codespace"
    APP_PORT: int = 8015

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    OAUTH_REDIRECT_URI: str = ""

    # JWT Configuration
    JWT_SECRET: str = ""          # Must be injected via GCP Secret Manager in UAT/prod
    JWT_ALGORITHM: str = "HS256"
    JWT_ISSUER: str = "waooaw.com"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # DB updates scoped token (break-glass, dev-only)
    DB_UPDATES_TOKEN_EXPIRE_MINUTES: int = 480
    DB_UPDATES_TOKEN_SCOPE: str = "db_updates"

    # Auth allowlists
    ALLOWED_EMAIL_DOMAINS: str = "dlaisd.com,waooaw.com"

    # URLs
    FRONTEND_URL: str = "http://localhost:3000"
    CORS_ORIGINS: str = "*"
    PLANT_API_URL: str = "http://localhost:8000"  # Plant backend API
    PLANT_GATEWAY_URL: str = ""  # Preferred when routing through the Plant Gateway

    # Redis cache (optional — ops proxy responses cached with TTL)
    REDIS_URL: str = ""
    OPS_CACHE_TTL_SECONDS: int = 60

    # Admin tools (disabled by default; enable only in safe environments)
    ENABLE_AGENT_SEEDING: bool = False
    ENABLE_DB_UPDATES: bool = False
    ENABLE_DEV_TOKEN: bool = False         # Enable /auth/dev-token (development only)
    ENABLE_E2E_HOOKS: bool = False         # Enable secret-guarded /auth/e2e/* hooks
    E2E_SHARED_SECRET: str = ""           # Runtime-injected shared secret for E2E hooks
    ENABLE_METERING_DEBUG: bool = False    # Enable /metering/debug endpoints (development only)
    DEBUG_VERBOSE: bool = False            # Enable verbose debug logging (development only)

    # Audit service (PP-N4) — key used to write audit events to Plant Audit API
    AUDIT_SERVICE_KEY: str = ""

    @model_validator(mode="after")
    def _require_secrets_in_live_envs(self) -> "Settings":
        live = {"demo", "uat", "prod", "production"}
        if self.ENVIRONMENT.lower() in live and not self.JWT_SECRET:
            raise ValueError(
                "JWT_SECRET must be set — refusing to start with empty secret. "
                "Inject via GCP Secret Manager."
            )
        return self

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def access_token_expire_seconds(self) -> int:
        """Get access token expiry in seconds"""
        return self.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    @property
    def refresh_token_expire_seconds(self) -> int:
        """Get refresh token expiry in seconds"""
        return self.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

    @property
    def plant_base_url(self) -> str:
        """Base URL for Plant calls (prefer gateway when configured)."""
        return self.PLANT_GATEWAY_URL or self.PLANT_API_URL

    @property
    def is_prod_like(self) -> bool:
        """Return True for environments where admin-only tools must be disabled."""
        return self.ENVIRONMENT.lower() in {"prod", "production", "uat"}


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Dependency for FastAPI to get settings"""
    return settings
