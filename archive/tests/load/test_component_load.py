"""
Component Load Tests

Load tests for specific system components.
"""
import pytest
import sys
import time
import asyncio
sys.path.insert(0, '/workspaces/WAOOAW')

from tests.load.test_load_framework import LoadTestRunner, LoadTestResult
from waooaw.learning.memory_system import MemorySystem
from waooaw.learning.knowledge_graph import KnowledgeGraph, NodeType, RelationType
from waooaw.common.idempotency import IdempotencyManager
from waooaw.common.metrics import MetricsCollector


@pytest.fixture
def load_runner():
    """Provide load test runner."""
    return LoadTestRunner(max_workers=20)


class TestMemorySystemLoad:
    """Load tests for Memory System."""
    
    def test_memory_storage_throughput(self, load_runner):
        """Test memory storage under load."""
        memory = MemorySystem()
        
        def store_memory(index: int):
            memory.store(
                content=f"Test memory {index}",
                memory_type="episodic",
                importance=0.5
            )
        
        result = load_runner.run_load_test(
            target_function=store_memory,
            num_requests=100,
            concurrent_users=10,
            index=0
        )
        
        print(result)
        assert result.successful_requests == 100
        assert result.requests_per_second > 10  # Should handle 10+ RPS
        assert result.p95_response_time < 0.5   # P95 under 500ms
    
    def test_memory_retrieval_performance(self, load_runner):
        """Test memory retrieval performance."""
        memory = MemorySystem()
        
        # Pre-populate with memories
        for i in range(50):
            memory.store(
                content=f"Memory {i}",
                memory_type="episodic",
                importance=0.5
            )
        
        def retrieve_memory():
            memory.retrieve(query="test", limit=10)
        
        result = load_runner.run_load_test(
            target_function=retrieve_memory,
            num_requests=200,
            concurrent_users=20
        )
        
        assert result.successful_requests == 200
        assert result.mean_response_time < 0.1  # Mean under 100ms


class TestKnowledgeGraphLoad:
    """Load tests for Knowledge Graph."""
    
    def test_node_creation_throughput(self, load_runner):
        """Test knowledge graph node creation under load."""
        kg = KnowledgeGraph()
        
        def add_node(index: int):
            kg.add_node(NodeType.SKILL, f"Skill_{index}")
        
        result = load_runner.run_load_test(
            target_function=add_node,
            num_requests=500,
            concurrent_users=25,
            index=0
        )
        
        print(result)
        assert result.successful_requests == 500
        assert result.requests_per_second > 50  # High throughput
        assert result.max_response_time < 0.2   # Fast operations
    
    def test_relation_query_performance(self, load_runner):
        """Test knowledge graph query performance."""
        kg = KnowledgeGraph()
        
        # Build a small graph
        node_ids = []
        for i in range(20):
            node_id = kg.add_node(NodeType.SKILL, f"Skill_{i}")
            node_ids.append(node_id)
        
        # Add relations
        for i in range(len(node_ids) - 1):
            kg.add_relation(node_ids[i], node_ids[i+1], RelationType.RELATED_TO)
        
        def query_relations(node_id: str):
            kg.get_related_nodes(node_id)
        
        result = load_runner.run_load_test(
            target_function=query_relations,
            num_requests=1000,
            concurrent_users=50,
            node_id=node_ids[0]
        )
        
        assert result.successful_requests == 1000
        assert result.p99_response_time < 0.1  # P99 under 100ms


class TestIdempotencyLoad:
    """Load tests for Idempotency Manager."""
    
    def test_duplicate_detection_throughput(self, load_runner):
        """Test idempotency checking under load."""
        idempotency = IdempotencyManager()
        
        def check_idempotency(request_id: int):
            key = idempotency.generate_key("operation", {"id": request_id % 10})
            
            if not idempotency.is_duplicate(key):
                idempotency.start_operation(key, "operation")
                time.sleep(0.001)  # Simulate work
                idempotency.complete_operation(key, {"status": "success"})
        
        result = load_runner.run_load_test(
            target_function=check_idempotency,
            num_requests=200,
            concurrent_users=20,
            request_id=0
        )
        
        print(result)
        assert result.successful_requests == 200
        # Should deduplicate many requests (10 unique keys, 200 requests)
        assert result.requests_per_second > 20


class TestMetricsLoad:
    """Load tests for Metrics Collector."""
    
    def test_metrics_collection_throughput(self, load_runner):
        """Test metrics collection under high load."""
        metrics = MetricsCollector()
        counter = metrics.counter("test_metric", "Test metric")
        
        def increment_metric():
            counter.inc()
        
        result = load_runner.run_load_test(
            target_function=increment_metric,
            num_requests=10000,
            concurrent_users=50
        )
        
        print(result)
        assert result.successful_requests == 10000
        assert result.requests_per_second > 1000  # Very high throughput
        assert counter.get() == 10000
    
    def test_histogram_performance(self, load_runner):
        """Test histogram recording performance."""
        metrics = MetricsCollector()
        histogram = metrics.histogram("response_time", "Response time")
        
        import random
        
        def record_timing():
            value = random.uniform(0.01, 0.5)
            histogram.observe(value)
        
        result = load_runner.run_load_test(
            target_function=record_timing,
            num_requests=5000,
            concurrent_users=25
        )
        
        assert result.successful_requests == 5000
        assert result.requests_per_second > 500


class TestStressScenarios:
    """Stress test scenarios."""
    
    @pytest.mark.asyncio
    async def test_sustained_load(self, load_runner):
        """Test system under sustained load."""
        memory = MemorySystem()
        kg = KnowledgeGraph()
        
        async def mixed_operations(index: int):
            # Simulate mixed workload
            memory.store(f"Memory {index}", "episodic", 0.5)
            await asyncio.sleep(0.001)
            kg.add_node(NodeType.SKILL, f"Skill_{index}")
            await asyncio.sleep(0.001)
            memory.retrieve("test", limit=5)
        
        result = await load_runner.run_async_load_test(
            target_function=mixed_operations,
            num_requests=500,
            concurrent_users=30,
            index=0
        )
        
        print(result)
        assert result.successful_requests >= 450  # 90% success rate
        assert result.mean_response_time < 0.5
    
    def test_spike_load(self, load_runner):
        """Test system recovery from load spikes."""
        metrics = MetricsCollector()
        counter = metrics.counter("requests", "Requests")
        
        def simple_operation():
            counter.inc()
            time.sleep(0.001)
        
        # First wave - normal load
        result1 = load_runner.run_load_test(
            target_function=simple_operation,
            num_requests=50,
            concurrent_users=5
        )
        
        # Second wave - spike
        result2 = load_runner.run_load_test(
            target_function=simple_operation,
            num_requests=200,
            concurrent_users=50
        )
        
        # Third wave - back to normal
        result3 = load_runner.run_load_test(
            target_function=simple_operation,
            num_requests=50,
            concurrent_users=5
        )
        
        # System should handle all phases
        assert result1.successful_requests == 50
        assert result2.successful_requests == 200
        assert result3.successful_requests == 50
        
        # Recovery should be good (similar perf to first wave)
        assert abs(result3.mean_response_time - result1.mean_response_time) < 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
