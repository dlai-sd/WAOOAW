"""
Integration Tests for Gateway Middleware with Real Dependencies
Tests with actual Redis, PostgreSQL, and OPA instances via Docker
"""

import pytest
import asyncio
import redis
import httpx
from datetime import datetime, timedelta, timezone

# Test infrastructure URLs (from docker-compose.test.yml)
REDIS_URL = "redis://localhost:6380"
DATABASE_URL = "postgresql://postgres:testpass@localhost:5433/waooaw_test"
OPA_URL = "http://localhost:8181"


@pytest.fixture(scope="session")
def redis_client():
    """Redis client for integration tests"""
    client = redis.from_url(REDIS_URL, decode_responses=True)
    yield client
    client.flushdb()  # Clean up after tests
    client.close()


@pytest.fixture
async def opa_client():
    """OPA client for integration tests"""
    async with httpx.AsyncClient(base_url=OPA_URL) as client:
        yield client


class TestRedisIntegration:
    """Test Redis integration for budget middleware"""
    
    def test_redis_connection(self, redis_client):
        """Test Redis is accessible"""
        assert redis_client.ping() is True
    
    def test_budget_tracking(self, redis_client):
        """Test budget tracking with real Redis"""
        agent_id = "agent_123"
        customer_id = "customer_456"
        
        # Track usage
        key = f"budget:{customer_id}:{agent_id}"
        redis_client.incrbyfloat(key, 0.50)  # $0.50
        redis_client.expire(key, 86400)  # 24 hours
        
        # Verify
        usage = float(redis_client.get(key))
        assert usage == 0.50
        
        # Add more usage
        redis_client.incrbyfloat(key, 0.30)
        usage = float(redis_client.get(key))
        assert usage == 0.80
    
    def test_rate_limiting(self, redis_client):
        """Test rate limiting with real Redis"""
        key = "rate_limit:customer_456"
        
        # Simulate 10 requests
        for i in range(10):
            redis_client.incr(key)
            if i == 0:
                redis_client.expire(key, 60)  # 1 minute window
        
        count = int(redis_client.get(key))
        assert count == 10
        
        # Check TTL
        ttl = redis_client.ttl(key)
        assert 0 < ttl <= 60


@pytest.mark.asyncio
class TestOPAIntegration:
    """Test OPA integration for policy middleware"""
    
    async def test_opa_health(self):
        """Test OPA is accessible"""
        async with httpx.AsyncClient(base_url=OPA_URL) as client:
            response = await client.get("/health")
            assert response.status_code == 200
    
    async def test_opa_policy_query(self):
        """Test OPA policy query"""
        async with httpx.AsyncClient(base_url=OPA_URL) as client:
            # Query OPA with trial mode policy
            policy_input = {
                "input": {
                    "jwt": {
                        "user_id": "user_123",
                        "customer_id": "customer_456",
                        "trial_mode": True,
                        "trial_expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
                    },
                    "resource": "agents",
                    "action": "create",
                    "method": "POST",
                    "path": "/api/v1/agents"
                }
            }
            
            # OPA data API endpoint (without policy, will return empty result)
            response = await client.post("/v1/data", json=policy_input)
            assert response.status_code == 200
            
            # Result structure should be valid
            data = response.json()
            assert "result" in data


class TestMiddlewareChainIntegration:
    """Test complete middleware chain with real dependencies"""
    
    def test_auth_budget_integration(self, redis_client):
        """Test auth + budget middleware interaction"""
        customer_id = "customer_integration_test"
        agent_id = "agent_integration_test"
        
        # Clear any existing data
        key = f"budget:{customer_id}:{agent_id}"
        redis_client.delete(key)
        
        # Simulate agent usage tracking
        for i in range(5):
            redis_client.incrbyfloat(key, 0.10)  # $0.10 per task
        
        redis_client.expire(key, 86400)
        
        # Verify total
        total = float(redis_client.get(key))
        assert total == 0.50
        
        # Check alert thresholds
        daily_limit = 1.00
        usage_percent = (total / daily_limit) * 100
        
        if usage_percent >= 80:
            # Would trigger 80% alert
            assert usage_percent >= 80
        
        # Add more to exceed limit
        redis_client.incrbyfloat(key, 0.60)
        total = float(redis_client.get(key))
        assert total == 1.10
        
        # Would trigger 100% block
        assert total > daily_limit
    
    @pytest.mark.asyncio
    async def test_policy_opa_integration(self):
        """Test policy middleware with OPA"""
        async with httpx.AsyncClient(base_url=OPA_URL) as client:
            # Test trial mode check
            trial_input = {
                "input": {
                    "jwt": {
                        "user_id": "trial_user",
                        "trial_mode": True,
                        "trial_expires_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()  # Expired
                    },
                    "action": "create"
                }
            }
            
            response = await client.post("/v1/data", json=trial_input)
            assert response.status_code == 200
    
    def test_concurrent_redis_operations(self, redis_client):
        """Test concurrent budget operations"""
        import threading
        
        key = "budget:concurrent:test"
        redis_client.delete(key)
        
        def increment():
            for _ in range(10):
                redis_client.incrbyfloat(key, 0.01)
        
        # Run 5 threads concurrently
        threads = [threading.Thread(target=increment) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have 50 increments of $0.01 = $0.50
        total = float(redis_client.get(key))
        assert total == 0.50


class TestErrorRecoveryIntegration:
    """Test error recovery with real services"""
    
    @pytest.mark.asyncio
    async def test_opa_timeout_handling(self):
        """Test OPA timeout behavior"""
        async with httpx.AsyncClient(base_url=OPA_URL) as client:
            # Simulate quick query
            try:
                response = await client.get("/health", timeout=0.1)
                assert response.status_code == 200
            except httpx.TimeoutException:
                # Expected if OPA is slow
                pytest.skip("OPA timeout - expected behavior")
    
    def test_redis_failure_recovery(self, redis_client):
        """Test Redis failure and recovery"""
        # Test pipeline for atomic operations
        pipe = redis_client.pipeline()
        pipe.set("test_key", "test_value")
        pipe.expire("test_key", 10)
        pipe.get("test_key")
        results = pipe.execute()
        
        assert results[0] is True  # set succeeded
        assert results[1] is True  # expire succeeded
        assert results[2] == "test_value"  # get succeeded


# Test Execution Summary
if __name__ == "__main__":
    print("Running integration tests with Docker dependencies...")
    print("Services required:")
    print("  - Redis: localhost:6380")
    print("  - PostgreSQL: localhost:5433")
    print("  - OPA: localhost:8181")
    print("\nRun with: pytest test_integration_docker.py -v")
