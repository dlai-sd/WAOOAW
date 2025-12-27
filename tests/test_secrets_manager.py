"""
Unit Tests for Secrets Management - Story 5.3
"""
import pytest
import os
import tempfile

import sys
sys.path.insert(0, '/workspaces/WAOOAW')

from waooaw.common.secrets_manager import (
    SecretsManager,
    SecretNotFoundError,
    SecretValidationError,
    init_secrets
)


class TestSecretsManager:
    """Test secrets manager."""
    
    def test_init(self):
        """Should initialize secrets manager."""
        manager = SecretsManager()
        
        assert manager.environment == "development"
        assert len(manager._secrets) == 0
    
    def test_register_secret(self):
        """Should register secret metadata."""
        manager = SecretsManager()
        
        manager.register_secret(
            "api_key",
            description="API Key",
            required=True
        )
        
        assert "api_key" in manager._metadata
        assert manager._metadata["api_key"].env_var == "API_KEY"
    
    def test_load_secret_from_env(self):
        """Should load secret from environment."""
        os.environ["TEST_SECRET"] = "secret_value"
        
        try:
            manager = SecretsManager()
            manager.register_secret("test_secret", "Test Secret")
            manager.load_secret("test_secret")
            
            assert manager.has_secret("test_secret")
            assert manager.get_secret("test_secret") == "secret_value"
        finally:
            del os.environ["TEST_SECRET"]
    
    def test_required_secret_missing(self):
        """Should raise if required secret missing."""
        manager = SecretsManager()
        manager.register_secret("missing_secret", "Missing", required=True)
        
        with pytest.raises(SecretNotFoundError):
            manager.load_secret("missing_secret")
    
    def test_optional_secret_with_default(self):
        """Should use default for optional secrets."""
        manager = SecretsManager()
        manager.register_secret("optional", "Optional", required=False)
        
        manager.load_secret("optional", default="default_value")
        
        assert manager.get_secret("optional") == "default_value"
    
    def test_secret_validation(self):
        """Should validate secret format."""
        os.environ["VALIDATED_SECRET"] = "invalid"
        
        try:
            manager = SecretsManager()
            manager.register_secret(
                "validated_secret",
                "Validated",
                validation_pattern=r"^sk-[a-zA-Z0-9]{32}$"
            )
            
            with pytest.raises(SecretValidationError):
                manager.load_secret("validated_secret")
        finally:
            del os.environ["VALIDATED_SECRET"]
    
    def test_get_secret_safe(self):
        """Should return None safely if secret not found."""
        manager = SecretsManager()
        
        value = manager.get_secret_safe("nonexistent")
        
        assert value is None
    
    def test_list_secrets(self):
        """Should list all registered secrets."""
        manager = SecretsManager()
        
        manager.register_secret("secret1", "Secret 1")
        manager.register_secret("secret2", "Secret 2")
        
        secrets = manager.list_secrets()
        
        assert len(secrets) == 2
        assert "secret1" in secrets
        assert secrets["secret1"]["description"] == "Secret 1"
    
    def test_load_all_secrets(self):
        """Should load all secrets."""
        os.environ["SECRET1"] = "value1"
        os.environ["SECRET2"] = "value2"
        
        try:
            manager = SecretsManager()
            manager.register_secret("secret1", "Secret 1")
            manager.register_secret("secret2", "Secret 2")
            
            results = manager.load_all_secrets()
            
            assert results["secret1"] is True
            assert results["secret2"] is True
        finally:
            del os.environ["SECRET1"]
            del os.environ["SECRET2"]
    
    def test_env_file_loading(self):
        """Should load secrets from .env file."""
        # Create temp .env file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("TEST_ENV_SECRET=env_file_value\n")
            f.write("# Comment line\n")
            f.write("ANOTHER_SECRET=another_value\n")
            temp_file = f.name
        
        try:
            manager = SecretsManager(
                env_file=temp_file,
                environment="development"
            )
            manager.register_secret("test_env_secret", "Test")
            manager.load_secret("test_env_secret")
            
            assert manager.get_secret("test_env_secret") == "env_file_value"
        finally:
            os.unlink(temp_file)
            if "TEST_ENV_SECRET" in os.environ:
                del os.environ["TEST_ENV_SECRET"]
    
    def test_production_no_env_file(self):
        """Should not load .env in production."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("PROD_SECRET=should_not_load\n")
            temp_file = f.name
        
        try:
            manager = SecretsManager(
                env_file=temp_file,
                environment="production"
            )
            
            # Env file should not be loaded in production
            assert "PROD_SECRET" not in os.environ
        finally:
            os.unlink(temp_file)
    
    def test_stats(self):
        """Should report statistics."""
        manager = SecretsManager()
        manager.register_secret("s1", "Secret 1")
        manager.register_secret("s2", "Secret 2", required=False)
        
        os.environ["S1"] = "value1"
        try:
            manager.load_secret("s1")
            
            stats = manager.get_stats()
            
            assert stats["total_registered"] == 2
            assert stats["total_loaded"] == 1
            assert stats["required_count"] == 1
        finally:
            del os.environ["S1"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
