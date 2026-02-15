"""Unit tests for models/agent_type.py."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from models.agent_type import AgentTypeDefinitionModel


@pytest.mark.unit
def test_agent_type_definition_model_sets_default_timestamps():
    model = AgentTypeDefinitionModel(
        id="marketing.digital_marketing.v1@1.0.0",
        agent_type_id="marketing.digital_marketing.v1",
        version="1.0.0",
        payload={"k": "v"},
    )

    assert model.created_at is not None
    assert model.updated_at is not None
    assert model.created_at.tzinfo is not None
    assert model.updated_at.tzinfo is not None

    rendered = repr(model)
    assert "AgentTypeDefinitionModel" in rendered
    assert "marketing.digital_marketing.v1" in rendered


@pytest.mark.unit
def test_agent_type_definition_model_respects_explicit_timestamps():
    created_at = datetime(2026, 2, 15, 12, 0, 0, tzinfo=timezone.utc)
    updated_at = created_at + timedelta(hours=1)

    model = AgentTypeDefinitionModel(
        id="test.agent.v1@2.0.0",
        agent_type_id="test.agent.v1",
        version="2.0.0",
        payload={},
        created_at=created_at,
        updated_at=updated_at,
    )

    assert model.created_at == created_at
    assert model.updated_at == updated_at
