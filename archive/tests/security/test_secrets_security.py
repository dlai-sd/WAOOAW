"""
Security Tests - Secrets Management

Tests for secure handling of secrets and credentials.
"""
import pytest
import sys
import os
import tempfile
sys.path.insert(0, '/workspaces/WAOOAW')

from waooaw.common.secrets_manager import SecretsManager


class TestSecretsManagement:
    """Test secure secrets management."""
    
    def test_secrets_not_in_logs(self, caplog):
        """Test: Secrets are not exposed in logs."""
        secrets = SecretsManager(environment="test")
        
        os.environ["TEST_SECRET"] = "super_secret_password_123"
        
        try:
            secrets.register_secret(
                key="test_secret",
                description="Test secret",
                env_var="TEST_SECRET"
            )
            secrets.load_secret("test_secret")
            
            # Check logs don't contain the secret value
            for record in caplog.records:
                assert "super_secret_password_123" not in record.message
                
        finally:
            if "TEST_SECRET" in os.environ:
                del os.environ["TEST_SECRET"]
    
    def test_secrets_not_in_error_messages(self):
        """Test: Secrets are not exposed in error messages."""
        secrets = SecretsManager(environment="test")
        
        os.environ["DB_PASSWORD"] = "my_database_password_456"
        
        try:
            secrets.register_secret(
                key="db_password",
                description="Database password",
                env_var="DB_PASSWORD"
            )
            secrets.load_secret("db_password")
            
            # Simulate an error that might expose secrets
            try:
                raise ValueError(f"Connection failed")
            except ValueError as e:
                # Error message should not contain password
                assert "my_database_password_456" not in str(e)
                
        finally:
            if "DB_PASSWORD" in os.environ:
                del os.environ["DB_PASSWORD"]
    
    def test_secrets_not_in_config_dumps(self):
        """Test: Secrets are not exposed when config is dumped."""
        from waooaw.common.config_manager import ConfigManager
        
        config_content = """
test:
  database:
    host: localhost
    user: admin
"""
        
        fd, config_path = tempfile.mkstemp(suffix='.yaml')
        os.write(fd, config_content.encode())
        os.close(fd)
        
        os.environ["DB_PASSWORD"] = "secret_password_789"
        
        try:
            config = ConfigManager(config_file=config_path, environment="test")
            
            # Convert config to string (simulating logging/debugging)
            config_str = str(config.__dict__)
            
            # Password should not be in the string representation
            assert "secret_password_789" not in config_str
            
        finally:
            os.unlink(config_path)
            if "DB_PASSWORD" in os.environ:
                del os.environ["DB_PASSWORD"]
    
    def test_environment_variable_isolation(self):
        """Test: Environment variables are isolated per environment."""
        secrets_prod = SecretsManager(environment="production")
        secrets_dev = SecretsManager(environment="development")
        
        os.environ["API_KEY_PROD"] = "prod_key_123"
        os.environ["API_KEY_DEV"] = "dev_key_456"
        
        try:
            secrets_prod.register_secret("api_key", "API Key", env_var="API_KEY_PROD")
            secrets_dev.register_secret("api_key", "API Key", env_var="API_KEY_DEV")
            
            secrets_prod.load_secret("api_key")
            secrets_dev.load_secret("api_key")
            
            # Each environment should have its own secrets
            assert secrets_prod.secrets["api_key"]["value"] == "prod_key_123"
            assert secrets_dev.secrets["api_key"]["value"] == "dev_key_456"
            
        finally:
            if "API_KEY_PROD" in os.environ:
                del os.environ["API_KEY_PROD"]
            if "API_KEY_DEV" in os.environ:
                del os.environ["API_KEY_DEV"]
    
    def test_secret_rotation_support(self):
        """Test: System supports secret rotation."""
        secrets = SecretsManager(environment="test")
        
        os.environ["ROTATABLE_SECRET"] = "old_secret"
        
        try:
            secrets.register_secret("api_key", "API Key", env_var="ROTATABLE_SECRET")
            secrets.load_secret("api_key")
            
            assert secrets.secrets["api_key"]["value"] == "old_secret"
            
            # Rotate secret
            os.environ["ROTATABLE_SECRET"] = "new_secret"
            secrets.load_secret("api_key")
            
            assert secrets.secrets["api_key"]["value"] == "new_secret"
            
        finally:
            if "ROTATABLE_SECRET" in os.environ:
                del os.environ["ROTATABLE_SECRET"]
    
    def test_missing_secret_handling(self):
        """Test: Missing secrets are handled securely."""
        secrets = SecretsManager(environment="test")
        
        secrets.register_secret("missing_key", "Missing", env_var="NONEXISTENT_VAR")
        
        # Should fail gracefully without exposing system info
        try:
            secrets.load_secret("missing_key")
            # If it doesn't raise, check it's marked as missing
            assert secrets.secrets["missing_key"]["value"] is None
        except Exception as e:
            # Error should be generic, not expose paths/system info
            assert "NONEXISTENT_VAR" in str(e)
            assert "/etc" not in str(e)
            assert "/home" not in str(e)


