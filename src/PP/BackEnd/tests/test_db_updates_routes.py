from __future__ import annotations

import time

import jwt

from core.config import settings


def _mint_admin_token() -> str:
    now = int(time.time())
    payload = {
        "sub": "test-admin",
        "iat": now,
        "exp": now + 60,
        "iss": settings.JWT_ISSUER,
        "roles": ["admin"],
        "email": "admin@waooaw.com",
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def _mint_non_admin_token() -> str:
    now = int(time.time())
    payload = {
        "sub": "test-user",
        "iat": now,
        "exp": now + 60,
        "iss": settings.JWT_ISSUER,
        "roles": ["viewer"],
        "email": "viewer@waooaw.com",
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def _mint_expired_admin_token() -> str:
    now = int(time.time())
    payload = {
        "sub": "test-admin",
        "iat": now - 120,
        "exp": now - 60,
        "iss": settings.JWT_ISSUER,
        "roles": ["admin"],
        "email": "admin@waooaw.com",
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def _mint_scoped_admin_token(scope: str) -> str:
    now = int(time.time())
    payload = {
        "sub": "test-admin",
        "iat": now,
        "exp": now + 60,
        "iss": settings.JWT_ISSUER,
        "roles": ["admin"],
        "email": "admin@waooaw.com",
        "scope": scope,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


async def test_db_connection_info_redacts_password(client, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development", raising=False)
    monkeypatch.setattr(settings, "ENABLE_DB_UPDATES", True, raising=False)
    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret", raising=False)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256", raising=False)
    monkeypatch.setattr(settings, "JWT_ISSUER", "waooaw.com", raising=False)
    monkeypatch.setattr(settings, "PLANT_GATEWAY_URL", "http://plant-gateway:8000", raising=False)

    class _Resp:
        status_code = 200

        def json(self):
            return {
                "environment": "development",
                "database_url": "postgresql+asyncpg://waooaw:***@postgres:5432/waooaw_db",
            }

        text = ""

    async def _mock_get(self, url, headers=None, **kwargs):
        assert url.endswith("/api/v1/admin/db/connection-info")
        assert (headers or {}).get("Authorization", "").startswith("Bearer ")
        return _Resp()

    class _MockAsyncClient:
        def __init__(self, *args, **kwargs):
            _ = args
            _ = kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            _ = exc_type
            _ = exc
            _ = tb
            return False

        async def get(self, url, headers=None, **kwargs):
            return await _mock_get(self, url, headers=headers, **kwargs)

    monkeypatch.setattr("api.db_updates.httpx.AsyncClient", _MockAsyncClient)

    token = _mint_admin_token()
    resp = await client.get(
        "/api/pp/db/connection-info",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["environment"] == "development"
    assert "***" in body["database_url"]
    assert "waooaw_dev_password" not in body["database_url"]


async def test_db_connection_info_accepts_db_updates_scoped_token(client, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development", raising=False)
    monkeypatch.setattr(settings, "ENABLE_DB_UPDATES", True, raising=False)
    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret", raising=False)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256", raising=False)
    monkeypatch.setattr(settings, "JWT_ISSUER", "waooaw.com", raising=False)
    monkeypatch.setattr(settings, "DB_UPDATES_TOKEN_SCOPE", "db_updates", raising=False)
    monkeypatch.setattr(settings, "PLANT_GATEWAY_URL", "http://plant-gateway:8000", raising=False)

    class _Resp:
        status_code = 200

        def json(self):
            return {
                "environment": "development",
                "database_url": "postgresql+asyncpg://waooaw:***@postgres:5432/waooaw_db",
            }

        text = ""

    async def _mock_get(self, url, headers=None, **kwargs):
        assert url.endswith("/api/v1/admin/db/connection-info")
        assert (headers or {}).get("Authorization", "").startswith("Bearer ")
        return _Resp()

    class _MockAsyncClient:
        def __init__(self, *args, **kwargs):
            _ = args
            _ = kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            _ = exc_type
            _ = exc
            _ = tb
            return False

        async def get(self, url, headers=None, **kwargs):
            return await _mock_get(self, url, headers=headers, **kwargs)

    monkeypatch.setattr("api.db_updates.httpx.AsyncClient", _MockAsyncClient)

    token = _mint_scoped_admin_token("db_updates")
    resp = await client.get(
        "/api/pp/db/connection-info",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200


async def test_db_connection_info_rejects_wrong_scope(client, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development", raising=False)
    monkeypatch.setattr(settings, "ENABLE_DB_UPDATES", True, raising=False)
    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret", raising=False)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256", raising=False)
    monkeypatch.setattr(settings, "JWT_ISSUER", "waooaw.com", raising=False)
    monkeypatch.setattr(settings, "DB_UPDATES_TOKEN_SCOPE", "db_updates", raising=False)

    token = _mint_scoped_admin_token("other")
    resp = await client.get(
        "/api/pp/db/connection-info",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


async def test_db_connection_info_requires_token(client, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development", raising=False)
    monkeypatch.setattr(settings, "ENABLE_DB_UPDATES", True, raising=False)
    resp = await client.get("/api/pp/db/connection-info")
    assert resp.status_code == 401


async def test_db_connection_info_requires_admin_role(client, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development", raising=False)
    monkeypatch.setattr(settings, "ENABLE_DB_UPDATES", True, raising=False)
    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret", raising=False)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256", raising=False)
    monkeypatch.setattr(settings, "JWT_ISSUER", "waooaw.com", raising=False)

    token = _mint_non_admin_token()
    resp = await client.get(
        "/api/pp/db/connection-info",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


async def test_db_connection_info_rejects_bad_auth_scheme(client, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development", raising=False)
    monkeypatch.setattr(settings, "ENABLE_DB_UPDATES", True, raising=False)
    resp = await client.get(
        "/api/pp/db/connection-info",
        headers={"Authorization": "Token not-a-bearer"},
    )
    assert resp.status_code == 401


async def test_db_connection_info_rejects_expired_token(client, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development", raising=False)
    monkeypatch.setattr(settings, "ENABLE_DB_UPDATES", True, raising=False)
    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret", raising=False)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256", raising=False)
    monkeypatch.setattr(settings, "JWT_ISSUER", "waooaw.com", raising=False)

    token = _mint_expired_admin_token()
    resp = await client.get(
        "/api/pp/db/connection-info",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 401


async def test_db_connection_info_rejects_invalid_token(client, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development", raising=False)
    monkeypatch.setattr(settings, "ENABLE_DB_UPDATES", True, raising=False)
    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret", raising=False)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256", raising=False)
    monkeypatch.setattr(settings, "JWT_ISSUER", "waooaw.com", raising=False)

    resp = await client.get(
        "/api/pp/db/connection-info",
        headers={"Authorization": "Bearer not-a-jwt"},
    )
    assert resp.status_code == 401


async def test_db_execute_requires_confirm(client, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development", raising=False)
    monkeypatch.setattr(settings, "ENABLE_DB_UPDATES", True, raising=False)
    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret", raising=False)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256", raising=False)
    monkeypatch.setattr(settings, "JWT_ISSUER", "waooaw.com", raising=False)

    token = _mint_admin_token()
    resp = await client.post(
        "/api/pp/db/execute",
        headers={"Authorization": f"Bearer {token}"},
        json={"sql": "SELECT 1", "confirm": False},
    )
    assert resp.status_code == 400


async def test_db_execute_select_smoke(client, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development", raising=False)
    monkeypatch.setattr(settings, "ENABLE_DB_UPDATES", True, raising=False)
    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret", raising=False)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256", raising=False)
    monkeypatch.setattr(settings, "JWT_ISSUER", "waooaw.com", raising=False)
    monkeypatch.setattr(settings, "PLANT_GATEWAY_URL", "http://plant-gateway:8000", raising=False)

    class _Resp:
        status_code = 200

        def json(self):
            return {
                "type": "select",
                "columns": ["?column?"],
                "rows": [[1]],
                "row_count": 1,
                "truncated": False,
            }

        text = ""

    async def _mock_post(self, url, headers=None, json=None, **kwargs):
        assert url.endswith("/api/v1/admin/db/execute")
        assert (headers or {}).get("Authorization", "").startswith("Bearer ")
        assert json and json.get("confirm") is True
        return _Resp()

    class _MockAsyncClient:
        def __init__(self, *args, **kwargs):
            _ = args
            _ = kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            _ = exc_type
            _ = exc
            _ = tb
            return False

        async def post(self, url, headers=None, json=None, **kwargs):
            return await _mock_post(self, url, headers=headers, json=json, **kwargs)

    monkeypatch.setattr("api.db_updates.httpx.AsyncClient", _MockAsyncClient)

    token = _mint_admin_token()
    resp = await client.post(
        "/api/pp/db/execute",
        headers={"Authorization": f"Bearer {token}"},
        json={"sql": "SELECT 1", "confirm": True, "max_rows": 10},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["type"] == "select"
    assert isinstance(body["columns"], list)
    assert isinstance(body["rows"], list)


async def test_db_connection_info_missing_plant_base_url_returns_500(client, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development", raising=False)
    monkeypatch.setattr(settings, "ENABLE_DB_UPDATES", True, raising=False)
    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret", raising=False)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256", raising=False)
    monkeypatch.setattr(settings, "JWT_ISSUER", "waooaw.com", raising=False)
    monkeypatch.setattr(settings, "PLANT_GATEWAY_URL", "", raising=False)
    monkeypatch.setattr(settings, "PLANT_API_URL", "", raising=False)

    token = _mint_admin_token()
    resp = await client.get(
        "/api/pp/db/connection-info",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 500


async def test_db_execute_rejects_multiple_statements(client, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development", raising=False)
    monkeypatch.setattr(settings, "ENABLE_DB_UPDATES", True, raising=False)
    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret", raising=False)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256", raising=False)
    monkeypatch.setattr(settings, "JWT_ISSUER", "waooaw.com", raising=False)

    token = _mint_admin_token()
    resp = await client.post(
        "/api/pp/db/execute",
        headers={"Authorization": f"Bearer {token}"},
        json={"sql": "SELECT 1; SELECT 2", "confirm": True},
    )
    assert resp.status_code == 400


async def test_db_execute_upstream_error_uses_text_detail(client, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development", raising=False)
    monkeypatch.setattr(settings, "ENABLE_DB_UPDATES", True, raising=False)
    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret", raising=False)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256", raising=False)
    monkeypatch.setattr(settings, "JWT_ISSUER", "waooaw.com", raising=False)
    monkeypatch.setattr(settings, "PLANT_GATEWAY_URL", "http://plant-gateway:8000", raising=False)

    class _Resp:
        status_code = 503
        text = "gateway unavailable"

        def json(self):
            raise ValueError("not json")

    async def _mock_post(self, url, headers=None, json=None, **kwargs):
        assert url.endswith("/api/v1/admin/db/execute")
        return _Resp()

    class _MockAsyncClient:
        def __init__(self, *args, **kwargs):
            _ = args
            _ = kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            _ = exc_type
            _ = exc
            _ = tb
            return False

        async def post(self, url, headers=None, json=None, **kwargs):
            return await _mock_post(self, url, headers=headers, json=json, **kwargs)

    monkeypatch.setattr("api.db_updates.httpx.AsyncClient", _MockAsyncClient)

    token = _mint_admin_token()
    resp = await client.post(
        "/api/pp/db/execute",
        headers={"Authorization": f"Bearer {token}"},
        json={"sql": "SELECT 1", "confirm": True},
    )
    assert resp.status_code == 503
    assert resp.json()["detail"] == "gateway unavailable"

