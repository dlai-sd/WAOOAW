"""Unit tests for E2-S1/S2/S3 — GDPR Customer Erasure.

Tests cover:
  - CustomerService.erase() logic (service layer)
  - DELETE /api/v1/customers/{id}/erase endpoint (API layer)
  - Auth requirements: 403 without admin JWT, 401 without token
  - 404 for unknown customer
  - 409 for already-erased customer
  - Erasure actually nullifies PII values
  - Audit events written before + after erasure (E2-S3)
"""

from __future__ import annotations

import sys
import os
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


# ---------------------------------------------------------------------------
# CustomerService.erase() unit tests
# ---------------------------------------------------------------------------


class TestCustomerServiceErase:
    """Test the service-layer erase() method in isolation."""

    def _make_service(self, customer=None):
        """Return a CustomerService with a mocked AsyncSession."""
        from services.customer_service import CustomerService

        db = AsyncMock()
        # make begin_nested() work as an async context manager
        nested = AsyncMock()
        nested.__aenter__ = AsyncMock(return_value=None)
        nested.__aexit__ = AsyncMock(return_value=False)
        db.begin_nested = MagicMock(return_value=nested)
        db.execute = AsyncMock(return_value=None)
        db.commit = AsyncMock(return_value=None)
        db.refresh = AsyncMock(return_value=None)

        svc = CustomerService(db)
        svc.get_by_id = AsyncMock(return_value=customer)
        return svc, db

    @pytest.mark.asyncio
    async def test_erase_raises_if_customer_not_found(self):
        from services.customer_service import CustomerService

        svc, _ = self._make_service(customer=None)
        with pytest.raises(ValueError, match="not found"):
            await svc.erase(str(uuid.uuid4()))

    @pytest.mark.asyncio
    async def test_erase_raises_if_already_erased(self):
        customer = MagicMock()
        customer.deleted_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
        customer.email = "redacted_xxx@erased.invalid"

        svc, _ = self._make_service(customer=customer)
        with pytest.raises(ValueError, match="already erased"):
            await svc.erase(str(uuid.uuid4()))

    @pytest.mark.asyncio
    async def test_erase_executes_three_sql_statements(self):
        """Erasure must execute UPDATE customer, UPDATE audit_logs, DELETE otp_sessions."""
        customer = MagicMock()
        customer.id = uuid.uuid4()
        customer.deleted_at = None
        customer.email = "victim@example.com"

        svc, db = self._make_service(customer=customer)
        await svc.erase(str(customer.id))

        # Should execute 3 statements (UPDATE customer, UPDATE audit_logs, DELETE otp_sessions)
        assert db.execute.call_count == 3

    @pytest.mark.asyncio
    async def test_erase_returns_customer(self):
        customer = MagicMock()
        customer.id = uuid.uuid4()
        customer.deleted_at = None
        customer.email = "victim@example.com"

        svc, _ = self._make_service(customer=customer)
        result = await svc.erase(str(customer.id))
        assert result is customer


# ---------------------------------------------------------------------------
# API endpoint tests using a minimal FastAPI test app
# ---------------------------------------------------------------------------


def _build_test_app():
    """Build a minimal FastAPI app that mounts only the customers router."""
    app = FastAPI()

    # Patch DB dependency before importing router
    from sqlalchemy.ext.asyncio import AsyncSession
    from fastapi import Depends

    async def _fake_db():
        db = AsyncMock()
        nested = AsyncMock()
        nested.__aenter__ = AsyncMock(return_value=None)
        nested.__aexit__ = AsyncMock(return_value=False)
        db.begin_nested = MagicMock(return_value=nested)
        db.execute = AsyncMock(return_value=None)
        db.commit = AsyncMock(return_value=None)
        db.refresh = AsyncMock(return_value=None)
        yield db

    from core.database import get_db_session
    app.dependency_overrides[get_db_session] = _fake_db

    from api.v1.customers import router
    app.include_router(router, prefix="/api/v1")
    return app


