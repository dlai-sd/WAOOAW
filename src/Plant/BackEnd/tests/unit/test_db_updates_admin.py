from __future__ import annotations

import pytest
import httpx


@pytest.mark.asyncio
async def test_db_updates_undefined_table_returns_400_with_hint(monkeypatch):
    from fastapi import FastAPI

    from api.v1 import db_updates

    # Enable the feature gate.
    monkeypatch.setattr(db_updates.settings, "environment", "development", raising=False)
    monkeypatch.setattr(db_updates.settings, "enable_db_updates", True, raising=False)

    # Bypass token verification and role checks.
    def _ok_verify_token(_: str):
        return {"roles": ["admin"]}

    monkeypatch.setattr(db_updates, "verify_token", _ok_verify_token)

    # Fake session that raises a ProgrammingError with an UndefinedTable-like message.
    from sqlalchemy.exc import ProgrammingError

    class _Begin:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class _FakeSession:
        def begin(self):
            return _Begin()

        async def execute(self, statement):
            # statement is a SQLAlchemy TextClause; stringify it for matching.
            sql = str(statement)
            if "SET LOCAL statement_timeout" in sql:
                return None
            raise ProgrammingError("SELECT * FROM agents", {}, Exception('relation "agents" does not exist'))

    async def _fake_get_db_session():
        yield _FakeSession()

    app = FastAPI()
    app.include_router(db_updates.router, prefix="/api/v1")
    app.dependency_overrides[db_updates.get_db_session] = _fake_get_db_session

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/admin/db/execute",
            headers={
                "X-Gateway": "plant-gateway",
                "Authorization": "Bearer test",
            },
            json={"sql": "SELECT * FROM agents", "confirm": True},
        )

    assert resp.status_code == 400
    body = resp.json()
    assert body["detail"]["error"] == "sql_error"
    assert "does not exist" in body["detail"]["message"]
    assert "agent_entity" in body["detail"].get("hint", "")
