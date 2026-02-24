from __future__ import annotations

import pytest

import jwt

from core.config import settings


def _mint_admin_token() -> str:
    import time

    now = int(time.time())
    payload = {
        "sub": "test-admin",
        "iat": now,
        "exp": now + 60,
        "iss": settings.JWT_ISSUER,
        "roles": ["admin"],
        "email": "admin@waooaw.com",
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


@pytest.mark.auth
async def test_admin_me_requires_google_client_id(client, monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "", raising=False)
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 503


@pytest.mark.auth
async def test_admin_me_success(client, monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "test-client", raising=False)
    monkeypatch.setattr(settings, "ENVIRONMENT", "test", raising=False)

    resp = await client.get("/api/auth/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "google"
    assert data["environment"] == "test"


@pytest.mark.auth
async def test_google_verify_success_mints_jwt(client, monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "test-client", raising=False)
    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret", raising=False)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256", raising=False)
    monkeypatch.setattr(settings, "JWT_ISSUER", "waooaw.com", raising=False)
    monkeypatch.setattr(settings, "ALLOWED_EMAIL_DOMAINS", "waooaw.com", raising=False)

    def _mock_verify_oauth2_token(id_token_str, request, audience):
        return {
            "aud": "test-client",
            "iss": "accounts.google.com",
            "email": "admin@waooaw.com",
            "email_verified": True,
            "sub": "google-sub-123",
        }

    monkeypatch.setattr("google.oauth2.id_token.verify_oauth2_token", _mock_verify_oauth2_token)

    resp = await client.post("/api/auth/google/verify", json={"credential": "fake"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert body["user"]["email"] == "admin@waooaw.com"

    claims = jwt.decode(
        body["access_token"],
        "test-secret",
        algorithms=["HS256"],
        issuer="waooaw.com",
        options={"require": ["exp", "iat", "iss", "sub"]},
    )
    assert claims["email"] == "admin@waooaw.com"
    assert claims["sub"] == "google-sub-123"
    assert claims["iss"] == "waooaw.com"


@pytest.mark.auth
async def test_google_verify_rejects_wrong_audience(client, monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "expected-client", raising=False)
    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret", raising=False)
    monkeypatch.setattr(settings, "ALLOWED_EMAIL_DOMAINS", "waooaw.com", raising=False)

    def _mock_verify_oauth2_token(id_token_str, request, audience):
        # Simulate google-auth raising ValueError for wrong audience
        raise ValueError("Token has wrong audience")

    monkeypatch.setattr("google.oauth2.id_token.verify_oauth2_token", _mock_verify_oauth2_token)

    resp = await client.post("/api/auth/google/verify", json={"credential": "fake"})
    assert resp.status_code == 401


@pytest.mark.auth
async def test_dev_token_disabled_in_prod(client, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "prod", raising=False)
    resp = await client.post("/api/auth/dev-token")
    assert resp.status_code == 404


@pytest.mark.auth
async def test_db_updates_token_disabled_when_feature_off(client, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development", raising=False)
    monkeypatch.setattr(settings, "ENABLE_DB_UPDATES", False, raising=False)
    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret", raising=False)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256", raising=False)
    monkeypatch.setattr(settings, "JWT_ISSUER", "waooaw.com", raising=False)

    token = _mint_admin_token()
    resp = await client.post(
        "/api/auth/db-updates-token",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


@pytest.mark.auth
async def test_db_updates_token_mints_scoped_jwt(client, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development", raising=False)
    monkeypatch.setattr(settings, "ENABLE_DB_UPDATES", True, raising=False)
    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret", raising=False)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256", raising=False)
    monkeypatch.setattr(settings, "JWT_ISSUER", "waooaw.com", raising=False)
    monkeypatch.setattr(settings, "DB_UPDATES_TOKEN_SCOPE", "db_updates", raising=False)
    monkeypatch.setattr(settings, "DB_UPDATES_TOKEN_EXPIRE_MINUTES", 120, raising=False)

    token = _mint_admin_token()
    resp = await client.post(
        "/api/auth/db-updates-token",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["scope"] == "db_updates"

    claims = jwt.decode(
        body["access_token"],
        "test-secret",
        algorithms=["HS256"],
        issuer="waooaw.com",
        options={"require": ["exp", "iat", "iss", "sub"]},
    )
    assert claims["scope"] == "db_updates"
    assert "admin" in (claims.get("roles") or [])
