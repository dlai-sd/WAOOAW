import pytest


@pytest.mark.unit
def test_2fa_enroll_confirm_and_login_requires_totp(client, mocker, tmp_path):
    two_fa_path = tmp_path / "cp_2fa.jsonl"
    mocker.patch.dict("os.environ", {"CP_2FA_STORE_PATH": str(two_fa_path)})

    async def _mock_verify_google_token(_id_token: str):
        return {
            "iss": "https://accounts.google.com",
            "sub": "1234567890",
            "email": "test@example.com",
            "email_verified": True,
            "name": "Test User",
            "picture": "https://example.com/photo.jpg",
            "iat": 1234567890,
            "exp": 9999999999,
        }

    mocker.patch("api.auth.routes.verify_google_token", side_effect=_mock_verify_google_token)

    # First login: no 2FA yet.
    login_resp = client.post("/api/auth/google/verify", json={"id_token": "mock", "source": "cp"})
    assert login_resp.status_code == 200
    access_token = login_resp.json()["access_token"]

    # Enroll
    enroll_resp = client.post(
        "/api/auth/2fa/enroll",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert enroll_resp.status_code == 200
    secret = enroll_resp.json()["secret_base32"]
    assert secret

    # Confirm
    from services.cp_2fa import totp

    code = totp(secret)
    confirm_resp = client.post(
        "/api/auth/2fa/confirm",
        json={"code": code},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert confirm_resp.status_code == 200
    assert confirm_resp.json()["enabled"] is True

    # Now login requires totp_code
    denied = client.post("/api/auth/google/verify", json={"id_token": "mock", "source": "cp"})
    assert denied.status_code == 401

    ok = client.post(
        "/api/auth/google/verify",
        json={"id_token": "mock", "source": "cp", "totp_code": totp(secret)},
    )
    assert ok.status_code == 200
    assert ok.json()["access_token"]
