import uuid

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api.v1 import customers
from schemas.customer import CustomerCreate
from services.security_audit import InMemorySecurityAuditStore
from services.security_throttle import InMemoryThrottleStore, SecurityThrottle


class _FakeCustomer:
    def __init__(self, email: str):
        self.id = uuid.uuid4()
        self.email = email
        self.phone = "+911234567890"
        self.full_name = "Test User"
        self.business_name = "Test Biz"
        self.business_industry = "marketing"
        self.business_address = "Somewhere"
        self.website = None
        self.gst_number = None
        self.preferred_contact_method = "email"
        self.consent = True


class _FakeCustomerService:
    async def upsert_by_email(self, payload: CustomerCreate):
        email = str(payload.email).strip().lower()
        return _FakeCustomer(email), True


def _make_test_app(audit_store: InMemorySecurityAuditStore, throttle: SecurityThrottle) -> FastAPI:
    app = FastAPI()

    app.dependency_overrides[customers.get_customer_service] = lambda: _FakeCustomerService()
    app.dependency_overrides[customers.get_security_audit_store] = lambda: audit_store
    app.dependency_overrides[customers.get_security_throttle] = lambda: throttle

    app.include_router(customers.router, prefix="/api/v1")
    return app


@pytest.mark.asyncio
async def test_customer_upsert_throttles_and_logs_security_events():
    audit_store = InMemorySecurityAuditStore()
    throttle = SecurityThrottle(
        InMemoryThrottleStore(),
        max_attempts=2,
        window_seconds=60,
        lockout_seconds=300,
    )
    app = _make_test_app(audit_store, throttle)

    payload = {
        "email": "user@example.com",
        "phone": "+911234567890",
        "full_name": "Test User",
        "business_name": "Test Biz",
        "business_industry": "marketing",
        "business_address": "Somewhere",
        "website": None,
        "gst_number": None,
        "preferred_contact_method": "email",
        "consent": True,
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r1 = await client.post(
            "/api/v1/customers",
            json=payload,
            headers={"X-Forwarded-For": "1.2.3.4", "User-Agent": "pytest"},
        )
        r2 = await client.post(
            "/api/v1/customers",
            json=payload,
            headers={"X-Forwarded-For": "1.2.3.4", "User-Agent": "pytest"},
        )
        r3 = await client.post(
            "/api/v1/customers",
            json=payload,
            headers={"X-Forwarded-For": "1.2.3.4", "User-Agent": "pytest"},
        )

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r3.status_code == 429
    assert "Retry-After" in r3.headers

    # We should have at least two success records and one throttle block.
    events = audit_store.list_records(limit=50)
    assert any(e.event_type == "customer_upsert" and e.success is True for e in events)
    assert any(e.event_type == "throttle_block" and e.success is False for e in events)
