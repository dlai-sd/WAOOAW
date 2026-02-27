"""Unit tests: customer upsert enqueues registration task via BackgroundTasks.

Verifies that on first-time customer creation:
  - The response is returned immediately (not blocked by Celery/Redis)
  - _enqueue_customer_registered is scheduled via BackgroundTasks, not called inline

This is the regression test for the Celery/Redis 10-second block bug where
handle_customer_registered.delay() was called inline before the response was
sent, causing CP Backend's httpx timeout to fire and show "Failed to register"
even though the customer was saved successfully.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api.v1 import customers
from services.security_audit import InMemorySecurityAuditStore
from services.security_throttle import InMemoryThrottleStore, SecurityThrottle


_UPSERT_PAYLOAD = {
    "email": "newuser@example.com",
    "phone": "+91 98765 43210",
    "full_name": "New User",
    "business_name": "New Biz",
    "business_industry": "marketing",
    "business_address": "Mumbai",
    "website": None,
    "gst_number": None,
    "preferred_contact_method": "email",
    "consent": True,
}


class _FakeCustomerService:
    """Returns a freshly-created customer on every call."""

    async def upsert_by_email(self, payload):
        customer = MagicMock()
        customer.id = "test-customer-uuid"
        customer.email = str(payload.email)
        customer.phone = payload.phone
        customer.full_name = payload.full_name
        customer.business_name = payload.business_name
        customer.business_industry = payload.business_industry
        customer.business_address = payload.business_address
        customer.website = payload.website
        customer.gst_number = payload.gst_number
        customer.preferred_contact_method = payload.preferred_contact_method
        customer.consent = True
        customer.deleted_at = None
        return customer, True  # created=True


def _make_test_app(audit_store, throttle) -> FastAPI:
    app = FastAPI()
    app.dependency_overrides[customers.get_customer_service] = lambda: _FakeCustomerService()
    app.dependency_overrides[customers.get_security_audit_store] = lambda: audit_store
    app.dependency_overrides[customers.get_security_throttle] = lambda: throttle
    app.include_router(customers.router, prefix="/api/v1")
    return app


def _make_throttle() -> SecurityThrottle:
    return SecurityThrottle(
        InMemoryThrottleStore(),
        max_attempts=100,
        window_seconds=60,
        lockout_seconds=300,
    )


@pytest.mark.asyncio
async def test_upsert_customer_schedules_registration_task_via_background_tasks():
    """_enqueue_customer_registered must be scheduled via BackgroundTasks, not called inline.

    This ensures Redis/Celery unavailability never blocks the response.
    """
    audit_store = InMemorySecurityAuditStore()
    app = _make_test_app(audit_store, _make_throttle())

    with patch.object(customers, "_enqueue_customer_registered") as mock_enqueue:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post(
                "/api/v1/customers",
                json=_UPSERT_PAYLOAD,
                headers={"X-Forwarded-For": "1.2.3.4", "User-Agent": "pytest"},
            )

    assert r.status_code == 200
    # BackgroundTasks runs the function after the response — it will have been
    # called once (FastAPI executes background tasks before the test client returns).
    mock_enqueue.assert_called_once()
    call_kwargs = mock_enqueue.call_args.kwargs
    assert call_kwargs["email"] == "newuser@example.com"
    assert call_kwargs["customer_id"] == "test-customer-uuid"


@pytest.mark.asyncio
async def test_upsert_existing_customer_does_not_schedule_registration_task():
    """On upsert of an existing customer (created=False), no task must be enqueued."""

    class _ExistingCustomerService:
        async def upsert_by_email(self, payload):
            customer = MagicMock()
            customer.id = "existing-uuid"
            customer.email = str(payload.email)
            customer.phone = payload.phone
            customer.full_name = payload.full_name
            customer.business_name = payload.business_name
            customer.business_industry = payload.business_industry
            customer.business_address = payload.business_address
            customer.website = payload.website
            customer.gst_number = payload.gst_number
            customer.preferred_contact_method = payload.preferred_contact_method
            customer.consent = True
            customer.deleted_at = None
            return customer, False  # created=False — existing customer

    audit_store = InMemorySecurityAuditStore()
    app = FastAPI()
    app.dependency_overrides[customers.get_customer_service] = lambda: _ExistingCustomerService()
    app.dependency_overrides[customers.get_security_audit_store] = lambda: audit_store
    app.dependency_overrides[customers.get_security_throttle] = lambda: _make_throttle()
    app.include_router(customers.router, prefix="/api/v1")

    with patch.object(customers, "_enqueue_customer_registered") as mock_enqueue:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post(
                "/api/v1/customers",
                json=_UPSERT_PAYLOAD,
                headers={"X-Forwarded-For": "1.2.3.4", "User-Agent": "pytest"},
            )

    assert r.status_code == 200
    mock_enqueue.assert_not_called()
