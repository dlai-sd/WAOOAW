import pytest


@pytest.mark.unit
def test_cp_otp_start_and_verify_returns_tokens(client, monkeypatch, tmp_path):
    reg_path = tmp_path / "cp_registrations.jsonl"
    otp_path = tmp_path / "cp_otp.jsonl"

    monkeypatch.setenv("CP_REGISTRATIONS_STORE_PATH", str(reg_path))
    monkeypatch.setenv("CP_OTP_STORE_PATH", str(otp_path))
    monkeypatch.setenv("CP_OTP_FIXED_CODE", "123456")
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("CP_REGISTRATION_KEY", "test-registration-key")

    from services import cp_registrations, cp_otp
    from api import cp_otp as cp_otp_api

    cp_registrations.default_cp_registration_store.cache_clear()
    cp_otp.default_cp_otp_store.cache_clear()

    called = {"ok": False}

    async def _noop_upsert(record):
        called["ok"] = True

    monkeypatch.setattr(cp_otp_api, "_upsert_customer_in_plant", _noop_upsert)

    reg_resp = client.post(
        "/api/cp/auth/register",
        json={
            "fullName": "Test User",
            "businessName": "ACME",
            "businessIndustry": "marketing",
            "businessAddress": "Bengaluru",
            "email": "test@example.com",
            "phone": "+919876543210",
            "preferredContactMethod": "email",
            "consent": True,
        },
    )
    assert reg_resp.status_code == 201
    registration_id = reg_resp.json()["registration_id"]

    start_resp = client.post(
        "/api/cp/auth/otp/start",
        json={"registration_id": registration_id},
    )
    assert start_resp.status_code == 200
    start_body = start_resp.json()
    assert start_body["otp_id"].startswith("OTP-")
    assert start_body["otp_code"] == "123456"

    verify_resp = client.post(
        "/api/cp/auth/otp/verify",
        json={"otp_id": start_body["otp_id"], "code": "123456"},
    )
    assert verify_resp.status_code == 200
    assert called["ok"] is True
    token_body = verify_resp.json()
    assert token_body["access_token"]
    assert token_body["token_type"] == "bearer"


@pytest.mark.unit
def test_cp_otp_rate_limit(client, monkeypatch, tmp_path):
    reg_path = tmp_path / "cp_registrations.jsonl"
    otp_path = tmp_path / "cp_otp.jsonl"

    monkeypatch.setenv("CP_REGISTRATIONS_STORE_PATH", str(reg_path))
    monkeypatch.setenv("CP_OTP_STORE_PATH", str(otp_path))
    monkeypatch.setenv("CP_OTP_FIXED_CODE", "123456")
    monkeypatch.setenv("ENVIRONMENT", "development")

    from services import cp_registrations, cp_otp

    cp_registrations.default_cp_registration_store.cache_clear()
    cp_otp.default_cp_otp_store.cache_clear()

    reg_resp = client.post(
        "/api/cp/auth/register",
        json={
            "fullName": "Test User",
            "businessName": "ACME",
            "businessIndustry": "marketing",
            "businessAddress": "Bengaluru",
            "email": "test@example.com",
            "phone": "+919876543210",
            "preferredContactMethod": "email",
            "consent": True,
        },
    )
    registration_id = reg_resp.json()["registration_id"]

    for _ in range(3):
        resp = client.post("/api/cp/auth/otp/start", json={"registration_id": registration_id})
        assert resp.status_code == 200

    resp = client.post("/api/cp/auth/otp/start", json={"registration_id": registration_id})
    assert resp.status_code == 429


@pytest.mark.unit
def test_cp_otp_verify_rejects_bad_code(client, monkeypatch, tmp_path):
    reg_path = tmp_path / "cp_registrations.jsonl"
    otp_path = tmp_path / "cp_otp.jsonl"

    monkeypatch.setenv("CP_REGISTRATIONS_STORE_PATH", str(reg_path))
    monkeypatch.setenv("CP_OTP_STORE_PATH", str(otp_path))
    monkeypatch.setenv("CP_OTP_FIXED_CODE", "123456")
    monkeypatch.setenv("ENVIRONMENT", "development")

    from services import cp_registrations, cp_otp

    cp_registrations.default_cp_registration_store.cache_clear()
    cp_otp.default_cp_otp_store.cache_clear()

    reg_resp = client.post(
        "/api/cp/auth/register",
        json={
            "fullName": "Test User",
            "businessName": "ACME",
            "businessIndustry": "marketing",
            "businessAddress": "Bengaluru",
            "email": "test@example.com",
            "phone": "+919876543210",
            "preferredContactMethod": "email",
            "consent": True,
        },
    )
    registration_id = reg_resp.json()["registration_id"]

    start_resp = client.post("/api/cp/auth/otp/start", json={"registration_id": registration_id})
    otp_id = start_resp.json()["otp_id"]

    bad_resp = client.post("/api/cp/auth/otp/verify", json={"otp_id": otp_id, "code": "000000"})
    assert bad_resp.status_code == 400
