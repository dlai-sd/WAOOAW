import os


def test_cp_otp_login_start_and_verify_returns_tokens(client, monkeypatch, tmp_path):
    os.environ["ENVIRONMENT"] = "development"

    # Keep CP stores isolated for the test.
    reg_path = tmp_path / "regs.jsonl"
    otp_path = tmp_path / "otp.jsonl"
    monkeypatch.setenv("CP_REGISTRATIONS_STORE_PATH", str(reg_path))
    monkeypatch.setenv("CP_OTP_STORE_PATH", str(otp_path))

    # Avoid calling Plant gateway during tests.
    async def _noop_upsert(record):
        return None

    monkeypatch.setattr("api.cp_otp._upsert_customer_in_plant", _noop_upsert)

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
    tokens = verify_resp.json()
    assert tokens["access_token"]
    assert tokens["token_type"] == "bearer"
