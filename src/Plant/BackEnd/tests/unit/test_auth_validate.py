import uuid

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api.v1 import auth
from middleware.rate_limit import InMemoryRateLimitStore
from services.security_audit import InMemorySecurityAuditStore


class _FakeCustomer:
    def __init__(self, email: str):
        self.id = uuid.uuid4()
        self.email = email


class _FakeCustomerService:
    async def get_by_email(self, email: str):
        return _FakeCustomer(email)


class _MissingCustomerService:
    async def get_by_email(self, email: str):
        return None


class _PolymorphicMismatchCustomerService:
    async def get_by_email(self, email: str):
        raise AssertionError("No such polymorphic_identity 'NotCustomer' is defined")


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


@pytest.mark.asyncio
async def test_auth_validate_expired_token(monkeypatch):
    audit_store = InMemorySecurityAuditStore()
    app = _make_test_app(audit_store)

    from core.exceptions import JWTTokenExpiredError

    def mock_verify_token(token):
        raise JWTTokenExpiredError(expired_at="2026-01-01T00:00:00")

    monkeypatch.setattr(auth, "verify_token", mock_verify_token)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get(
            "/api/v1/auth/validate",
            headers={"Authorization": "Bearer expired"},
        )

    assert r.status_code == 401
    events = audit_store.list_records(event_type="auth_validate", limit=10)
    assert any(e.success is False and (e.detail or "").lower().find("expired") >= 0 for e in events)


@pytest.mark.asyncio
async def test_auth_validate_invalid_signature(monkeypatch):
    audit_store = InMemorySecurityAuditStore()
    app = _make_test_app(audit_store)

    from core.exceptions import JWTInvalidSignatureError

    def mock_verify_token(token):
        raise JWTInvalidSignatureError()

    monkeypatch.setattr(auth, "verify_token", mock_verify_token)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get(
            "/api/v1/auth/validate",
            headers={"Authorization": "Bearer badsig"},
        )

    assert r.status_code == 401
    events = audit_store.list_records(event_type="auth_validate", limit=10)
    assert any(e.success is False and (e.detail or "").lower().find("signature") >= 0 for e in events)


@pytest.mark.asyncio
async def test_auth_validate_wrong_token_type(monkeypatch):
    audit_store = InMemorySecurityAuditStore()
    app = _make_test_app(audit_store)

    monkeypatch.setattr(auth, "verify_token", lambda token: {"email": "user@example.com", "token_type": "refresh"})

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get(
            "/api/v1/auth/validate",
            headers={"Authorization": "Bearer refresh"},
        )

    assert r.status_code == 401


@pytest.mark.asyncio
async def test_auth_validate_missing_email_claim(monkeypatch):
    audit_store = InMemorySecurityAuditStore()
    app = _make_test_app(audit_store)

    monkeypatch.setattr(auth, "verify_token", lambda token: {"token_type": "access"})

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get(
            "/api/v1/auth/validate",
            headers={"Authorization": "Bearer noemail"},
        )

    assert r.status_code == 401


@pytest.mark.asyncio
async def test_auth_validate_customer_not_found(monkeypatch):
    audit_store = InMemorySecurityAuditStore()
    app = FastAPI()
    app.dependency_overrides[auth.get_customer_service] = lambda: _MissingCustomerService()
    app.dependency_overrides[auth.get_security_audit_store] = lambda: audit_store
    app.include_router(auth.router, prefix="/api/v1")

    monkeypatch.setattr(auth, "verify_token", lambda token: {"email": "user@example.com", "token_type": "access"})

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get(
            "/api/v1/auth/validate",
            headers={"Authorization": "Bearer test"},
        )

    assert r.status_code == 404


@pytest.mark.asyncio
async def test_auth_validate_polymorphic_identity_mismatch(monkeypatch):
    audit_store = InMemorySecurityAuditStore()
    app = FastAPI()
    app.dependency_overrides[auth.get_customer_service] = lambda: _PolymorphicMismatchCustomerService()
    app.dependency_overrides[auth.get_security_audit_store] = lambda: audit_store
    app.include_router(auth.router, prefix="/api/v1")

    monkeypatch.setattr(auth, "verify_token", lambda token: {"email": "user@example.com", "token_type": "access"})

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get(
            "/api/v1/auth/validate",
            headers={"Authorization": "Bearer test"},
        )

    assert r.status_code == 500



