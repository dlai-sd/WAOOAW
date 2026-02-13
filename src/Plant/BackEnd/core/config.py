"""
Configuration management using Pydantic BaseSettings
Loads from .env file with validation
"""

from typing import Optional, List

from pydantic import AliasChoices, Field, field_validator
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
    version: str = "0.1.0"  # Alias for app_version
    environment: str = "development"
    debug: bool = True
    log_level: str = "info"
    
    # GCP Configuration
    gcp_project_id: str = Field(
        default="waooaw-demo",
        validation_alias=AliasChoices("GCP_PROJECT_ID", "GOOGLE_CLOUD_PROJECT"),
    )
    
    # Observability Flags (can be enabled in production for debugging)
    enable_request_logging: bool = False       # Log every HTTP request/response with details
    enable_route_registration_logging: bool = False  # Log route registration at startup
    enable_sql_logging: bool = False          # Enable SQLAlchemy SQL statement logging
    enable_startup_diagnostics: bool = False   # Detailed startup sequence logging
    enable_uvicorn_access_logs: bool = True   # Uvicorn access logs (disabled when using gunicorn)
    enable_json_logs: bool = False            # Use JSON structured logging format

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, value: object) -> str:
        """Normalize and validate Uvicorn log levels.

        Uvicorn expects: critical, error, warning, info, debug, trace.
        """
        allowed = {"critical", "error", "warning", "info", "debug", "trace"}

        if value is None:
            return "info"

        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized == "warn":
                normalized = "warning"
            if normalized in allowed:
                return normalized

        raise ValueError(f"Invalid log_level: {value!r}. Allowed: {sorted(allowed)}")
    
    # Database (Async-first SQLAlchemy configuration)
    database_url: str = "postgresql+asyncpg://user:password@localhost/plant"
    database_pool_size: int = 20  # Per environment (overridden by environment config)
    database_max_overflow: int = 40  # Per environment
    database_pool_timeout: int = 30  # Seconds to wait for a connection from the pool
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
    # NOTE: Terraform/Cloud Run stacks provide secrets/config as JWT_*.
    # Accept those names while keeping legacy secret_key/algorithm fields.
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        validation_alias=AliasChoices("JWT_SECRET", "SECRET_KEY"),
    )
    algorithm: str = Field(
        default="HS256",
        validation_alias=AliasChoices("JWT_ALGORITHM", "ALGORITHM"),
    )
    access_token_expire_minutes: int = 30
    
    # Cryptography
    rsa_key_size: int = 4096
    hash_algorithm: str = "SHA256"

    # Security throttles (REG-1.9)
    # Applied to registration-sensitive endpoints in Plant (e.g. customer upsert).
    security_customer_upsert_max_attempts: int = 10
    security_customer_upsert_window_seconds: int = 60
    security_customer_upsert_lockout_seconds: int = 300
    
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

    # Admin tools (dev-only)
    enable_db_updates: bool = False
    db_updates_statement_timeout_ms: int = 10_000
    db_updates_max_statement_timeout_ms: int = 60_000
    db_updates_max_rows: int = 500
    db_updates_max_sql_length: int = 20_000
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
