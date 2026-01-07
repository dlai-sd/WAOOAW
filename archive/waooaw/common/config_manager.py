"""
Configuration Management - Story 5.2

Centralized configuration with validation and environment support.
Part of Epic 5: Common Components.
"""
import logging
import os
import yaml
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ConfigSchema:
    """Configuration schema definition."""
    required_keys: List[str] = field(default_factory=list)
    optional_keys: List[str] = field(default_factory=list)
    defaults: Dict[str, Any] = field(default_factory=dict)
    validators: Dict[str, callable] = field(default_factory=dict)


class ConfigurationError(Exception):
    """Configuration error."""
    pass


class ConfigManager:
    """
    Centralized configuration management.
    
    Features:
    - Load from YAML files
    - Environment variable overrides
    - Schema validation
    - Default values
    - Environment-specific configs (dev/staging/prod)
    - Hot reload (watch for changes)
    """
    
    def __init__(
        self,
        config_file: Optional[str] = None,
        environment: str = "development",
        schema: Optional[ConfigSchema] = None
    ):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to YAML config file
            environment: Environment name (development, staging, production)
            schema: Configuration schema for validation
        """
        self.config_file = config_file
        self.environment = environment
        self.schema = schema or ConfigSchema()
        
        self.config: Dict[str, Any] = {}
        self._load_config()
        self._apply_env_overrides()
        self._validate()
        
        logger.info(
            f"ConfigManager initialized: env={environment}, file={config_file}"
        )
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Config key (supports dot notation: "database.host")
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        # Support dot notation
        keys = key.split(".")
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value (runtime only, not persisted).
        
        Args:
            key: Config key
            value: New value
        """
        keys = key.split(".")
        config = self.config
        
        # Navigate to parent
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set value
        config[keys[-1]] = value
        
        logger.debug(f"Config updated: {key} = {value}")
    
    def get_all(self) -> Dict[str, Any]:
        """Get entire configuration."""
        return self.config.copy()
    
    def reload(self) -> None:
        """Reload configuration from file."""
        self.config.clear()
        self._load_config()
        self._apply_env_overrides()
        self._validate()
        
        logger.info("Configuration reloaded")
    
    def _load_config(self) -> None:
        """Load configuration from file."""
        if not self.config_file:
            # No file, use empty config
            self.config = {}
            return
        
        config_path = Path(self.config_file)
        
        if not config_path.exists():
            logger.warning(f"Config file not found: {self.config_file}")
            self.config = {}
            return
        
        try:
            with open(config_path, 'r') as f:
                loaded = yaml.safe_load(f) or {}
            
            # Check for environment-specific section
            if self.environment in loaded:
                self.config = loaded[self.environment]
                logger.debug(f"Loaded environment-specific config: {self.environment}")
            else:
                self.config = loaded
                logger.debug("Loaded base configuration")
        
        except Exception as e:
            logger.error(f"Failed to load config: {e}", exc_info=True)
            raise ConfigurationError(f"Failed to load config from {self.config_file}: {e}")
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides."""
        # Convention: WAOOAW_CONFIG_KEY__SUBKEY=value
        prefix = "WAOOAW_CONFIG_"
        
        for env_key, env_value in os.environ.items():
            if env_key.startswith(prefix):
                # Extract config key
                config_key = env_key[len(prefix):].lower().replace("__", ".")
                
                # Parse value
                parsed_value = self._parse_env_value(env_value)
                
                # Set in config
                self.set(config_key, parsed_value)
                
                logger.debug(f"Applied env override: {config_key} = {parsed_value}")
    
    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable value."""
        # Try boolean
        if value.lower() in ["true", "yes", "1"]:
            return True
        if value.lower() in ["false", "no", "0"]:
            return False
        
        # Try int
        try:
            return int(value)
        except ValueError:
            pass
        
        # Try float
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def _validate(self) -> None:
        """Validate configuration against schema."""
        # Check required keys
        for key in self.schema.required_keys:
            if self.get(key) is None:
                raise ConfigurationError(f"Required config key missing: {key}")
        
        # Apply defaults for optional keys
        for key, default in self.schema.defaults.items():
            if self.get(key) is None:
                self.set(key, default)
        
        # Run custom validators
        for key, validator in self.schema.validators.items():
            value = self.get(key)
            if value is not None:
                try:
                    if not validator(value):
                        raise ConfigurationError(
                            f"Validation failed for {key}: {value}"
                        )
                except Exception as e:
                    raise ConfigurationError(
                        f"Validator error for {key}: {e}"
                    )
        
        logger.debug("Configuration validated")


# Global config instance
_global_config: Optional[ConfigManager] = None


def init_config(
    config_file: Optional[str] = None,
    environment: Optional[str] = None,
    schema: Optional[ConfigSchema] = None
) -> ConfigManager:
    """
    Initialize global configuration.
    
    Args:
        config_file: Path to config file
        environment: Environment name
        schema: Config schema
        
    Returns:
        ConfigManager instance
    """
    global _global_config
    
    if environment is None:
        environment = os.environ.get("WAOOAW_ENV", "development")
    
    _global_config = ConfigManager(
        config_file=config_file,
        environment=environment,
        schema=schema
    )
    
    return _global_config


def get_config() -> ConfigManager:
    """
    Get global configuration instance.
    
    Returns:
        ConfigManager instance
        
    Raises:
        ConfigurationError: If not initialized
    """
    if _global_config is None:
        raise ConfigurationError("Configuration not initialized. Call init_config() first.")
    
    return _global_config


def get(key: str, default: Any = None) -> Any:
    """Convenience function to get config value."""
    return get_config().get(key, default)
