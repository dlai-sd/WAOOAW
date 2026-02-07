"""
Pytest configuration and shared fixtures for CP Backend tests
"""
import pytest
from fastapi.testclient import TestClient
from api.auth.user_store import user_store as _user_store_singleton, UserStore

# Ensure environment parity for tests
import os
from pathlib import Path

import dotenv

# Load .env before app initialization
@pytest.fixture(scope="session", autouse=True)
def load_dotenv():
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        dotenv.load_dotenv(dotenv_path=env_path, override=True)
    else:
        print(f"Warning: .env file not found at {env_path}")


@pytest.fixture(autouse=True)
def reset_user_store():
    """Reset user store before each test"""
    _user_store_singleton._users.clear()
    _user_store_singleton._email_index.clear()
    _user_store_singleton._provider_index.clear()
    yield
    _user_store_singleton._users.clear()
    _user_store_singleton._email_index.clear()
    _user_store_singleton._provider_index.clear()


@pytest.fixture
def user_store() -> UserStore:
    """Provide clean user store instance"""
    return _user_store_singleton


@pytest.fixture
def client():
    """FastAPI test client"""
    from main import app
    return TestClient(app)


@pytest.fixture
def mock_google_token():
    """Mock Google ID token payload"""
    return {
        "iss": "https://accounts.google.com",
        "sub": "1234567890",
        "email": "test@example.com",
        "email_verified": True,
        "name": "Test User",
        "picture": "https://example.com/photo.jpg",
        "given_name": "Test",
        "family_name": "User",
        "iat": 1234567890,
        "exp": 9999999999
    }


@pytest.fixture
def auth_headers(client, mock_google_token, mocker):
    """Generate valid JWT auth headers"""
    # Mock Google token verification.
    # NOTE: api.auth.routes imports verify_google_token into its module namespace,
    # so we patch that symbol to avoid real network calls.
    async def _mock_verify_google_token(_id_token: str):
        return mock_google_token

    mocker.patch('api.auth.routes.verify_google_token', side_effect=_mock_verify_google_token)
    
    # Login to get JWT token
    response = client.post(
        "/api/auth/google/verify",
        json={"id_token": "mock_token", "source": "cp"}
    )
    assert response.status_code == 200
    
    access_token = response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}
