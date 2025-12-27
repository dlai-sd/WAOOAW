"""
Configuration Loader

Loads agent configuration from YAML and environment variables.
Extended with Message Bus configuration support (v0.2.5)
"""

import os
import yaml
from typing import Any, Dict, Optional
from pathlib import Path
from dataclasses import dataclass


@dataclass
class RedisConfig:
    """Redis connection configuration"""
    url: str
    max_connections: int = 50
    socket_timeout: int = 5
    db: int = 0


@dataclass
class PostgresConfig:
    """PostgreSQL connection configuration"""
    url: str
    max_connections: int = 20


@dataclass
class MessageBusConfig:
    """Message Bus configuration"""
    priority_streams: int = 5
    max_retries: int = 3
    dlq_stream: str = "messages:dlq"
    retention_days: int = 730
    consumer_read_count: int = 10
    consumer_block_ms: int = 5000
    signature_required: bool = True
    signature_algo: str = "hmac-sha256"


@dataclass
class ObservabilityConfig:
    """Observability configuration"""
    log_level: str = "INFO"
    log_format: str = "json"
    enable_opentelemetry: bool = False
    otel_endpoint: Optional[str] = None
    prometheus_port: int = 9090
    metrics_enabled: bool = True


@dataclass
class AppConfig:
    """Main application configuration"""
    redis: RedisConfig
    postgres: PostgresConfig
    message_bus: MessageBusConfig
    observability: ObservabilityConfig
    environment: str = "development"
    debug: bool = True
    agent_config_path: str = "waooaw/config/agent_config.yaml"
    message_bus_config_path: str = "waooaw/config/message_bus_config.yaml"


def load_app_config() -> AppConfig:
    """
    Load application configuration from environment variables.
    
    Environment variables take precedence over YAML files.
    Missing required vars will raise ValueError.
    
    Returns:
        AppConfig: Complete application configuration
        
    Raises:
        ValueError: If required environment variables are missing
    """
    # Load Redis config
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        raise ValueError("REDIS_URL environment variable is required")
    
    redis_config = RedisConfig(
        url=redis_url,
        max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "50")),
        socket_timeout=int(os.getenv("REDIS_SOCKET_TIMEOUT", "5")),
        db=int(os.getenv("REDIS_DB", "0"))
    )
    
    # Load PostgreSQL config
    postgres_url = os.getenv("POSTGRES_URL")
    if not postgres_url:
        raise ValueError("POSTGRES_URL environment variable is required")
    
    postgres_config = PostgresConfig(
        url=postgres_url,
        max_connections=int(os.getenv("POSTGRES_MAX_CONNECTIONS", "20"))
    )
    
    # Load Message Bus config
    message_bus_config = MessageBusConfig(
        priority_streams=int(os.getenv("MESSAGE_BUS_PRIORITY_STREAMS", "5")),
        max_retries=int(os.getenv("MESSAGE_BUS_MAX_RETRIES", "3")),
        dlq_stream=os.getenv("MESSAGE_BUS_DLQ_STREAM", "messages:dlq"),
        retention_days=int(os.getenv("MESSAGE_BUS_RETENTION_DAYS", "730")),
        consumer_read_count=int(os.getenv("MESSAGE_BUS_CONSUMER_READ_COUNT", "10")),
        consumer_block_ms=int(os.getenv("MESSAGE_BUS_CONSUMER_BLOCK_MS", "5000")),
        signature_required=os.getenv("MESSAGE_BUS_SIGNATURE_REQUIRED", "true").lower() == "true",
        signature_algo=os.getenv("MESSAGE_BUS_SIGNATURE_ALGO", "hmac-sha256")
    )
    
    # Load Observability config
    observability_config = ObservabilityConfig(
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_format=os.getenv("LOG_FORMAT", "json"),
        enable_opentelemetry=os.getenv("ENABLE_OPENTELEMETRY", "false").lower() == "true",
        otel_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
        prometheus_port=int(os.getenv("PROMETHEUS_PORT", "9090")),
        metrics_enabled=os.getenv("METRICS_ENABLED", "true").lower() == "true"
    )
    
    # Create main config
    config = AppConfig(
        environment=os.getenv("ENVIRONMENT", "development"),
        debug=os.getenv("DEBUG", "true").lower() == "true",
        redis=redis_config,
        postgres=postgres_config,
        message_bus=message_bus_config,
        observability=observability_config,
        agent_config_path=os.getenv("AGENT_CONFIG_PATH", "waooaw/config/agent_config.yaml"),
        message_bus_config_path=os.getenv("MESSAGE_BUS_CONFIG_PATH", "waooaw/config/message_bus_config.yaml")
    )
    
    return config


