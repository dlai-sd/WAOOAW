"""
Epic 6: Story 6.3 - Load Tests

Tests performance under load:
- Simulate 100 wake cycles/day
- Measure latency (p50, p95, p99)
- Measure throughput (decisions/second)
- Validate performance targets

Requirements from WOWVISION_PRIME_PROJECT_PLAN.md:
- Wake latency <5s (p95)
- Decision latency <500ms deterministic, <2s LLM (p95)
- Throughput >10 decisions/second
"""

import pytest
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch
from datetime import datetime

from waooaw.agents.wowvision_prime import WowVisionPrime
from waooaw.agents.event_types import AgentEvent


class TestLoadPerformance:
    """Test performance under load."""
    
    @pytest.mark.load
    def test_100_wake_cycles_simulation(self):
        """Test: Simulate 100 wake cycles (typical daily load)."""
        agent = WowVisionPrime(agent_id="load-test-agent")
        
        wake_times = []
        
        for i in range(100):
            event = AgentEvent(
                event_type="github.pull_request.opened",
                source="github",
                data={
                    "action": "opened",
                    "pull_request": {"number": i, "title": f"PR {i}"}
                },
                timestamp=datetime.now()
            )
            
            start = time.time()
            agent.receive_event(event)
            elapsed = time.time() - start
            wake_times.append(elapsed)
        
        # Calculate statistics
        p50 = statistics.median(wake_times)
        p95 = statistics.quantiles(wake_times, n=20)[18]  # 95th percentile
        p99 = statistics.quantiles(wake_times, n=100)[98]  # 99th percentile
        
        print(f"\n100 Wake Cycles:")
        print(f"  p50: {p50:.3f}s")
        print(f"  p95: {p95:.3f}s")
        print(f"  p99: {p99:.3f}s")
        
        # Validate targets
        assert p95 < 5.0, f"p95 wake latency {p95:.3f}s exceeds 5s target"
    
    @pytest.mark.load
    def test_decision_latency_percentiles(self):
        """Test: Measure decision latency percentiles."""
        agent = WowVisionPrime(agent_id="load-test-agent")
        
        deterministic_times = []
        llm_times = []
        
        # Test deterministic decisions (100x)
        for i in range(100):
            context = {
                "decision_type": "simple",
                "context": {"index": i}
            }
            
            start = time.time()
            decision = agent.make_decision(context)
            elapsed = time.time() - start
            deterministic_times.append(elapsed)
        
        # Test LLM decisions (20x - fewer due to cost)
        with patch.object(agent, '_call_llm', return_value="approve"):
            for i in range(20):
                context = {
                    "decision_type": "complex",
                    "context": {"index": i, "requires_llm": True}
                }
                
                start = time.time()
                decision = agent.make_decision(context)
                elapsed = time.time() - start
                llm_times.append(elapsed)
        
        # Calculate statistics
        det_p50 = statistics.median(deterministic_times)
        det_p95 = statistics.quantiles(deterministic_times, n=20)[18]
        
        llm_p50 = statistics.median(llm_times)
        llm_p95 = statistics.quantiles(llm_times, n=20)[18]
        
        print(f"\nDeterministic Decisions:")
        print(f"  p50: {det_p50*1000:.1f}ms")
        print(f"  p95: {det_p95*1000:.1f}ms")
        
        print(f"\nLLM Decisions (mocked):")
        print(f"  p50: {llm_p50*1000:.1f}ms")
        print(f"  p95: {llm_p95*1000:.1f}ms")
        
        # Validate targets
        assert det_p95 < 0.5, f"Deterministic p95 {det_p95:.3f}s exceeds 0.5s target"
        assert llm_p95 < 2.0, f"LLM p95 {llm_p95:.3f}s exceeds 2s target"
    
    @pytest.mark.load
    def test_throughput_decisions_per_second(self):
        """Test: Measure throughput (decisions/second)."""
        agent = WowVisionPrime(agent_id="load-test-agent")
        
        num_decisions = 100
        
        start = time.time()
        
        for i in range(num_decisions):
            context = {
                "decision_type": "test",
                "context": {"index": i}
            }
            decision = agent.make_decision(context)
        
        elapsed = time.time() - start
        throughput = num_decisions / elapsed
        
        print(f"\nThroughput:")
        print(f"  {num_decisions} decisions in {elapsed:.2f}s")
        print(f"  {throughput:.1f} decisions/second")
        
        # Validate target (>10 decisions/second)
        assert throughput > 10, f"Throughput {throughput:.1f} d/s is below 10 d/s target"
    
    @pytest.mark.load
    def test_concurrent_decisions(self):
        """Test: Handle concurrent decisions (thread safety)."""
        agent = WowVisionPrime(agent_id="load-test-agent")
        
        def make_decision(index):
            context = {
                "decision_type": "test",
                "context": {"index": index}
            }
            start = time.time()
            decision = agent.make_decision(context)
            elapsed = time.time() - start
            return elapsed
        
        num_concurrent = 10
        latencies = []
        
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(make_decision, i) for i in range(100)]
            
            for future in as_completed(futures):
                latency = future.result()
                latencies.append(latency)
        
        avg_latency = statistics.mean(latencies)
        print(f"\nConcurrent Decisions:")
        print(f"  {len(latencies)} decisions with {num_concurrent} workers")
        print(f"  Average latency: {avg_latency*1000:.1f}ms")
        
        # No crashes = success
        assert len(latencies) == 100


