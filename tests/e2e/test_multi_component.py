"""
E2E Test Scenarios - Multi-Component Coordination
"""
import pytest
import sys
sys.path.insert(0, '/workspaces/WAOOAW')

from waooaw.learning.knowledge_graph import KnowledgeGraph, NodeType, RelationType
from waooaw.common.idempotency import IdempotencyManager
from waooaw.common.metrics import MetricsCollector


class TestMultiComponentE2E:
    """E2E tests for multi-component coordination."""
    
    def test_knowledge_graph_metrics(self):
        """E2E: Knowledge graph with metrics tracking."""
        kg = KnowledgeGraph()
        metrics = MetricsCollector()
        
        nodes_counter = metrics.counter("kg_nodes", "Knowledge graph nodes")
        edges_counter = metrics.counter("kg_edges", "Knowledge graph edges")
        
        # Build knowledge graph
        python_id = kg.add_node(NodeType.SKILL, "Python")
        fastapi_id = kg.add_node(NodeType.SKILL, "FastAPI")
        
        nodes_counter.inc(2)
        
        kg.add_relation(fastapi_id, python_id, RelationType.REQUIRES)
        edges_counter.inc()
        
        # Verify
        assert nodes_counter.get() == 2.0
        assert edges_counter.get() == 1.0
        assert len(kg.nodes) == 2
    
    def test_idempotent_operations_tracking(self):
        """E2E: Idempotent operations with metrics."""
        idempotency = IdempotencyManager()
        metrics = MetricsCollector()
        
        operations = metrics.counter("operations_total", "Operations")
        duplicates = metrics.counter("duplicates_total", "Duplicates")
        
        # Process requests (some duplicates)
        requests = [
            {"to": "user1@example.com"},
            {"to": "user1@example.com"},  # Duplicate
            {"to": "user2@example.com"},
        ]
        
        for req in requests:
            key = idempotency.generate_key("send_email", req)
            
            if idempotency.is_duplicate(key):
                duplicates.inc()
            else:
                idempotency.start_operation(key, "send_email")
                idempotency.complete_operation(key, {"sent": True})
                operations.inc()
        
        # Verify deduplication
        assert operations.get() == 2.0  # Only 2 unique
        assert duplicates.get() == 1.0  # 1 duplicate


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
