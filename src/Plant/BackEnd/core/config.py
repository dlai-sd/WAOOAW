"""
Configuration management using Pydantic BaseSettings
Loads from .env file with validation
"""

from typing import Optional, List
from pydantic_settings import BaseSettings
from functools import lru_cache
import json


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Example:
        settings = get_settings()
        db_url = settings.database_url
    """
    
    # Application
    app_name: str = "WAOOAW Plant Phase API"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    # Database (Async-first SQLAlchemy configuration)
    database_url: str = "postgresql+asyncpg://user:password@localhost/plant"
    database_pool_size: int = 5  # Per environment (overridden by environment config)
    database_max_overflow: int = 10  # Per environment
    database_echo: bool = False  # Set to True for SQL logging
    database_pool_pre_ping: bool = True  # Validate connections before use
    database_statement_timeout_ms: int = 60000  # 60 seconds
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_ttl_seconds: int = 86400  # 24 hours
    
    # ML Service
    ml_service_url: str = "http://localhost:8005"
    ml_service_timeout_ms: int = 100
    ml_embedding_dimension: int = 384
    ml_model: str = "MiniLM-384"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Cryptography
    rsa_key_size: int = 4096
    hash_algorithm: str = "SHA256"
    
    # Performance SLAs
    validate_self_sla_ms: int = 10
    evolve_sla_ms: int = 5
    verify_amendment_sla_ms: int = 20
    pgvector_search_sla_ms: int = 500
    schema_migration_sla_latency_increase_percent: int = 10
    
    # Cost Governance
    embedding_quality_stability_threshold: float = 0.85
    embedding_quality_check_schedule: str = "02:00"  # Daily at 2 AM UTC
    
    # API
    api_v1_prefix: str = "/api/v1"
    cors_origins: List[str] = [
        "http://localhost:3000",      # CP frontend (local dev)
        "http://localhost:5173",      # PP frontend (Vite dev server)
        "http://localhost:8080",      # CP frontend (alternative port)
        "http://localhost:8006",      # PP frontend (alternative port)
        "http://localhost:8015",      # CP frontend (FastAPI dev server)
        "https://cp.demo.waooaw.com",       # CP demo environment
        "https://pp.demo.waooaw.com",       # PP demo environment
        "https://cp.uat.waooaw.com",        # CP UAT environment
        "https://pp.uat.waooaw.com",        # PP UAT environment
        "https://cp.waooaw.com",            # CP production
        "https://pp.waooaw.com",            # PP production
    ]
    
    @classmethod
    def parse_env_var(cls, field_name: str, raw_val: str):
        """Parse environment variables, especially for list fields."""
        if field_name == 'cors_origins' and isinstance(raw_val, str):
            # Handle JSON list format or comma-separated format
            if raw_val.startswith('['):
                return json.loads(raw_val)
            return [origin.strip() for origin in raw_val.split(',')]
        return raw_val
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Returns:
        Settings: Singleton settings object
        
    Example:
        settings = get_settings()
    """
    return Settings()


# Singleton instance
settings = get_settings()
