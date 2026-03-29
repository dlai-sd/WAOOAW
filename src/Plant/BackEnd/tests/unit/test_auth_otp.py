"""Unit tests for POST /auth/otp/start and POST /auth/otp/verify (AUTH-MOBILE-OTP-1).

Covers:
- otp/start: success with otp_code echoed (dev env)
- otp/start: customer not found → 404
- otp/start: rate limit exceeded → 429
- otp/start: no email/phone on file → 400
- otp/verify: correct code → 200, access_token + refresh_token
- otp/verify: wrong code → 400
- otp/verify: expired challenge → 400 with "expired"
- otp/verify: too many attempts → 429
- otp/verify: unknown otp_id → 400
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api.v1 import auth
from services.otp_service import OtpStore, OtpChallenge, OTP_TTL_SECONDS
from services.security_audit import InMemorySecurityAuditStore
from services.security_throttle import InMemoryThrottleStore, SecurityThrottle

# ---------------------------------------------------------------------------
# Helpers / fakes
# ---------------------------------------------------------------------------

_REGISTRATION_ID = str(uuid.uuid4())


class _FakeCustomer:
    def __init__(
        self,
        customer_id: str = _REGISTRATION_ID,
        email: str = "priya@example.com",
        phone: str = "+919876543210",
        preferred_contact_method: str = "email",
    ):
        self.id = uuid.UUID(customer_id)
        self.email = email
        self.phone = phone
        self.preferred_contact_method = preferred_contact_method
        self.full_name = "Priya Sharma"


class _FakeCustomerService:
    """Fake CustomerService that implements get_by_id."""

    def __init__(self, customer: _FakeCustomer | None = "default"):
        # Pass None to simulate customer-not-found.
        if customer == "default":
            self._customer: _FakeCustomer | None = _FakeCustomer(
                customer_id=_REGISTRATION_ID
            )
        else:
            self._customer = customer

    async def get_by_id(self, customer_id: str) -> _FakeCustomer | None:
        return self._customer


def _make_test_app(
    audit_store: InMemorySecurityAuditStore,
    otp_store: OtpStore,
    service: _FakeCustomerService | None = None,
) -> FastAPI:
    app = FastAPI()
    svc = service or _FakeCustomerService()
    app.dependency_overrides[auth.get_customer_service] = lambda: svc
    app.dependency_overrides[auth.get_security_audit_store] = lambda: audit_store
    app.dependency_overrides[auth.get_otp_store] = lambda: otp_store
    # OTP routes do not use the registration throttle, but the override keeps
    # the app from trying to resolve a real DB session.
    from services.security_throttle import SecurityThrottle
    permissive = SecurityThrottle(
        InMemoryThrottleStore(), max_attempts=1000, window_seconds=60, lockout_seconds=300
    )
    app.dependency_overrides[auth.get_security_throttle] = lambda: permissive
    app.include_router(auth.router, prefix="/api/v1")
    return app


# ---------------------------------------------------------------------------
# POST /api/v1/auth/otp/start
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_otp_start_returns_otp_id_and_code_in_dev():
    """Successful otp/start in dev env returns otp_id and echoes otp_code."""
    audit_store = InMemorySecurityAuditStore()
    otp_store = OtpStore()

    app = _make_test_app(audit_store, otp_store)

    # Force dev/demo environment so otp_code is echoed.
    with patch("api.v1.auth._otp_echo_enabled", return_value=True):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post(
                "/api/v1/auth/otp/start",
                json={"registration_id": _REGISTRATION_ID},
                headers={"X-Forwarded-For": "1.2.3.4", "User-Agent": "pytest"},
            )

    assert r.status_code == 200, r.text
    body = r.json()
    assert "otp_id" in body
    assert body["channel"] == "email"
    assert "destination_masked" in body
    assert body["expires_in_seconds"] == OTP_TTL_SECONDS
    # In dev, code is echoed.
    assert body.get("otp_code") is not None
    assert len(body["otp_code"]) == 6


@pytest.mark.asyncio
async def test_otp_start_no_code_in_prod():
    """otp_code must be None when _otp_echo_enabled returns False (prod/uat)."""
    audit_store = InMemorySecurityAuditStore()
    otp_store = OtpStore()
    app = _make_test_app(audit_store, otp_store)

    with patch("api.v1.auth._otp_echo_enabled", return_value=False):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post(
                "/api/v1/auth/otp/start",
                json={"registration_id": _REGISTRATION_ID},
            )

    assert r.status_code == 200
    assert r.json().get("otp_code") is None


@pytest.mark.asyncio
async def test_otp_start_customer_not_found_returns_404():
    """Unknown registration_id → 404."""
    audit_store = InMemorySecurityAuditStore()
    otp_store = OtpStore()
    app = _make_test_app(audit_store, otp_store, service=_FakeCustomerService(customer=None))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/auth/otp/start",
            json={"registration_id": str(uuid.uuid4())},
        )

    assert r.status_code == 404


@pytest.mark.asyncio
async def test_otp_start_no_email_on_file_returns_400():
    """Customer with no email and requesting email channel → 400."""
    audit_store = InMemorySecurityAuditStore()
    otp_store = OtpStore()
    # Create customer with no email.
    customer = _FakeCustomer(
        customer_id=_REGISTRATION_ID,
        email="",
        phone="",
        preferred_contact_method="email",
    )
    app = _make_test_app(audit_store, otp_store, service=_FakeCustomerService(customer=customer))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/auth/otp/start",
            json={"registration_id": _REGISTRATION_ID, "channel": "email"},
        )

    assert r.status_code == 400


@pytest.mark.asyncio
async def test_otp_start_rate_limit_blocks_after_max_requests():
    """Exceeding OTP_RATE_MAX_PER_WINDOW challenges for same destination → 429."""
    from services.otp_service import OTP_RATE_MAX_PER_WINDOW

    audit_store = InMemorySecurityAuditStore()
    otp_store = OtpStore()
    app = _make_test_app(audit_store, otp_store)

    with patch("api.v1.auth._otp_echo_enabled", return_value=True):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Issue max allowed challenges.
            for _ in range(OTP_RATE_MAX_PER_WINDOW):
                r = await client.post(
                    "/api/v1/auth/otp/start",
                    json={"registration_id": _REGISTRATION_ID},
                )
                assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"

            # Next request must be rate-limited.
            r_blocked = await client.post(
                "/api/v1/auth/otp/start",
                json={"registration_id": _REGISTRATION_ID},
            )

    assert r_blocked.status_code == 429


# ---------------------------------------------------------------------------
# POST /api/v1/auth/otp/verify
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_otp_verify_correct_code_returns_tokens():
    """Correct code → 200, access_token and refresh_token in body, cookie still set."""
    audit_store = InMemorySecurityAuditStore()
    otp_store = OtpStore()

    # Create challenge manually so we know the plain code.
    challenge, plain_code = otp_store.create_challenge(
        registration_id=_REGISTRATION_ID,
        channel="email",
        destination="priya@example.com",
        ttl_seconds=OTP_TTL_SECONDS,
    )
    app = _make_test_app(audit_store, otp_store)

    transport = ASGITransport(app=app)
    # Mock Redis-dependent helpers so the test passes without a live Redis.
    with patch("api.v1.auth.generate_refresh_token", new_callable=AsyncMock) as mock_gen, \
         patch("api.v1.auth.cache_token_version", new_callable=AsyncMock):
        mock_gen.return_value = ("fake-refresh-token-value", "fake-jti-001")
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post(
                "/api/v1/auth/otp/verify",
                json={"otp_id": challenge.otp_id, "code": plain_code},
            )

    assert r.status_code == 200, r.text
    body = r.json()
    assert "access_token" in body
    assert body["refresh_token"] == "fake-refresh-token-value"
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0
    set_cookie = r.headers.get("set-cookie", "")
    assert "refresh_token" in set_cookie


@pytest.mark.asyncio
async def test_otp_verify_wrong_code_returns_400():
    """Wrong code → 400."""
    audit_store = InMemorySecurityAuditStore()
    otp_store = OtpStore()

    challenge, _ = otp_store.create_challenge(
        registration_id=_REGISTRATION_ID,
        channel="email",
        destination="priya@example.com",
        ttl_seconds=OTP_TTL_SECONDS,
    )
    app = _make_test_app(audit_store, otp_store)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/auth/otp/verify",
            json={"otp_id": challenge.otp_id, "code": "000000"},
        )

    assert r.status_code == 400


@pytest.mark.asyncio
async def test_otp_verify_expired_challenge_returns_400():
    """Expired challenge → 400 with 'expired' in detail."""
    audit_store = InMemorySecurityAuditStore()
    otp_store = OtpStore()

    # Create challenge, then backdate its expiry.
    challenge, plain_code = otp_store.create_challenge(
        registration_id=_REGISTRATION_ID,
        channel="email",
        destination="priya@example.com",
        ttl_seconds=OTP_TTL_SECONDS,
    )
    # Force expiry by mutating the stored challenge.
    with otp_store._lock:
        stored = otp_store._challenges[challenge.otp_id]
        otp_store._challenges[challenge.otp_id] = stored.model_copy(
            update={"expires_at": datetime.now(timezone.utc) - timedelta(seconds=1)}
        )

    app = _make_test_app(audit_store, otp_store)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/auth/otp/verify",
            json={"otp_id": challenge.otp_id, "code": plain_code},
        )

    assert r.status_code == 400
    assert "expired" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_otp_verify_too_many_attempts_returns_429():
    """Exceeding OTP_MAX_ATTEMPTS with wrong codes → 429."""
    from services.otp_service import OTP_MAX_ATTEMPTS

    audit_store = InMemorySecurityAuditStore()
    otp_store = OtpStore()

    challenge, _ = otp_store.create_challenge(
        registration_id=_REGISTRATION_ID,
        channel="email",
        destination="priya@example.com",
        ttl_seconds=OTP_TTL_SECONDS,
    )
    app = _make_test_app(audit_store, otp_store)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Submit wrong code OTP_MAX_ATTEMPTS times to exhaust attempts.
        for _ in range(OTP_MAX_ATTEMPTS):
            await client.post(
                "/api/v1/auth/otp/verify",
                json={"otp_id": challenge.otp_id, "code": "000000"},
            )

        # Next attempt must be rejected with 429.
        r = await client.post(
            "/api/v1/auth/otp/verify",
            json={"otp_id": challenge.otp_id, "code": "000000"},
        )

    assert r.status_code == 429


@pytest.mark.asyncio
async def test_otp_verify_unknown_otp_id_returns_400():
    """Completely unknown otp_id → 400."""
    audit_store = InMemorySecurityAuditStore()
    otp_store = OtpStore()
    app = _make_test_app(audit_store, otp_store)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/auth/otp/verify",
            json={"otp_id": "nonexistent-otp-id", "code": "123456"},
        )

    assert r.status_code == 400
