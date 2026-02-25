"""Unit tests for POST /auth/register (AUTH-MOBILE-REG-1).

Covers:
- Successful registration (new customer) → 200, created=True
- Idempotent re-registration (existing customer) → 200, created=False
- Rate limiting (throttle) → 429 with Retry-After header
- Audit events written for success and throttle block
"""

import uuid

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api.v1 import auth
from schemas.customer import CustomerCreate
from services.security_audit import InMemorySecurityAuditStore
from services.security_throttle import InMemoryThrottleStore, SecurityThrottle

# ---------------------------------------------------------------------------
# Helpers / fakes
# ---------------------------------------------------------------------------

_VALID_PAYLOAD = {
    "fullName": "Priya Sharma",
    "email": "priya@example.com",
    "phone": "+919876543210",
    "businessName": "Priya Exports",
    "businessIndustry": "marketing",
    "businessAddress": "Mumbai, India",
    "preferredContactMethod": "email",
    "consent": True,
}


class _FakeCustomer:
    def __init__(self, email: str, created: bool = True):
        self.id = uuid.uuid4()
        self.email = email
        self.phone = "+919876543210"
        self.full_name = "Priya Sharma"
        self.business_name = "Priya Exports"
        self.business_industry = "marketing"
        self.business_address = "Mumbai, India"
        self.website = None
        self.gst_number = None
        self.preferred_contact_method = "email"
        self.consent = True
        self._created = created


class _FakeCustomerService:
    def __init__(self, created: bool = True):
        self._created = created

    async def upsert_by_email(self, payload: CustomerCreate):
        email = str(payload.email).strip().lower()
        return _FakeCustomer(email, created=self._created), self._created


def _make_test_app(
    audit_store: InMemorySecurityAuditStore,
    throttle: SecurityThrottle,
    service: _FakeCustomerService | None = None,
) -> FastAPI:
    app = FastAPI()
    svc = service or _FakeCustomerService()
    app.dependency_overrides[auth.get_customer_service] = lambda: svc
    app.dependency_overrides[auth.get_security_audit_store] = lambda: audit_store
    app.dependency_overrides[auth.get_security_throttle] = lambda: throttle
    app.include_router(auth.router, prefix="/api/v1")
    return app


def _permissive_throttle() -> SecurityThrottle:
    """Throttle that never blocks (max 1000 attempts per window)."""
    return SecurityThrottle(
        InMemoryThrottleStore(),
        max_attempts=1000,
        window_seconds=60,
        lockout_seconds=300,
    )


def _tight_throttle() -> SecurityThrottle:
    """Throttle that blocks after the first attempt."""
    return SecurityThrottle(
        InMemoryThrottleStore(),
        max_attempts=1,
        window_seconds=60,
        lockout_seconds=300,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_register_new_customer_returns_registration_id():
    """New registration succeeds, returns registration_id, created=True."""
    audit_store = InMemorySecurityAuditStore()
    app = _make_test_app(audit_store, _permissive_throttle(), _FakeCustomerService(created=True))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/auth/register",
            json=_VALID_PAYLOAD,
            headers={"X-Forwarded-For": "1.2.3.4", "User-Agent": "pytest"},
        )

    assert r.status_code == 200
    body = r.json()
    assert "registration_id" in body
    assert body["email"] == "priya@example.com"
    assert body["phone"] == "+919876543210"
    assert body["created"] is True


@pytest.mark.asyncio
async def test_register_existing_customer_returns_created_false():
    """Re-registration of known email is idempotent, created=False."""
    audit_store = InMemorySecurityAuditStore()
    app = _make_test_app(audit_store, _permissive_throttle(), _FakeCustomerService(created=False))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/auth/register",
            json=_VALID_PAYLOAD,
            headers={"X-Forwarded-For": "1.2.3.4", "User-Agent": "pytest"},
        )

    assert r.status_code == 200
    body = r.json()
    assert body["created"] is False
    assert "registration_id" in body


@pytest.mark.asyncio
async def test_register_writes_audit_event_on_success():
    """Successful registration writes a mobile_register audit event."""
    audit_store = InMemorySecurityAuditStore()
    app = _make_test_app(audit_store, _permissive_throttle())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/v1/auth/register", json=_VALID_PAYLOAD)

    events = audit_store.list_records(event_type="mobile_register", limit=5)
    assert len(events) == 1
    assert events[0].success is True
    assert events[0].email == "priya@example.com"


@pytest.mark.asyncio
async def test_register_throttle_blocks_after_limit():
    """Third request from same IP is throttled with 429 and Retry-After header."""
    audit_store = InMemorySecurityAuditStore()
    throttle = _tight_throttle()
    app = _make_test_app(audit_store, throttle)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First request (within limit)
        r1 = await client.post(
            "/api/v1/auth/register",
            json=_VALID_PAYLOAD,
            headers={"X-Forwarded-For": "9.9.9.9", "User-Agent": "pytest"},
        )
        # Second request triggers throttle
        r2 = await client.post(
            "/api/v1/auth/register",
            json=_VALID_PAYLOAD,
            headers={"X-Forwarded-For": "9.9.9.9", "User-Agent": "pytest"},
        )

    assert r1.status_code == 200
    assert r2.status_code == 429
    assert "Retry-After" in r2.headers

    throttle_events = audit_store.list_records(event_type="throttle_block", limit=5)
    assert len(throttle_events) >= 1
    assert throttle_events[0].success is False


@pytest.mark.asyncio
async def test_register_rejects_missing_required_fields():
    """Omitting required fields (businessName) returns 422."""
    audit_store = InMemorySecurityAuditStore()
    app = _make_test_app(audit_store, _permissive_throttle())

    incomplete = {k: v for k, v in _VALID_PAYLOAD.items() if k != "businessName"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/api/v1/auth/register", json=incomplete)

    assert r.status_code == 422
