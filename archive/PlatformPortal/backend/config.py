"""
Configuration Management - Platform Portal Backend
Mirrored from WaooawPortal for consistency
"""

import os
from typing import Dict, List


class Settings:
    """Application settings with environment detection"""

    # Environment
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = ENV == "development"

    # OAuth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")

    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080  # 7 days

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
                    f"https://{codespace_name}-3001.app.github.dev",  # Platform Portal frontend (Reflex)
                    f"https://{codespace_name}-8080.app.github.dev",  # Customer Portal
                    f"https://{codespace_name}-8000.app.github.dev",  # Backend itself
                ]
            return [
                "http://localhost:3001",  # Reflex default
                "http://localhost:3000",
                "http://localhost:8080",
                "http://localhost:8000",
            ]
        elif self.ENV == "demo":
            return [
                "https://pp.demo.waooaw.com",  # Platform Portal
                "https://demo.waooaw.com",  # Customer Portal
            ]
        elif self.ENV == "uat":
            return [
                "https://uat-pp.waooaw.com",
                "https://uat-www.waooaw.com",
            ]
        elif self.ENV == "production":
            return [
                "https://pp.waooaw.com",
                "https://www.waooaw.com",
            ]
        else:
            # Development
            return [
                "http://localhost:3001",  # Reflex
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
                "www": "https://demo.waooaw.com",
                "pp": "https://pp.demo.waooaw.com",
                "api": "https://demo.waooaw.com/api",
            },
            "uat": {
                "www": "https://uat-www.waooaw.com",
                "pp": "https://uat-pp.waooaw.com",
                "api": "https://uat-api.waooaw.com",
            },
            "production": {
                "www": "https://www.waooaw.com",
                "pp": "https://pp.waooaw.com",
                "api": "https://api.waooaw.com",
            },
            "development": {
                "www": "http://localhost:8080",
                "pp": "http://localhost:3001",  # Reflex default port
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


# Global settings instance
settings = Settings()
