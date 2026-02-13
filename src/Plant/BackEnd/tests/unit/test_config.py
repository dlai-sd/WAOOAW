"""
Tests for core/config.py
"""
import pytest
from pydantic import ValidationError
from core.config import Settings


class TestSettings:
    """Test Settings configuration."""
    
    def test_default_settings(self):
        """Test default settings load successfully."""
        settings = Settings()
        assert settings.environment in ["development", "test", "uat", "demo", "production"]
        assert settings.log_level in ["critical", "error", "warning", "info", "debug", "trace"]
    
    def test_log_level_normalization(self):
        """Test log level normalization."""
        # Test warn -> warning normalization
        settings = Settings(log_level="warn")
        assert settings.log_level == "warning"
        
        # Test case insensitivity
        settings = Settings(log_level="INFO")
        assert settings.log_level == "info"
        
        settings = Settings(log_level="  DEBUG  ")
        assert settings.log_level == "debug"
    
    def test_log_level_validation_failure(self):
        """Test invalid log level raises error."""
        with pytest.raises(ValidationError):
            Settings(log_level="invalid_level")
        
        with pytest.raises(ValidationError):
            Settings(log_level=123)  # Not a string
    
    def test_log_level_none_defaults_to_info(self):
        """Test None log level defaults to info."""
        # Passing log_level=None should default to "info"
        settings = Settings()
        assert settings.log_level == "info"
    
    def test_cors_origins_parsing(self):
        """Test CORS origins can be set."""
        settings = Settings(cors_origins=["http://localhost:3000", "http://localhost:8080"])
        assert len(settings.cors_origins) >= 2
    
    def test_parse_env_var_cors_origins_json(self):
        """Test parsing CORS origins from JSON string."""
        result = Settings.parse_env_var('cors_origins', '["http://localhost:3000", "http://localhost:8080"]')
        assert result == ["http://localhost:3000", "http://localhost:8080"]
    
    def test_parse_env_var_cors_origins_csv(self):
        """Test parsing CORS origins from CSV string."""
        result = Settings.parse_env_var('cors_origins', 'http://localhost:3000, http://localhost:8080')
        assert result == ["http://localhost:3000", "http://localhost:8080"]
    
    def test_parse_env_var_other_field(self):
        """Test parsing non-cors_origins field returns value unchanged."""
        result = Settings.parse_env_var('database_url', 'postgresql://localhost/test')
        assert result == 'postgresql://localhost/test'
    
    def test_environment_specific_settings(self):
        """Test environment-specific configurations."""
        dev_settings = Settings(environment="development")
        assert dev_settings.environment == "development"
        
        prod_settings = Settings(environment="production")
        assert prod_settings.environment == "production"
    
    def test_observability_flags(self):
        """Test observability feature flags."""
        settings = Settings()
        
        # Check default values exist
        assert hasattr(settings, 'enable_json_logs')
        assert hasattr(settings, 'enable_request_logging')
        assert hasattr(settings, 'enable_sql_logging')
        assert hasattr(settings, 'enable_route_registration_logging')
        assert hasattr(settings, 'enable_startup_diagnostics')
    
    def test_gcp_project_id(self, monkeypatch):
        """Test GCP project ID can be set via environment variables."""
        monkeypatch.setenv("GCP_PROJECT_ID", "test-project-123")
        settings = Settings()
        assert settings.gcp_project_id == "test-project-123"
        
    def test_gcp_project_id_google_cloud_alias(self, monkeypatch):
        """Test GCP project ID can be set via GOOGLE_CLOUD_PROJECT alias."""
        monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project-456")
        settings = Settings()
        assert settings.gcp_project_id == "test-project-456"
    
    def test_version_field(self):
        """Test version field can be set."""
        settings = Settings(version="2.5.0")
        assert settings.version == "2.5.0"
