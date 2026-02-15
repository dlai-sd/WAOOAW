from __future__ import annotations


from unittest.mock import AsyncMock, Mock

import pytest

from models.skill import Skill


def _result_all(items):
    scalars = Mock()
    scalars.all.return_value = items
    result = Mock()
    result.scalars.return_value = scalars
    return result


@pytest.mark.unit
def test_publish_agent_type_rejects_unknown_required_skill_key(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")

    from fastapi.testclient import TestClient

    from api.v1 import agent_types_simple
    from main import app

    agent_type_id = "test.skill.validation.v1"
    original = agent_types_simple._DEFINITIONS.get(agent_type_id)

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[_result_all([])])

    async def override_db():
        yield db

    app.dependency_overrides[agent_types_simple._get_agent_types_db_session] = override_db

    try:
        with TestClient(app) as client:
            payload = {
                "agent_type_id": agent_type_id,
                "version": "9.9.9",
                "required_skill_keys": ["skill.does_not_exist"],
                "config_schema": {"fields": []},
                "goal_templates": [],
                "enforcement_defaults": {"approval_required": True, "deterministic": False},
            }
            res = client.put(f"/api/v1/agent-types/{agent_type_id}", json=payload)

        assert res.status_code == 422
        body = res.json()
        assert "missing_required_skill_keys" in body
        assert "skill.does_not_exist" in (body.get("missing_required_skill_keys") or [])
    finally:
        app.dependency_overrides.pop(agent_types_simple._get_agent_types_db_session, None)
        if original is None:
            agent_types_simple._DEFINITIONS.pop(agent_type_id, None)
        else:
            agent_types_simple._DEFINITIONS[agent_type_id] = original


@pytest.mark.unit
def test_publish_agent_type_rejects_uncertified_required_skill_key(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")

    from fastapi.testclient import TestClient

    from api.v1 import agent_types_simple
    from main import app

    agent_type_id = "test.skill.validation.v1"
    original = agent_types_simple._DEFINITIONS.get(agent_type_id)

    skill = Skill(
        entity_type="Skill",
        external_id="skill.pending",
        name="Pending",
        description="d",
        category="technical",
        status="pending_certification",
    )

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[_result_all([skill])])

    async def override_db():
        yield db

    app.dependency_overrides[agent_types_simple._get_agent_types_db_session] = override_db

    try:
        with TestClient(app) as client:
            payload = {
                "agent_type_id": agent_type_id,
                "version": "9.9.9",
                "required_skill_keys": ["skill.pending"],
                "config_schema": {"fields": []},
                "goal_templates": [],
                "enforcement_defaults": {"approval_required": True, "deterministic": False},
            }
            res = client.put(f"/api/v1/agent-types/{agent_type_id}", json=payload)

        assert res.status_code == 422
        body = res.json()
        assert "uncertified_required_skill_keys" in body
        assert "skill.pending" in (body.get("uncertified_required_skill_keys") or [])
    finally:
        app.dependency_overrides.pop(agent_types_simple._get_agent_types_db_session, None)
        if original is None:
            agent_types_simple._DEFINITIONS.pop(agent_type_id, None)
        else:
            agent_types_simple._DEFINITIONS[agent_type_id] = original


@pytest.mark.unit
def test_publish_agent_type_accepts_certified_required_skill_keys(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")

    from fastapi.testclient import TestClient

    from api.v1 import agent_types_simple
    from main import app

    agent_type_id = "test.skill.validation.v1"
    original = agent_types_simple._DEFINITIONS.get(agent_type_id)

    skill = Skill(
        entity_type="Skill",
        external_id="skill.certified",
        name="Certified",
        description="d",
        category="technical",
        status="certified",
    )

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[_result_all([skill])])

    async def override_db():
        yield db

    app.dependency_overrides[agent_types_simple._get_agent_types_db_session] = override_db

    try:
        with TestClient(app) as client:
            payload = {
                "agent_type_id": agent_type_id,
                "version": "9.9.9",
                "required_skill_keys": ["skill.certified"],
                "config_schema": {"fields": []},
                "goal_templates": [],
                "enforcement_defaults": {"approval_required": True, "deterministic": False},
            }
            res = client.put(f"/api/v1/agent-types/{agent_type_id}", json=payload)

        assert res.status_code == 200
        body = res.json()
        assert body.get("required_skill_keys") == ["skill.certified"]
    finally:
        app.dependency_overrides.pop(agent_types_simple._get_agent_types_db_session, None)
        if original is None:
            agent_types_simple._DEFINITIONS.pop(agent_type_id, None)
        else:
            agent_types_simple._DEFINITIONS[agent_type_id] = original
