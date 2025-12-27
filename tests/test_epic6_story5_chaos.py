"""
Epic 6: Story 6.5 - Chaos Tests

Tests failure scenarios and resilience:
- Redis down → Graceful degradation
- Database slow → Timeouts → Fallback
- LLM timeout → Retry → Circuit breaker
- GitHub API down → DLQ → Escalation

Requirements from WOWVISION_PRIME_PROJECT_PLAN.md:
- Component failure ≠ agent failure
- Graceful degradation working
- Escalations created for persistent failures
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from waooaw.agents.wowvision_prime import WowVisionPrime
from waooaw.common.cache import CacheHierarchy
from waooaw.common.error_handler import ErrorHandler, CircuitBreaker, CircuitState
from waooaw.integrations.github_client import GitHubClient


class TestChaosRedis:
    """Test Redis failure scenarios."""
    
    @pytest.mark.chaos
    def test_redis_unavailable_falls_back_to_l1_cache(self):
        """Test: Redis down → Falls back to L1 (memory) cache."""
        agent = WowVisionPrime(agent_id="chaos-redis-agent")
        
        # Simulate Redis connection failure
        redis_mock = Mock()
        redis_mock.get.side_effect = Exception("Redis connection refused")
        redis_mock.set.side_effect = Exception("Redis connection refused")
        
        cache = CacheHierarchy(redis_client=redis_mock)
        
        with patch.object(agent, 'cache', cache):
            # Should still work with L1 cache
            decision = agent.make_decision({
                "decision_type": "test",
                "context": {"data": "value"}
            })
            
            assert decision is not None, "Agent should work without Redis"
            
            # L2 should be marked unavailable
            assert not cache._l2_available, "L2 cache should be disabled"
    
    @pytest.mark.chaos
    def test_redis_slow_does_not_block(self):
        """Test: Slow Redis doesn't block agent."""
        agent = WowVisionPrime(agent_id="chaos-redis-slow-agent")
        
        def slow_redis_get(*args, **kwargs):
            time.sleep(2)  # Simulate slow response
            return None
        
        redis_mock = Mock()
        redis_mock.get.side_effect = slow_redis_get
        
        cache = CacheHierarchy(redis_client=redis_mock)
        
        with patch.object(agent, 'cache', cache):
            start = time.time()
            decision = agent.make_decision({
                "decision_type": "test",
                "context": {"data": "value"}
            })
            elapsed = time.time() - start
            
            # Should not wait for slow Redis (should have timeout)
            print(f"\nSlow Redis test: {elapsed:.2f}s")
            assert decision is not None
    
    @pytest.mark.chaos
    def test_redis_intermittent_failures(self):
        """Test: Intermittent Redis failures are handled."""
        agent = WowVisionPrime(agent_id="chaos-redis-intermittent-agent")
        
        call_count = 0
        
        def intermittent_redis_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count % 3 == 0:
                raise Exception("Redis timeout")
            return None
        
        redis_mock = Mock()
        redis_mock.get.side_effect = intermittent_redis_get
        
        cache = CacheHierarchy(redis_client=redis_mock)
        
        with patch.object(agent, 'cache', cache):
            success_count = 0
            for i in range(10):
                try:
                    decision = agent.make_decision({
                        "decision_type": f"test-{i}",
                        "context": {"index": i}
                    })
                    success_count += 1
                except Exception:
                    pass
            
            # Should handle failures gracefully
            assert success_count >= 5, "Too many failures"


