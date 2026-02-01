"""
Configuration settings for WAOOAW Platform Portal
Loads from environment variables and provides validated settings
"""

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment variables"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

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
    JWT_SECRET: str = "dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ISSUER: str = "waooaw.com"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Auth allowlists
    ALLOWED_EMAIL_DOMAINS: str = "dlaisd.com,waooaw.com"

    # URLs
    FRONTEND_URL: str = "http://localhost:3000"
    CORS_ORIGINS: str = "*"
    PLANT_API_URL: str = "http://localhost:8000"  # Plant backend API
    PLANT_GATEWAY_URL: str = ""  # Preferred when routing through the Plant Gateway

    # Database (optional for now)
    DATABASE_URL: str = "sqlite:///./waooaw_pp.db"

    # Admin tools (disabled by default; enable only in safe environments)
    ENABLE_AGENT_SEEDING: bool = False
    ENABLE_DB_UPDATES: bool = False

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )

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
        return self.ENVIRONMENT.lower() in {"prod", "production", "uat", "demo"}


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Dependency for FastAPI to get settings"""
    return settings
