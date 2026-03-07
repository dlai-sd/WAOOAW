"""Tests for constraint-policy routes (E3-S1, E3-S2)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException

from core.authorization import require_role


def _bypass_role(role: str):
    return lambda: {"sub": "test-user", "roles": [role]}


def _raise_forbidden():
    raise HTTPException(status_code=403, detail="forbidden")


# ---------------------------------------------------------------------------
# PATCH /{agent_setup_id}/constraint-policy
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_patch_constraint_policy_ok(app, client, monkeypatch, tmp_path: Path):
    store_path = tmp_path / "agent_setups.jsonl"
    monkeypatch.setenv("PP_AGENT_SETUP_STORE_PATH", str(store_path))
    monkeypatch.setenv("PP_AGENT_SETUP_SECRET", "test-secret")

    # Invalidate lru_cache so the new env var path is picked up.
    from services.agent_setups import default_agent_setup_store, _fernet
    default_agent_setup_store.cache_clear()
    _fernet.cache_clear()

    # Pre-create an AgentSetup record.
    upsert = await client.put(
        "/api/pp/agent-setups",
        json={
            "customer_id": "CUST-001",
            "agent_id": "AGT-001",
            "channels": [],
            "credential_refs": {},
        },
    )
    assert upsert.status_code == 200

    app.dependency_overrides[require_role("admin")] = _bypass_role("admin")
    try:
        resp = await client.patch(
            "/api/pp/agent-setups/CUST-001:AGT-001/constraint-policy",
            json={"approval_mode": "auto", "max_tasks_per_day": 10},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["agent_setup_id"] == "CUST-001:AGT-001"
        policy = body["constraint_policy"]
        assert policy["approval_mode"] == "auto"
        assert policy["max_tasks_per_day"] == 10
    finally:
        app.dependency_overrides.clear()
        default_agent_setup_store.cache_clear()
        _fernet.cache_clear()


@pytest.mark.asyncio
async def test_patch_constraint_policy_partial_update(app, client, monkeypatch, tmp_path: Path):
    store_path = tmp_path / "agent_setups2.jsonl"
    monkeypatch.setenv("PP_AGENT_SETUP_STORE_PATH", str(store_path))
    monkeypatch.setenv("PP_AGENT_SETUP_SECRET", "test-secret")

    from services.agent_setups import default_agent_setup_store, _fernet
    default_agent_setup_store.cache_clear()
    _fernet.cache_clear()

    await client.put(
        "/api/pp/agent-setups",
        json={"customer_id": "C2", "agent_id": "A2", "channels": [], "credential_refs": {}},
    )

    app.dependency_overrides[require_role("admin")] = _bypass_role("admin")
    try:
        # First patch
        await client.patch(
            "/api/pp/agent-setups/C2:A2/constraint-policy",
            json={"approval_mode": "manual", "trial_task_limit": 5},
        )
        # Second patch — should only change max_tasks_per_day
        resp2 = await client.patch(
            "/api/pp/agent-setups/C2:A2/constraint-policy",
            json={"max_tasks_per_day": 20},
        )
        assert resp2.status_code == 200
        policy = resp2.json()["constraint_policy"]
        # Previous fields must still exist
        assert policy["approval_mode"] == "manual"
        assert policy["trial_task_limit"] == 5
        assert policy["max_tasks_per_day"] == 20
    finally:
        app.dependency_overrides.clear()
        default_agent_setup_store.cache_clear()
        _fernet.cache_clear()


@pytest.mark.asyncio
async def test_patch_constraint_policy_422_empty_body(app, client, monkeypatch, tmp_path: Path):
    store_path = tmp_path / "agent_setups3.jsonl"
    monkeypatch.setenv("PP_AGENT_SETUP_STORE_PATH", str(store_path))
    monkeypatch.setenv("PP_AGENT_SETUP_SECRET", "test-secret")

    from services.agent_setups import default_agent_setup_store, _fernet
    default_agent_setup_store.cache_clear()
    _fernet.cache_clear()

    await client.put(
        "/api/pp/agent-setups",
        json={"customer_id": "C3", "agent_id": "A3", "channels": [], "credential_refs": {}},
    )
    app.dependency_overrides[require_role("admin")] = _bypass_role("admin")
    try:
        resp = await client.patch(
            "/api/pp/agent-setups/C3:A3/constraint-policy",
            json={},
        )
        assert resp.status_code == 422
    finally:
        app.dependency_overrides.clear()
        default_agent_setup_store.cache_clear()
        _fernet.cache_clear()


@pytest.mark.asyncio
async def test_patch_constraint_policy_404_unknown_id(app, client, monkeypatch, tmp_path: Path):
    store_path = tmp_path / "agent_setups4.jsonl"
    monkeypatch.setenv("PP_AGENT_SETUP_STORE_PATH", str(store_path))
    monkeypatch.setenv("PP_AGENT_SETUP_SECRET", "test-secret")

    from services.agent_setups import default_agent_setup_store, _fernet
    default_agent_setup_store.cache_clear()
    _fernet.cache_clear()

    app.dependency_overrides[require_role("admin")] = _bypass_role("admin")
    try:
        resp = await client.patch(
            "/api/pp/agent-setups/UNKNOWN:AGENT/constraint-policy",
            json={"approval_mode": "auto"},
        )
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.clear()
        default_agent_setup_store.cache_clear()
        _fernet.cache_clear()


@pytest.mark.asyncio
async def test_patch_constraint_policy_forbidden_for_developer(app, client):
    app.dependency_overrides[require_role("admin")] = _raise_forbidden
    try:
        resp = await client.patch(
            "/api/pp/agent-setups/C1:A1/constraint-policy",
            json={"approval_mode": "auto"},
        )
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# GET /{agent_setup_id}/constraint-policy
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_constraint_policy_ok(app, client, monkeypatch, tmp_path: Path):
    store_path = tmp_path / "agent_setups5.jsonl"
    monkeypatch.setenv("PP_AGENT_SETUP_STORE_PATH", str(store_path))
    monkeypatch.setenv("PP_AGENT_SETUP_SECRET", "test-secret")

    from services.agent_setups import default_agent_setup_store, _fernet
    default_agent_setup_store.cache_clear()
    _fernet.cache_clear()

    await client.put(
        "/api/pp/agent-setups",
        json={"customer_id": "C5", "agent_id": "A5", "channels": [], "credential_refs": {}},
    )

    app.dependency_overrides[require_role("admin")] = _bypass_role("admin")
    app.dependency_overrides[require_role("developer")] = _bypass_role("developer")
    try:
        await client.patch(
            "/api/pp/agent-setups/C5:A5/constraint-policy",
            json={"approval_mode": "manual", "max_tasks_per_day": 5},
        )
        resp = await client.get("/api/pp/agent-setups/C5:A5/constraint-policy")
        assert resp.status_code == 200
        body = resp.json()
        assert body["agent_setup_id"] == "C5:A5"
        assert body["constraint_policy"]["approval_mode"] == "manual"
    finally:
        app.dependency_overrides.clear()
        default_agent_setup_store.cache_clear()
        _fernet.cache_clear()


@pytest.mark.asyncio
async def test_get_constraint_policy_404_unknown(app, client, monkeypatch, tmp_path: Path):
    store_path = tmp_path / "agent_setups6.jsonl"
    monkeypatch.setenv("PP_AGENT_SETUP_STORE_PATH", str(store_path))
    monkeypatch.setenv("PP_AGENT_SETUP_SECRET", "test-secret")

    from services.agent_setups import default_agent_setup_store, _fernet
    default_agent_setup_store.cache_clear()
    _fernet.cache_clear()

    app.dependency_overrides[require_role("developer")] = _bypass_role("developer")
    try:
        resp = await client.get("/api/pp/agent-setups/NOBODY:NOTHING/constraint-policy")
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.clear()
        default_agent_setup_store.cache_clear()
        _fernet.cache_clear()


@pytest.mark.asyncio
async def test_get_constraint_policy_forbidden_for_viewer(app, client):
    app.dependency_overrides[require_role("developer")] = _raise_forbidden
    try:
        resp = await client.get("/api/pp/agent-setups/C1:A1/constraint-policy")
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.clear()