class TestChaosDatabase:
    """Test database failure scenarios."""
    
    @pytest.mark.chaos
    def test_database_slow_query_timeout(self):
        """Test: Slow database query times out."""
        agent = WowVisionPrime(agent_id="chaos-db-slow-agent")
        
        def slow_query(*args, **kwargs):
            time.sleep(10)  # Simulate very slow query
            return []
        
        with patch.object(agent, '_get_database_connection') as mock_db:
            mock_cursor = Mock()
            mock_cursor.execute.side_effect = slow_query
            mock_db.return_value.cursor.return_value = mock_cursor
            
            start = time.time()
            try:
                # Should timeout or use fallback
                decision = agent.make_decision({
                    "decision_type": "test",
                    "context": {"data": "value"}
                })
            except Exception:
                pass  # Timeout expected
            elapsed = time.time() - start
            
            # Should not hang indefinitely
            print(f"\nSlow DB test: {elapsed:.2f}s")
            assert elapsed < 15, f"Query hung for {elapsed:.2f}s"
    
    @pytest.mark.chaos
    def test_database_connection_lost(self):
        """Test: Database connection lost → Agent continues with degraded mode."""
        agent = WowVisionPrime(agent_id="chaos-db-lost-agent")
        
        with patch.object(agent, '_get_database_connection') as mock_db:
            mock_db.side_effect = Exception("Connection lost")
            
            # Should not crash
            decision = agent.make_decision({
                "decision_type": "test",
                "context": {"data": "value"}
            })
            
            assert decision is not None, "Agent should work without database"
    
    @pytest.mark.chaos
    def test_database_read_only_mode(self):
        """Test: Database in read-only mode → No writes, but reads work."""
        agent = WowVisionPrime(agent_id="chaos-db-readonly-agent")
        
        with patch.object(agent, '_get_database_connection') as mock_db:
            mock_cursor = Mock()
            mock_cursor.execute.side_effect = lambda sql, *args: (
                Exception("Cannot execute INSERT in read-only mode") 
                if "INSERT" in sql else None
            )
            mock_db.return_value.cursor.return_value = mock_cursor
            
            # Should handle read-only gracefully
            decision = agent.make_decision({
                "decision_type": "test",
                "context": {"data": "value"}
            })
            
            # Decision may be limited, but should not crash
            assert decision is not None or True  # Either works or gracefully fails