@pytest.mark.asyncio
async def test_auth_token_issue_success(monkeypatch):
    audit_store = InMemorySecurityAuditStore()
    app = _make_test_app(audit_store)

    monkeypatch.setenv("PLANT_OAUTH_CLIENT_ID", "test-client")
    monkeypatch.setenv("PLANT_OAUTH_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("AUTH_TOKEN_RATE_LIMIT_PER_MINUTE", "100")
    monkeypatch.setattr(auth, "_AUTH_TOKEN_RATE_STORE", InMemoryRateLimitStore())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/auth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": "test-client",
                "client_secret": "test-secret",
                "tenant_id": "tenant-123",
                "customer_email": "user@example.com",
            },
        )

    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 3600
    assert isinstance(body["access_token"], str) and body["access_token"]
    assert isinstance(body["refresh_token"], str) and body["refresh_token"]

    access_claims = auth.verify_token(body["access_token"])
    assert access_claims["tenant_id"] == "tenant-123"
    assert access_claims["user_id"]
    assert access_claims["token_type"] == "access"

    refresh_claims = auth.verify_token(body["refresh_token"])
    assert refresh_claims["tenant_id"] == "tenant-123"
    assert refresh_claims["user_id"]
    assert refresh_claims["token_type"] == "refresh"

    events = audit_store.list_records(event_type="auth_token_issue", limit=10)
    assert any(e.success is True for e in events)


@pytest.mark.asyncio
async def test_auth_token_issue_success_via_clients_json(monkeypatch):
    audit_store = InMemorySecurityAuditStore()
    app = _make_test_app(audit_store)

    monkeypatch.setenv("PLANT_OAUTH_CLIENTS_JSON", '{"json-client": "json-secret"}')
    monkeypatch.setattr(auth, "_AUTH_TOKEN_RATE_STORE", InMemoryRateLimitStore())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/auth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": "json-client",
                "client_secret": "json-secret",
                "tenant_id": "tenant-123",
                "customer_email": "user@example.com",
            },
        )

    assert r.status_code == 200


@pytest.mark.asyncio
async def test_auth_token_issue_unsupported_grant(monkeypatch):
    audit_store = InMemorySecurityAuditStore()
    app = _make_test_app(audit_store)

    monkeypatch.setenv("PLANT_OAUTH_CLIENT_ID", "test-client")
    monkeypatch.setenv("PLANT_OAUTH_CLIENT_SECRET", "test-secret")
    monkeypatch.setattr(auth, "_AUTH_TOKEN_RATE_STORE", InMemoryRateLimitStore())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/auth/token",
            data={
                "grant_type": "password",
                "client_id": "test-client",
                "client_secret": "test-secret",
                "tenant_id": "tenant-123",
                "customer_email": "user@example.com",
            },
        )

    assert r.status_code == 400


@pytest.mark.asyncio
async def test_auth_token_issue_tenant_id_email_fallback(monkeypatch):
    audit_store = InMemorySecurityAuditStore()
    app = _make_test_app(audit_store)

    monkeypatch.setenv("PLANT_OAUTH_CLIENT_ID", "test-client")
    monkeypatch.setenv("PLANT_OAUTH_CLIENT_SECRET", "test-secret")
    monkeypatch.setattr(auth, "_AUTH_TOKEN_RATE_STORE", InMemoryRateLimitStore())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/auth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": "test-client",
                "client_secret": "test-secret",
                "tenant_id": "tenantuser@example.com",
            },
        )

    assert r.status_code == 200


@pytest.mark.asyncio
async def test_auth_token_issue_invalid_client_credentials(monkeypatch):
    audit_store = InMemorySecurityAuditStore()
    app = _make_test_app(audit_store)

    monkeypatch.setenv("PLANT_OAUTH_CLIENT_ID", "test-client")
    monkeypatch.setenv("PLANT_OAUTH_CLIENT_SECRET", "test-secret")
    monkeypatch.setattr(auth, "_AUTH_TOKEN_RATE_STORE", InMemoryRateLimitStore())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/auth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": "test-client",
                "client_secret": "wrong",
                "tenant_id": "tenant-123",
                "customer_email": "user@example.com",
            },
        )

    assert r.status_code == 401


@pytest.mark.asyncio
async def test_auth_token_issue_rate_limited(monkeypatch):
    audit_store = InMemorySecurityAuditStore()
    app = _make_test_app(audit_store)

    monkeypatch.setenv("PLANT_OAUTH_CLIENT_ID", "test-client")
    monkeypatch.setenv("PLANT_OAUTH_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("AUTH_TOKEN_RATE_LIMIT_PER_MINUTE", "2")
    monkeypatch.setattr(auth, "_AUTH_TOKEN_RATE_STORE", InMemoryRateLimitStore())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for i in range(2):
            r = await client.post(
                "/api/v1/auth/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": "test-client",
                    "client_secret": "test-secret",
                    "tenant_id": "tenant-rl",
                    "customer_email": f"user{i}@example.com",
                },
            )
            assert r.status_code == 200

        r3 = await client.post(
            "/api/v1/auth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": "test-client",
                "client_secret": "test-secret",
                "tenant_id": "tenant-rl",
                "customer_email": "user2@example.com",
            },
        )

    assert r3.status_code == 429
    assert "Retry-After" in r3.headers


