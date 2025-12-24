"""
Configuration Loader

Loads agent configuration from YAML and environment variables.
"""

import os
import yaml
from typing import Any, Dict
from pathlib import Path


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