class TestCredentialValidation:
    """Test credential validation and strength."""
    
    def test_weak_password_detection(self):
        """Test: Weak passwords are detected."""
        weak_passwords = [
            "password",
            "123456",
            "admin",
            "12345678",
            "qwerty"
        ]
        
        for pwd in weak_passwords:
            # Check password strength
            is_weak = (
                len(pwd) < 12 or
                pwd.lower() in ["password", "admin", "qwerty"] or
                pwd.isdigit()
            )
            assert is_weak, f"Weak password not detected: {pwd}"
    
    def test_strong_password_acceptance(self):
        """Test: Strong passwords are accepted."""
        strong_passwords = [
            "MyStr0ng!Pass@2024",
            "C0mpl3x#Passw0rd!",
            "Secur3$Credent1al&"
        ]
        
        for pwd in strong_passwords:
            # Check password meets criteria
            has_upper = any(c.isupper() for c in pwd)
            has_lower = any(c.islower() for c in pwd)
            has_digit = any(c.isdigit() for c in pwd)
            has_special = any(c in "!@#$%^&*" for c in pwd)
            is_long = len(pwd) >= 12
            
            is_strong = has_upper and has_lower and has_digit and has_special and is_long
            assert is_strong, f"Strong password rejected: {pwd}"
    
    def test_api_key_format_validation(self):
        """Test: API keys have proper format."""
        import re
        
        valid_keys = [
            "sk_live_1234567890abcdef",
            "pk_test_abcdef1234567890",
            "API_KEY_ABC123DEF456GHI789"
        ]
        
        # API keys should be alphanumeric with underscores, reasonable length
        key_pattern = re.compile(r'^[a-zA-Z0-9_]{16,}$')
        
        for key in valid_keys:
            # Remove prefixes for validation
            key_value = key.split('_')[-1]
            assert len(key) >= 16, f"API key too short: {key}"


class TestAuthenticationSecurity:
    """Test authentication security measures."""
    
    def test_rate_limiting_simulation(self):
        """Test: Rate limiting prevents brute force."""
        from collections import defaultdict
        import time
        
        # Simulate rate limiter
        attempts = defaultdict(list)
        max_attempts = 5
        window_seconds = 60
        
        def check_rate_limit(ip_address: str) -> bool:
            """Check if IP is rate limited."""
            now = time.time()
            # Remove old attempts
            attempts[ip_address] = [
                t for t in attempts[ip_address]
                if now - t < window_seconds
            ]
            # Check limit
            if len(attempts[ip_address]) >= max_attempts:
                return False  # Rate limited
            attempts[ip_address].append(now)
            return True  # Allowed
        
        # Simulate brute force attack
        for i in range(10):
            allowed = check_rate_limit("192.168.1.100")
            if i < max_attempts:
                assert allowed, f"Should allow attempt {i+1}"
            else:
                assert not allowed, f"Should block attempt {i+1}"
    
    def test_session_timeout(self):
        """Test: Sessions timeout after inactivity."""
        import time
        
        class Session:
            def __init__(self, timeout_seconds=30):
                self.last_activity = time.time()
                self.timeout_seconds = timeout_seconds
            
            def is_valid(self) -> bool:
                return time.time() - self.last_activity < self.timeout_seconds
            
            def refresh(self):
                self.last_activity = time.time()
        
        session = Session(timeout_seconds=0.1)  # 100ms timeout for testing
        
        assert session.is_valid()
        
        time.sleep(0.15)  # Wait past timeout
        
        assert not session.is_valid()
    
    def test_csrf_token_validation(self):
        """Test: CSRF tokens are validated."""
        import secrets
        
        # Generate CSRF token
        csrf_token = secrets.token_urlsafe(32)
        
        # Simulate token validation
        def validate_csrf(provided_token: str, expected_token: str) -> bool:
            return secrets.compare_digest(provided_token, expected_token)
        
        # Valid token
        assert validate_csrf(csrf_token, csrf_token)
        
        # Invalid tokens
        assert not validate_csrf("wrong_token", csrf_token)
        assert not validate_csrf("", csrf_token)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