@pytest.mark.asyncio
async def test_auth_token_refresh_success(monkeypatch):
    audit_store = InMemorySecurityAuditStore()
    app = _make_test_app(audit_store)

    monkeypatch.setenv("PLANT_OAUTH_CLIENT_ID", "test-client")
    monkeypatch.setenv("PLANT_OAUTH_CLIENT_SECRET", "test-secret")
    monkeypatch.setattr(auth, "_AUTH_TOKEN_RATE_STORE", InMemoryRateLimitStore())

    refresh = auth.create_access_token(
        {
            "email": "user@example.com",
            "customer_id": "cust-1",
            "tenant_id": "tenant-123",
            "user_id": "cust-1",
            "token_type": "refresh",
        },
        expires_delta=auth.timedelta(days=1),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/auth/token/refresh",
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh,
                "tenant_id": "tenant-123",
                "client_id": "test-client",
                "client_secret": "test-secret",
            },
        )

    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 3600
    assert isinstance(body["access_token"], str) and body["access_token"]
    assert body.get("refresh_token") is None

    claims = auth.verify_token(body["access_token"])
    assert claims["tenant_id"] == "tenant-123"
    assert claims["token_type"] == "access"
    assert claims["user_id"]

    events = audit_store.list_records(event_type="auth_token_refresh", limit=10)
    assert any(e.success is True for e in events)


@pytest.mark.asyncio
async def test_auth_token_refresh_wrong_token_type(monkeypatch):
    audit_store = InMemorySecurityAuditStore()
    app = _make_test_app(audit_store)

    monkeypatch.setenv("PLANT_OAUTH_CLIENT_ID", "test-client")
    monkeypatch.setenv("PLANT_OAUTH_CLIENT_SECRET", "test-secret")
    monkeypatch.setattr(auth, "_AUTH_TOKEN_RATE_STORE", InMemoryRateLimitStore())

    not_refresh = auth.create_access_token(
        {"email": "user@example.com", "customer_id": "cust-1", "tenant_id": "tenant-123", "token_type": "access"},
        expires_delta=auth.timedelta(days=1),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/auth/token/refresh",
            data={
                "grant_type": "refresh_token",
                "refresh_token": not_refresh,
                "tenant_id": "tenant-123",
                "client_id": "test-client",
                "client_secret": "test-secret",
            },
        )

    assert r.status_code == 401


@pytest.mark.asyncio
async def test_auth_token_refresh_tenant_mismatch(monkeypatch):
    audit_store = InMemorySecurityAuditStore()
    app = _make_test_app(audit_store)

    monkeypatch.setenv("PLANT_OAUTH_CLIENT_ID", "test-client")
    monkeypatch.setenv("PLANT_OAUTH_CLIENT_SECRET", "test-secret")
    monkeypatch.setattr(auth, "_AUTH_TOKEN_RATE_STORE", InMemoryRateLimitStore())

    refresh = auth.create_access_token(
        {"email": "user@example.com", "customer_id": "cust-1", "tenant_id": "tenant-A", "token_type": "refresh"},
        expires_delta=auth.timedelta(days=1),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/auth/token/refresh",
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh,
                "tenant_id": "tenant-B",
                "client_id": "test-client",
                "client_secret": "test-secret",
            },
        )

    assert r.status_code == 403


@pytest.mark.asyncio
async def test_auth_token_refresh_invalid_token_audited(monkeypatch):
    audit_store = InMemorySecurityAuditStore()
    app = _make_test_app(audit_store)

    monkeypatch.setenv("PLANT_OAUTH_CLIENT_ID", "test-client")
    monkeypatch.setenv("PLANT_OAUTH_CLIENT_SECRET", "test-secret")
    monkeypatch.setattr(auth, "_AUTH_TOKEN_RATE_STORE", InMemoryRateLimitStore())

    from core.exceptions import JWTInvalidTokenError

    def mock_verify_token(token):
        raise JWTInvalidTokenError(reason="bad")

    monkeypatch.setattr(auth, "verify_token", mock_verify_token)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/auth/token/refresh",
            data={
                "grant_type": "refresh_token",
                "refresh_token": "not-a-jwt",
                "tenant_id": "tenant-123",
                "client_id": "test-client",
                "client_secret": "test-secret",
            },
        )

    assert r.status_code == 401
    events = audit_store.list_records(event_type="auth_token_refresh", limit=10)
    assert any(e.success is False for e in events)

