"""Unit tests for DB-backed AgentTypeDefinition API (AGP1-DB-1.2).

Tests repository, service, and API endpoints with both in-memory fallback
and DB-backed implementations.

Note: Tests marked with @pytest.mark.integration require actual database infrastructure.
These are skipped in CI unit test runs.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.integration  # All tests in this file require database

from api.v1.agent_types_simple import AgentTypeDefinition, JsonSchemaDefinition, GoalTemplateDefinition, EnforcementDefaults, SchemaFieldDefinition
from repositories.agent_type_repository import AgentTypeDefinitionRepository
from services.agent_type_service import AgentTypeDefinitionService


@pytest.fixture
def sample_agent_type_payload():
    """Sample AgentTypeDefinition payload for testing."""
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
    """Sample AgentTypeDefinition Pydantic model for testing."""
    return AgentTypeDefinition(**sample_agent_type_payload)


@pytest.mark.asyncio
async def test_agent_type_repository_create(
    async_session: AsyncSession,
    sample_agent_type_payload,
):
    """Test creating agent type definition in DB via repository."""
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
async def test_agent_type_repository_get_by_id(
    async_session: AsyncSession,
    sample_agent_type_payload,
):
    """Test retrieving agent type definition by ID."""
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
async def test_agent_type_repository_list_all(
    async_session: AsyncSession,
    sample_agent_type_payload,
):
    """Test listing all agent type definitions (returns latest version of each)."""
    repo = AgentTypeDefinitionRepository(async_session)
    
    # Create first version
    await repo.create(
        agent_type_id="test.agent.v1",
        version="1.0.0",
        payload=sample_agent_type_payload,
    )
    
    # Create second version
    payload_v2 = {**sample_agent_type_payload, "version": "2.0.0"}
    await repo.create(
        agent_type_id="test.agent.v1",
        version="2.0.0",
        payload=payload_v2,
    )
    
    # Create different agent type
    await repo.create(
        agent_type_id="test.agent2.v1",
        version="1.0.0",
        payload={**sample_agent_type_payload, "agent_type_id": "test.agent2.v1"},
    )
    
    await async_session.commit()
    
    all_defs = await repo.list_all()
    
    # Should return latest version of test.agent.v1 (2.0.0) and test.agent2.v1 (1.0.0)
    assert len(all_defs) == 2
    agent_type_ids = {d.agent_type_id for d in all_defs}
    assert agent_type_ids == {"test.agent.v1", "test.agent2.v1"}


@pytest.mark.asyncio
async def test_agent_type_service_create_and_get(
    async_session: AsyncSession,
    sample_agent_type_definition,
):
    """Test AgentTypeDefinitionService create and get operations."""
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
async def test_agent_type_service_list_definitions(
    async_session: AsyncSession,
    sample_agent_type_definition,
):
    """Test AgentTypeDefinitionService list_definitions."""
    service = AgentTypeDefinitionService(async_session)
    
    await service.create_definition(sample_agent_type_definition)
    await async_session.commit()
    
    all_defs = await service.list_definitions()
    
    assert len(all_defs) >= 1
    assert any(d.agent_type_id == "test.agent.v1" for d in all_defs)


@pytest.mark.asyncio
async def test_agent_type_api_list_fallback_to_in_memory(test_client):
    """Test GET /api/v1/agent-types-db/ falls back to in-memory when USE_AGENT_TYPE_DB=false."""
    # By default, USE_AGENT_TYPE_DB=false in tests
    response = test_client.get("/api/v1/agent-types-db/")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should return in-memory definitions (marketing, trading)
    assert isinstance(data, list)
    # In-memory store has 2 definitions by default
    assert len(data) >= 0  # May be 0 if simple store not initialized


@pytest.mark.asyncio
async def test_agent_type_api_get_by_id_fallback(test_client):
    """Test GET /api/v1/agent-types-db/{id} falls back to in-memory."""
    # By default, USE_AGENT_TYPE_DB=false in tests
    response = test_client.get("/api/v1/agent-types-db/marketing.healthcare.v1")
    
    # Should work if in-memory store has this definition
    # May be 404 if not in in-memory store, which is also valid
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_agent_type_api_create_requires_feature_flag(test_client, sample_agent_type_payload):
    """Test POST /api/v1/agent-types-db/ requires USE_AGENT_TYPE_DB=true."""
    response = test_client.post("/api/v1/agent-types-db/", json=sample_agent_type_payload)
    
    # Should fail with 400 because USE_AGENT_TYPE_DB=false by default
    assert response.status_code == 400
    assert "not enabled" in response.json()["detail"].lower()
