"""Unit tests for Platform Connections API.

PLANT-SKILLS-1 E4-S1

Covers:
- Router import + prefix/tags
- _to_response() omits secret_ref
- GET — empty list for unknown hired_instance_id
- POST — 201 created, secret_ref not in response
- POST — 409 on IntegrityError (duplicate)
- DELETE — 204 on success
- DELETE — 404 if connection not found
- PATCH /verify — sets status=connected, last_verified_at set
- PATCH /verify — 404 if not found
- All routes registered

Run:
    docker-compose -f docker-compose.test.yml run --rm \\
      --entrypoint "python -m pytest" plant-backend-test \\
      -q --no-cov tests/unit/test_platform_connections_api.py
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── Router import / structural ───────────────────────────────────────────────

def test_import_platform_connections_router():
    """Module must import without error and expose 'router'."""
    from api.v1.platform_connections import router
    assert router is not None


def test_router_prefix():
    from api.v1.platform_connections import router
    assert router.prefix == "/hired-agents"


def test_router_tags():
    from api.v1.platform_connections import router
    assert "platform-connections" in router.tags


def test_all_routes_registered():
    """GET, POST, DELETE, PATCH /verify must all be registered."""
    from api.v1.platform_connections import router

    routes = {(frozenset(r.methods), r.path) for r in router.routes}
    assert any("GET" in m and "platform-connections" in p and "verify" not in p for m, p in routes), \
        "GET list route not registered"
    assert any("POST" in m and "platform-connections" in p for m, p in routes), \
        "POST create route not registered"
    assert any("DELETE" in m and "platform-connections" in p for m, p in routes), \
        "DELETE route not registered"
    assert any("PATCH" in m and "verify" in p for m, p in routes), \
        "PATCH /verify route not registered"


# ── _to_response() — secret_ref exclusion ────────────────────────────────────

def _make_conn_model(**overrides):
    """Build a minimal PlatformConnectionModel-like MagicMock."""
    now = datetime.now(timezone.utc)
    conn = MagicMock()
    conn.id = str(uuid.uuid4())
    conn.hired_instance_id = str(uuid.uuid4())
    conn.skill_id = str(uuid.uuid4())
    conn.platform_key = "delta_exchange"
    conn.secret_ref = "projects/waooaw-oauth/secrets/test/versions/latest"
    conn.status = "pending"
    conn.connected_at = None
    conn.last_verified_at = None
    conn.created_at = now
    conn.updated_at = now
    for k, v in overrides.items():
        setattr(conn, k, v)
    return conn


def test_to_response_omits_secret_ref():
    """_to_response must never include secret_ref in the returned object."""
    from api.v1.platform_connections import _to_response
    conn = _make_conn_model()
    resp = _to_response(conn)
    resp_dict = resp.model_dump()
    assert "secret_ref" not in resp_dict, "secret_ref must NOT appear in API response"


def test_to_response_fields_present():
    from api.v1.platform_connections import _to_response
    conn = _make_conn_model(status="connected")
    resp = _to_response(conn)
    assert resp.status == "connected"
    assert resp.id == conn.id
    assert resp.platform_key == conn.platform_key


@pytest.mark.asyncio
async def test_get_connected_platform_connection_returns_only_connected_rows(mock_db):
    from api.v1.platform_connections import get_connected_platform_connection

    conn = _make_conn_model(status="connected", platform_key="youtube")
    result_mock = MagicMock()
    result_mock.scalars.return_value.first.return_value = conn
    mock_db.execute = AsyncMock(return_value=result_mock)

    found = await get_connected_platform_connection(
        mock_db,
        hired_instance_id=conn.hired_instance_id,
        skill_id=conn.skill_id,
        platform_key="youtube",
    )

    assert found is conn


# ── Endpoint logic (mocked DB) ───────────────────────────────────────────────

@pytest.fixture
def hired_id():
    return str(uuid.uuid4())


@pytest.fixture
def conn_id():
    return str(uuid.uuid4())


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.refresh = AsyncMock()
    db.delete = AsyncMock()
    return db


@pytest.mark.asyncio
async def test_list_connections_empty(hired_id, mock_db):
    """GET returns empty list for unknown hired_instance_id."""
    from api.v1.platform_connections import list_connections

    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = []
    mock_db.execute = AsyncMock(return_value=result_mock)

    resp = await list_connections(hired_id, db=mock_db)
    assert resp == []


@pytest.mark.asyncio
async def test_list_connections_returns_list(hired_id, mock_db):
    """GET returns list of ConnectionResponse objects."""
    from api.v1.platform_connections import list_connections

    conn = _make_conn_model(hired_instance_id=hired_id)
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = [conn]
    mock_db.execute = AsyncMock(return_value=result_mock)

    resp = await list_connections(hired_id, db=mock_db)
    assert len(resp) == 1
    resp_dict = resp[0].model_dump()
    assert "secret_ref" not in resp_dict


@pytest.mark.asyncio
async def test_create_connection_201(hired_id, mock_db):
    """POST returns 201 and never reveals secret_ref."""
    from api.v1.platform_connections import create_connection, CreateConnectionRequest

    conn = _make_conn_model(hired_instance_id=hired_id)

    async def mock_refresh(obj):
        for attr, val in conn.__dict__.items():
            if not attr.startswith("_"):
                setattr(obj, attr, val)

    mock_db.refresh = mock_refresh

    body = CreateConnectionRequest(
        skill_id=str(uuid.uuid4()),
        platform_key="facebook",
        secret_ref="projects/waooaw-oauth/secrets/test/versions/latest",
    )
    resp = await create_connection(hired_id, body, db=mock_db)
    resp_dict = resp.model_dump()
    assert "secret_ref" not in resp_dict


@pytest.mark.asyncio
async def test_create_connection_409_on_duplicate(hired_id, mock_db):
    """POST raises HTTP 409 when IntegrityError from DB."""
    from fastapi import HTTPException
    from sqlalchemy.exc import IntegrityError
    from api.v1.platform_connections import create_connection, CreateConnectionRequest

    mock_db.commit = AsyncMock(side_effect=IntegrityError("dup", None, None))

    body = CreateConnectionRequest(
        skill_id=str(uuid.uuid4()),
        platform_key="linkedin",
        secret_ref="projects/waooaw-oauth/secrets/test/versions/latest",
    )
    with pytest.raises(HTTPException) as exc:
        await create_connection(hired_id, body, db=mock_db)
    assert exc.value.status_code == 409
    mock_db.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_delete_connection_204(hired_id, conn_id, mock_db):
    """DELETE returns 204 when connection exists."""
    from api.v1.platform_connections import delete_connection

    conn = _make_conn_model(id=conn_id, hired_instance_id=hired_id)
    result_mock = MagicMock()
    result_mock.scalars.return_value.first.return_value = conn
    mock_db.execute = AsyncMock(return_value=result_mock)

    result = await delete_connection(hired_id, conn_id, db=mock_db)
    assert result is None  # 204 No Content
    mock_db.delete.assert_called_once_with(conn)
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_connection_404_not_found(hired_id, conn_id, mock_db):
    """DELETE raises HTTP 404 when connection not found."""
    from fastapi import HTTPException
    from api.v1.platform_connections import delete_connection

    result_mock = MagicMock()
    result_mock.scalars.return_value.first.return_value = None
    mock_db.execute = AsyncMock(return_value=result_mock)

    with pytest.raises(HTTPException) as exc:
        await delete_connection(hired_id, conn_id, db=mock_db)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_verify_connection_sets_status(hired_id, conn_id, mock_db):
    """PATCH /verify sets status='connected' and last_verified_at."""
    from api.v1.platform_connections import verify_connection

    conn = _make_conn_model(id=conn_id, hired_instance_id=hired_id, status="pending")
    result_mock = MagicMock()
    result_mock.scalars.return_value.first.return_value = conn
    mock_db.execute = AsyncMock(return_value=result_mock)

    resp = await verify_connection(hired_id, conn_id, db=mock_db)
    assert resp.status == "connected"
    assert resp.last_verified_at is not None
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_verify_connection_404_not_found(hired_id, conn_id, mock_db):
    """PATCH /verify raises HTTP 404 when connection not found."""
    from fastapi import HTTPException
    from api.v1.platform_connections import verify_connection

    result_mock = MagicMock()
    result_mock.scalars.return_value.first.return_value = None
    mock_db.execute = AsyncMock(return_value=result_mock)

    with pytest.raises(HTTPException) as exc:
        await verify_connection(hired_id, conn_id, db=mock_db)
    assert exc.value.status_code == 404
