import pytest


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cp_upsert_customer_missing_key_nonprod_is_best_effort(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.delenv("CP_REGISTRATION_KEY", raising=False)

    from types import SimpleNamespace

    from api import cp_otp as cp_otp_api

    record = SimpleNamespace(
        full_name="Test User",
        business_name="ACME",
        business_industry="marketing",
        business_address="Bengaluru",
        email="test@example.com",
        phone="+919876543210",
        website=None,
        gst_number=None,
        preferred_contact_method="email",
        consent=True,
    )

    # Should not raise.
    await cp_otp_api._upsert_customer_in_plant(record)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cp_upsert_customer_missing_key_prod_raises(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("CP_REGISTRATION_KEY", raising=False)

    from types import SimpleNamespace

    import fastapi

    from api import cp_otp as cp_otp_api

    record = SimpleNamespace(
        full_name="Test User",
        business_name="ACME",
        business_industry="marketing",
        business_address="Bengaluru",
        email="test@example.com",
        phone="+919876543210",
        website=None,
        gst_number=None,
        preferred_contact_method="email",
        consent=True,
    )

    with pytest.raises(fastapi.HTTPException) as exc:
        await cp_otp_api._upsert_customer_in_plant(record)
    assert exc.value.status_code == 503


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

    emitted: list[str] = []

    async def _fake_emit(*, event_type: str, metadata: dict) -> None:
        emitted.append(str(event_type))

    async def _noop_upsert(record):
        called["ok"] = True

    monkeypatch.setattr(cp_otp_api, "_upsert_customer_in_plant", _noop_upsert)
    monkeypatch.setattr(cp_otp_api, "_emit_notification_event_best_effort", _fake_emit)

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
    assert emitted.count("otp_sent") == 1
    assert emitted.count("otp_verified") == 1
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


@pytest.mark.unit
def test_cp_otp_start_production_calls_delivery_and_hides_code(client, monkeypatch, tmp_path):
    reg_path = tmp_path / "cp_registrations.jsonl"
    otp_path = tmp_path / "cp_otp.jsonl"

    monkeypatch.setenv("CP_REGISTRATIONS_STORE_PATH", str(reg_path))
    monkeypatch.setenv("CP_OTP_STORE_PATH", str(otp_path))
    monkeypatch.setenv("CP_OTP_FIXED_CODE", "123456")
    monkeypatch.setenv("ENVIRONMENT", "production")

    from api import cp_registration as cp_registration_api

    async def _noop_verify(*, token: str, remote_ip: str | None) -> None:
        return None

    monkeypatch.setattr(cp_registration_api, "_verify_turnstile_token", _noop_verify)

    from services import cp_registrations, cp_otp
    from api import cp_otp as cp_otp_api

    cp_registrations.default_cp_registration_store.cache_clear()
    cp_otp.default_cp_otp_store.cache_clear()

    async def _noop_upsert(record):
        return None

    monkeypatch.setattr(cp_otp_api, "_upsert_customer_in_plant", _noop_upsert)

    calls = {"count": 0, "last": None}

    async def _fake_deliver_otp(*, channel, destination, code, ttl_seconds=300):
        calls["count"] += 1
        calls["last"] = {
            "channel": channel,
            "destination": destination,
            "code": code,
            "ttl_seconds": ttl_seconds,
        }

    monkeypatch.setattr(cp_otp_api, "deliver_otp", _fake_deliver_otp)

    reg_resp = client.post(
        "/api/cp/auth/register",
        json={
            "fullName": "Test User",
            "businessName": "ACME",
            "businessIndustry": "marketing",
            "businessAddress": "Bengaluru",
            "email": "test@example.com",
            "phone": "+919876543210",
            "captchaToken": "test-captcha-token",
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
    body = start_resp.json()
    assert body["otp_id"].startswith("OTP-")
    assert body["otp_code"] is None
    assert calls["count"] == 1
    assert calls["last"]["code"] == "123456"


@pytest.mark.unit
def test_cp_otp_start_production_without_provider_returns_500(client, monkeypatch, tmp_path):
    reg_path = tmp_path / "cp_registrations.jsonl"
    otp_path = tmp_path / "cp_otp.jsonl"

    monkeypatch.setenv("CP_REGISTRATIONS_STORE_PATH", str(reg_path))
    monkeypatch.setenv("CP_OTP_STORE_PATH", str(otp_path))
    monkeypatch.setenv("CP_OTP_FIXED_CODE", "123456")
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("CP_OTP_DELIVERY_PROVIDER", raising=False)

    from api import cp_registration as cp_registration_api

    async def _noop_verify(*, token: str, remote_ip: str | None) -> None:
        return None

    monkeypatch.setattr(cp_registration_api, "_verify_turnstile_token", _noop_verify)

    from services import cp_registrations, cp_otp
    from api import cp_otp as cp_otp_api

    cp_registrations.default_cp_registration_store.cache_clear()
    cp_otp.default_cp_otp_store.cache_clear()

    async def _noop_upsert(record):
        return None

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
            "captchaToken": "test-captcha-token",
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
    assert start_resp.status_code == 500
    assert "OTP delivery provider not configured" in start_resp.json()["detail"]


@pytest.mark.unit
def test_cp_otp_start_demo_skips_delivery_and_echoes_code(client, monkeypatch, tmp_path):
    reg_path = tmp_path / "cp_registrations.jsonl"
    otp_path = tmp_path / "cp_otp.jsonl"

    monkeypatch.setenv("CP_REGISTRATIONS_STORE_PATH", str(reg_path))
    monkeypatch.setenv("CP_OTP_STORE_PATH", str(otp_path))
    monkeypatch.setenv("CP_OTP_FIXED_CODE", "123456")
    monkeypatch.setenv("ENVIRONMENT", "demo")
    monkeypatch.delenv("OTP_DELIVERY_MODE", raising=False)
    monkeypatch.delenv("CP_OTP_DELIVERY_PROVIDER", raising=False)

    from api import cp_registration as cp_registration_api

    async def _noop_verify(*, token: str, remote_ip: str | None) -> None:
        return None

    monkeypatch.setattr(cp_registration_api, "_verify_turnstile_token", _noop_verify)

    from services import cp_registrations, cp_otp
    from api import cp_otp as cp_otp_api

    cp_registrations.default_cp_registration_store.cache_clear()
    cp_otp.default_cp_otp_store.cache_clear()

    async def _noop_upsert(record):
        return None

    monkeypatch.setattr(cp_otp_api, "_upsert_customer_in_plant", _noop_upsert)

    calls = {"count": 0}

    async def _fake_deliver_otp(*, channel, destination, code, ttl_seconds=300):
        calls["count"] += 1

    monkeypatch.setattr(cp_otp_api, "deliver_otp", _fake_deliver_otp)

    reg_resp = client.post(
        "/api/cp/auth/register",
        json={
            "fullName": "Test User",
            "businessName": "ACME",
            "businessIndustry": "marketing",
            "businessAddress": "Bengaluru",
            "email": "test@example.com",
            "phone": "+919876543210",
            "captchaToken": "test-captcha-token",
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
    body = start_resp.json()
    assert body["otp_id"].startswith("OTP-")
    assert body["otp_code"] == "123456"
    assert calls["count"] == 0
