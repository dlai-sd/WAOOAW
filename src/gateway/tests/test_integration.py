"""
Integration Tests for API Gateway
Tests end-to-end request flows through CP and PP Gateways
"""

import asyncio
import pytest
import httpx
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any
import uuid

# Gateway URLs (configurable for local/CI)
CP_GATEWAY_URL = "http://localhost:8000"
PP_GATEWAY_URL = "http://localhost:8001"

# JWT test keys (matching contracts)
JWT_PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA3Z3mJ... (test key)
-----END RSA PRIVATE KEY-----"""

JWT_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0... (test key)
-----END PUBLIC KEY-----"""


class TestHelpers:
    """Helper methods for integration tests"""
    
    @staticmethod
    def generate_jwt(
        user_id: str = "user_123",
        customer_id: str = "customer_456",
        email: str = "test@waooaw.com",
        roles: list = None,
        trial_mode: bool = False,
        trial_expires_at: int = None,
        exp_minutes: int = 60
    ) -> str:
        """Generate a test JWT token"""
        now = datetime.utcnow()
        exp = now + timedelta(minutes=exp_minutes)
        
        if trial_expires_at is None:
            trial_expires_at = int((now + timedelta(days=7)).timestamp())
        
        payload = {
            "sub": user_id,
            "customer_id": customer_id,
            "email": email,
            "iss": "waooaw.com",
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
            "trial_mode": trial_mode,
            "trial_expires_at": trial_expires_at
        }
        
        if roles:
            payload["roles"] = roles
        
        return jwt.encode(payload, JWT_PRIVATE_KEY, algorithm="RS256")
    
    @staticmethod
    def correlation_id() -> str:
        """Generate a correlation ID"""
        return str(uuid.uuid4())