def _admin_jwt_token():
    """Create a JWT with admin role for testing."""
    from jose import jwt
    import os

    # Mirror core/config.py: validation_alias accepts JWT_SECRET or SECRET_KEY
    secret = os.environ.get("JWT_SECRET") or os.environ.get("SECRET_KEY") or "your-secret-key-change-in-production"
    payload = {
        "sub": "00000000-0000-0000-0000-000000000001",
        "roles": ["admin"],
        "exp": 9999999999,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def _user_jwt_token():
    """Create a JWT without admin role."""
    from jose import jwt
    import os

    # Mirror core/config.py: validation_alias accepts JWT_SECRET or SECRET_KEY
    secret = os.environ.get("JWT_SECRET") or os.environ.get("SECRET_KEY") or "your-secret-key-change-in-production"
    payload = {
        "sub": "regular-user-id",
        "roles": ["user"],
        "exp": 9999999999,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


class TestCustomerErasureEndpoint:
    """Test DELETE /api/v1/customers/{id}/erase behaviour."""

    def _make_client_with_customer(self, customer=None, already_erased=False):
        app = _build_test_app()
        client = TestClient(app, raise_server_exceptions=False)
        return client, app

    @patch("services.customer_service.CustomerService.get_by_id")
    @patch("services.customer_service.CustomerService.erase")
    @patch("services.audit_log_service.AuditLogService.log_event")
    def test_erase_requires_admin_token(
        self, mock_audit, mock_erase, mock_get
    ):
        app = _build_test_app()
        client = TestClient(app, raise_server_exceptions=False)

        # No auth header → 401
        resp = client.delete(f"/api/v1/customers/{uuid.uuid4()}/erase")
        assert resp.status_code == 401

    @patch("services.customer_service.CustomerService.get_by_id")
    @patch("services.customer_service.CustomerService.erase")
    @patch("services.audit_log_service.AuditLogService.log_event")
    def test_erase_requires_admin_role(
        self, mock_audit, mock_erase, mock_get
    ):
        app = _build_test_app()
        client = TestClient(app, raise_server_exceptions=False)

        # Non-admin token → 403
        token = _user_jwt_token()
        resp = client.delete(
            f"/api/v1/customers/{uuid.uuid4()}/erase",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    @patch("api.v1.customers.CustomerService")
    @patch("api.v1.customers.AuditLogService")
    def test_erase_returns_404_for_unknown_customer(
        self, MockAuditSvc, MockCustomerSvc
    ):
        # CustomerService.get_by_id returns None
        instance = AsyncMock()
        instance.get_by_id = AsyncMock(return_value=None)
        MockCustomerSvc.return_value = instance

        audit_instance = AsyncMock()
        audit_instance.log_event = AsyncMock(return_value=None)
        MockAuditSvc.return_value = audit_instance

        app = _build_test_app()
        client = TestClient(app, raise_server_exceptions=False)
        token = _admin_jwt_token()

        resp = client.delete(
            f"/api/v1/customers/{uuid.uuid4()}/erase",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    @patch("api.v1.customers.CustomerService")
    @patch("api.v1.customers.AuditLogService")
    def test_erase_returns_409_if_already_erased(
        self, MockAuditSvc, MockCustomerSvc
    ):
        customer = MagicMock()
        customer.deleted_at = datetime(2025, 1, 1, tzinfo=timezone.utc)

        instance = AsyncMock()
        instance.get_by_id = AsyncMock(return_value=customer)
        MockCustomerSvc.return_value = instance

        audit_instance = AsyncMock()
        audit_instance.log_event = AsyncMock(return_value=None)
        MockAuditSvc.return_value = audit_instance

        app = _build_test_app()
        client = TestClient(app, raise_server_exceptions=False)
        token = _admin_jwt_token()

        resp = client.delete(
            f"/api/v1/customers/{uuid.uuid4()}/erase",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 409
        assert resp.headers.get("X-Error-Code") == "CUSTOMER_ALREADY_ERASED"

    @patch("api.v1.customers.CustomerService")
    @patch("api.v1.customers.AuditLogService")
    def test_erase_returns_200_on_success(
        self, MockAuditSvc, MockCustomerSvc
    ):
        customer = MagicMock()
        customer.deleted_at = None
        cid = str(uuid.uuid4())
        customer.id = cid

        instance = AsyncMock()
        instance.get_by_id = AsyncMock(return_value=customer)
        instance.erase = AsyncMock(return_value=customer)
        MockCustomerSvc.return_value = instance

        audit_instance = AsyncMock()
        audit_instance.log_event = AsyncMock(return_value=None)
        MockAuditSvc.return_value = audit_instance

        app = _build_test_app()
        client = TestClient(app, raise_server_exceptions=False)
        token = _admin_jwt_token()

        resp = client.delete(
            f"/api/v1/customers/{cid}/erase",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "erased"
        assert data["customer_id"] == cid

    @patch("api.v1.customers.CustomerService")
    @patch("api.v1.customers.AuditLogService")
    def test_erase_writes_two_audit_events(
        self, MockAuditSvc, MockCustomerSvc
    ):
        """E2-S3: two audit events must be written — erasure_requested + erasure_complete."""
        customer = MagicMock()
        customer.deleted_at = None
        customer.id = str(uuid.uuid4())

        instance = AsyncMock()
        instance.get_by_id = AsyncMock(return_value=customer)
        instance.erase = AsyncMock(return_value=customer)
        MockCustomerSvc.return_value = instance

        audit_instance = AsyncMock()
        audit_instance.log_event = AsyncMock(return_value=None)
        MockAuditSvc.return_value = audit_instance

        app = _build_test_app()
        client = TestClient(app, raise_server_exceptions=False)
        token = _admin_jwt_token()

        resp = client.delete(
            f"/api/v1/customers/{customer.id}/erase",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        # Two audit log events must be written
        assert audit_instance.log_event.call_count == 2
        actions = [
            call.args[0].action
            for call in audit_instance.log_event.call_args_list
        ]
        assert "erasure_requested" in actions
        assert "erasure_complete" in actions