class TestLoadStress:
    """Test system under stress conditions."""
    
    @pytest.mark.load
    def test_sustained_load_1000_decisions(self):
        """Test: Sustained load of 1000 decisions."""
        agent = WowVisionPrime(agent_id="stress-test-agent")
        
        success_count = 0
        error_count = 0
        latencies = []
        
        for i in range(1000):
            try:
                context = {
                    "decision_type": "test",
                    "context": {"index": i}
                }
                
                start = time.time()
                decision = agent.make_decision(context)
                elapsed = time.time() - start
                
                latencies.append(elapsed)
                success_count += 1
                
            except Exception as e:
                error_count += 1
        
        success_rate = success_count / 1000
        avg_latency = statistics.mean(latencies)
        p95_latency = statistics.quantiles(latencies, n=20)[18]
        
        print(f"\nSustained Load (1000 decisions):")
        print(f"  Success rate: {success_rate:.1%}")
        print(f"  Average latency: {avg_latency*1000:.1f}ms")
        print(f"  p95 latency: {p95_latency*1000:.1f}ms")
        print(f"  Errors: {error_count}")
        
        # Validate high success rate
        assert success_rate > 0.95, f"Success rate {success_rate:.1%} is below 95%"
    
    @pytest.mark.load
    def test_cache_performance_under_load(self):
        """Test: Cache hit rate under load."""
        agent = WowVisionPrime(agent_id="cache-test-agent")
        
        # Make same decision 100 times (should be cached)
        context = {
            "decision_type": "repeated",
            "context": {"same": "value"}
        }
        
        first_call_time = None
        subsequent_times = []
        
        for i in range(100):
            start = time.time()
            decision = agent.make_decision(context)
            elapsed = time.time() - start
            
            if i == 0:
                first_call_time = elapsed
            else:
                subsequent_times.append(elapsed)
        
        avg_cached_time = statistics.mean(subsequent_times)
        speedup = first_call_time / avg_cached_time if avg_cached_time > 0 else 0
        
        print(f"\nCache Performance:")
        print(f"  First call: {first_call_time*1000:.1f}ms")
        print(f"  Cached calls average: {avg_cached_time*1000:.3f}ms")
        print(f"  Speedup: {speedup:.1f}x")
        
        # Cached calls should be much faster
        assert avg_cached_time < first_call_time, "Cache not providing speedup"
    
    @pytest.mark.load
    def test_memory_stability_over_1000_operations(self):
        """Test: Memory remains stable over 1000 operations."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        agent = WowVisionPrime(agent_id="memory-test-agent")
        
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run 1000 operations
        for i in range(1000):
            context = {
                "decision_type": "test",
                "context": {"index": i, "data": "x" * 100}
            }
            decision = agent.make_decision(context)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - initial_memory
        
        print(f"\nMemory Stability:")
        print(f"  Initial: {initial_memory:.1f} MB")
        print(f"  Final: {final_memory:.1f} MB")
        print(f"  Growth: {memory_growth:.1f} MB")
        
        # Memory growth should be reasonable (<100MB for 1000 operations)
        assert memory_growth < 100, f"Memory grew by {memory_growth:.1f}MB (potential leak)"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "load"])
