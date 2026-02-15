"""Integration tests for DB-backed AgentTypeDefinition API (AGP1-DB-1.2).

These tests require a Postgres test database (async_session fixture) and are
marked as integration.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.agent_types_simple import AgentTypeDefinition
from repositories.agent_type_repository import AgentTypeDefinitionRepository
from services.agent_type_service import AgentTypeDefinitionService


pytestmark = pytest.mark.integration


@pytest.fixture
def sample_agent_type_payload():
    return {
        "agent_type_id": "test.agent.v1",
        "version": "1.0.0",
        "config_schema": {
            "fields": [
                {
                    "key": "nickname",
                    "label": "Agent nickname",
                    "type": "text",
                    "required": True,
                }
            ]
        },
        "goal_templates": [
            {
                "goal_template_id": "test.goal.v1",
                "name": "Test Goal",
                "default_frequency": "weekly",
                "settings_schema": {"fields": []},
            }
        ],
        "enforcement_defaults": {
            "approval_required": True,
            "deterministic": False,
        },
    }


@pytest.fixture
def sample_agent_type_definition(sample_agent_type_payload):
    return AgentTypeDefinition(**sample_agent_type_payload)


@pytest.mark.asyncio
async def test_agent_type_repository_create(async_session: AsyncSession, sample_agent_type_payload):
    repo = AgentTypeDefinitionRepository(async_session)

    created = await repo.create(
        agent_type_id="test.agent.v1",
        version="1.0.0",
        payload=sample_agent_type_payload,
    )

    await async_session.commit()

    assert created.id == "test.agent.v1@1.0.0"
    assert created.agent_type_id == "test.agent.v1"
    assert created.version == "1.0.0"
    assert created.payload == sample_agent_type_payload


@pytest.mark.asyncio
async def test_agent_type_repository_get_by_id(async_session: AsyncSession, sample_agent_type_payload):
    repo = AgentTypeDefinitionRepository(async_session)

    await repo.create(
        agent_type_id="test.agent.v1",
        version="1.0.0",
        payload=sample_agent_type_payload,
    )
    await async_session.commit()

    retrieved = await repo.get_by_id("test.agent.v1")

    assert retrieved is not None
    assert retrieved.agent_type_id == "test.agent.v1"
    assert retrieved.version == "1.0.0"


@pytest.mark.asyncio
async def test_agent_type_repository_list_all(async_session: AsyncSession, sample_agent_type_payload):
    repo = AgentTypeDefinitionRepository(async_session)

    await repo.create(
        agent_type_id="test.agent.v1",
        version="1.0.0",
        payload=sample_agent_type_payload,
    )

    payload_v2 = {**sample_agent_type_payload, "version": "2.0.0"}
    await repo.create(
        agent_type_id="test.agent.v1",
        version="2.0.0",
        payload=payload_v2,
    )

    await repo.create(
        agent_type_id="test.agent2.v1",
        version="1.0.0",
        payload={**sample_agent_type_payload, "agent_type_id": "test.agent2.v1"},
    )

    await async_session.commit()

    all_defs = await repo.list_all()

    assert len(all_defs) == 2
    agent_type_ids = {d.agent_type_id for d in all_defs}
    assert agent_type_ids == {"test.agent.v1", "test.agent2.v1"}


@pytest.mark.asyncio
async def test_agent_type_service_create_and_get(async_session: AsyncSession, sample_agent_type_definition):
    service = AgentTypeDefinitionService(async_session)

    created = await service.create_definition(sample_agent_type_definition)
    await async_session.commit()

    assert created.agent_type_id == "test.agent.v1"
    assert created.version == "1.0.0"

    retrieved = await service.get_definition("test.agent.v1")

    assert retrieved is not None
    assert retrieved.agent_type_id == "test.agent.v1"
    assert retrieved.version == "1.0.0"
    assert retrieved.config_schema.fields[0].key == "nickname"


@pytest.mark.asyncio
async def test_agent_type_service_list_definitions(async_session: AsyncSession, sample_agent_type_definition):
    service = AgentTypeDefinitionService(async_session)

    await service.create_definition(sample_agent_type_definition)
    await async_session.commit()

    all_defs = await service.list_definitions()

    assert len(all_defs) >= 1
    assert any(d.agent_type_id == "test.agent.v1" for d in all_defs)
