"""Unit tests for SK-3.1 hire-time skill-chain enforcement.

CI's "Backend Unit Tests (Plant)" job does not provision Postgres. These tests
therefore exercise the validator directly with mocked DB calls (no HTTP layer).
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, Mock

import pytest

from fastapi import HTTPException

from models.agent import Agent
from models.job_role import JobRole
from models.skill import Skill


def _result_first(obj):
    scalars = Mock()
    scalars.first.return_value = obj
    result = Mock()
    result.scalars.return_value = scalars
    return result


def _result_all(items):
    scalars = Mock()
    scalars.all.return_value = items
    result = Mock()
    result.scalars.return_value = scalars
    return result


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_agent_job_role_skill_chain_fails_when_any_required_skill_not_certified(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("HIRE_ENFORCE_SKILL_CHAIN", "true")

    from api.v1 import hired_agents_simple

    skill_certified = Skill(
        id=uuid.uuid4(),
        entity_type="Skill",
        name="Certified Skill",
        description="desc",
        category="technical",
        status="certified",
    )
    skill_pending = Skill(
        id=uuid.uuid4(),
        entity_type="Skill",
        name="Pending Skill",
        description="desc",
        category="technical",
        status="pending_certification",
    )
    job_role = JobRole(
        id=uuid.uuid4(),
        entity_type="JobRole",
        name="Role",
        description="role",
        required_skills=[skill_certified.id, skill_pending.id],
        seniority_level="mid",
        status="active",
    )
    agent = Agent(
        id=uuid.uuid4(),
        entity_type="Agent",
        name="Agent",
        skill_id=skill_certified.id,
        job_role_id=job_role.id,
        industry_id=uuid.uuid4(),
        status="active",
    )

    db = AsyncMock()
    db.execute = AsyncMock(
        side_effect=[
            _result_first(agent),
            _result_first(job_role),
            _result_all([skill_certified, skill_pending]),
        ]
    )


    with pytest.raises(HTTPException) as exc:
        await hired_agents_simple._validate_agent_job_role_skill_chain(agent_id=str(agent.id), db=db)

    assert exc.value.status_code == 422
    detail = exc.value.detail
    assert isinstance(detail, dict)
    assert str(skill_pending.id) in (detail.get("uncertified_skill_ids") or [])


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_agent_job_role_skill_chain_fails_closed_when_required_skills_missing_or_uncertified(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("HIRE_ENFORCE_SKILL_CHAIN", "true")

    from api.v1 import hired_agents_simple

    missing_skill_id = uuid.uuid4()
    skill_uncertified = Skill(
        id=uuid.uuid4(),
        entity_type="Skill",
        name="Uncertified Skill",
        description="desc",
        category="technical",
        status="pending_certification",
    )
    job_role = JobRole(
        id=uuid.uuid4(),
        entity_type="JobRole",
        name="Role",
        description="role",
        required_skills=[missing_skill_id, skill_uncertified.id],
        seniority_level="mid",
        status="active",
    )
    agent = Agent(
        id=uuid.uuid4(),
        entity_type="Agent",
        name="Agent",
        skill_id=skill_uncertified.id,
        job_role_id=job_role.id,
        industry_id=uuid.uuid4(),
        status="active",
    )

    db = AsyncMock()
    db.execute = AsyncMock(
        side_effect=[
            _result_first(agent),
            _result_first(job_role),
            _result_all([skill_uncertified]),
        ]
    )


    with pytest.raises(HTTPException) as exc:
        await hired_agents_simple._validate_agent_job_role_skill_chain(agent_id=str(agent.id), db=db)

    assert exc.value.status_code == 422
    detail = exc.value.detail
    assert isinstance(detail, dict)
    assert str(missing_skill_id) in (detail.get("missing_skill_ids") or [])
    assert str(skill_uncertified.id) in (detail.get("uncertified_skill_ids") or [])


@pytest.mark.unit
@pytest.mark.asyncio
async def test_db_mode_does_not_enforce_skill_chain_when_flag_unset(monkeypatch):
    """Phase-1 compatibility: DB mode should not require Genesis skills by default."""

    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.delenv("HIRE_ENFORCE_SKILL_CHAIN", raising=False)

    from api.v1 import hired_agents_simple

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=AssertionError("SK-3.1 should not query DB when flag is unset"))

    await hired_agents_simple._validate_agent_job_role_skill_chain(agent_id="AGT-MKT-HEALTH-001", db=db)
