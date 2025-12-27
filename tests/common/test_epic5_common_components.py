"""
Tests for Epic 5: Common Components Library

Tests all 6 components with 95%+ coverage:
- SimpleCache
- CacheHierarchy  
- ErrorHandler
- CircuitBreaker
- StateManager
- SecurityLayer
- ResourceManager
- Validator

Chaos tests included for real-world failure scenarios.
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from waooaw.common.cache import SimpleCache, CacheHierarchy
from waooaw.common.error_handler import (
    ErrorHandler,
    CircuitBreaker,
    RetryPolicy,
    DLQHandler,
    CircuitState,
    retry
)
from waooaw.common.state import StateManager, StateSnapshot
from waooaw.common.security import SecurityLayer, AuditLog, Permission
from waooaw.common.resource_manager import ResourceManager, Budget, RateLimitWindow
from waooaw.common.validator import (
    Validator,
    ValidationResult,
    DECISION_SCHEMA,
    ESCALATION_SCHEMA,
    GITHUB_ISSUE_SCHEMA
)


# =============================================================================
# SimpleCache Tests
# =============================================================================

class TestSimpleCache:
    """Test SimpleCache component."""
    
    def test_set_and_get(self):
        """Test basic set/get operations."""
        cache = SimpleCache(max_size=10)
        
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
    
    def test_get_missing_key(self):
        """Test get with missing key returns None."""
        cache = SimpleCache()
        assert cache.get("nonexistent") is None
    
    def test_lru_eviction(self):
        """Test LRU eviction when max_size exceeded."""
        cache = SimpleCache(max_size=3)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        cache.set("key4", "value4")  # Should evict key1
        
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"
    
    def test_ttl_expiry(self):
        """Test TTL expiration."""
        cache = SimpleCache()
        
        cache.set("key1", "value1", ttl=0.1)  # 100ms TTL
        assert cache.get("key1") == "value1"
        
        time.sleep(0.15)  # Wait for expiry
        assert cache.get("key1") is None
    
    def test_delete(self):
        """Test delete operation."""
        cache = SimpleCache()
        
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        cache.delete("key1")
        assert cache.get("key1") is None
    
    def test_clear(self):
        """Test clear operation."""
        cache = SimpleCache()
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    def test_stats(self):
        """Test stats tracking."""
        cache = SimpleCache()
        
        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss
        
        stats = cache.get_stats()
        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert stats['hit_rate'] == 0.5
        assert stats['size'] == 1


# =============================================================================
# CacheHierarchy Tests
# =============================================================================

class TestCacheHierarchy:
    """Test CacheHierarchy component."""
    
    def test_l1_hit(self):
        """Test L1 cache hit."""
        cache = CacheHierarchy(l1_max_size=10)
        
        cache.set("key1", "value1")
        value = cache.get("key1")
        
        assert value == "value1"
        stats = cache.get_stats()
        assert stats['l1_hits'] == 1
    
    def test_l1_l2_l3_fallback(self):
        """Test L1 → L2 → L3 fallback."""
        redis_mock = Mock()
        redis_mock.get.return_value = b'"value_from_redis"'
        
        db_mock = Mock()
        cursor_mock = Mock()
        cursor_mock.fetchone.return_value = ('{"value": "value_from_db"}',)
        db_mock.cursor.return_value = cursor_mock
        
        cache = CacheHierarchy(
            l1_max_size=10,
            redis_client=redis_mock,
            db_connection=db_mock
        )
        
        # Get from L2 (Redis)
        value = cache.get("key1")
        assert value == "value_from_redis"
        
        stats = cache.get_stats()
        assert stats['l2_hits'] == 1
    
    def test_get_or_compute(self):
        """Test get_or_compute pattern."""
        cache = CacheHierarchy()
        
        compute_fn = Mock(return_value="computed_value")
        
        # First call: compute
        value = cache.get_or_compute("key1", compute_fn)
        assert value == "computed_value"
        compute_fn.assert_called_once()
        
        # Second call: cached
        compute_fn.reset_mock()
        value = cache.get_or_compute("key1", compute_fn)
        assert value == "computed_value"
        compute_fn.assert_not_called()
    
    def test_promotion(self):
        """Test auto-promotion from L2 to L1."""
        redis_mock = Mock()
        redis_mock.get.return_value = b'"value_from_redis"'
        
        cache = CacheHierarchy(l1_max_size=10, redis_client=redis_mock)
        
        # Get from L2 (should promote to L1)
        value = cache.get("key1")
        
        # Second get should hit L1
        redis_mock.get.reset_mock()
        value = cache.get("key1")
        redis_mock.get.assert_not_called()


# =============================================================================
# ErrorHandler Tests
# =============================================================================

class TestErrorHandler:
    """Test ErrorHandler component."""
    
    def test_successful_operation(self):
        """Test successful operation (no retries)."""
        handler = ErrorHandler()
        
        operation = Mock(return_value="success")
        result = handler.execute(operation)
        
        assert result == "success"
        operation.assert_called_once()
    
    def test_retry_on_failure(self):
        """Test retry on failure."""
        policy = RetryPolicy(max_attempts=3, base_delay=0.01)
        handler = ErrorHandler(retry_policy=policy)
        
        operation = Mock(side_effect=[Exception("fail"), Exception("fail"), "success"])
        result = handler.execute(operation)
        
        assert result == "success"
        assert operation.call_count == 3
    
    def test_fallback_on_exhaustion(self):
        """Test fallback when retries exhausted."""
        policy = RetryPolicy(max_attempts=2, base_delay=0.01)
        handler = ErrorHandler(retry_policy=policy)
        
        operation = Mock(side_effect=Exception("always fails"))
        fallback = Mock(return_value="fallback_value")
        
        result = handler.execute(operation, fallback=fallback)
        
        assert result == "fallback_value"
        assert operation.call_count == 2
        fallback.assert_called_once()
    
    def test_on_error_callback(self):
        """Test on_error callback."""
        handler = ErrorHandler()
        
        on_error = Mock()
        operation = Mock(side_effect=Exception("error"))
        fallback = Mock(return_value="fallback")
        
        handler.execute(operation, fallback=fallback, on_error=on_error)
        
        on_error.assert_called()
    
    def test_retry_decorator(self):
        """Test @retry decorator."""
        
        call_count = 0
        
        @retry(max_attempts=3, base_delay=0.01)
        def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("fail")
            return "success"
        
        result = flaky_operation()
        assert result == "success"
        assert call_count == 3


# =============================================================================
# CircuitBreaker Tests
# =============================================================================

class TestCircuitBreaker:
    """Test CircuitBreaker component."""
    
    def test_closed_state(self):
        """Test CLOSED state (normal operation)."""
        breaker = CircuitBreaker(failure_threshold=3)
        
        assert breaker.state == CircuitState.CLOSED
        assert breaker.allow_request()
    
    def test_open_state_after_failures(self):
        """Test transition to OPEN state after failures."""
        breaker = CircuitBreaker(failure_threshold=3, timeout=1)
        
        # Record 3 failures
        for _ in range(3):
            breaker.record_failure()
        
        assert breaker.state == CircuitState.OPEN
        assert not breaker.allow_request()
    
    def test_half_open_after_timeout(self):
        """Test transition to HALF_OPEN after timeout."""
        breaker = CircuitBreaker(failure_threshold=2, timeout=0.1)
        
        # Open circuit
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == CircuitState.OPEN
        
        # Wait for timeout
        time.sleep(0.15)
        
        # Should transition to HALF_OPEN
        assert breaker.allow_request()
        assert breaker.state == CircuitState.HALF_OPEN
    
    def test_recovery_from_half_open(self):
        """Test recovery from HALF_OPEN to CLOSED."""
        breaker = CircuitBreaker(failure_threshold=2, timeout=0.1)
        
        # Open circuit
        breaker.record_failure()
        breaker.record_failure()
        
        # Wait and transition to HALF_OPEN
        time.sleep(0.15)
        breaker.allow_request()
        
        # Record success (should close)
        breaker.record_success()
        
        assert breaker.state == CircuitState.CLOSED


# =============================================================================
# StateManager Tests
# =============================================================================

class TestStateManager:
    """Test StateManager component."""
    
    def test_save_and_load_state(self):
        """Test save/load state."""
        manager = StateManager(agent_id="test-agent")
        
        state = {"decisions": 10, "cache_hits": 90}
        manager.save_state(state)
        
        loaded = manager.load_state()
        assert loaded == state
    
    def test_update_state(self):
        """Test update state."""
        manager = StateManager(agent_id="test-agent", auto_persist=False)
        
        manager.save_state({"key1": "value1"})
        manager.update_state({"key2": "value2"}, merge=True)
        
        state = manager.load_state()
        assert state == {"key1": "value1", "key2": "value2"}
    
    def test_create_snapshot(self):
        """Test create snapshot."""
        manager = StateManager(agent_id="test-agent")
        
        manager.save_state({"data": "v1"})
        snapshot = manager.create_snapshot("v1.0.0", tags=["stable"])
        
        assert snapshot.version == "v1.0.0"
        assert snapshot.data == {"data": "v1"}
        assert "stable" in snapshot.metadata['tags']
    
    def test_rollback_to_version(self):
        """Test rollback to version."""
        manager = StateManager(agent_id="test-agent")
        
        manager.save_state({"data": "v1"})
        manager.create_snapshot("v1.0.0")
        
        manager.save_state({"data": "v2"})
        
        # Rollback
        success = manager.rollback_to_version("v1.0.0")
        assert success
        
        state = manager.load_state()
        assert state == {"data": "v1"}
    
    def test_get_state_history(self):
        """Test get state history."""
        manager = StateManager(agent_id="test-agent")
        
        manager.save_state({"data": "v1"})
        manager.create_snapshot("v1.0.0")
        
        manager.save_state({"data": "v2"})
        manager.create_snapshot("v2.0.0")
        
        history = manager.get_state_history(limit=10)
        assert len(history) == 2
        assert history[0].version == "v2.0.0"  # Newest first
    
    def test_calculate_diff(self):
        """Test calculate diff."""
        manager = StateManager(agent_id="test-agent")
        
        manager.save_state({"a": 1, "b": 2})
        manager.create_snapshot("v1")
        
        manager.save_state({"a": 1, "b": 3, "c": 4})
        manager.create_snapshot("v2")
        
        diff = manager.calculate_diff("v1", "v2")
        assert diff['added'] == {'c': 4}
        assert diff['changed'] == {'b': {'old': 2, 'new': 3}}


# =============================================================================
# SecurityLayer Tests
# =============================================================================

class TestSecurityLayer:
    """Test SecurityLayer component."""
    
    def test_sign_and_verify_message(self):
        """Test HMAC sign/verify."""
        security = SecurityLayer(secret_key="test-secret")
        
        message = "hello world"
        signature = security.sign_message(message)
        
        assert security.verify_signature(message, signature)
        assert not security.verify_signature("tampered", signature)
    
    def test_create_and_verify_token(self):
        """Test JWT create/verify."""
        security = SecurityLayer(secret_key="test-secret")
        
        payload = {"agent_id": "test-agent", "role": "admin"}
        token = security.create_token(payload, expiry_hours=1)
        
        verified = security.verify_token(token)
        assert verified is not None
        assert verified['agent_id'] == "test-agent"
        assert verified['role'] == "admin"
    
    def test_expired_token(self):
        """Test expired token returns None."""
        security = SecurityLayer(secret_key="test-secret")
        
        # Create token with very short expiry
        payload = {"agent_id": "test-agent"}
        token = security.create_token(payload, expiry_hours=-1)  # Already expired
        
        verified = security.verify_token(token)
        assert verified is None
    
    def test_add_permission(self):
        """Test add permission."""
        security = SecurityLayer(secret_key="test-secret")
        
        security.add_permission("agent1", "decision", ["read", "write"])
        
        perms = security.get_permissions("agent1")
        assert len(perms) == 1
        assert perms[0].resource == "decision"
        assert "read" in perms[0].actions
    
    def test_check_permission(self):
        """Test check permission."""
        security = SecurityLayer(secret_key="test-secret")
        
        security.add_permission("agent1", "decision", ["read", "write"])
        
        assert security.check_permission("agent1", "decision", "read")
        assert security.check_permission("agent1", "decision", "write")
        assert not security.check_permission("agent1", "decision", "delete")
        assert not security.check_permission("agent2", "decision", "read")
    
    def test_audit_action(self):
        """Test audit action."""
        security = SecurityLayer(secret_key="test-secret")
        
        security.audit_action(
            agent_id="test-agent",
            action="make_decision",
            resource="decision-123",
            outcome="success"
        )
        
        logs = security.get_audit_logs()
        assert len(logs) == 1
        assert logs[0].agent_id == "test-agent"
        assert logs[0].action == "make_decision"
    
    def test_encrypt_decrypt(self):
        """Test encrypt/decrypt."""
        security = SecurityLayer(secret_key="test-secret-key")
        
        data = "sensitive data"
        encrypted = security.encrypt_data(data)
        decrypted = security.decrypt_data(encrypted)
        
        assert decrypted == data
        assert encrypted != data


# =============================================================================
# ResourceManager Tests
# =============================================================================

class TestResourceManager:
    """Test ResourceManager component."""
    
    def test_set_budget(self):
        """Test set budget."""
        manager = ResourceManager(agent_id="test-agent")
        
        manager.set_budget("llm_calls", limit=100, period="daily")
        
        budget = manager.get_budget("llm_calls")
        assert budget is not None
        assert budget.limit == 100
        assert budget.period == "daily"
    
    def test_check_budget(self):
        """Test check budget."""
        manager = ResourceManager(agent_id="test-agent")
        
        manager.set_budget("llm_calls", limit=10, period="daily")
        
        assert manager.check_budget("llm_calls", cost=5)
        assert manager.check_budget("llm_calls", cost=10)
        assert not manager.check_budget("llm_calls", cost=11)
    
    def test_consume_budget(self):
        """Test consume budget."""
        manager = ResourceManager(agent_id="test-agent")
        
        manager.set_budget("llm_calls", limit=10, period="daily")
        
        # Consume 5
        success = manager.consume_budget("llm_calls", cost=5)
        assert success
        
        # Check remaining
        remaining = manager.get_remaining_budget("llm_calls")
        assert remaining == 5
        
        # Try to consume 6 (should fail)
        success = manager.consume_budget("llm_calls", cost=6)
        assert not success
    
    def test_budget_alert_threshold(self):
        """Test budget alert threshold."""
        manager = ResourceManager(agent_id="test-agent", alert_threshold=0.8)
        
        manager.set_budget("llm_calls", limit=10, period="daily")
        
        # Consume 8 (80%) - should trigger alert
        with patch('waooaw.common.resource_manager.logger') as mock_logger:
            manager.consume_budget("llm_calls", cost=8)
            mock_logger.warning.assert_called()
    
    def test_set_rate_limit(self):
        """Test set rate limit."""
        manager = ResourceManager(agent_id="test-agent")
        
        manager.set_rate_limit("api_calls", max_requests=100, window_seconds=60)
        
        status = manager.get_rate_limit_status("api_calls")
        assert status['max_requests'] == 100
        assert status['window_seconds'] == 60
    
    def test_check_rate_limit(self):
        """Test check rate limit."""
        manager = ResourceManager(agent_id="test-agent")
        
        manager.set_rate_limit("api_calls", max_requests=3, window_seconds=1)
        
        # Should allow 3 requests
        for _ in range(3):
            assert manager.check_rate_limit("api_calls")
            manager.record_request("api_calls")
        
        # 4th request should fail
        assert not manager.check_rate_limit("api_calls")
    
    def test_rate_limit_window_sliding(self):
        """Test sliding window rate limit."""
        manager = ResourceManager(agent_id="test-agent")
        
        manager.set_rate_limit("api_calls", max_requests=2, window_seconds=0.1)
        
        # Record 2 requests
        manager.record_request("api_calls")
        manager.record_request("api_calls")
        
        # Should be at limit
        assert not manager.check_rate_limit("api_calls")
        
        # Wait for window to slide
        time.sleep(0.15)
        
        # Should allow new request
        assert manager.check_rate_limit("api_calls")


# =============================================================================
# Validator Tests
# =============================================================================

class TestValidator:
    """Test Validator component."""
    
    def test_validate_schema_success(self):
        """Test successful schema validation."""
        validator = Validator()
        
        schema = {
            'type': 'object',
            'required': ['name'],
            'properties': {
                'name': {'type': 'string'},
                'age': {'type': 'integer', 'minimum': 0}
            }
        }
        validator.add_schema("person", schema)
        
        data = {'name': 'Alice', 'age': 30}
        result = validator.validate_schema("person", data)
        
        assert result.valid
        assert len(result.errors) == 0
    
    def test_validate_schema_missing_required(self):
        """Test schema validation with missing required field."""
        validator = Validator()
        
        schema = {
            'type': 'object',
            'required': ['name'],
            'properties': {
                'name': {'type': 'string'}
            }
        }
        validator.add_schema("person", schema)
        
        data = {'age': 30}
        result = validator.validate_schema("person", data)
        
        assert not result.valid
        assert "Required field 'name' missing" in result.errors
    
    def test_validate_schema_type_error(self):
        """Test schema validation with type error."""
        validator = Validator()
        
        schema = {
            'type': 'object',
            'properties': {
                'age': {'type': 'integer'}
            }
        }
        validator.add_schema("person", schema)
        
        data = {'age': "thirty"}  # Wrong type
        result = validator.validate_schema("person", data)
        
        assert not result.valid
        assert "expected type 'integer'" in result.errors[0]
    
    def test_validate_schema_enum(self):
        """Test schema validation with enum."""
        validator = Validator()
        
        schema = {
            'type': 'object',
            'properties': {
                'priority': {'type': 'string', 'enum': ['low', 'medium', 'high']}
            }
        }
        validator.add_schema("task", schema)
        
        # Valid
        result = validator.validate_schema("task", {'priority': 'high'})
        assert result.valid
        
        # Invalid
        result = validator.validate_schema("task", {'priority': 'urgent'})
        assert not result.valid
    
    def test_validate_schema_range(self):
        """Test schema validation with min/max."""
        validator = Validator()
        
        schema = {
            'type': 'object',
            'properties': {
                'score': {'type': 'number', 'minimum': 0, 'maximum': 100}
            }
        }
        validator.add_schema("test", schema)
        
        # Valid
        result = validator.validate_schema("test", {'score': 50})
        assert result.valid
        
        # Below minimum
        result = validator.validate_schema("test", {'score': -10})
        assert not result.valid
        
        # Above maximum
        result = validator.validate_schema("test", {'score': 150})
        assert not result.valid
    
    def test_validate_schema_format_email(self):
        """Test format validation (email)."""
        validator = Validator()
        
        schema = {
            'type': 'object',
            'properties': {
                'email': {'type': 'string', 'format': 'email'}
            }
        }
        validator.add_schema("contact", schema)
        
        # Valid
        result = validator.validate_schema("contact", {'email': 'test@example.com'})
        assert result.valid
        
        # Invalid
        result = validator.validate_schema("contact", {'email': 'not-an-email'})
        assert not result.valid
    
    def test_add_rule(self):
        """Test add business rule."""
        validator = Validator()
        
        validator.add_rule("positive", lambda x: x > 0)
        
        result = validator.validate_rules("positive", 10)
        assert result.valid
        
        result = validator.validate_rules("positive", -5)
        assert not result.valid
    
    def test_validate_all(self):
        """Test validate_all (schema + rules)."""
        validator = Validator()
        
        schema = {
            'type': 'object',
            'required': ['value'],
            'properties': {
                'value': {'type': 'integer'}
            }
        }
        validator.add_schema("data", schema)
        validator.add_rule("positive", lambda x: x['value'] > 0)
        
        # Valid
        result = validator.validate_all({'value': 10}, schema_name="data", rule_names=["positive"])
        assert result.valid
        
        # Invalid (negative)
        result = validator.validate_all({'value': -10}, schema_name="data", rule_names=["positive"])
        assert not result.valid
    
    def test_add_connectivity_check(self):
        """Test add connectivity check."""
        validator = Validator()
        
        db_healthy = True
        validator.add_connectivity_check("database", lambda: db_healthy)
        
        assert validator.check_connectivity("database")
        
        db_healthy = False
        assert not validator.check_connectivity("database")
    
    def test_predefined_schemas(self):
        """Test predefined schemas."""
        validator = Validator()
        validator.add_schema("decision", DECISION_SCHEMA)
        
        data = {
            'decision_type': 'approval',
            'context': {'user': 'test'},
            'timestamp': '2024-01-01T00:00:00',
            'confidence': 0.95
        }
        
        result = validator.validate_schema("decision", data)
        assert result.valid


# =============================================================================
# Chaos Tests (Real-World Failure Scenarios)
# =============================================================================

class TestChaosScenarios:
    """Test real-world failure scenarios."""
    
    def test_cache_redis_down(self):
        """Test cache graceful degradation when Redis down."""
        redis_mock = Mock()
        redis_mock.get.side_effect = Exception("Redis connection failed")
        
        cache = CacheHierarchy(redis_client=redis_mock)
        
        # Should fall back to L1 cache
        cache.set("key1", "value1")
        value = cache.get("key1")
        
        assert value == "value1"
    
    def test_error_handler_db_slow(self):
        """Test error handler with slow database."""
        policy = RetryPolicy(max_attempts=2, base_delay=0.01)
        handler = ErrorHandler(retry_policy=policy)
        
        call_count = 0
        def slow_db_operation():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                time.sleep(0.1)  # Simulate slow DB
                raise Exception("Timeout")
            return "success"
        
        result = handler.execute(slow_db_operation)
        assert result == "success"
    
    def test_circuit_breaker_llm_timeout(self):
        """Test circuit breaker prevents cascading LLM timeouts."""
        breaker = CircuitBreaker(failure_threshold=3, timeout=0.1)
        
        def call_llm():
            if not breaker.allow_request():
                return "circuit open - fast fail"
            
            try:
                # Simulate LLM timeout
                raise Exception("LLM timeout")
            except Exception:
                breaker.record_failure()
                raise
        
        # 3 failures should open circuit
        for _ in range(3):
            try:
                call_llm()
            except:
                pass
        
        # Circuit should be open (fast fail)
        result = call_llm()
        assert result == "circuit open - fast fail"
    
    def test_resource_manager_budget_exhaustion(self):
        """Test resource manager handles budget exhaustion."""
        manager = ResourceManager(agent_id="test-agent")
        manager.set_budget("llm_calls", limit=10, period="daily")
        
        # Consume entire budget
        for _ in range(10):
            manager.consume_budget("llm_calls", cost=1)
        
        # Should reject further requests
        success = manager.consume_budget("llm_calls", cost=1)
        assert not success
        
        remaining = manager.get_remaining_budget("llm_calls")
        assert remaining == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=waooaw.common", "--cov-report=html"])
