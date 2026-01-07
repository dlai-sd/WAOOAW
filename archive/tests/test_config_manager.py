"""
Unit Tests for Configuration Management - Story 5.2
"""
import pytest
import os
import tempfile
from pathlib import Path

import sys
sys.path.insert(0, '/workspaces/WAOOAW')

from waooaw.common.config_manager import (
    ConfigManager,
    ConfigSchema,
    ConfigurationError,
    init_config,
    get_config
)


class TestConfigManager:
    """Test configuration manager."""
    
    def test_init_empty(self):
        """Should initialize with no config file."""
        config = ConfigManager()
        
        assert config.environment == "development"
        assert config.config == {}
    
    def test_load_yaml_config(self):
        """Should load configuration from YAML."""
        # Create temp YAML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("database:\n  host: localhost\n  port: 5432\n")
            temp_file = f.name
        
        try:
            config = ConfigManager(config_file=temp_file)
            
            assert config.get("database.host") == "localhost"
            assert config.get("database.port") == 5432
        finally:
            os.unlink(temp_file)
    
    def test_environment_specific_config(self):
        """Should load environment-specific section."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
development:
  debug: true
production:
  debug: false
""")
            temp_file = f.name
        
        try:
            config = ConfigManager(config_file=temp_file, environment="production")
            
            assert config.get("debug") is False
        finally:
            os.unlink(temp_file)
    
    def test_get_with_default(self):
        """Should return default if key not found."""
        config = ConfigManager()
        
        value = config.get("nonexistent.key", default="default_value")
        
        assert value == "default_value"
    
    def test_set_value(self):
        """Should set configuration value."""
        config = ConfigManager()
        
        config.set("test.key", "test_value")
        
        assert config.get("test.key") == "test_value"
    
    def test_env_overrides(self):
        """Should apply environment variable overrides."""
        # Set env variable
        os.environ["WAOOAW_CONFIG_TEST__KEY"] = "env_value"
        
        try:
            config = ConfigManager()
            
            assert config.get("test.key") == "env_value"
        finally:
            del os.environ["WAOOAW_CONFIG_TEST__KEY"]
    
    def test_env_value_parsing(self):
        """Should parse environment values correctly."""
        os.environ["WAOOAW_CONFIG_BOOL"] = "true"
        os.environ["WAOOAW_CONFIG_INT"] = "42"
        os.environ["WAOOAW_CONFIG_FLOAT"] = "3.14"
        os.environ["WAOOAW_CONFIG_STR"] = "hello"
        
        try:
            config = ConfigManager()
            
            assert config.get("bool") is True
            assert config.get("int") == 42
            assert config.get("float") == 3.14
            assert config.get("str") == "hello"
        finally:
            del os.environ["WAOOAW_CONFIG_BOOL"]
            del os.environ["WAOOAW_CONFIG_INT"]
            del os.environ["WAOOAW_CONFIG_FLOAT"]
            del os.environ["WAOOAW_CONFIG_STR"]
    
    def test_schema_required_keys(self):
        """Should validate required keys."""
        schema = ConfigSchema(required_keys=["required_field"])
        
        with pytest.raises(ConfigurationError):
            ConfigManager(schema=schema)
    
    def test_schema_defaults(self):
        """Should apply default values."""
        schema = ConfigSchema(
            defaults={"optional_field": "default_value"}
        )
        
        config = ConfigManager(schema=schema)
        
        assert config.get("optional_field") == "default_value"
    
    def test_schema_validators(self):
        """Should run custom validators."""
        def validate_port(value):
            return 1 <= value <= 65535
        
        schema = ConfigSchema(
            validators={"port": validate_port}
        )
        
        config = ConfigManager(schema=schema)
        config.set("port", 8080)
        
        # Should not raise
        config._validate()
        
        # Invalid port should raise
        config.set("port", 99999)
        with pytest.raises(ConfigurationError):
            config._validate()
    
    def test_reload(self):
        """Should reload configuration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("version: 1\n")
            temp_file = f.name
        
        try:
            config = ConfigManager(config_file=temp_file)
            assert config.get("version") == 1
            
            # Update file
            with open(temp_file, 'w') as f:
                f.write("version: 2\n")
            
            # Reload
            config.reload()
            assert config.get("version") == 2
        finally:
            os.unlink(temp_file)


class TestGlobalConfig:
    """Test global configuration functions."""
    
    def test_init_and_get(self):
        """Should initialize and retrieve global config."""
        config = init_config(environment="test")
        
        retrieved = get_config()
        
        assert retrieved is config
    
    def test_get_without_init(self):
        """Should raise if not initialized."""
        # Clear global
        import waooaw.common.config_manager as cm
        cm._global_config = None
        
        with pytest.raises(ConfigurationError):
            get_config()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
