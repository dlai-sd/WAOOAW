"""
Configuration Management - Backend v2
Environment-aware configuration with multi-domain support
"""

import os
from typing import Dict, List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment detection"""

    # Environment
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = ENV == "development"

    # Database
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "waooaw-db")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_SCHEMA: str = os.getenv("DB_SCHEMA", "public")  # demo, uat, or public

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # OAuth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")

    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24 hours

    # CORS - Multi-domain support
    @property
    def CORS_ORIGINS(self) -> List[str]:
        """Get CORS origins based on environment"""
        # Allow override via env var (comma-separated)
        override_origins = os.getenv("CORS_ORIGINS")
        if override_origins:
            return [
                origin.strip()
                for origin in override_origins.split(",")
                if origin.strip()
            ]

        if self.ENV == "codespace":
            # Codespace - allow app.github.dev domain
            codespace_name = os.getenv("CODESPACE_NAME", "")
            if codespace_name:
                return [
                    f"https://{codespace_name}-3001.app.github.dev",  # Platform Portal frontend
                    f"https://{codespace_name}-8080.app.github.dev",  # Customer Portal
                    f"https://{codespace_name}-8000.app.github.dev",  # Backend itself
                ]
            return [
                "http://localhost:3000",
                "http://localhost:8080",
                "http://localhost:8000",
            ]
        elif self.ENV == "demo":
            # Using Load Balancer with custom domain
            return [
                "https://demo.waooaw.com",
                "https://waooaw-portal-demo-ryvhxvrdna-el.a.run.app",
                "https://waooaw-platform-portal-demo-ryvhxvrdna-el.a.run.app",
            ]
        elif self.ENV == "uat":
            # UAT will use Load Balancer with custom domains
            return [
                "https://uat-www.waooaw.com",
                "https://uat-pp.waooaw.com",
            ]
        elif self.ENV == "production":
            # Production will use Load Balancer with custom domains
            return [
                "https://www.waooaw.com",
                "https://pp.waooaw.com",
                "https://dp.waooaw.com",
                "https://yk.waooaw.com",
            ]
        else:
            # Development
            return [
                "http://localhost:3000",
                "http://localhost:8080",
                "http://localhost:5173",  # Vite default
            ]

    # Domain Configuration
    @property
    def DOMAIN_CONFIG(self) -> Dict[str, Dict[str, str]]:
        """Get domain configuration for environment"""
        codespace_name = os.getenv("CODESPACE_NAME", "")

        config = {
            "demo": {
                # Using Load Balancer with custom domain
                "www": "https://demo.waooaw.com",
                "pp": "https://demo.waooaw.com",
                "api": "https://demo.waooaw.com/api",
            },
            "uat": {
                # UAT will use Load Balancer with custom domains
                "www": "https://uat-www.waooaw.com",
                "pp": "https://uat-pp.waooaw.com",
                "api": "https://uat-api.waooaw.com",
            },
            "production": {
                "www": "https://www.waooaw.com",
                "pp": "https://pp.waooaw.com",
                "api": "https://api.waooaw.com",
                "dp": "https://dp.waooaw.com",
                "yk": "https://yk.waooaw.com",
            },
            "development": {
                "www": "http://localhost:8080",
                "pp": "http://localhost:3000",
                "api": "http://localhost:8000",
            },
        }

        # Add codespace config dynamically if CODESPACE_NAME is set
        if codespace_name:
            config["codespace"] = {
                "www": f"https://{codespace_name}-8080.app.github.dev",
                "pp": f"https://{codespace_name}-3001.app.github.dev",  # Reflex frontend port
                "api": f"https://{codespace_name}-8000.app.github.dev",
            }

        return config

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
