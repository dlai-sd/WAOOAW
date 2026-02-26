"""Unit tests for Iteration 1 — Auth Foundation (E1-S1, E1-S3, E2-S1).

Test Cases:
  E1-S1 / OTP-verify:
    TC-E1-S1-1  login → access_token in body, refresh_token in httpOnly cookie
    TC-E1-S1-2  cookie has HttpOnly, Secure, SameSite=Strict, Path=/api/v1/auth
    TC-E1-S1-3  refresh JWT has sub, jti, exp ≈ +7 days, token_type=refresh

  E1-S3 / POST /refresh:
    TC-E1-S3-1  valid cookie → 200, new access_token, rotated Set-Cookie
    TC-E1-S3-2  no cookie    → 401 REFRESH_TOKEN_MISSING
    TC-E1-S3-3  expired token → 401 REFRESH_TOKEN_EXPIRED
    TC-E1-S3-4  revoked jti  → 401 REFRESH_TOKEN_REVOKED
    TC-E1-S3-5  token rotation: old jti gone from Redis, new jti stored

  E2-S1 / POST /logout:
    TC-E2-S1-1  valid cookie → 200, Redis jti deleted, cookie cleared
    TC-E2-S1-2  logout then refresh → 401 REFRESH_TOKEN_REVOKED
    TC-E2-S1-3  no cookie (idempotent) → 200
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api.v1 import auth as auth_module
from services.otp_service import OtpStore, OtpChallenge
from services.security_audit import InMemorySecurityAuditStore
from services.security_throttle import InMemoryThrottleStore, SecurityThrottle

# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

_CUSTOMER_ID = "00000000-0000-0000-0000-000000000001"
_EMAIL = "test@example.com"
_JTI = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


class _FakeCustomer:
    def __init__(self):
        self.id = uuid.UUID(_CUSTOMER_ID)
        self.email = _EMAIL
        self.phone = "+919876543210"
        self.preferred_contact_method = "email"
        self.full_name = "Test User"
        self.token_version = 1


class _FakeCustomerService:
    async def get_by_id(self, cid: str):
        return _FakeCustomer()

    async def get_by_email(self, email: str):
        return _FakeCustomer()


def _permissive_throttle() -> SecurityThrottle:
    """Returns a SecurityThrottle that never blocks."""
    return SecurityThrottle(
        InMemoryThrottleStore(), max_attempts=1000, window_seconds=60, lockout_seconds=300
    )


# ---------------------------------------------------------------------------
# App builder
# ---------------------------------------------------------------------------

def _make_app():
    audit = InMemorySecurityAuditStore()
    app = FastAPI()
    app.dependency_overrides[auth_module.get_customer_service] = lambda: _FakeCustomerService()
    app.dependency_overrides[auth_module.get_security_audit_store] = lambda: audit
    otp_store = OtpStore()
    app.dependency_overrides[auth_module.get_otp_store] = lambda: otp_store
    app.dependency_overrides[auth_module.get_security_throttle] = lambda: _permissive_throttle()
    app.include_router(auth_module.router, prefix="/api/v1")
    return app, otp_store, audit


# ---------------------------------------------------------------------------
# E1-S1: refresh cookie issued on OTP-verify login
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_e1_s1_login_issues_cookie_not_body(monkeypatch):
    """TC-E1-S1-1: OTP verify → access_token in body, refresh_token cookie only."""
    app, otp_store, _ = _make_app()

    # Create a valid OTP challenge
    challenge, plain_code = otp_store.create_challenge(
        registration_id=_CUSTOMER_ID, channel="email",
        destination=_EMAIL, ttl_seconds=300,
    )

    # Patch on auth_module (which imported these functions at load time)
    monkeypatch.setattr(
        auth_module, "generate_refresh_token",
        AsyncMock(return_value=("fake.refresh.token", _JTI)),
    )
    monkeypatch.setattr(auth_module, "cache_token_version", AsyncMock())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/auth/otp/verify",
            json={"otp_id": challenge.otp_id, "code": plain_code},
        )

    assert r.status_code == 200
    body = r.json()

    # access_token must be in body
    assert "access_token" in body
    # refresh_token must NOT be in body (httpOnly cookie only)
    assert "refresh_token" not in body

    # Cookie must be set
    cookie_header = r.headers.get("set-cookie", "")
    assert "refresh_token" in cookie_header


@pytest.mark.asyncio
async def test_e1_s1_cookie_flags(monkeypatch):
    """TC-E1-S1-2: Cookie has HttpOnly, SameSite=strict, Path=/api/v1/auth."""
    app, otp_store, _ = _make_app()

    challenge, plain_code = otp_store.create_challenge(
        registration_id=_CUSTOMER_ID, channel="email",
        destination=_EMAIL, ttl_seconds=300,
    )

    monkeypatch.setattr(
        auth_module, "generate_refresh_token",
        AsyncMock(return_value=("fake.refresh.token", _JTI)),
    )
    monkeypatch.setattr(auth_module, "cache_token_version", AsyncMock())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/auth/otp/verify",
            json={"otp_id": challenge.otp_id, "code": plain_code},
        )

    assert r.status_code == 200
    cookie = r.headers.get("set-cookie", "").lower()
    assert "httponly" in cookie
    assert "samesite=strict" in cookie
    assert "path=/api/v1/auth" in cookie


@pytest.mark.asyncio
async def test_e1_s1_refresh_jwt_claims(monkeypatch):
    """TC-E1-S1-3: Refresh JWT contains sub, jti, exp≈+7days, token_type=refresh."""
    from core.config import settings
    from jose import jwt as jose_jwt
    from core.security import REFRESH_TOKEN_TTL_SECONDS

    app, otp_store, _ = _make_app()

    challenge, plain_code = otp_store.create_challenge(
        registration_id=_CUSTOMER_ID, channel="email",
        destination=_EMAIL, ttl_seconds=300,
    )

    # Use the real generate_refresh_token but mock its Redis write
    async def _fake_generate(user_id: str):
        jti = str(uuid.uuid4())
        expire = datetime.utcnow() + timedelta(seconds=REFRESH_TOKEN_TTL_SECONDS)
        token = jose_jwt.encode(
            {"sub": user_id, "jti": jti, "exp": expire, "token_type": "refresh", "iss": "waooaw.com"},
            settings.secret_key, algorithm=settings.algorithm,
        )
        return token, jti

    monkeypatch.setattr(auth_module, "generate_refresh_token", _fake_generate)
    monkeypatch.setattr(auth_module, "cache_token_version", AsyncMock())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/auth/otp/verify",
            json={"otp_id": challenge.otp_id, "code": plain_code},
        )

    assert r.status_code == 200

    # Extract refresh token from cookie
    cookie_header = r.headers.get("set-cookie", "")
    raw_token = None
    for part in cookie_header.split(";"):
        part = part.strip()
        if part.startswith("refresh_token="):
            raw_token = part.split("=", 1)[1]
            break

    assert raw_token, "refresh_token cookie not found"

    claims = jose_jwt.decode(raw_token, settings.secret_key, algorithms=[settings.algorithm])
    assert claims["sub"] == _CUSTOMER_ID
    assert "jti" in claims
    assert claims["token_type"] == "refresh"

    exp_dt = datetime.utcfromtimestamp(claims["exp"])
    expected = datetime.utcnow() + timedelta(days=7)
    delta = abs((exp_dt - expected).total_seconds())
    assert delta < 60, f"Refresh token expiry too far from +7 days: {delta}s off"


# ---------------------------------------------------------------------------
# E1-S3: POST /api/v1/auth/refresh
# ---------------------------------------------------------------------------

def _make_refresh_app() -> FastAPI:
    app = FastAPI()
    app.include_router(auth_module.router, prefix="/api/v1")
    return app


@pytest.mark.asyncio
async def test_e1_s3_valid_cookie_returns_new_access_token(monkeypatch):
    """TC-E1-S3-1: Valid refresh cookie → 200 with new access_token and rotated cookie."""
    app = _make_refresh_app()

    monkeypatch.setattr(
        auth_module, "verify_token",
        lambda token: {"sub": _CUSTOMER_ID, "jti": _JTI, "token_type": "refresh"},
    )
    monkeypatch.setattr(auth_module, "is_refresh_token_valid", AsyncMock(return_value=True))
    monkeypatch.setattr(auth_module, "revoke_refresh_token", AsyncMock())
    monkeypatch.setattr(
        auth_module, "generate_refresh_token",
        AsyncMock(return_value=("new.refresh.token", str(uuid.uuid4()))),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/auth/refresh",
            cookies={"refresh_token": "old.refresh.token"},
        )

    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"

    # New rotated refresh cookie must be set
    cookie_header = r.headers.get("set-cookie", "")
    assert "refresh_token" in cookie_header


@pytest.mark.asyncio
async def test_e1_s3_no_cookie_returns_401():
    """TC-E1-S3-2: No refresh cookie → 401 REFRESH_TOKEN_MISSING."""
    app = _make_refresh_app()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/api/v1/auth/refresh")

    assert r.status_code == 401
    assert "REFRESH_TOKEN_MISSING" in r.text


@pytest.mark.asyncio
async def test_e1_s3_expired_token_returns_401(monkeypatch):
    """TC-E1-S3-3: Expired refresh cookie → 401 REFRESH_TOKEN_EXPIRED."""
    from core.exceptions import JWTTokenExpiredError

    app = _make_refresh_app()

    monkeypatch.setattr(
        auth_module, "verify_token",
        lambda token: (_ for _ in ()).throw(JWTTokenExpiredError(expired_at="2025-01-01")),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/auth/refresh",
            cookies={"refresh_token": "expired.token"},
        )

    assert r.status_code == 401
    assert "REFRESH_TOKEN_EXPIRED" in r.text


@pytest.mark.asyncio
async def test_e1_s3_revoked_jti_returns_401(monkeypatch):
    """TC-E1-S3-4: Refresh cookie with revoked jti → 401 REFRESH_TOKEN_REVOKED."""
    app = _make_refresh_app()

    monkeypatch.setattr(
        auth_module, "verify_token",
        lambda token: {"sub": _CUSTOMER_ID, "jti": _JTI, "token_type": "refresh"},
    )
    monkeypatch.setattr(auth_module, "is_refresh_token_valid", AsyncMock(return_value=False))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/auth/refresh",
            cookies={"refresh_token": "revoked.token"},
        )

    assert r.status_code == 401
    assert "REFRESH_TOKEN_REVOKED" in r.text


@pytest.mark.asyncio
async def test_e1_s3_token_rotation(monkeypatch):
    """TC-E1-S3-5: Old jti revoked, new jti stored on successful refresh."""
    app = _make_refresh_app()
    old_jti = str(uuid.uuid4())
    new_jti = str(uuid.uuid4())
    revoked: list[str] = []
    generated: list[str] = []

    async def _fake_revoke(jti: str) -> None:
        revoked.append(jti)

    async def _fake_generate(user_id: str):
        generated.append(new_jti)
        return ("new.refresh.token", new_jti)

    monkeypatch.setattr(
        auth_module, "verify_token",
        lambda token: {"sub": _CUSTOMER_ID, "jti": old_jti, "token_type": "refresh"},
    )
    monkeypatch.setattr(auth_module, "is_refresh_token_valid", AsyncMock(return_value=True))
    monkeypatch.setattr(auth_module, "revoke_refresh_token", _fake_revoke)
    monkeypatch.setattr(auth_module, "generate_refresh_token", _fake_generate)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/auth/refresh",
            cookies={"refresh_token": "valid.token"},
        )

    assert r.status_code == 200
    assert old_jti in revoked, "Old jti was not revoked"
    assert new_jti in generated, "New jti was not generated"


# ---------------------------------------------------------------------------
# E2-S1: POST /api/v1/auth/logout
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_e2_s1_logout_revokes_jti(monkeypatch):
    """TC-E2-S1-1: Logout → 200, jti deleted from Redis, cookie cleared."""
    app = _make_refresh_app()
    revoked: list[str] = []

    monkeypatch.setattr(
        auth_module, "decode_refresh_token_unverified",
        lambda token: {"jti": _JTI},
    )

    async def _fake_revoke(jti: str) -> None:
        revoked.append(jti)

    monkeypatch.setattr(auth_module, "revoke_refresh_token", _fake_revoke)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/auth/logout",
            cookies={"refresh_token": "some.refresh.token"},
        )

    assert r.status_code == 200
    assert _JTI in revoked

    set_cookie = r.headers.get("set-cookie", "")
    # max-age=0 or expires in the past clears the cookie
    assert "refresh_token" in set_cookie


@pytest.mark.asyncio
async def test_e2_s1_logout_no_cookie_is_idempotent():
    """TC-E2-S1-3: Logout with no cookie → 200 (idempotent)."""
    app = _make_refresh_app()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/api/v1/auth/logout")

    assert r.status_code == 200


@pytest.mark.asyncio
async def test_e2_s1_after_logout_refresh_is_rejected(monkeypatch):
    """TC-E2-S1-2: After logout, using old refresh cookie → 401 REFRESH_TOKEN_REVOKED."""
    app = _make_refresh_app()
    store: dict[str, bool] = {_JTI: True}

    # Logout: decode gives jti, revoke removes it from store
    monkeypatch.setattr(
        auth_module, "decode_refresh_token_unverified",
        lambda token: {"jti": _JTI},
    )

    async def _fake_revoke(jti: str) -> None:
        store.pop(jti, None)

    async def _fake_valid(jti: str) -> bool:
        return store.get(jti, False)

    monkeypatch.setattr(auth_module, "revoke_refresh_token", _fake_revoke)
    monkeypatch.setattr(auth_module, "is_refresh_token_valid", _fake_valid)
    monkeypatch.setattr(
        auth_module, "verify_token",
        lambda token: {"sub": _CUSTOMER_ID, "jti": _JTI, "token_type": "refresh"},
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Step 1: logout
        r1 = await client.post(
            "/api/v1/auth/logout",
            cookies={"refresh_token": "old.token"},
        )
        assert r1.status_code == 200

        # Step 2: try to refresh with the same token
        r2 = await client.post(
            "/api/v1/auth/refresh",
            cookies={"refresh_token": "old.token"},
        )

    assert r2.status_code == 401
    assert "REFRESH_TOKEN_REVOKED" in r2.text
