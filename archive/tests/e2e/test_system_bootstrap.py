"""
E2E Test Scenarios - System Bootstrap & Configuration
"""
import pytest
import tempfile
import os
import sys
sys.path.insert(0, '/workspaces/WAOOAW')

from waooaw.common.config_manager import ConfigManager
from waooaw.common.secrets_manager import SecretsManager
from waooaw.common.health_checks import HealthCheckManager


class TestSystemBootstrapE2E:
    """End-to-end tests for system initialization."""
    
    def test_complete_system_bootstrap(self):
        """E2E: System starts from zero to fully operational."""
        # Create test config
        config_content = """
production:
  app:
    name: WowVision
  database:
    host: localhost
"""
        fd, config_path = tempfile.mkstemp(suffix='.yaml')
        os.write(fd, config_content.encode())
        os.close(fd)
        
        os.environ["DB_PASSWORD"] = "test_password"
        
        try:
            # Load configuration
            config = ConfigManager(config_file=config_path, environment="production")
            assert config.get("app.name") == "WowVision"
            
            # Load secrets
            secrets = SecretsManager(environment="production")
            secrets.register_secret("db_password", "Password", env_var="DB_PASSWORD")
            secrets.load_secret("db_password")
            
            # Set up health checks
            health = HealthCheckManager()
            health.register_function(
                "config_loaded",
                lambda: config.get("app.name") is not None,
                critical=True
            )
            
            # Run health checks
            report = health.get_health_report()
            
            # Verify system operational
            assert report["status"] == "healthy"
            
        finally:
            os.unlink(config_path)
            if "DB_PASSWORD" in os.environ:
                del os.environ["DB_PASSWORD"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
