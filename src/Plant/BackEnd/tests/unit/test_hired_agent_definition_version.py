"""Unit tests for HiredAgentModel.definition_version_id (EXEC-ENGINE-001 E2-S1).

Verifies that the new column is declared on the model and that the
repository's draft_upsert method accepts definition_version_id.

Run:
    docker compose -f docker-compose.test.yml run plant-test \\
      pytest tests/unit/test_hired_agent_definition_version.py -v --cov=models --cov-fail-under=80
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from models.hired_agent import HiredAgentModel


# ── E2-S1-T1: definition_version_id column declared on HiredAgentModel ────────

@pytest.mark.unit
def test_hired_agent_model_has_definition_version_id_column():
    """E2-S1-T1: HiredAgentModel declares definition_version_id column."""
    columns = {c.name for c in HiredAgentModel.__table__.columns}
    assert "definition_version_id" in columns
    assert "catalog_release_id" in columns
    assert "internal_definition_version_id" in columns
    assert "external_catalog_version" in columns
    assert "catalog_status_at_hire" in columns


@pytest.mark.unit
def test_hired_agent_model_definition_version_id_nullable():
    """E2-S1-T2: definition_version_id column is nullable."""
    col = HiredAgentModel.__table__.c["definition_version_id"]
    assert col.nullable is True


@pytest.mark.unit
def test_hired_agent_model_with_definition_version_id():
    """E2-S1-T1+T2: HiredAgentModel can be instantiated with definition_version_id."""
    now = datetime.now(timezone.utc)
    model = HiredAgentModel(
        hired_instance_id="HAI-test-001",
        subscription_id="SUB-001",
        agent_id="AGT-TRD-001",
        agent_type_id="trading.share_trader.v1",
        definition_version_id="1.0.0",
        customer_id="CUST-001",
        created_at=now,
        updated_at=now,
    )
    assert model.definition_version_id == "1.0.0"


@pytest.mark.unit
def test_hired_agent_model_without_definition_version_id():
    """Existing rows (pre-migration) have definition_version_id=None."""
    now = datetime.now(timezone.utc)
    model = HiredAgentModel(
        hired_instance_id="HAI-test-002",
        subscription_id="SUB-002",
        agent_id="AGT-MKT-001",
        agent_type_id="marketing.digital_marketing.v1",
        customer_id="CUST-001",
        created_at=now,
        updated_at=now,
    )
    assert model.definition_version_id is None


# ── E2-S1-T1+T2: draft_upsert in repository accepts definition_version_id ────

@pytest.mark.unit
@pytest.mark.asyncio
async def test_draft_upsert_passes_definition_version_id():
    """E2-S1: draft_upsert creates HiredAgentModel with definition_version_id."""
    from repositories.hired_agent_repository import HiredAgentRepository

    # Build a mock async session
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()

    created_model: list[HiredAgentModel] = []

    def _capture_add(model):
        created_model.append(model)

    session.add.side_effect = _capture_add

    async def _noop_refresh(m):
        pass

    session.refresh = AsyncMock(side_effect=_noop_refresh)

    # Simulate no existing record
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=result_mock)

    repo = HiredAgentRepository(session)
    await repo.draft_upsert(
        subscription_id="SUB-TEST-001",
        agent_id="AGT-TRD-001",
        agent_type_id="trading.share_trader.v1",
        customer_id="CUST-001",
        definition_version_id="1.0.0",
        catalog_release_id="CAR-001",
        internal_definition_version_id="1.0.0",
        external_catalog_version="v1",
        catalog_status_at_hire="live_on_cp",
    )

    assert len(created_model) == 1
    assert created_model[0].definition_version_id == "1.0.0"
    assert created_model[0].catalog_release_id == "CAR-001"
    assert created_model[0].internal_definition_version_id == "1.0.0"
    assert created_model[0].external_catalog_version == "v1"
    assert created_model[0].catalog_status_at_hire == "live_on_cp"