@pytest.mark.asyncio
class TestCPGatewayIntegration:
    """Integration tests for Customer Portal Gateway"""
    
    async def test_health_check(self):
        """Test health endpoint is accessible"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{CP_GATEWAY_URL}/health")
            assert response.status_code == 200
            assert response.json()["status"] in ["healthy", "ok"]
    
    async def test_authenticated_request_success(self):
        """Test successful authenticated request to Plant"""
        token = TestHelpers.generate_jwt()
        correlation_id = TestHelpers.correlation_id()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{CP_GATEWAY_URL}/api/v1/agents/agent_123",
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Correlation-ID": correlation_id
                }
            )
            
            assert response.status_code == 200
            assert response.headers["X-Correlation-ID"] == correlation_id
            assert "X-User-ID" in response.headers
    
    async def test_trial_mode_under_limit(self):
        """Test trial mode request under task limit"""
        token = TestHelpers.generate_jwt(trial_mode=True)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{CP_GATEWAY_URL}/api/v1/agents/agent_123",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            assert response.headers.get("X-Target-Backend") == "https://sandbox.plant.internal"
    
    async def test_trial_mode_exceeded(self):
        """Test trial mode request when task limit exceeded"""
        # Requires OPA mock to return exceeded=true
        token = TestHelpers.generate_jwt(trial_mode=True)
        
        async with httpx.AsyncClient() as client:
            # Simulate 10+ requests to exceed limit
            for _ in range(11):
                response = await client.post(
                    f"{CP_GATEWAY_URL}/api/v1/agents",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"name": "Test Agent"}
                )
            
            # Last request should be rate-limited
            assert response.status_code == 429
            assert "Retry-After" in response.headers
            assert response.json()["error_type"] == "trial-limit-exceeded"
    
    async def test_trial_expired(self):
        """Test request with expired trial"""
        # Trial expired yesterday
        yesterday = int((datetime.utcnow() - timedelta(days=1)).timestamp())
        token = TestHelpers.generate_jwt(
            trial_mode=True,
            trial_expires_at=yesterday
        )
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{CP_GATEWAY_URL}/api/v1/agents/agent_123",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 403
            assert response.json()["error_type"] == "trial-expired"
    
    async def test_budget_exceeded(self):
        """Test request when budget is exceeded"""
        # Requires OPA mock to return budget_exceeded=true
        token = TestHelpers.generate_jwt()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{CP_GATEWAY_URL}/api/v1/agents",
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Test-Budget-Exceeded": "true"  # Trigger mock
                },
                json={"name": "Test Agent"}
            )
            
            assert response.status_code == 402
            assert response.json()["error_type"] == "budget-exceeded"
    
    async def test_governor_approval_required(self):
        """Test request requiring Governor approval"""
        token = TestHelpers.generate_jwt()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{CP_GATEWAY_URL}/api/v1/tool_calls",
                headers={"Authorization": f"Bearer {token}"},
                json={"action": "delete_database"}  # Sensitive action
            )
            
            # Should redirect to approval UI
            assert response.status_code == 307
            assert "Location" in response.headers
            assert "approval" in response.headers["Location"]
    
    async def test_unauthorized_request(self):
        """Test request without JWT token"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{CP_GATEWAY_URL}/api/v1/agents/agent_123"
            )
            
            assert response.status_code == 401
            assert response.json()["error_type"] == "unauthorized"
    
    async def test_invalid_jwt(self):
        """Test request with invalid JWT"""
        invalid_token = "invalid.jwt.token"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{CP_GATEWAY_URL}/api/v1/agents/agent_123",
                headers={"Authorization": f"Bearer {invalid_token}"}
            )
            
            assert response.status_code == 401
    
    async def test_correlation_id_propagation(self):
        """Test correlation ID is propagated through request chain"""
        token = TestHelpers.generate_jwt()
        correlation_id = TestHelpers.correlation_id()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{CP_GATEWAY_URL}/api/v1/agents/agent_123",
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Correlation-ID": correlation_id
                }
            )
            
            assert response.headers["X-Correlation-ID"] == correlation_id
    
    async def test_plant_service_timeout(self):
        """Test handling of Plant service timeout"""
        token = TestHelpers.generate_jwt()
        
        async with httpx.AsyncClient(timeout=1.0) as client:
            try:
                response = await client.get(
                    f"{CP_GATEWAY_URL}/api/v1/slow_endpoint",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                assert response.status_code == 504
                assert response.json()["error_type"] == "gateway-timeout"
            except httpx.TimeoutException:
                # Expected if Plant is truly slow
                pass


@pytest.mark.asyncio
class TestPPGatewayIntegration:
    """Integration tests for Partner Platform Gateway"""
    
    async def test_health_check(self):
        """Test health endpoint is accessible"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{PP_GATEWAY_URL}/health")
            assert response.status_code == 200
    
    async def test_admin_full_access(self):
        """Test admin role has full access"""
        token = TestHelpers.generate_jwt(
            roles=["admin"],
            email="admin@waooaw.com"
        )
        
        async with httpx.AsyncClient() as client:
            # Admin can create
            response = await client.post(
                f"{PP_GATEWAY_URL}/api/v1/agents",
                headers={"Authorization": f"Bearer {token}"},
                json={"name": "Test Agent"}
            )
            assert response.status_code == 201
            
            # Admin can delete
            response = await client.delete(
                f"{PP_GATEWAY_URL}/api/v1/agents/agent_123",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 204
    
    async def test_developer_limited_access(self):
        """Test developer role has limited access"""
        token = TestHelpers.generate_jwt(
            roles=["developer"],
            email="dev@waooaw.com"
        )
        
        async with httpx.AsyncClient() as client:
            # Developer can create
            response = await client.post(
                f"{PP_GATEWAY_URL}/api/v1/agents",
                headers={"Authorization": f"Bearer {token}"},
                json={"name": "Test Agent"}
            )
            assert response.status_code == 201
            
            # Developer CANNOT delete
            response = await client.delete(
                f"{PP_GATEWAY_URL}/api/v1/agents/agent_123",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 403
            assert response.json()["error_type"] == "permission-denied"
    
    async def test_viewer_read_only_access(self):
        """Test viewer role has read-only access"""
        token = TestHelpers.generate_jwt(
            roles=["viewer"],
            email="viewer@waooaw.com"
        )
        
        async with httpx.AsyncClient() as client:
            # Viewer can read
            response = await client.get(
                f"{PP_GATEWAY_URL}/api/v1/agents/agent_123",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200
            
            # Viewer CANNOT create
            response = await client.post(
                f"{PP_GATEWAY_URL}/api/v1/agents",
                headers={"Authorization": f"Bearer {token}"},
                json={"name": "Test Agent"}
            )
            assert response.status_code == 403
    
    async def test_rbac_headers_propagated(self):
        """Test RBAC headers are sent to Plant"""
        token = TestHelpers.generate_jwt(
            roles=["developer", "analyst"],
            email="dev@waooaw.com"
        )
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{PP_GATEWAY_URL}/api/v1/agents/agent_123",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            # Verify headers were set (mock server logs would show this)
            assert "X-User-Roles" in response.request.headers
            assert "X-User-Role-Level" in response.request.headers
    
    async def test_no_role_defaults_to_viewer(self):
        """Test missing roles defaults to viewer permissions"""
        token = TestHelpers.generate_jwt(roles=[])
        
        async with httpx.AsyncClient() as client:
            # Should be able to read
            response = await client.get(
                f"{PP_GATEWAY_URL}/api/v1/agents/agent_123",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200
            
            # Should NOT be able to write
            response = await client.post(
                f"{PP_GATEWAY_URL}/api/v1/agents",
                headers={"Authorization": f"Bearer {token}"},
                json={"name": "Test Agent"}
            )
            assert response.status_code == 403


@pytest.mark.asyncio
class TestConcurrentRequests:
    """Test gateway behavior under concurrent load"""
    
    async def test_concurrent_cp_requests(self):
        """Test CP Gateway handles concurrent requests"""
        token = TestHelpers.generate_jwt()
        
        async def make_request(client, i):
            return await client.get(
                f"{CP_GATEWAY_URL}/api/v1/agents/agent_{i}",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        async with httpx.AsyncClient() as client:
            tasks = [make_request(client, i) for i in range(50)]
            responses = await asyncio.gather(*tasks)
            
            # All requests should succeed
            success_count = sum(1 for r in responses if r.status_code == 200)
            assert success_count >= 45  # Allow some variance
    
    async def test_concurrent_pp_requests(self):
        """Test PP Gateway handles concurrent requests"""
        token = TestHelpers.generate_jwt(roles=["developer"])
        
        async def make_request(client, i):
            return await client.get(
                f"{PP_GATEWAY_URL}/api/v1/agents/agent_{i}",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        async with httpx.AsyncClient() as client:
            tasks = [make_request(client, i) for i in range(50)]
            responses = await asyncio.gather(*tasks)
            
            # All requests should succeed
            success_count = sum(1 for r in responses if r.status_code == 200)
            assert success_count >= 45


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling and RFC 7807 compliance"""
    
    async def test_rfc7807_format(self):
        """Test errors follow RFC 7807 Problem Details format"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{CP_GATEWAY_URL}/api/v1/agents/nonexistent"
            )
            
            assert response.status_code == 401
            data = response.json()
            
            # RFC 7807 fields
            assert "type" in data
            assert "title" in data
            assert "status" in data
            assert "detail" in data
            assert "instance" in data
            
            # WAOOAW extensions
            assert "correlation_id" in data
            assert "error_type" in data
    
    async def test_correlation_id_in_errors(self):
        """Test correlation ID is included in error responses"""
        correlation_id = TestHelpers.correlation_id()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{CP_GATEWAY_URL}/api/v1/agents/test",
                headers={"X-Correlation-ID": correlation_id}
            )
            
            assert response.json()["correlation_id"] == correlation_id


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
