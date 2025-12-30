"""
Test Agent Registry

Story: #80 Tests & Docs (2 pts)
Epic: #68 WowAgentFactory Core (v0.4.1)
Theme: CONCEIVE
"""

import pytest
from datetime import datetime

from waooaw.factory.registry import AgentRegistry, AgentMetadata, AgentStatus, AgentTier


@pytest.fixture
def registry():
    """Create test registry"""
    reg = AgentRegistry()
    reg._agents.clear()  # Clear pre-loaded agents for clean tests
    return reg


@pytest.fixture
def test_metadata():
    """Create test agent metadata"""
    return AgentMetadata(
        agent_id="TestAgent",
        did="did:waooaw:test",
        name="Test Agent",
        tier=AgentTier.TIER_3_COMMUNICATION,
        version="0.1.0",
        status=AgentStatus.DRAFT,
        capabilities={"test": ["can:test"]},
        dependencies=[]
    )


class TestAgentRegistry:
    """Test AgentRegistry"""
    
    def test_singleton(self):
        """Test singleton pattern"""
        reg1 = AgentRegistry()
        reg2 = AgentRegistry()
        assert reg1 is reg2
    
    def test_register_agent(self, registry, test_metadata):
        """Test agent registration"""
        registry.register_agent(test_metadata)
        assert "TestAgent" in registry._agents
        assert registry.get_agent("TestAgent") == test_metadata
    
    def test_unregister_agent(self, registry, test_metadata):
        """Test agent unregistration"""
        registry.register_agent(test_metadata)
        registry.unregister_agent("TestAgent")
        assert "TestAgent" not in registry._agents
    
    def test_get_agent(self, registry, test_metadata):
        """Test get agent by ID"""
        registry.register_agent(test_metadata)
        agent = registry.get_agent("TestAgent")
        assert agent is not None
        assert agent.agent_id == "TestAgent"
    
    def test_get_agent_by_did(self, registry, test_metadata):
        """Test get agent by DID"""
        registry.register_agent(test_metadata)
        agent = registry.get_agent_by_did("did:waooaw:test")
        assert agent is not None
        assert agent.did == "did:waooaw:test"
    
    def test_list_agents(self, registry, test_metadata):
        """Test list all agents"""
        registry.register_agent(test_metadata)
        agents = registry.list_agents()
        assert len(agents) == 1
        assert agents[0].agent_id == "TestAgent"
    
    def test_list_agents_by_status(self, registry, test_metadata):
        """Test filter by status"""
        registry.register_agent(test_metadata)
        
        draft_agents = registry.list_agents(status=AgentStatus.DRAFT)
        assert len(draft_agents) == 1
        
        active_agents = registry.list_agents(status=AgentStatus.ACTIVE)
        assert len(active_agents) == 0
    
    def test_list_agents_by_tier(self, registry, test_metadata):
        """Test filter by tier"""
        registry.register_agent(test_metadata)
        
        tier3_agents = registry.list_agents(tier=AgentTier.TIER_3_COMMUNICATION)
        assert len(tier3_agents) == 1
        
        tier1_agents = registry.list_agents(tier=AgentTier.TIER_1_GUARDIAN)
        assert len(tier1_agents) == 0
    
    def test_find_agents_with_capability(self, registry, test_metadata):
        """Test find by capability"""
        registry.register_agent(test_metadata)
        
        agents = registry.find_agents_with_capability("can:test")
        assert len(agents) == 1
        
        agents = registry.find_agents_with_capability("can:other")
        assert len(agents) == 0
    
    def test_get_dependencies(self, registry):
        """Test get agent dependencies"""
        # Create agents with dependencies
        factory = AgentMetadata(
            agent_id="Factory",
            did="did:waooaw:factory",
            name="Factory",
            tier=AgentTier.TIER_2_CREATION,
            version="0.1.0",
            status=AgentStatus.DRAFT,
            dependencies=[]
        )
        
        domain = AgentMetadata(
            agent_id="Domain",
            did="did:waooaw:domain",
            name="Domain",
            tier=AgentTier.TIER_2_CREATION,
            version="0.1.0",
            status=AgentStatus.DRAFT,
            dependencies=["Factory"]
        )
        
        registry.register_agent(factory)
        registry.register_agent(domain)
        
        deps = registry.get_dependencies("Domain")
        assert len(deps) == 1
        assert deps[0].agent_id == "Factory"
    
    def test_get_dependents(self, registry):
        """Test get agents dependent on this agent"""
        # Create agents with dependencies
        factory = AgentMetadata(
            agent_id="Factory",
            did="did:waooaw:factory",
            name="Factory",
            tier=AgentTier.TIER_2_CREATION,
            version="0.1.0",
            status=AgentStatus.DRAFT,
            dependencies=[]
        )
        
        domain = AgentMetadata(
            agent_id="Domain",
            did="did:waooaw:domain",
            name="Domain",
            tier=AgentTier.TIER_2_CREATION,
            version="0.1.0",
            status=AgentStatus.DRAFT,
            dependencies=["Factory"]
        )
        
        registry.register_agent(factory)
        registry.register_agent(domain)
        
        dependents = registry.get_dependents("Factory")
        assert len(dependents) == 1
        assert dependents[0].agent_id == "Domain"
    
    def test_update_status(self, registry, test_metadata):
        """Test status updates"""
        registry.register_agent(test_metadata)
        
        registry.update_status("TestAgent", AgentStatus.ACTIVE)
        agent = registry.get_agent("TestAgent")
        assert agent.status == AgentStatus.ACTIVE
        assert agent.deployed_at is not None
    
    def test_mark_deployed(self, registry, test_metadata):
        """Test mark as deployed"""
        registry.register_agent(test_metadata)
        registry.mark_deployed("TestAgent")
        
        agent = registry.get_agent("TestAgent")
        assert agent.status == AgentStatus.ACTIVE
    
    def test_get_statistics(self, registry, test_metadata):
        """Test registry statistics"""
        registry.register_agent(test_metadata)
        
        stats = registry.get_statistics()
        assert stats["total_agents"] == 1
        assert stats["by_status"][AgentStatus.DRAFT.value] == 1
        assert stats["draft_count"] == 1
