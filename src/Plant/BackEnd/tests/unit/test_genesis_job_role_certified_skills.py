"""Unit tests for Genesis JobRole certified-only composition (SK-1.3)."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, Mock

import pytest

from core.exceptions import ValidationError
from models.schemas import JobRoleCreate
from models.skill import Skill
from services import job_role_service


def _mock_execute_returning_skills(db: AsyncMock, skills: list[Skill]) -> None:
    scalars = Mock()
    scalars.all.return_value = skills
    result = Mock()
    result.scalars.return_value = scalars
    db.execute = AsyncMock(return_value=result)


@pytest.mark.asyncio
async def test_create_job_role_rejects_uncertified_required_skills(monkeypatch):
    db = AsyncMock()
    db.add = Mock()
    service = job_role_service.JobRoleService(db)

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

    _mock_execute_returning_skills(db, [skill_certified, skill_pending])

    monkeypatch.setattr(job_role_service, "validate_entity_uniqueness", AsyncMock(return_value=None))
    monkeypatch.setattr(job_role_service, "validate_constitutional_alignment", lambda _: {"compliant": True})

    role_data = JobRoleCreate(
        name="Role A",
        description="role",
        required_skills=[skill_certified.id, skill_pending.id],
        seniority_level="mid",
    )

    with pytest.raises(ValidationError) as exc:
        await service.create_job_role(role_data)

    assert "must be certified" in str(exc.value)
    assert str(skill_pending.id) in str(exc.value)


@pytest.mark.asyncio
async def test_create_job_role_allows_all_certified_skills(monkeypatch):
    db = AsyncMock()
    db.add = Mock()
    service = job_role_service.JobRoleService(db)

    skill_1 = Skill(
        id=uuid.uuid4(),
        entity_type="Skill",
        name="Skill 1",
        description="desc",
        category="technical",
        status="certified",
    )
    skill_2 = Skill(
        id=uuid.uuid4(),
        entity_type="Skill",
        name="Skill 2",
        description="desc",
        category="technical",
        status="certified",
    )

    _mock_execute_returning_skills(db, [skill_1, skill_2])

    monkeypatch.setattr(job_role_service, "validate_entity_uniqueness", AsyncMock(return_value=None))
    monkeypatch.setattr(job_role_service, "validate_constitutional_alignment", lambda _: {"compliant": True})

    role_data = JobRoleCreate(
        name="Role B",
        description="role",
        required_skills=[skill_1.id, skill_2.id],
        seniority_level="mid",
    )

    created = await service.create_job_role(role_data)

    assert created.name == "Role B"
    assert created.required_skills == [skill_1.id, skill_2.id]
    assert db.commit.await_count == 1
    assert db.refresh.await_count == 1
