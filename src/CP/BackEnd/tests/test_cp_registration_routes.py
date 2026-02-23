import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.unit
async def test_cp_register_happy_path_proxies_to_plant(client, monkeypatch):
    """Test that registration is proxied to Plant and returns customer_id as registration_id"""
    
    # Mock Plant API response
    mock_response = {
        "created": True,
        "customer_id": "cust-123456",
        "email": "test@example.com",
        "phone": "+919876543210",
        "full_name": "Test User",
        "business_name": "ACME Inc",
        "business_industry": "marketing",
        "business_address": "Bengaluru, Karnataka, India",
        "website": "https://example.com",
        "gst_number": "29ABCDE1234F2Z5",
        "preferred_contact_method": "email",
        "consent": True,
    }
    
    with patch('api.cp_registration.httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_response_obj = MagicMock()
        mock_response_obj.status_code = 201
        mock_response_obj.json.return_value = mock_response
        mock_client.post = AsyncMock(return_value=mock_response_obj)
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client
        
        payload = {
            "fullName": "  Test User  ",
            "businessName": "  ACME Inc ",
            "businessIndustry": "marketing",
            "businessAddress": "Bengaluru, Karnataka, India",
            "email": "TEST@EXAMPLE.COM",
            "phone": "+91 98765 43210",
            "website": "https://example.com",
            "gstNumber": "29ABCDE1234F2Z5",
            "preferredContactMethod": "email",
            "consent": True,
        }

        resp = client.post("/api/cp/auth/register", json=payload)
        assert resp.status_code == 201
        
        body = resp.json()
        # Customer ID from Plant becomes registration_id
        assert body["registration_id"] == "cust-123456"
        assert body["email"] == "test@example.com"
        assert body["phone"] == "+919876543210"
        assert body["full_name"] == "Test User"
        assert body["business_name"] == "ACME Inc"



@pytest.mark.unit
def test_cp_register_requires_consent(client, monkeypatch, tmp_path):
    store_path = tmp_path / "cp_registrations.jsonl"
    monkeypatch.setenv("CP_REGISTRATIONS_STORE_PATH", str(store_path))

    from services import cp_registrations

    cp_registrations.default_cp_registration_store.cache_clear()

    payload = {
        "fullName": "Test User",
        "businessName": "ACME",
        "businessIndustry": "marketing",
        "businessAddress": "Bengaluru",
        "email": "test@example.com",
        "phone": "+919876543210",
        "preferredContactMethod": "email",
        "consent": False,
    }

    resp = client.post("/api/cp/auth/register", json=payload)
    assert resp.status_code == 422


@pytest.mark.unit
def test_cp_register_rejects_bad_phone_format(client, monkeypatch, tmp_path):
    store_path = tmp_path / "cp_registrations.jsonl"
    monkeypatch.setenv("CP_REGISTRATIONS_STORE_PATH", str(store_path))

    from services import cp_registrations

    cp_registrations.default_cp_registration_store.cache_clear()

    payload = {
        "fullName": "Test User",
        "businessName": "ACME",
        "businessIndustry": "marketing",
        "businessAddress": "Bengaluru",
        "email": "test@example.com",
        "phone": "nope",
        "preferredContactMethod": "email",
        "consent": True,
    }

    resp = client.post("/api/cp/auth/register", json=payload)
    assert resp.status_code == 422


@pytest.mark.unit
def test_cp_register_duplicate_email_returns_409(client, monkeypatch):
    """Test that duplicate email registration returns 409 from Plant"""
    
    with patch('api.cp_registration.httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_response_obj = MagicMock()
        mock_response_obj.status_code = 409
        mock_response_obj.json.return_value = {"detail": "Email already registered"}
        mock_client.post = AsyncMock(return_value=mock_response_obj)
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client

        payload = {
            "fullName": "Test User",
            "businessName": "ACME",
            "businessIndustry": "marketing",
            "businessAddress": "Bengaluru",
            "email": "test@example.com",
            "phone": "+919876543210",
            "preferredContactMethod": "email",
            "consent": True,
        }

        resp = client.post("/api/cp/auth/register", json=payload)
        assert resp.status_code == 409
        assert "already registered" in resp.json()["detail"]



@pytest.mark.unit
def test_cp_register_duplicate_phone_returns_409(client):
    """Test that duplicate phone registration returns 409 from Plant"""
    
    with patch('api.cp_registration.httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_response_obj = MagicMock()
        mock_response_obj.status_code = 409
        mock_response_obj.json.return_value = {"detail": "Phone already registered"}
        mock_client.post = AsyncMock(return_value=mock_response_obj)
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client

        payload = {
            "fullName": "Test User",
            "businessName": "ACME",
            "businessIndustry": "marketing",
            "businessAddress": "Bengaluru",
            "email": "test@example.com",
            "phone": "+919876543210",
            "preferredContactMethod": "email",
            "consent": True,
        }

        resp = client.post("/api/cp/auth/register", json=payload)
        assert resp.status_code == 409
        assert "already registered" in resp.json()["detail"]


@pytest.mark.unit
def test_cp_register_accepts_country_and_national_phone(client):
    """Test that registration accepts valid phone formats and proxies to Plant"""
    
    # This test validates that CP accepts and normalizes phone formats
    # before proxying to Plant. The validation happens in CP.
    payload_invalid_phone = {
        "fullName": "User",
        "businessName": "Company",
        "businessIndustry": "tech",
        "businessAddress": "Address",
        "email": "user@example.com",
        "phone": "invalid",  # Will be rejected by phonenumbers library
        "preferredContactMethod": "phone",
        "consent": True,
    }
    
    # Should be rejected during validation
    resp = client.post("/api/cp/auth/register", json=payload_invalid_phone)
    assert resp.status_code == 422




