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
    ENABLE_E2E_HOOKS: bool = False
    E2E_SHARED_SECRET: str = ""

    # URLs
    API_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"
    # Never use "*" in staging/prod — always explicit origins (E3-S1 Iteration 3)
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8015,http://localhost:5173,http://localhost:8080"
    # Plant backend URL for server-to-server calls (audit, etc.)
    PLANT_API_URL: str = "http://localhost:8000"
    # Audit API service key — must match Plant backend AUDIT_SERVICE_KEY
    AUDIT_SERVICE_KEY: str = "dev-audit-key-change-in-production"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/waooaw_cp"
    DEBUG: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
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
    def e2e_hooks_ready(self) -> bool:
        """Return True only when E2E hooks are enabled and properly configured."""
        return self.ENABLE_E2E_HOOKS and bool(self.E2E_SHARED_SECRET)


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Dependency for FastAPI to get settings"""
    return settings
