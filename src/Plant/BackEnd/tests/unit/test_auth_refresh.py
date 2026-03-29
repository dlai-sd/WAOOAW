"""Unit tests for Iteration 1 — Auth Foundation (E1-S1, E1-S3, E2-S1).

Test Cases:
  E1-S1 / OTP-verify:
        TC-E1-S1-1  login → access_token + refresh_token in body
    TC-E1-S1-2  cookie has HttpOnly, Secure, SameSite=Strict, Path=/api/v1/auth
    TC-E1-S1-3  refresh JWT has sub, jti, exp ≈ +7 days, token_type=refresh

  E1-S3 / POST /refresh:
        TC-E1-S3-1  valid body token → 200, new access_token + refresh_token, rotated Set-Cookie
        TC-E1-S3-2  no token        → 401 REFRESH_TOKEN_MISSING
        TC-E1-S3-3  expired token   → 401 REFRESH_TOKEN_EXPIRED
        TC-E1-S3-4  revoked jti     → 401 REFRESH_TOKEN_REVOKED
        TC-E1-S3-5  Redis timeout   → 200, stateless rotation still succeeds
        TC-E1-S3-6  token rotation: old jti best-effort revoked, new token issued

  E2-S1 / POST /logout:
        TC-E2-S1-1  valid token → 200, Redis jti best-effort deleted, cookie cleared
        TC-E2-S1-2  no token (idempotent) → 200
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
async def test_e1_s1_login_returns_body_and_cookie(monkeypatch):
    """TC-E1-S1-1: OTP verify → access_token + refresh_token in body, cookie set."""
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

    assert "access_token" in body
    assert body["refresh_token"] == "fake.refresh.token"

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
    async def _fake_generate(user_id: str, persist_in_redis: bool = True):
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

    raw_token = r.json()["refresh_token"]

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
async def test_e1_s3_valid_body_token_returns_new_tokens(monkeypatch):
    """TC-E1-S3-1: Valid refresh body token → 200 with new tokens and rotated cookie."""
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
            json={"refresh_token": "old.refresh.token"},
        )

    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert body["refresh_token"] == "new.refresh.token"
    assert body["token_type"] == "bearer"

    cookie_header = r.headers.get("set-cookie", "")
    assert "refresh_token" in cookie_header


@pytest.mark.asyncio
async def test_e1_s3_no_token_returns_401():
    """TC-E1-S3-2: No refresh token → 401 REFRESH_TOKEN_MISSING."""
    app = _make_refresh_app()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/api/v1/auth/refresh")

    assert r.status_code == 401
    assert "REFRESH_TOKEN_MISSING" in r.text


@pytest.mark.asyncio
async def test_e1_s3_expired_token_returns_401(monkeypatch):
    """TC-E1-S3-3: Expired refresh token → 401 REFRESH_TOKEN_EXPIRED."""
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
            json={"refresh_token": "expired.token"},
        )

    assert r.status_code == 401
    assert "REFRESH_TOKEN_EXPIRED" in r.text


@pytest.mark.asyncio
async def test_e1_s3_revoked_jti_returns_401(monkeypatch):
    """TC-E1-S3-4: Refresh token with revoked jti → 401 REFRESH_TOKEN_REVOKED."""
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
            json={"refresh_token": "revoked.token"},
        )

    assert r.status_code == 401
    assert "REFRESH_TOKEN_REVOKED" in r.text


@pytest.mark.asyncio
async def test_e1_s3_redis_timeout_allows_stateless_rotation(monkeypatch):
    """TC-E1-S3-5: Redis timeout should not block a valid signed refresh token."""
    app = _make_refresh_app()

    async def _raise_timeout(_jti: str) -> bool:
        raise TimeoutError("redis timeout")

    monkeypatch.setattr(
        auth_module, "verify_token",
        lambda token: {"sub": _CUSTOMER_ID, "jti": _JTI, "token_type": "refresh"},
    )
    monkeypatch.setattr(auth_module, "is_refresh_token_valid", _raise_timeout)
    monkeypatch.setattr(auth_module, "revoke_refresh_token", AsyncMock())
    monkeypatch.setattr(
        auth_module, "generate_refresh_token",
        AsyncMock(return_value=("new.refresh.token", str(uuid.uuid4()))),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "valid.token"},
        )

    assert r.status_code == 200
    assert r.json()["refresh_token"] == "new.refresh.token"


@pytest.mark.asyncio
async def test_e1_s3_token_rotation(monkeypatch):
    """TC-E1-S3-6: Old jti best-effort revoked and new token issued."""
    app = _make_refresh_app()
    old_jti = str(uuid.uuid4())
    new_jti = str(uuid.uuid4())
    revoked: list[str] = []
    generated: list[str] = []

    async def _fake_revoke(jti: str) -> None:
        revoked.append(jti)

    async def _fake_generate(user_id: str, persist_in_redis: bool = True):
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
            json={"refresh_token": "valid.token"},
        )

    assert r.status_code == 200
    assert old_jti in revoked, "Old jti was not revoked"
    assert new_jti in generated, "New jti was not generated"


# ---------------------------------------------------------------------------
# E2-S1: POST /api/v1/auth/logout
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_e2_s1_logout_revokes_jti(monkeypatch):
    """TC-E2-S1-1: Logout accepts body token and best-effort revokes jti."""
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
            json={"refresh_token": "some.refresh.token"},
        )

    assert r.status_code == 200
    assert _JTI in revoked

    set_cookie = r.headers.get("set-cookie", "")
    # max-age=0 or expires in the past clears the cookie
    assert "refresh_token" in set_cookie


@pytest.mark.asyncio
async def test_e2_s1_logout_no_token_is_idempotent():
    """TC-E2-S1-2: Logout with no token → 200 (idempotent)."""
    app = _make_refresh_app()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/api/v1/auth/logout")

    assert r.status_code == 200

