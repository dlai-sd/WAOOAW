import uuid

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api.v1 import auth
from services.security_audit import InMemorySecurityAuditStore


class _FakeCustomer:
    def __init__(self, email: str):
        self.id = uuid.uuid4()
        self.email = email


class _FakeCustomerService:
    async def get_by_email(self, email: str):
        return _FakeCustomer(email)


def _make_test_app(audit_store: InMemorySecurityAuditStore) -> FastAPI:
    app = FastAPI()
    app.dependency_overrides[auth.get_customer_service] = lambda: _FakeCustomerService()
    app.dependency_overrides[auth.get_security_audit_store] = lambda: audit_store
    app.include_router(auth.router, prefix="/api/v1")
    return app


@pytest.mark.asyncio
async def test_auth_validate_success(monkeypatch):
    audit_store = InMemorySecurityAuditStore()
    app = _make_test_app(audit_store)

    monkeypatch.setattr(
        auth,
        "verify_token",
        lambda token: {"email": "USER@EXAMPLE.COM", "token_type": "access"},
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get(
            "/api/v1/auth/validate",
            headers={"Authorization": "Bearer test"},
        )

    assert r.status_code == 200
    body = r.json()
    assert body["valid"] is True
    assert body["email"] == "user@example.com"
    assert "customer_id" in body

    events = audit_store.list_records(event_type="auth_validate", limit=10)
    assert any(e.success is True for e in events)


@pytest.mark.asyncio
async def test_auth_validate_missing_token_audits_failure():
    audit_store = InMemorySecurityAuditStore()
    app = _make_test_app(audit_store)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/v1/auth/validate")

    assert r.status_code == 401
    events = audit_store.list_records(event_type="auth_validate", limit=10)
    assert any(e.success is False and (e.detail or "").lower().startswith("missing") for e in events)


@pytest.mark.asyncio
async def test_auth_validate_invalid_token_audits_failure(monkeypatch):
    audit_store = InMemorySecurityAuditStore()
    app = _make_test_app(audit_store)

    # Mock verify_token to raise JWTInvalidTokenError (new behavior)
    from core.exceptions import JWTInvalidTokenError
    def mock_verify_token(token):
        raise JWTInvalidTokenError(reason="Invalid token format")
    
    monkeypatch.setattr(auth, "verify_token", mock_verify_token)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get(
            "/api/v1/auth/validate",
            headers={"Authorization": "Bearer bad"},
        )

    assert r.status_code == 401
    events = audit_store.list_records(event_type="auth_validate", limit=10)
    assert any(e.success is False and (e.detail or "").lower().find("token") >= 0 for e in events)

