"""Tests for internal Plant credential resolver API in CP Backend."""

import pytest
from pathlib import Path

from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch, tmp_path: Path):
    """Create test client with mocked credential store."""
    store_path = tmp_path / "cp_platform_credentials.jsonl"
    monkeypatch.setenv("CP_PLATFORM_CREDENTIALS_STORE_PATH", str(store_path))
    monkeypatch.setenv("CP_PLATFORM_CREDENTIALS_SECRET", "test-secret")
    monkeypatch.setenv("PLANT_INTERNAL_API_KEY", "test-plant-key")
    
    # Import main after env vars are set
    from main import app
    from services import platform_credentials as svc
    
    # Clear LRU cache to pick up new env vars
    svc.default_platform_credential_store.cache_clear()
    
    return TestClient(app)


@pytest.fixture
def internal_headers():
    """Headers for Plant internal API requests."""
    return {
        "X-Plant-Internal-Key": "test-plant-key",
        "Content-Type": "application/json",
    }


@pytest.fixture
def auth_headers():
    """Headers for CP user requests (for setting up test credentials)."""
    # In real usage, this would come from CP auth middleware
    # For tests, we'll mock it
    return {
        "Authorization": "Bearer test-token",
        "X-User-ID": "user123",
    }


def test_resolve_credential_success(client, internal_headers, auth_headers, monkeypatch):
    """Test successful credential resolution for Plant."""
    # Setup: Create a credential via CP API first
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    
    # Import auth dependencies after env vars are set
    from api.auth.dependencies import get_current_user
    from models.user import User
    from datetime import datetime,timezone
    
    # Mock authentication
    def mock_get_current_user():
        return User(
            id="user123",
            email="test@example.com",
            provider="google",
            provider_id="google_123",
            created_at=datetime.now(timezone.utc)
        )
    
    from main import app
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    # Create a credential
    create_response = client.put(
        "/api/cp/platform-credentials",
        headers=auth_headers,
        json={
            "platform": "youtube",
            "posting_identity": "test-channel",
            "access_token": "secret-access-token",
            "refresh_token": "secret-refresh-token",
        },
    )
    assert create_response.status_code == 200
    credential_ref = create_response.json()["credential_ref"]
    
    # Test: Resolve credential via internal Plant API
    resolve_response = client.post(
        "/api/internal/plant/credentials/resolve",
        headers=internal_headers,
        json={
            "customer_id": "CUST-user123",
            "credential_ref": credential_ref,
        },
    )
    
    assert resolve_response.status_code == 200
    body = resolve_response.json()
    
    assert body["credential_ref"] == credential_ref
    assert body["customer_id"] == "CUST-user123"
    assert body["platform"] == "youtube"
    assert body["posting_identity"] == "test-channel"
    assert body["access_token"] == "secret-access-token"
    assert body["refresh_token"] == "secret-refresh-token"
    assert "created_at" in body
    assert "updated_at" in body


def test_resolve_credential_not_found(client, internal_headers):
    """Test credential resolution when credential doesn't exist."""
    resolve_response = client.post(
        "/api/internal/plant/credentials/resolve",
        headers=internal_headers,
        json={
            "customer_id": "CUST-user999",
            "credential_ref": "CRED-nonexistent",
        },
    )
    
    assert resolve_response.status_code == 404
    assert "not found" in resolve_response.json()["detail"].lower()


def test_resolve_credential_invalid_api_key(client):
    """Test credential resolution with invalid internal API key."""
    resolve_response = client.post(
        "/api/internal/plant/credentials/resolve",
        headers={
            "X-Plant-Internal-Key": "wrong-key",
            "Content-Type": "application/json",
        },
        json={
            "customer_id": "CUST-user123",
            "credential_ref": "CRED-test",
        },
    )
    
    assert resolve_response.status_code == 403
    assert "Forbidden" in resolve_response.json()["detail"]


def test_update_access_token_success(client, internal_headers, auth_headers, monkeypatch):
    """Test updating access token after OAuth2 refresh."""
    # Setup: Create a credential first
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    
    from api.auth.dependencies import get_current_user
    from models.user import User
    from datetime import datetime, timezone
    
    def mock_get_current_user():
        return User(
            id="user123",
            email="test@example.com",
            provider="google",
            provider_id="google_123",
            created_at=datetime.now(timezone.utc)
        )
    
    from main import app
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    create_response = client.put(
        "/api/cp/platform-credentials",
        headers=auth_headers,
        json={
            "platform": "youtube",
            "posting_identity": "test-channel",
            "access_token": "old-access-token",
            "refresh_token": "refresh-token",
        },
    )
    assert create_response.status_code == 200
    credential_ref = create_response.json()["credential_ref"]
    
    # Test: Update access token
    update_response = client.post(
        "/api/internal/plant/credentials/update-token",
        headers=internal_headers,
        json={
            "customer_id": "CUST-user123",
            "credential_ref": credential_ref,
            "new_access_token": "new-access-token",
        },
    )
    
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "success"
    
    # Verify token was updated by resolving again
    resolve_response = client.post(
        "/api/internal/plant/credentials/resolve",
        headers=internal_headers,
        json={
            "customer_id": "CUST-user123",
            "credential_ref": credential_ref,
        },
    )
    
    assert resolve_response.status_code == 200
    body = resolve_response.json()
    assert body["access_token"] == "new-access-token"
    assert body["refresh_token"] == "refresh-token"  # Unchanged


def test_update_access_token_not_found(client, internal_headers):
    """Test updating access token when credential doesn't exist."""
    update_response = client.post(
        "/api/internal/plant/credentials/update-token",
        headers=internal_headers,
        json={
            "customer_id": "CUST-user999",
            "credential_ref": "CRED-nonexistent",
            "new_access_token": "new-token",
        },
    )
    
    assert update_response.status_code == 404
    assert "not found" in update_response.json()["detail"].lower()


def test_resolve_credential_different_customer(client, internal_headers, auth_headers, monkeypatch):
    """Test that Plant cannot resolve credentials for wrong customer_id."""
    # Setup: Create credential for user123
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    
    from api.auth.dependencies import get_current_user
    from models.user import User
    from datetime import datetime, timezone
    
    def mock_get_current_user():
        return User(
            id="user123",
            email="test@example.com",
            provider="google",
            provider_id="google_123",
            created_at=datetime.now(timezone.utc)
        )
    
    from main import app
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    create_response = client.put(
        "/api/cp/platform-credentials",
        headers=auth_headers,
        json={
            "platform": "youtube",
            "posting_identity": "test-channel",
            "access_token": "secret-token",
            "refresh_token": "refresh-token",
        },
    )
    assert create_response.status_code == 200
    credential_ref = create_response.json()["credential_ref"]
    
    # Test: Try to resolve with wrong customer_id
    resolve_response = client.post(
        "/api/internal/plant/credentials/resolve",
        headers=internal_headers,
        json={
            "customer_id": "CUST-attacker",  # Different customer
            "credential_ref": credential_ref,
        },
    )
    
    # Should not find credential (customer_id mismatch)
    assert resolve_response.status_code == 404
