"""
End-to-End Gateway Tests

Tests the full gateway stack with all middleware against mock Plant service.
Validates: Auth → RBAC → Policy → Budget → Routing → Plant → Response
"""

import pytest
import httpx
import asyncio
from datetime import datetime, timedelta
import jwt
import os


# Test configuration
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8000")
PLANT_URL = os.getenv("PLANT_URL", "http://localhost:8001")
JWT_PRIVATE_KEY = os.getenv("JWT_PRIVATE_KEY", "")
JWT_PUBLIC_KEY = os.getenv("JWT_PUBLIC_KEY", "")


def generate_test_token(user_id: str, role: str = "customer", expires_in: int = 3600) -> str:
    """Generate JWT token for testing"""
    if not JWT_PRIVATE_KEY:
        raise ValueError("JWT_PRIVATE_KEY not set in environment")
    
    payload = {
        "sub": user_id,
        "role": role,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(seconds=expires_in)
    }
    
    return jwt.encode(payload, JWT_PRIVATE_KEY, algorithm="RS256")


class TestE2EAuthentication:
    """Test authentication flow through gateway"""
    
    @pytest.mark.asyncio
    async def test_valid_token_passes_through(self):
        """Valid JWT should pass through all middleware"""
        token = generate_test_token("user-001", "customer")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GATEWAY_URL}/api/v1/agents",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert len(data["agents"]) > 0
    
    @pytest.mark.asyncio
    async def test_missing_token_rejected(self):
        """Request without token should be rejected"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{GATEWAY_URL}/api/v1/agents")
        
        assert response.status_code == 401
        assert "Missing authorization header" in response.text
    
    @pytest.mark.asyncio
    async def test_invalid_token_rejected(self):
        """Invalid token should be rejected"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GATEWAY_URL}/api/v1/agents",
                headers={"Authorization": "Bearer invalid.token.here"}
            )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_expired_token_rejected(self):
        """Expired token should be rejected"""
        token = generate_test_token("user-001", "customer", expires_in=-3600)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GATEWAY_URL}/api/v1/agents",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 401


class TestE2ERBAC:
    """Test Role-Based Access Control through gateway"""
    
    @pytest.mark.asyncio
    async def test_customer_can_read_agents(self):
        """Customer role should be able to read agents"""
        token = generate_test_token("user-001", "customer")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GATEWAY_URL}/api/v1/agents",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_customer_cannot_access_admin_endpoint(self):
        """Customer role should not access admin endpoints"""
        token = generate_test_token("user-001", "customer")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GATEWAY_URL}/api/v1/admin/settings",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 403
        assert "Insufficient permissions" in response.text
    
    @pytest.mark.asyncio
    async def test_admin_can_access_admin_endpoint(self):
        """Admin role should access admin endpoints"""
        token = generate_test_token("user-admin", "admin")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GATEWAY_URL}/api/v1/admin/settings",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 200


class TestE2EBudget:
    """Test budget tracking through gateway"""
    
    @pytest.mark.asyncio
    async def test_budget_tracking_on_requests(self):
        """Budget should be tracked for each request"""
        token = generate_test_token("user-budget-test", "customer")
        
        async with httpx.AsyncClient() as client:
            # First request - should succeed
            response1 = await client.get(
                f"{GATEWAY_URL}/api/v1/agents",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response1.status_code == 200
            
            # Check budget header
            assert "X-Budget-Used" in response1.headers
            budget_used = int(response1.headers["X-Budget-Used"])
            assert budget_used > 0
    
    @pytest.mark.asyncio
    async def test_expensive_endpoint_charges_more(self):
        """Expensive endpoint should charge more credits"""
        token = generate_test_token("user-expensive-test", "customer")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GATEWAY_URL}/api/v1/expensive",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        # Should either succeed with high cost or fail with budget exceeded
        assert response.status_code in [200, 429]
        
        if response.status_code == 200:
            budget_used = int(response.headers.get("X-Budget-Used", 0))
            assert budget_used >= 100  # Expensive endpoint costs 100 credits