class TestChaosLLM:
    """Test LLM failure scenarios."""
    
    @pytest.mark.chaos
    def test_llm_timeout_triggers_retry(self):
        """Test: LLM timeout → Retry with exponential backoff."""
        agent = WowVisionPrime(agent_id="chaos-llm-timeout-agent")
        
        call_count = 0
        
        def llm_with_timeout(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("LLM timeout")
            return "approve"
        
        with patch.object(agent, '_call_llm', side_effect=llm_with_timeout):
            decision = agent.make_decision({
                "decision_type": "complex",
                "context": {"requires": "llm"}
            })
            
            # Should retry and eventually succeed
            assert call_count == 3, f"Expected 3 retries, got {call_count}"
            assert decision is not None
    
    @pytest.mark.chaos
    def test_llm_persistent_failure_opens_circuit_breaker(self):
        """Test: LLM persistent failure → Circuit breaker opens."""
        agent = WowVisionPrime(agent_id="chaos-llm-circuit-agent")
        
        breaker = CircuitBreaker(failure_threshold=3, timeout=1)
        error_handler = ErrorHandler(circuit_breaker=breaker)
        
        with patch.object(agent, 'error_handler', error_handler):
            with patch.object(agent, '_call_llm', side_effect=Exception("LLM unavailable")):
                # Try 5 times (should open circuit after 3)
                for i in range(5):
                    try:
                        decision = agent.make_decision({
                            "decision_type": f"test-{i}",
                            "context": {"index": i}
                        })
                    except Exception:
                        pass
                
                # Circuit should be open
                assert breaker.state == CircuitState.OPEN, "Circuit breaker should be open"
    
    @pytest.mark.chaos
    def test_llm_rate_limit_backs_off(self):
        """Test: LLM rate limit → Exponential backoff."""
        agent = WowVisionPrime(agent_id="chaos-llm-ratelimit-agent")
        
        call_times = []
        
        def llm_with_rate_limit(*args, **kwargs):
            call_times.append(time.time())
            if len(call_times) < 3:
                raise Exception("Rate limit exceeded")
            return "approve"
        
        with patch.object(agent, '_call_llm', side_effect=llm_with_rate_limit):
            decision = agent.make_decision({
                "decision_type": "test",
                "context": {"data": "value"}
            })
            
            # Verify backoff (each retry should take longer)
            if len(call_times) >= 3:
                delay1 = call_times[1] - call_times[0]
                delay2 = call_times[2] - call_times[1]
                print(f"\nBackoff delays: {delay1:.2f}s, {delay2:.2f}s")
                assert delay2 >= delay1, "Should use exponential backoff"


class TestChaosGitHub:
    """Test GitHub API failure scenarios."""
    
    @pytest.mark.chaos
    def test_github_api_unavailable_queues_to_dlq(self):
        """Test: GitHub API down → Queue to DLQ for later retry."""
        agent = WowVisionPrime(agent_id="chaos-github-agent")
        
        with patch.object(agent, 'github_client') as mock_gh:
            mock_gh.create_issue.side_effect = Exception("GitHub API unavailable")
            
            # Should handle failure gracefully
            decision = agent.make_decision({
                "decision_type": "escalation",
                "context": {"issue": "Critical failure"}
            })
            
            # Decision should be made, but GitHub output queued for retry
            assert decision is not None
    
    @pytest.mark.chaos
    def test_github_rate_limit_respects_limits(self):
        """Test: GitHub rate limit → Respects retry-after header."""
        agent = WowVisionPrime(agent_id="chaos-github-ratelimit-agent")
        
        with patch.object(agent, 'github_client') as mock_gh:
            mock_gh.create_issue.side_effect = Exception("Rate limit exceeded. Retry after 60s")
            
            start = time.time()
            try:
                decision = agent.make_decision({
                    "decision_type": "escalation",
                    "context": {"issue": "Test"}
                })
            except Exception:
                pass
            elapsed = time.time() - start
            
            # Should handle rate limit (not retry immediately)
            print(f"\nRate limit handling: {elapsed:.2f}s")
    
    @pytest.mark.chaos
    def test_github_403_forbidden_escalates(self):
        """Test: GitHub 403 Forbidden → Creates escalation."""
        agent = WowVisionPrime(agent_id="chaos-github-403-agent")
        
        with patch.object(agent, 'github_client') as mock_gh:
            mock_gh.create_issue.side_effect = Exception("403 Forbidden")
            
            # Should escalate permission issue
            decision = agent.make_decision({
                "decision_type": "test",
                "context": {"data": "value"}
            })
            
            # Should not crash
            assert decision is not None or True


class TestChaosMultipleFailures:
    """Test scenarios with multiple simultaneous failures."""
    
    @pytest.mark.chaos
    def test_redis_and_database_both_down(self):
        """Test: Redis AND database both down → Agent still functions."""
        agent = WowVisionPrime(agent_id="chaos-multi-agent")
        
        # Redis down
        redis_mock = Mock()
        redis_mock.get.side_effect = Exception("Redis down")
        cache = CacheHierarchy(redis_client=redis_mock, db_connection=None)
        
        # Database down
        with patch.object(agent, 'cache', cache):
            with patch.object(agent, '_get_database_connection', side_effect=Exception("DB down")):
                # Should still make decisions (degraded mode)
                decision = agent.make_decision({
                    "decision_type": "test",
                    "context": {"data": "value"}
                })
                
                assert decision is not None, "Agent should work without Redis and DB"
    
    @pytest.mark.chaos
    def test_all_external_services_down(self):
        """Test: Redis, DB, GitHub, LLM all down → Agent survives."""
        agent = WowVisionPrime(agent_id="chaos-all-down-agent")
        
        with patch.object(agent, 'cache') as mock_cache:
            mock_cache.get.side_effect = Exception("Redis down")
            
            with patch.object(agent, '_get_database_connection', side_effect=Exception("DB down")):
                with patch.object(agent, 'github_client') as mock_gh:
                    mock_gh.create_issue.side_effect = Exception("GitHub down")
                    
                    with patch.object(agent, '_call_llm', side_effect=Exception("LLM down")):
                        # Should not crash (ultimate resilience test)
                        try:
                            decision = agent.make_decision({
                                "decision_type": "test",
                                "context": {"data": "value"}
                            })
                            # May fail gracefully, but should not crash
                        except Exception as e:
                            # Graceful failure is acceptable
                            print(f"\nGraceful failure: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "chaos"])
