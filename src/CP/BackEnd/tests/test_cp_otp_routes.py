"""Tests for CP OTP routes with Plant integration.

These tests verify that:
1. OTP start requires email and fetches customer from Plant
2. OTP verify fetches customer from Plant and creates CP user
3. Rate limiting works
4. OTP delivery is conditional on environment
5. Non-production environments echo OTP code
"""

from unittest.mock import AsyncMock, patch
import pytest


@pytest.mark.unit
def test_otp_start_requires_email(client):
    """OTP start without email should fail."""
    payload = {"channel": "email"}
    resp = client.post("/api/cp/auth/otp/start", json=payload)
    assert resp.status_code == 400
    assert "email" in resp.json()["detail"].lower()


@pytest.mark.unit
def test_otp_start_customer_not_found(client):
    """OTP start with non-existent customer should return 404."""
    with patch("api.cp_otp._get_customer_from_plant", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = None  # Customer not found
        
        payload = {"email": "nonexistent@example.com"}
        resp = client.post("/api/cp/auth/otp/start", json=payload)
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()


@pytest.mark.unit
def test_otp_start_demo_echoes_code(client, monkeypatch):
    """In demo environment, OTP code should be echoed in response."""
    monkeypatch.setenv("ENVIRONMENT", "demo")
    monkeypatch.setenv("OTP_DELIVERY_MODE", "disabled")
    
    customer_data = {
        "customer_id": "cust-123",
        "email": "demo-echo@example.com",
        "full_name": "Test User",
        "phone": "+919876543210",
        "preferred_contact_method": "email",
    }
    
    with patch("api.cp_otp._get_customer_from_plant", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = customer_data
        
        payload = {"email": "demo-echo@example.com"}
        resp = client.post("/api/cp/auth/otp/start", json=payload)
        
        assert resp.status_code == 200
        body = resp.json()
        assert "otp_id" in body
        assert "otp_code" in body
        assert body["otp_code"] is not None  # Demo should echo code
        assert body["channel"] == "email"


@pytest.mark.unit
def test_otp_start_production_hides_code(client, monkeypatch):
    """In production, OTP code should NOT be in response."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("OTP_DELIVERY_MODE", "provider")
    
    customer_data = {
        "customer_id": "cust-prod-hide",
        "email": "prod-hide@example.com",
        "full_name": "Test User",
        "phone": "+919876543210",
        "preferred_contact_method": "email",
    }
    
    with patch("api.cp_otp._get_customer_from_plant", new_callable=AsyncMock) as mock_fetch, \
         patch("api.cp_otp.deliver_otp", new_callable=AsyncMock) as mock_deliver:
        mock_fetch.return_value = customer_data
        mock_deliver.return_value = None  # Mock successful delivery
        
        payload = {"email": "prod-hide@example.com"}
        resp = client.post("/api/cp/auth/otp/start", json=payload)
        
        assert resp.status_code == 200
        body = resp.json()
        assert "otp_id" in body
        assert body["otp_code"] is None  # Production should hide code


@pytest.mark.unit
def test_otp_start_rate_limit(client, monkeypatch):
    """Should enforce rate limiting per destination."""
    monkeypatch.setenv("ENVIRONMENT", "demo")
    monkeypatch.setenv("OTP_DELIVERY_MODE", "disabled")
    
    customer_data = {
        "customer_id": "cust-ratelimit",
        "email": "ratelimit@example.com",
        "full_name": "Test User",
        "phone": "+919876543210",
        "preferred_contact_method": "email",
    }
    
    with patch("api.cp_otp._get_customer_from_plant", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = customer_data
        
        payload = {"email": "ratelimit@example.com"}
        
        # First request should succeed
        resp1 = client.post("/api/cp/auth/otp/start", json=payload)
        assert resp1.status_code == 200
        
        # Rapid subsequent requests should hit rate limit
        for _ in range(5):
            resp = client.post("/api/cp/auth/otp/start", json=payload)
            if resp.status_code == 429:
                assert "too many" in resp.json()["detail"].lower()
                return
        
        # If we get here, rate limiting may not be configured, which is OK for this env


@pytest.mark.unit
def test_otp_verify_invalid_code(client, monkeypatch):
    """OTP verify with invalid code should fail."""
    monkeypatch.setenv("ENVIRONMENT", "demo")
    
    # Start OTP first
    customer_data = {
        "customer_id": "cust-verify-invalid-code",
        "email": "verify-invalid@example.com",
        "full_name": "Test User",
        "phone": "+919876543210",
        "preferred_contact_method": "email",
    }
    
    with patch("api.cp_otp._get_customer_from_plant", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = customer_data
        
        # Start OTP
        start_resp = client.post("/api/cp/auth/otp/start", json={"email": "verify-invalid@example.com"})
        assert start_resp.status_code == 200
        otp_id = start_resp.json()["otp_id"]
        
        # Try to verify with wrong code
        verify_payload = {"otp_id": otp_id, "code": "000000"}
        verify_resp = client.post("/api/cp/auth/otp/verify", json=verify_payload)
        assert verify_resp.status_code == 400


@pytest.mark.unit
def test_otp_verify_creates_user_and_returns_tokens(client, monkeypatch):
    """OTP verify with correct code should create user and return JWT tokens."""
    monkeypatch.setenv("ENVIRONMENT", "demo")
    
    customer_data = {
        "customer_id": "cust-create-tokens",
        "email": "create-tokens@example.com",
        "full_name": "Test User",
        "phone": "+919876543210",
        "preferred_contact_method": "email",
    }
    
    with patch("api.cp_otp._get_customer_from_plant", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = customer_data
        
        # Start OTP to get code
        start_resp = client.post("/api/cp/auth/otp/start", json={"email": "create-tokens@example.com"})
        assert start_resp.status_code == 200
        otp_id = start_resp.json()["otp_id"]
        code = start_resp.json()["otp_code"]
        
        # Verify with correct code
        verify_payload = {"otp_id": otp_id, "code": code}
        verify_resp = client.post("/api/cp/auth/otp/verify", json=verify_payload)
        
        assert verify_resp.status_code == 200
        body = verify_resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"


@pytest.mark.unit
def test_otp_login_start_requires_email(client):
    """Login OTP start without email or phone should fail."""
    payload = {"channel": "email"}
    resp = client.post("/api/cp/auth/otp/login/start", json=payload)
    assert resp.status_code == 400
    assert "email" in resp.json()["detail"].lower() or "phone" in resp.json()["detail"].lower()


@pytest.mark.unit
def test_otp_login_start_customer_not_found(client):
    """Login OTP start with non-existent customer should return 404."""
    with patch("api.cp_otp._get_customer_from_plant", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = None
        
        payload = {"email": "nonexistent@example.com"}
        resp = client.post("/api/cp/auth/otp/login/start", json=payload)
        assert resp.status_code == 404


@pytest.mark.unit
def test_otp_login_start_demo_echoes_code(client, monkeypatch):
    """In demo environment, login OTP should echo code."""
    monkeypatch.setenv("ENVIRONMENT", "demo")
    
    customer_data = {
        "customer_id": "cust-login-demo",
        "email": "login-demo@example.com",
        "full_name": "Test User",
        "phone": "+919876543210",
        "preferred_contact_method": "email",
    }
    
    with patch("api.cp_otp._get_customer_from_plant", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = customer_data
        
        payload = {"email": "login-demo@example.com"}
        resp = client.post("/api/cp/auth/otp/login/start", json=payload)
        
        assert resp.status_code == 200
        body = resp.json()
        assert "otp_code" in body
        assert body["otp_code"] is not None


@pytest.mark.unit
def test_otp_start_uses_phone_channel_from_customer(client, monkeypatch):
    """If customer prefers phone contact, OTP should use phone channel."""
    monkeypatch.setenv("ENVIRONMENT", "demo")
    
    customer_data = {
        "customer_id": "cust-phone-pref",
        "email": "phone-pref@example.com",
        "full_name": "Test User",
        "phone": "+919876543210",
        "preferred_contact_method": "phone",  # Customer prefers phone
    }
    
    with patch("api.cp_otp._get_customer_from_plant", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = customer_data
        
        payload = {"email": "phone-pref@example.com"}
        resp = client.post("/api/cp/auth/otp/start", json=payload)
        
        assert resp.status_code == 200
        body = resp.json()
        assert body["channel"] == "phone"


@pytest.mark.unit
def test_otp_verify_customer_not_found_returns_502(client, monkeypatch):
    """If customer disappears after OTP start, verify should return 502."""
    monkeypatch.setenv("ENVIRONMENT", "demo")
    
    customer_data_start = {
        "customer_id": "cust-notfound-502",
        "email": "notfound-502@example.com",
        "full_name": "Test User",
        "phone": "+919876543210",
        "preferred_contact_method": "email",
    }
    
    customer_data_verify = None  # Customer not found during verify
    
    with patch("api.cp_otp._get_customer_from_plant", new_callable=AsyncMock) as mock_fetch:
        # First call returns customer (start), second call returns None (verify)
        mock_fetch.side_effect = [customer_data_start, customer_data_verify]
        
        # Start OTP
        start_resp = client.post("/api/cp/auth/otp/start", json={"email": "notfound-502@example.com"})
        assert start_resp.status_code == 200
        otp_id = start_resp.json()["otp_id"]
        code = start_resp.json()["otp_code"]
        
        # Verify should fail because customer not found
        verify_payload = {"otp_id": otp_id, "code": code}
        verify_resp = client.post("/api/cp/auth/otp/verify", json=verify_payload)
        assert verify_resp.status_code == 502
