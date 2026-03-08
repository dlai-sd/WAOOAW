"""Unit smoke tests for EXEC-ENGINE-001 Iteration 1 model registration (E2-S2).

Verifies that FlowRunModel, ComponentRunModel, and SkillConfigModel are
importable from models/__init__.py and registered with the SQLAlchemy metadata.

Run:
    docker compose -f docker-compose.test.yml run plant-test \\
      pytest tests/unit/test_smoke_exec_engine_001.py -v
"""
from __future__ import annotations

import pytest


@pytest.mark.unit
def test_flow_run_model_registered():
    """E2-S2: FlowRunModel is importable from the models package."""
    from models import FlowRunModel  # noqa: F401
    assert FlowRunModel.__tablename__ == "flow_runs"


@pytest.mark.unit
def test_component_run_model_registered():
    """E2-S2: ComponentRunModel is importable from the models package."""
    from models import ComponentRunModel  # noqa: F401
    assert ComponentRunModel.__tablename__ == "component_runs"


@pytest.mark.unit
def test_skill_config_model_registered():
    """E2-S2: SkillConfigModel is importable from the models package."""
    from models import SkillConfigModel  # noqa: F401
    assert SkillConfigModel.__tablename__ == "skill_configs"


@pytest.mark.unit
def test_all_new_models_in_metadata():
    """E2-S2: All three new tables appear in Base.metadata.tables."""
    from core.database import Base
    # Force model registration by importing them
    import models  # noqa: F401
    table_names = set(Base.metadata.tables.keys())
    for expected_table in ("flow_runs", "component_runs", "skill_configs"):
        assert expected_table in table_names, (
            f"Table {expected_table!r} not found in Base.metadata. "
            "Make sure the model is imported in models/__init__.py."
        )
