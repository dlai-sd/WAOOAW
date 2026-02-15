"""Unit tests for Genesis Skill key semantics (SK-1.1).

These tests intentionally avoid the DB/migrations path so they stay reliable
even when Alembic history is in flux.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from core.exceptions import DuplicateEntityError
from models.schemas import SkillCreate
from services import skill_service


def test_derive_skill_key_slugifies_name():
    assert skill_service._derive_skill_key("Python 3.11") == "python-3-11"


@pytest.mark.asyncio
async def test_create_skill_sets_external_id_from_explicit_skill_key(monkeypatch):
    db = AsyncMock()
    db.add = Mock()
    service = skill_service.SkillService(db)

    validate_unique = AsyncMock(side_effect=[None, None])
    monkeypatch.setattr(skill_service, "validate_entity_uniqueness", validate_unique)
    monkeypatch.setattr(skill_service, "validate_constitutional_alignment", lambda _: {"compliant": True})

    created = await service.create_skill(
        SkillCreate(
            skill_key="SKILL.PYTHON.3_11",
            name="Python 3.11 Advanced",
            description="Advanced Python",
            category="technical",
        )
    )

    assert created.external_id == "SKILL.PYTHON.3_11"
    assert db.add.called
    assert db.commit.await_count == 1
    assert db.refresh.await_count == 1


@pytest.mark.asyncio
async def test_create_skill_rejects_duplicate_skill_key(monkeypatch):
    db = AsyncMock()
    db.add = Mock()
    service = skill_service.SkillService(db)

    validate_unique = AsyncMock(side_effect=[None, object()])
    monkeypatch.setattr(skill_service, "validate_entity_uniqueness", validate_unique)
    monkeypatch.setattr(skill_service, "validate_constitutional_alignment", lambda _: {"compliant": True})

    with pytest.raises(DuplicateEntityError):
        await service.create_skill(
            SkillCreate(
                skill_key="python-3-11",
                name="Python 3.11",
                description="Modern Python",
                category="technical",
            )
        )
