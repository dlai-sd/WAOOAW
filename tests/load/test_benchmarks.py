"""
Performance Benchmarks

Baseline performance benchmarks for tracking regression.
"""
import pytest
import sys
import time
sys.path.insert(0, '/workspaces/WAOOAW')

from tests.load.test_load_framework import LoadTestRunner
from waooaw.learning.memory_system import MemorySystem
from waooaw.learning.reflection_engine import ReflectionEngine
from waooaw.learning.knowledge_graph import KnowledgeGraph, NodeType
from waooaw.common.config_manager import ConfigManager
from waooaw.common.metrics import MetricsCollector


@pytest.fixture
def load_runner():
    """Provide load test runner."""
    return LoadTestRunner(max_workers=10)


class TestPerformanceBenchmarks:
    """Performance benchmark tests."""
    
    def test_benchmark_memory_store(self, load_runner, benchmark):
        """Benchmark: Memory storage operation."""
        memory = MemorySystem()
        
        def store_operation():
            memory.store(
                content="Benchmark memory",
                memory_type="episodic",
                importance=0.7
            )
        
        # Benchmark with pytest-benchmark
        result = benchmark(store_operation)
        
        # Performance targets
        assert result.stats.mean < 0.01  # Mean under 10ms
        assert result.stats.median < 0.01  # Median under 10ms
    
    def test_benchmark_memory_retrieve(self, load_runner, benchmark):
        """Benchmark: Memory retrieval operation."""
        memory = MemorySystem()
        
        # Pre-populate
        for i in range(100):
            memory.store(f"Memory {i}", "episodic", 0.5)
        
        def retrieve_operation():
            memory.retrieve(query="test", limit=10)
        
        result = benchmark(retrieve_operation)
        
        assert result.stats.mean < 0.05  # Mean under 50ms
    
    def test_benchmark_reflection(self, benchmark):
        """Benchmark: Reflection engine operation."""
        reflection = ReflectionEngine()
        
        def reflection_operation():
            action_id = reflection.log_action(
                action_type="test",
                input_data={"key": "value"},
                output_data={"result": "success"}
            )
            return action_id
        
        result = benchmark(reflection_operation)
        
        assert result.stats.mean < 0.01  # Mean under 10ms
    
    def test_benchmark_knowledge_graph_node(self, benchmark):
        """Benchmark: Knowledge graph node creation."""
        kg = KnowledgeGraph()
        
        counter = [0]
        
        def add_node_operation():
            kg.add_node(NodeType.SKILL, f"Skill_{counter[0]}")
            counter[0] += 1
        
        result = benchmark(add_node_operation)
        
        assert result.stats.mean < 0.005  # Mean under 5ms
    
    def test_benchmark_metrics_counter(self, benchmark):
        """Benchmark: Metrics counter operation."""
        metrics = MetricsCollector()
        counter = metrics.counter("benchmark_counter", "Benchmark")
        
        def counter_operation():
            counter.inc()
        
        result = benchmark(counter_operation)
        
        assert result.stats.mean < 0.001  # Mean under 1ms (very fast)


class TestThroughputBenchmarks:
    """Throughput benchmark tests."""
    
    def test_throughput_memory_system(self, load_runner):
        """Throughput benchmark: Memory system."""
        memory = MemorySystem()
        
        def store_memory(i: int):
            memory.store(f"Memory {i}", "episodic", 0.5)
        
        result = load_runner.run_load_test(
            target_function=store_memory,
            num_requests=1000,
            concurrent_users=25,
            i=0
        )
        
        print(f"\n{result}")
        
        # Throughput targets
        assert result.requests_per_second > 100
        assert result.successful_requests == 1000
        assert result.p95_response_time < 0.2
    
    def test_throughput_knowledge_graph(self, load_runner):
        """Throughput benchmark: Knowledge graph."""
        kg = KnowledgeGraph()
        
        def add_node(i: int):
            kg.add_node(NodeType.SKILL, f"Skill_{i}")
        
        result = load_runner.run_load_test(
            target_function=add_node,
            num_requests=2000,
            concurrent_users=50,
            i=0
        )
        
        print(f"\n{result}")
        
        assert result.requests_per_second > 200
        assert result.successful_requests == 2000
    
    def test_throughput_metrics_collection(self, load_runner):
        """Throughput benchmark: Metrics collection."""
        metrics = MetricsCollector()
        counter = metrics.counter("throughput_test", "Throughput test")
        
        def increment():
            counter.inc()
        
        result = load_runner.run_load_test(
            target_function=increment,
            num_requests=50000,
            concurrent_users=100
        )
        
        print(f"\n{result}")
        
        # Metrics should be extremely fast
        assert result.requests_per_second > 5000
        assert result.successful_requests == 50000
        assert counter.get() == 50000


class TestLatencyBenchmarks:
    """Latency benchmark tests."""
    
    def test_latency_p50_memory(self, load_runner):
        """Latency P50: Memory operations."""
        memory = MemorySystem()
        
        def memory_op(i: int):
            memory.store(f"Memory {i}", "episodic", 0.5)
            memory.retrieve("Memory", limit=5)
        
        result = load_runner.run_load_test(
            target_function=memory_op,
            num_requests=100,
            concurrent_users=10,
            i=0
        )
        
        print(f"\nP50 Latency: {result.median_response_time*1000:.2f}ms")
        assert result.median_response_time < 0.05  # P50 under 50ms
    
    def test_latency_p99_memory(self, load_runner):
        """Latency P99: Memory operations."""
        memory = MemorySystem()
        
        def memory_op(i: int):
            memory.store(f"Memory {i}", "episodic", 0.5)
        
        result = load_runner.run_load_test(
            target_function=memory_op,
            num_requests=500,
            concurrent_users=25,
            i=0
        )
        
        print(f"\nP99 Latency: {result.p99_response_time*1000:.2f}ms")
        assert result.p99_response_time < 0.2  # P99 under 200ms
    
    def test_latency_tail_analysis(self, load_runner):
        """Analyze tail latency distribution."""
        memory = MemorySystem()
        
        def memory_op(i: int):
            memory.store(f"Memory {i}", "episodic", 0.5)
            memory.retrieve("test", limit=10)
        
        result = load_runner.run_load_test(
            target_function=memory_op,
            num_requests=1000,
            concurrent_users=50,
            i=0
        )
        
        print(f"""
Latency Distribution:
  P50: {result.median_response_time*1000:.2f}ms
  P95: {result.p95_response_time*1000:.2f}ms
  P99: {result.p99_response_time*1000:.2f}ms
  Max: {result.max_response_time*1000:.2f}ms
""")
        
        # Tail latency targets
        assert result.median_response_time < 0.05
        assert result.p95_response_time < 0.15
        assert result.p99_response_time < 0.3
        assert result.max_response_time < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
