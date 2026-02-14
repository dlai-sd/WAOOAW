"""Unit tests for Genesis Skill lifecycle semantics (SK-1.2)."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock
import uuid

import pytest
from sqlalchemy.sql import operators

from models.skill import Skill
from models.schemas import SkillCreate
from services import skill_service


@pytest.mark.asyncio
async def test_create_skill_sets_pending_certification_status(monkeypatch):
    db = AsyncMock()
    db.add = Mock()
    service = skill_service.SkillService(db)

    monkeypatch.setattr(skill_service, "validate_entity_uniqueness", AsyncMock(side_effect=[None, None]))
    monkeypatch.setattr(skill_service, "validate_constitutional_alignment", lambda _: {"compliant": True})

    created = await service.create_skill(
        SkillCreate(
            name="Python 3.11",
            description="Modern Python programming",
            category="technical",
        )
    )

    assert created.status == "pending_certification"


@pytest.mark.asyncio
async def test_certify_skill_sets_certified_status(monkeypatch):
    db = AsyncMock()
    db.add = Mock()
    service = skill_service.SkillService(db)

    skill = Skill(
        entity_type="Skill",
        name="Python",
        description="desc",
        category="technical",
        custom_attributes={},
        status="pending_certification",
    )

    monkeypatch.setattr(service, "get_skill_by_id", AsyncMock(return_value=skill))

    updated = await service.certify_skill(uuid.uuid4(), {"certification_notes": "ok"})

    assert updated.status == "certified"
    assert updated.custom_attributes.get("genesis_certification", {}).get("certified") is True
    assert db.commit.await_count == 1
    assert db.refresh.await_count == 1


@pytest.mark.asyncio
async def test_list_skills_defaults_to_non_deleted_filter(monkeypatch):
    db = AsyncMock()
    service = skill_service.SkillService(db)

    scalars = Mock()
    scalars.all.return_value = []
    result = Mock()
    result.scalars.return_value = scalars
    db.execute = AsyncMock(return_value=result)

    await service.list_skills()

    stmt = db.execute.call_args.args[0]
    criteria = list(getattr(stmt, "_where_criteria", ()))

    assert any(
        getattr(c, "operator", None) == operators.ne
        and getattr(getattr(c, "left", None), "name", None) == "status"
        and getattr(getattr(c, "right", None), "value", None) == "deleted"
        for c in criteria
    )


@pytest.mark.asyncio
async def test_list_skills_applies_status_filter(monkeypatch):
    db = AsyncMock()
    service = skill_service.SkillService(db)

    scalars = Mock()
    scalars.all.return_value = []
    result = Mock()
    result.scalars.return_value = scalars
    db.execute = AsyncMock(return_value=result)

    await service.list_skills(status="certified")

    stmt = db.execute.call_args.args[0]
    criteria = list(getattr(stmt, "_where_criteria", ()))

    assert any(
        getattr(c, "operator", None) == operators.eq
        and getattr(getattr(c, "left", None), "name", None) == "status"
        and getattr(getattr(c, "right", None), "value", None) == "certified"
        for c in criteria
    )
