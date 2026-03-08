"""Unit tests for SkillConfigModel (EXEC-ENGINE-001 E1-S3).

Tests model instantiation, constraint declarations, and default values
without requiring a live database connection.

Run:
    docker compose -f docker-compose.test.yml run plant-test \\
      pytest tests/unit/test_skill_config_model.py -v --cov=models --cov-fail-under=80
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from models.skill_config import SkillConfigModel


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_skill_config(
    id: str = "sc-001",
    hired_instance_id: str = "hired-001",
    skill_id: str = "skill-001",
    definition_version_id: str = "v1",
) -> SkillConfigModel:
    now = datetime.now(timezone.utc)
    return SkillConfigModel(
        id=id,
        hired_instance_id=hired_instance_id,
        skill_id=skill_id,
        definition_version_id=definition_version_id,
        pp_locked_fields={"max_risk_pct": 0.02},
        customer_fields={"rsi_period": 14},
        created_at=now,
        updated_at=now,
    )


# ── E1-S3-T1: UniqueConstraint on (hired_instance_id, skill_id) is declared ──

@pytest.mark.unit
def test_skill_config_model_unique_constraint_declared():
    """E1-S3-T1: UniqueConstraint(hired_instance_id, skill_id) is declared."""
    constraint_names = {
        getattr(arg, "name", None)
        for arg in SkillConfigModel.__table_args__
    }
    assert "uq_skill_config_per_hire" in constraint_names


@pytest.mark.unit
def test_skill_config_model_tablename():
    """SkillConfigModel.__tablename__ == 'skill_configs'."""
    assert SkillConfigModel.__tablename__ == "skill_configs"


@pytest.mark.unit
def test_skill_config_model_fields():
    """SkillConfigModel fields are set correctly."""
    cfg = _make_skill_config()
    assert cfg.id == "sc-001"
    assert cfg.hired_instance_id == "hired-001"
    assert cfg.skill_id == "skill-001"
    assert cfg.definition_version_id == "v1"
    assert cfg.pp_locked_fields == {"max_risk_pct": 0.02}
    assert cfg.customer_fields == {"rsi_period": 14}


@pytest.mark.unit
def test_skill_config_model_repr():
    """SkillConfigModel __repr__ includes expected fields."""
    cfg = _make_skill_config()
    r = repr(cfg)
    assert "sc-001" in r
    assert "hired-001" in r
    assert "skill-001" in r


@pytest.mark.unit
def test_skill_config_model_empty_fields():
    """SkillConfigModel accepts empty dicts for pp_locked_fields and customer_fields."""
    now = datetime.now(timezone.utc)
    cfg = SkillConfigModel(
        id="sc-002",
        hired_instance_id="hired-002",
        skill_id="skill-002",
        definition_version_id="v2",
        pp_locked_fields={},
        customer_fields={},
        created_at=now,
        updated_at=now,
    )
    assert cfg.pp_locked_fields == {}
    assert cfg.customer_fields == {}
