"""
Tests for DID Registry - DID document storage and retrieval.
"""

import pytest
from waooaw.identity.did_service import DIDService, DIDDocument
from waooaw.identity.did_registry import DIDRegistry


class TestDIDRegistry:
    """Test DID registry functionality."""
    
    @pytest.fixture
    def registry(self):
        """Create fresh registry for each test."""
        return DIDRegistry()
    
    @pytest.fixture
    def did_service(self):
        """Create DID service for tests."""
        return DIDService()
    
    def test_register_did(self, registry, did_service):
        """Test registering DID document."""
        # Provision DID
        did_doc, _ = did_service.provision_agent_did("TestAgent")
        
        # Register
        registry.register(did_doc)
        
        # Verify registered
        assert registry.exists(did_doc.id)
        assert registry.count() == 1
        
    def test_get_did(self, registry, did_service):
        """Test retrieving DID document."""
        # Register DID
        did_doc, _ = did_service.provision_agent_did("TestAgent")
        registry.register(did_doc)
        
        # Retrieve
        retrieved = registry.get(did_doc.id)
        
        # Verify same document
        assert retrieved is not None
        assert retrieved.id == did_doc.id
        assert retrieved.created == did_doc.created
        
    def test_get_nonexistent_did(self, registry):
        """Test retrieving non-existent DID."""
        result = registry.get("did:waooaw:nonexistent")
        assert result is None
        
    def test_list_all_dids(self, registry, did_service):
        """Test listing all DID documents."""
        # Register multiple DIDs
        agents = ["Agent1", "Agent2", "Agent3"]
        for agent in agents:
            did_doc, _ = did_service.provision_agent_did(agent)
            registry.register(did_doc)
        
        # List all
        all_docs = registry.list_all()
        assert len(all_docs) == 3
        
        # Verify all agents present
        agent_names = [doc.id.split(":")[-1] for doc in all_docs]
        assert "agent1" in agent_names
        assert "agent2" in agent_names
        assert "agent3" in agent_names
        
    def test_list_dids_strings(self, registry, did_service):
        """Test listing DID strings."""
        # Register DIDs
        agents = ["Agent1", "Agent2"]
        for agent in agents:
            did_doc, _ = did_service.provision_agent_did(agent)
            registry.register(did_doc)
        
        # List DID strings
        dids = registry.list_dids()
        assert len(dids) == 2
        assert "did:waooaw:agent1" in dids
        assert "did:waooaw:agent2" in dids
        
    def test_update_did(self, registry, did_service):
        """Test updating DID document."""
        # Register DID
        did_doc, _ = did_service.provision_agent_did("TestAgent")
        registry.register(did_doc)
        
        original_updated = did_doc.updated
        
        # Modify document
        did_doc.service_endpoints.append({
            "id": f"{did_doc.id}#new-service",
            "type": "NewService",
            "serviceEndpoint": "https://new.service"
        })
        
        # Update
        import time
        time.sleep(0.01)  # Ensure timestamp changes
        registry.update(did_doc)
        
        # Verify updated
        retrieved = registry.get(did_doc.id)
        assert len(retrieved.service_endpoints) == 1
        assert retrieved.updated != original_updated
        
    def test_update_nonexistent_did(self, registry, did_service):
        """Test updating non-existent DID raises error."""
        did_doc, _ = did_service.provision_agent_did("TestAgent")
        
        # Try to update without registering first
        with pytest.raises(ValueError, match="not registered"):
            registry.update(did_doc)
            
    def test_delete_did(self, registry, did_service):
        """Test deleting DID document."""
        # Register DID
        did_doc, _ = did_service.provision_agent_did("TestAgent")
        registry.register(did_doc)
        
        # Delete
        result = registry.delete(did_doc.id)
        assert result is True
        
        # Verify deleted
        assert not registry.exists(did_doc.id)
        assert registry.count() == 0
        
        # History should still exist (audit trail)
        history = registry.get_history(did_doc.id)
        assert len(history) == 1
        
    def test_delete_nonexistent_did(self, registry):
        """Test deleting non-existent DID."""
        result = registry.delete("did:waooaw:nonexistent")
        assert result is False
        
    def test_did_history(self, registry, did_service):
        """Test DID document version history."""
        # Register DID
        did_doc, _ = did_service.provision_agent_did("TestAgent")
        registry.register(did_doc)
        
        # Update multiple times
        for i in range(3):
            did_doc.service_endpoints.append({
                "id": f"{did_doc.id}#service-{i}",
                "type": "TestService",
                "serviceEndpoint": f"https://test{i}.service"
            })
            registry.update(did_doc)
        
        # Get history
        history = registry.get_history(did_doc.id)
        
        # Should have 4 versions (1 initial + 3 updates)
        assert len(history) == 4
        
        # Verify service endpoints increased over time
        assert len(history[0].service_endpoints) == 0
        assert len(history[1].service_endpoints) == 1
        assert len(history[2].service_endpoints) == 2
        assert len(history[3].service_endpoints) == 3
        
    def test_exists(self, registry, did_service):
        """Test checking DID existence."""
        # Initially doesn't exist
        assert not registry.exists("did:waooaw:testagent")
        
        # Register
        did_doc, _ = did_service.provision_agent_did("TestAgent")
        registry.register(did_doc)
        
        # Now exists
        assert registry.exists(did_doc.id)
        
    def test_count(self, registry, did_service):
        """Test counting registered DIDs."""
        assert registry.count() == 0
        
        # Register DIDs
        for i in range(5):
            did_doc, _ = did_service.provision_agent_did(f"Agent{i}")
            registry.register(did_doc)
        
        assert registry.count() == 5
        
    def test_search_by_controller(self, registry, did_service):
        """Test searching DIDs by controller."""
        # Register multiple DIDs (all have same controller by default)
        agents = ["Agent1", "Agent2", "Agent3"]
        for agent in agents:
            did_doc, _ = did_service.provision_agent_did(agent)
            registry.register(did_doc)
        
        # Search by controller
        guardian_did = "did:waooaw:wowvision-prime"
        results = registry.search_by_controller(guardian_did)
        
        # All 3 agents should be controlled by guardian
        assert len(results) == 3
        
    def test_get_statistics(self, registry, did_service):
        """Test registry statistics."""
        # Register DIDs
        agents = ["Agent1", "Agent2", "Agent3"]
        for agent in agents:
            did_doc, _ = did_service.provision_agent_did(agent)
            registry.register(did_doc)
            
            # Update once to create history
            did_doc.service_endpoints.append({"id": "test", "type": "Test", "serviceEndpoint": "https://test"})
            registry.update(did_doc)
        
        # Get statistics
        stats = registry.get_statistics()
        
        # Verify stats
        assert stats["total_dids"] == 3
        assert stats["total_history_entries"] == 6  # 3 agents × 2 versions each
        assert "did:waooaw:wowvision-prime" in stats["by_controller"]
        assert stats["by_controller"]["did:waooaw:wowvision-prime"] == 3
        assert len(stats["dids"]) == 3
        
    def test_register_all_platform_agents(self, registry, did_service):
        """Test registering all 14 Platform CoE agents."""
        agents = [
            "WowVisionPrime", "WowAgentFactory", "WowDomain", "WowEvent",
            "WowCommunication", "WowMemory", "WowCache", "WowSearch",
            "WowSecurity", "WowSupport", "WowNotification", "WowScaling",
            "WowIntegration", "WowAnalytics"
        ]
        
        # Register all
        for agent in agents:
            did_doc, _ = did_service.provision_agent_did(agent)
            registry.register(did_doc)
        
        # Verify all registered
        assert registry.count() == 14
        
        # Verify all have DIDs
        dids = registry.list_dids()
        assert "did:waooaw:wowvisionprime" in dids
        assert "did:waooaw:wowagentfactory" in dids
        assert "did:waooaw:wowanalytics" in dids
