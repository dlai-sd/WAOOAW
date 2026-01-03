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
        if self.ENV == "demo":
            return [
                "https://demo-www.waooaw.com",
                "https://demo-pp.waooaw.com",
            ]
        elif self.ENV == "uat":
            return [
                "https://uat-www.waooaw.com",
                "https://uat-pp.waooaw.com",
            ]
        elif self.ENV == "production":
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
        return {
            "demo": {
                "www": "https://demo-www.waooaw.com",
                "pp": "https://demo-pp.waooaw.com",
                "api": "https://demo-api.waooaw.com",
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
                "dp": "https://dp.waooaw.com",
                "yk": "https://yk.waooaw.com",
            },
            "development": {
                "www": "http://localhost:8080",
                "pp": "http://localhost:3000",
                "api": "http://localhost:8000",
            }
        }
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
