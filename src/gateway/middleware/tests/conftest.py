"""
Pytest Configuration for Gateway Middleware Tests

Provides fixtures for mocking dependencies:
- Redis (for budget middleware)
- PostgreSQL (for audit middleware)
- OPA (for RBAC/policy middleware)
- JWT keys (for auth middleware)

IMPORTANT: Environment variables are set BEFORE pytest imports test modules
so that modules can read them at import time.
"""

import pytest
import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


# ========================================
# Setup environment BEFORE any imports
# ========================================
# Store keys globally so they can be imported by test modules
TEST_PRIVATE_KEY_PEM = None
TEST_PUBLIC_KEY_PEM = None

def pytest_configure(config):
    """
    Setup test environment before pytest starts collecting tests.
    This ensures env vars are set before any test modules are imported.
    """
    global TEST_PRIVATE_KEY_PEM, TEST_PUBLIC_KEY_PEM
    
    # Generate RSA key pair for JWT testing
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    public_key_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
    
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode()
    
    # Store globally
    TEST_PRIVATE_KEY_PEM = private_key_pem
    TEST_PUBLIC_KEY_PEM = public_key_pem
    
    # Set JWT environment variables
    os.environ["JWT_PUBLIC_KEY"] = public_key_pem
    os.environ["JWT_ALGORITHM"] = "RS256"
    os.environ["JWT_ISSUER"] = "waooaw.com"
    
    # Set Redis environment variables
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"
    
    # Set PostgreSQL environment variables
    os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/test_db"
    
    # Set OPA environment variables
    os.environ["OPA_URL"] = "http://localhost:8181"
    
    # Set Gateway environment
    os.environ["ENVIRONMENT"] = "test"
    os.environ["GATEWAY_TYPE"] = "cp"
    
    # Store keys for use in tests
    config.private_key_pem = private_key_pem
    config.public_key_pem = public_key_pem


@pytest.fixture(scope="session")
def jwt_keys(request):
    """
    Provide JWT keys for tests that need to generate tokens.
    """
    return {
        "private": request.config.private_key_pem,
        "public": request.config.public_key_pem
    }


@pytest.fixture
def mock_redis(monkeypatch):
    """
    Mock Redis client for budget middleware tests.
    """
    class MockRedis:
        def __init__(self):
            self.data = {}
        
        async def get(self, key):
            return self.data.get(key)
        
        async def set(self, key, value, ex=None):
            self.data[key] = value
            return True
        
        async def incr(self, key):
            current = int(self.data.get(key, 0))
            self.data[key] = str(current + 1)
            return current + 1
        
        async def close(self):
            pass
    
    return MockRedis()


@pytest.fixture
def mock_opa(monkeypatch):
    """
    Mock OPA client for RBAC/policy middleware tests.
    """
    class MockOPA:
        def __init__(self):
            self.policies = {}
        
        async def query(self, policy_path, input_data):
            # Default allow response
            return {
                "result": {
                    "allow": True,
                    "decision": "allow"
                }
            }
        
        async def close(self):
            pass
    
    return MockOPA()


@pytest.fixture
def mock_postgres(monkeypatch):
    """
    Mock PostgreSQL client for audit middleware tests.
    """
    class MockConnection:
        async def execute(self, query, *args):
            return "INSERT 1"
        
        async def close(self):
            pass
    
    class MockPool:
        async def acquire(self):
            return MockConnection()
        
        async def release(self, conn):
            pass
        
        async def close(self):
            pass
    
    return MockPool()