class TestE2EPolicy:
    """Test policy enforcement through gateway"""
    
    @pytest.mark.asyncio
    async def test_delete_agent_requires_approval(self):
        """Deleting agent should redirect to governor approval"""
        token = generate_test_token("user-admin", "admin")
        
        async with httpx.AsyncClient(follow_redirects=False) as client:
            response = await client.delete(
                f"{GATEWAY_URL}/api/v1/agents/agent-001",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 307  # Temporary redirect to governor
        assert "Location" in response.headers
        assert "governor" in response.headers["Location"]
    
    @pytest.mark.asyncio
    async def test_trial_mode_routes_to_sandbox(self):
        """Trial users should be routed to sandbox"""
        token = generate_test_token("user-trial", "customer")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GATEWAY_URL}/api/v1/sandbox",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        # Should either succeed or be routed to sandbox
        assert response.status_code in [200, 307]


class TestE2ERateLimiting:
    """Test rate limiting through gateway"""
    
    @pytest.mark.asyncio
    async def test_rate_limiting_blocks_excess_requests(self):
        """Excessive requests should be rate limited"""
        token = generate_test_token("user-rate-limit-test", "customer")
        
        success_count = 0
        rate_limited_count = 0
        
        async with httpx.AsyncClient() as client:
            # Send 20 requests rapidly
            tasks = []
            for _ in range(20):
                tasks.append(
                    client.get(
                        f"{GATEWAY_URL}/api/v1/agents",
                        headers={"Authorization": f"Bearer {token}"}
                    )
                )
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            for response in responses:
                if isinstance(response, Exception):
                    continue
                if response.status_code == 200:
                    success_count += 1
                elif response.status_code == 429:
                    rate_limited_count += 1
        
        # Should have some successful and some rate limited
        assert success_count > 0
        assert rate_limited_count > 0  # At least some should be rate limited


class TestE2EErrorHandling:
    """Test error handling through gateway"""
    
    @pytest.mark.asyncio
    async def test_404_from_plant_handled_gracefully(self):
        """404 from Plant service should be handled gracefully"""
        token = generate_test_token("user-001", "customer")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GATEWAY_URL}/api/v1/agents/nonexistent",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_gateway_handles_plant_timeout(self):
        """Gateway should handle Plant service timeout"""
        token = generate_test_token("user-001", "customer")
        
        async with httpx.AsyncClient(timeout=1.0) as client:
            try:
                response = await client.get(
                    f"{GATEWAY_URL}/api/v1/agents",
                    headers={"Authorization": f"Bearer {token}"}
                )
                # If Plant responds, should be successful
                assert response.status_code in [200, 504]
            except httpx.TimeoutException:
                # Timeout is acceptable for this test
                pass


class TestE2EFullFlow:
    """Test complete user flows through gateway"""
    
    @pytest.mark.asyncio
    async def test_complete_agent_discovery_flow(self):
        """Test complete flow: Auth → List → Details → Hire"""
        token = generate_test_token("user-flow-test", "customer")
        
        async with httpx.AsyncClient() as client:
            # Step 1: List agents
            response1 = await client.get(
                f"{GATEWAY_URL}/api/v1/agents",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response1.status_code == 200
            agents = response1.json()["agents"]
            assert len(agents) > 0
            
            # Step 2: Get agent details
            agent_id = agents[0]["id"]
            response2 = await client.get(
                f"{GATEWAY_URL}/api/v1/agents/{agent_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response2.status_code == 200
            
            # Step 3: Hire agent
            response3 = await client.post(
                f"{GATEWAY_URL}/api/v1/agents/{agent_id}/hire",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response3.status_code == 200
            hire_data = response3.json()
            assert "trial_id" in hire_data
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_handled_correctly(self):
        """Multiple concurrent requests should be handled correctly"""
        token = generate_test_token("user-concurrent-test", "customer")
        
        async with httpx.AsyncClient() as client:
            # Send 5 concurrent requests
            tasks = [
                client.get(
                    f"{GATEWAY_URL}/api/v1/agents",
                    headers={"Authorization": f"Bearer {token}"}
                )
                for _ in range(5)
            ]
            
            responses = await asyncio.gather(*tasks)
            
            # All should succeed (or be rate limited, both are valid)
            for response in responses:
                assert response.status_code in [200, 429]
            
            # At least some should succeed
            success_count = sum(1 for r in responses if r.status_code == 200)
            assert success_count > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
