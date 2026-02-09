import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient

from api.v1 import customers
from core.exceptions import DuplicateEntityError
from services.security_audit import InMemorySecurityAuditStore
from services.security_throttle import InMemoryThrottleStore, SecurityThrottle


class _FakeCustomerService:
    async def upsert_by_email(self, payload):
        _ = payload
        raise DuplicateEntityError("Customer with this phone already exists")


async def _duplicate_entity_handler(request, exc: DuplicateEntityError):
    return JSONResponse(
        status_code=409,
        content={
            "type": "https://waooaw.com/errors/duplicate-entity",
            "title": "Duplicate Entity Error",
            "status": 409,
            "detail": str(exc),
            "instance": str(request.url.path),
            "correlation_id": "test",
        },
    )


def _make_test_app(audit_store: InMemorySecurityAuditStore, throttle: SecurityThrottle) -> FastAPI:
    app = FastAPI()
    app.add_exception_handler(DuplicateEntityError, _duplicate_entity_handler)

    app.dependency_overrides[customers.get_customer_service] = lambda: _FakeCustomerService()
    app.dependency_overrides[customers.get_security_audit_store] = lambda: audit_store
    app.dependency_overrides[customers.get_security_throttle] = lambda: throttle

    app.include_router(customers.router, prefix="/api/v1")
    return app


@pytest.mark.asyncio
async def test_customer_upsert_duplicate_phone_returns_409_and_audits_conflict():
    audit_store = InMemorySecurityAuditStore()
    throttle = SecurityThrottle(
        InMemoryThrottleStore(),
        max_attempts=100,
        window_seconds=60,
        lockout_seconds=300,
    )
    app = _make_test_app(audit_store, throttle)

    payload = {
        "email": "user@example.com",
        "phone": "+91 123 456 7890",
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
        r = await client.post(
            "/api/v1/customers",
            json=payload,
            headers={"X-Forwarded-For": "1.2.3.4", "User-Agent": "pytest"},
        )

    assert r.status_code == 409
    body = r.json()
    assert body.get("status") == 409
    assert "duplicate" in (body.get("type") or "")

    events = audit_store.list_records(limit=50)
    assert any(e.event_type == "customer_upsert_conflict" and e.success is False for e in events)
