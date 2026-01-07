"""
Integration Tests - Config + Secrets + Health

Tests the integration of common components.
"""
import pytest
import tempfile
import os
import sys
sys.path.insert(0, '/workspaces/WAOOAW')

from waooaw.common.config_manager import ConfigManager
from waooaw.common.secrets_manager import SecretsManager
from waooaw.common.health_checks import HealthCheckManager


class TestCommonComponentsIntegration:
    """Integration tests for common components."""
    
    def test_config_secrets_integration(self):
        """Should integrate config and secrets."""
        # Create temp config file
        config_content = """
development:
  database:
    host: localhost
    port: 5432
  api:
    timeout: 30
"""
        fd, config_path = tempfile.mkstemp(suffix='.yaml')
        os.write(fd, config_content.encode())
        os.close(fd)
        
        try:
            # Load config
            config = ConfigManager(config_file=config_path, environment="development")
            
            # Set up secrets
            os.environ["DB_PASSWORD"] = "secret_password_123"
            
            secrets = SecretsManager(environment="development")
            secrets.register_secret(
                "db_password",
                "Database password",
                env_var="DB_PASSWORD"
            )
            secrets.load_secret("db_password")
            
            # Should work together
            db_host = config.get("database.host")
            db_password = secrets.get_secret("db_password")
            
            assert db_host == "localhost"
            assert db_password == "secret_password_123"
            
        finally:
            os.unlink(config_path)
            if "DB_PASSWORD" in os.environ:
                del os.environ["DB_PASSWORD"]
    
    def test_config_health_integration(self):
        """Should integrate config and health checks."""
        config_content = """
development:
  health:
    check_interval: 60
    timeout: 5
  database:
    host: localhost
"""
        fd, config_path = tempfile.mkstemp(suffix='.yaml')
        os.write(fd, config_content.encode())
        os.close(fd)
        
        try:
            config = ConfigManager(config_file=config_path, environment="development")
            health = HealthCheckManager()
            
            # Register health check using config
            def db_check():
                db_host = config.get("database.host")
                return db_host == "localhost"
            
            health.register_function("database", db_check)
            
            # Run check
            result = health.run_check("database")
            
            assert result.status.value == "healthy"
            
        finally:
            os.unlink(config_path)
    
    def test_secrets_health_integration(self):
        """Should integrate secrets and health checks."""
        os.environ["API_KEY"] = "test_key_123"
        
        try:
            secrets = SecretsManager()
            secrets.register_secret("api_key", "API Key", env_var="API_KEY")
            secrets.load_secret("api_key")
            
            health = HealthCheckManager()
            
            # Health check for secrets
            def secrets_check():
                return secrets.has_secret("api_key")
            
            health.register_function("secrets_loaded", secrets_check)
            
            result = health.run_check("secrets_loaded")
            
            assert result.status.value == "healthy"
            
        finally:
            if "API_KEY" in os.environ:
                del os.environ["API_KEY"]
    
    def test_full_bootstrap_sequence(self):
        """Should bootstrap all common components in order."""
        config_content = """
test:
  database:
    host: localhost
    port: 5432
  redis:
    host: localhost
    port: 6379
"""
        fd, config_path = tempfile.mkstemp(suffix='.yaml')
        os.write(fd, config_content.encode())
        os.close(fd)
        
        os.environ["DB_PASSWORD"] = "test_password"
        os.environ["REDIS_PASSWORD"] = "redis_password"
        
        try:
            # 1. Load config
            config = ConfigManager(config_file=config_path, environment="test")
            assert config.get("database.host") == "localhost"
            
            # 2. Load secrets
            secrets = SecretsManager(environment="test")
            secrets.register_secret("db_password", "DB Password", env_var="DB_PASSWORD")
            secrets.register_secret("redis_password", "Redis Password", env_var="REDIS_PASSWORD")
            secrets.load_all_secrets()
            
            assert secrets.has_secret("db_password")
            assert secrets.has_secret("redis_password")
            
            # 3. Set up health checks
            health = HealthCheckManager()
            
            health.register_function(
                "config_loaded",
                lambda: config.get("database.host") is not None
            )
            
            health.register_function(
                "secrets_loaded",
                lambda: secrets.has_secret("db_password")
            )
            
            # 4. Run health checks
            report = health.get_health_report()
            
            assert report["status"] == "healthy"
            assert len(report["checks"]) == 2
            
        finally:
            os.unlink(config_path)
            if "DB_PASSWORD" in os.environ:
                del os.environ["DB_PASSWORD"]
            if "REDIS_PASSWORD" in os.environ:
                del os.environ["REDIS_PASSWORD"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