def get_agent_secret_key(agent_id: str) -> str:
    """
    Get secret key for an agent from environment variables.
    
    Args:
        agent_id: Agent ID (e.g., "wow-vision-prime")
        
    Returns:
        Secret key as hex string
        
    Raises:
        ValueError: If secret key not found in environment
    """
    # Convert agent ID to env var name: wow-vision-prime -> WOW_VISION_PRIME
    env_var = f"AGENT_SECRET_KEY_{agent_id.upper().replace('-', '_')}"
    secret_key = os.getenv(env_var)
    
    if not secret_key:
        raise ValueError(
            f"Secret key not found for agent '{agent_id}'. "
            f"Set environment variable: {env_var}"
        )
    
    # Validate hex string (should be 64 chars for 32-byte key)
    if len(secret_key) != 64 or not all(c in '0123456789abcdefABCDEF' for c in secret_key):
        raise ValueError(
            f"Invalid secret key for agent '{agent_id}'. "
            f"Must be 64-character hex string. "
            f"Generate with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    
    return secret_key


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load agent configuration from YAML file with environment variable expansion.
    
    Args:
        config_path: Path to config file (default: waooaw/config/agent_config.yaml)
    
    Returns:
        Configuration dictionary
    """
    if config_path is None:
        # Default path
        config_dir = Path(__file__).parent
        config_path = config_dir / "agent_config.yaml"
        
        # Check for local override
        local_config = config_dir / "agent_config.local.yaml"
        if local_config.exists():
            config_path = local_config
    
    # Load YAML
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Expand environment variables recursively
    config = _expand_env_vars(config)
    
    # Build database URL if not provided
    if 'database' in config:
        if 'url' not in config['database'] or not config['database']['url']:
            db = config['database']
            config['database']['url'] = (
                f"postgresql://{db['user']}:{db['password']}"
                f"@{db['host']}:{db['port']}/{db['database']}"
            )
    
    # Flatten for compatibility with agent initialization
    flat_config = {
        'database_url': config.get('database', {}).get('url'),
        'github_token': config.get('github', {}).get('token'),
        'github_repo': config.get('github', {}).get('repo'),
        'pinecone_api_key': config.get('pinecone', {}).get('api_key'),
        'anthropic_api_key': config.get('anthropic', {}).get('api_key'),
        'openai_api_key': config.get('openai', {}).get('api_key'),
    }
    
    # Merge with full config
    flat_config.update(config)
    
    return flat_config


def _expand_env_vars(obj: Any) -> Any:
    """Recursively expand environment variables in config"""
    if isinstance(obj, dict):
        return {k: _expand_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_expand_env_vars(item) for item in obj]
    elif isinstance(obj, str):
        # Check for ${VAR} or ${VAR:-default} syntax
        if obj.startswith('${') and obj.endswith('}'):
            var_expr = obj[2:-1]
            
            # Handle default value syntax: ${VAR:-default}
            if ':-' in var_expr:
                var_name, default = var_expr.split(':-', 1)
                return os.getenv(var_name, default)
            else:
                return os.getenv(var_expr, obj)
        return obj
    else:
        return obj
