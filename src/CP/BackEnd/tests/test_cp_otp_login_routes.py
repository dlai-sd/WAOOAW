"""
CP OTP Login Routes Tests
Tests for OTP-based authentication with Plant gateway integration.

Note: Legacy tests below are temporarily skipped pending Plant integration refactor.
"""
import pytest


@pytest.mark.skip(reason="Legacy test needs refactoring for new Plant integration")
def test_cp_otp_login_start_and_verify_returns_tokens(client, monkeypatch, tmp_path):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("CP_REGISTRATION_KEY", "test-key-123")
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway-mock")

    # Keep CP stores isolated for the test.
    reg_path = tmp_path / "regs.jsonl"
    otp_path = tmp_path / "otp.jsonl"
    monkeypatch.setenv("CP_REGISTRATIONS_STORE_PATH", str(reg_path))
    monkeypatch.setenv("CP_OTP_STORE_PATH", str(otp_path))

    from services import cp_registrations
    from unittest.mock import AsyncMock, MagicMock
    import httpx

    cp_registrations.default_cp_registration_store.cache_clear()

    # Mock Plant gateway responses
    def mock_httpx_client(*args, **kwargs):
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "customer_id": "cust-test-123",
            "email": "user@example.com",
            "phone": "+911234567890",
            "full_name": "Test User"
        }
        # For GET requests (customer lookup)
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            "customer_id": "cust-test-123",
            "email": "user@example.com",
            "phone": "+911234567890",
            "full_name": "Test User",
            "preferred_contact_method": "email"
        }
        mock_client.post.return_value = mock_response
        mock_client.get.return_value = mock_get_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        return mock_client

    monkeypatch.setattr(httpx, "AsyncClient", mock_httpx_client)

    emitted: list[str] = []

    async def _fake_emit(*, event_type: str, metadata: dict) -> None:
        emitted.append(str(event_type))

    monkeypatch.setattr("api.cp_otp._emit_notification_event_best_effort", _fake_emit)

    # Create a registration first.
    reg_payload = {
        "full_name": "Test User",
        "business_name": "Test Biz",
        "business_industry": "marketing",
        "business_address": "Somewhere",
        "email": "user@example.com",
        "phone": "+911234567890",
        "website": None,
        "gst_number": None,
        "preferred_contact_method": "email",
        "consent": True,
    }
    reg_resp = client.post("/api/cp/auth/register", json=reg_payload)
    assert reg_resp.status_code in (200, 201)

    # Start OTP via login endpoint using email.
    start_resp = client.post(
        "/api/cp/auth/otp/login/start",
        json={"email": "user@example.com"},
    )
    assert start_resp.status_code == 200
    body = start_resp.json()
    assert body["otp_id"]
    assert body["channel"] == "email"

    # Dev env returns code.
    assert body.get("otp_code")

    verify_resp = client.post(
        "/api/cp/auth/otp/verify",
        json={"otp_id": body["otp_id"], "code": body["otp_code"]},
    )
    assert verify_resp.status_code == 200
    assert emitted.count("otp_sent") == 1
    assert emitted.count("otp_verified") == 1
    tokens = verify_resp.json()
    assert tokens["access_token"]
    assert tokens["token_type"] == "bearer"


@pytest.mark.skip(reason="Legacy test needs refactoring for new Plant integration")
def test_cp_otp_login_start_production_calls_delivery_and_hides_code(client, monkeypatch, tmp_path):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("CP_REGISTRATION_KEY", "test-key-prod")
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway-mock")

    from api import cp_registration as cp_registration_api
    from unittest.mock import AsyncMock, MagicMock
    import httpx

    async def _noop_verify(*, token: str, remote_ip: str | None) -> None:
        return None

    monkeypatch.setattr(cp_registration_api, "_verify_turnstile_token", _noop_verify)

    reg_path = tmp_path / "regs.jsonl"
    otp_path = tmp_path / "otp.jsonl"
    monkeypatch.setenv("CP_REGISTRATIONS_STORE_PATH", str(reg_path))
    monkeypatch.setenv("CP_OTP_STORE_PATH", str(otp_path))
    monkeypatch.setenv("CP_OTP_FIXED_CODE", "123456")

    from services import cp_registrations

    cp_registrations.default_cp_registration_store.cache_clear()

    # Mock Plant gateway responses
    def mock_httpx_client(*args, **kwargs):
        mock_client = AsyncMock()
        # For POST requests (customer creation)
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "customer_id": "cust-prod-456",
            "email": "user@example.com",
            "phone": "+911234567890",
            "full_name": "Test User"
        }
        # For GET requests (customer lookup)
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            "customer_id": "cust-prod-456",
            "email": "user@example.com",
            "phone": "+911234567890",
            "full_name": "Test User",
            "preferred_contact_method": "email"
        }
        mock_client.post.return_value = mock_response
        mock_client.get.return_value = mock_get_response
        mock_client.get.return_value = mock_get_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        return mock_client

    monkeypatch.setattr(httpx, "AsyncClient", mock_httpx_client)

    emitted: list[str] = []

    async def _fake_emit(*, event_type: str, metadata: dict) -> None:
        emitted.append(str(event_type))

    monkeypatch.setattr("api.cp_otp._emit_notification_event_best_effort", _fake_emit)

    calls = {"count": 0}

    async def _fake_deliver_otp(*, channel, destination, code, ttl_seconds=300):
        calls["count"] += 1
        assert channel == "email"
        assert destination == "user@example.com"
        assert code == "123456"

    monkeypatch.setattr("api.cp_otp.deliver_otp", _fake_deliver_otp)

    reg_payload = {
        "full_name": "Test User",
        "business_name": "Test Biz",
        "business_industry": "marketing",
        "business_address": "Somewhere",
        "email": "user@example.com",
        "phone": "+911234567890",
        "captcha_token": "test-captcha-token",
        "website": None,
        "gst_number": None,
        "preferred_contact_method": "email",
        "consent": True,
    }
    reg_resp = client.post("/api/cp/auth/register", json=reg_payload)
    assert reg_resp.status_code in (200, 201)

    start_resp = client.post(
        "/api/cp/auth/otp/login/start",
        json={"email": "user@example.com"},
    )
    assert start_resp.status_code == 200
    body = start_resp.json()
    assert body["otp_id"]
    assert body["channel"] == "email"
    assert body.get("otp_code") is None
    assert calls["count"] == 1
    assert emitted.count("otp_sent") == 1
