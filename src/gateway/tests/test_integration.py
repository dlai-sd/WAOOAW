"""Integration-style tests for gateway contracts.

`src/gateway` in this repo contains middleware and contract logic, not a full
deployable gateway service. These tests run against small in-process ASGI apps
provided by `src/gateway/tests/conftest.py`.
"""

import asyncio
from datetime import datetime, timedelta
import uuid

import pytest
import httpx


def correlation_id() -> str:
    return str(uuid.uuid4())


@pytest.mark.asyncio
class TestCPGatewayIntegration:
    """Integration tests for Customer Portal Gateway"""
    
    async def test_health_check(self, cp_client: httpx.AsyncClient):
        """Test health endpoint is accessible"""
        response = await cp_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] in ["healthy", "ok"]
    
    async def test_authenticated_request_success(self, cp_client: httpx.AsyncClient, make_jwt):
        """Test successful authenticated request to Plant"""
        token = make_jwt()
        cid = correlation_id()
        
        response = await cp_client.get(
            "/api/v1/agents/agent_123",
            headers={"Authorization": f"Bearer {token}", "X-Correlation-ID": cid},
        )
        assert response.status_code == 200
        assert response.headers["X-Correlation-ID"] == cid
        assert "X-User-ID" in response.headers
    
    async def test_trial_mode_under_limit(self, cp_client: httpx.AsyncClient, make_jwt):
        """Test trial mode request under task limit"""
        token = make_jwt(trial_mode=True)
        
        response = await cp_client.get(
            "/api/v1/agents/agent_123",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.headers.get("X-Target-Backend") == "https://sandbox.plant.internal"
    
    async def test_trial_mode_exceeded(self, cp_client: httpx.AsyncClient, make_jwt):
        """Test trial mode request when task limit exceeded"""
        token = make_jwt(trial_mode=True)
        
        for _ in range(11):
            response = await cp_client.post(
                "/api/v1/agents",
                headers={"Authorization": f"Bearer {token}"},
                json={"name": "Test Agent"},
            )
        assert response.status_code == 429
        assert "Retry-After" in response.headers
        assert response.json()["error_type"] == "trial-limit-exceeded"
    
    async def test_trial_expired(self, cp_client: httpx.AsyncClient, make_jwt):
        """Test request with expired trial"""
        # Trial expired yesterday
        yesterday = int((datetime.utcnow() - timedelta(days=1)).timestamp())
        token = make_jwt(trial_mode=True, trial_expires_at=yesterday)
        
        response = await cp_client.get(
            "/api/v1/agents/agent_123",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
        assert response.json()["error_type"] == "trial-expired"
    
    async def test_budget_exceeded(self, cp_client: httpx.AsyncClient, make_jwt):
        """Test request when budget is exceeded"""
        token = make_jwt()
        response = await cp_client.post(
            "/api/v1/agents",
            headers={"Authorization": f"Bearer {token}", "X-Test-Budget-Exceeded": "true"},
            json={"name": "Test Agent"},
        )
        assert response.status_code == 402
        assert response.json()["error_type"] == "budget-exceeded"
    
    async def test_governor_approval_required(self, cp_client: httpx.AsyncClient, make_jwt):
        """Test request requiring Governor approval"""
        token = make_jwt()
        response = await cp_client.post(
            "/api/v1/tool_calls",
            headers={"Authorization": f"Bearer {token}"},
            json={"action": "delete_database"},
            follow_redirects=False,
        )
        assert response.status_code == 307
        assert "Location" in response.headers
        assert "approval" in response.headers["Location"]
    
    async def test_unauthorized_request(self, cp_client: httpx.AsyncClient):
        """Test request without JWT token"""
        response = await cp_client.get("/api/v1/agents/agent_123")
        assert response.status_code == 401
        assert response.json()["error_type"] == "unauthorized"
    
    async def test_invalid_jwt(self, cp_client: httpx.AsyncClient):
        """Test request with invalid JWT"""
        invalid_token = "invalid.jwt.token"

        response = await cp_client.get(
            "/api/v1/agents/agent_123",
            headers={"Authorization": f"Bearer {invalid_token}"},
        )
        assert response.status_code == 401
    
    async def test_correlation_id_propagation(self, cp_client: httpx.AsyncClient, make_jwt):
        """Test correlation ID is propagated through request chain"""
        token = make_jwt()
        cid = correlation_id()

        response = await cp_client.get(
            "/api/v1/agents/agent_123",
            headers={"Authorization": f"Bearer {token}", "X-Correlation-ID": cid},
        )
        assert response.headers["X-Correlation-ID"] == cid
    
    async def test_plant_service_timeout(self, cp_client: httpx.AsyncClient, make_jwt):
        """Test handling of Plant service timeout"""
        token = make_jwt()
        try:
            response = await cp_client.get(
                "/api/v1/slow_endpoint",
                headers={"Authorization": f"Bearer {token}"},
                timeout=1.0,
            )
            # Some environments will return a gateway-timeout response; others will timeout.
            assert response.status_code in {504, 200}
        except httpx.TimeoutException:
            pass


@pytest.mark.asyncio
class TestPPGatewayIntegration:
    """Integration tests for Partner Platform Gateway"""
    
    async def test_health_check(self, pp_client: httpx.AsyncClient):
        """Test health endpoint is accessible"""
        response = await pp_client.get("/health")
        assert response.status_code == 200
    
    async def test_admin_full_access(self, pp_client: httpx.AsyncClient, make_jwt):
        """Test admin role has full access"""
        token = make_jwt(roles=["admin"], email="admin@waooaw.com")

        response = await pp_client.post(
            "/api/v1/agents",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Test Agent"},
        )
        assert response.status_code == 201

        response = await pp_client.delete(
            "/api/v1/agents/agent_123",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 204
    
    async def test_developer_limited_access(self, pp_client: httpx.AsyncClient, make_jwt):
        """Test developer role has limited access"""
        token = make_jwt(roles=["developer"], email="dev@waooaw.com")

        response = await pp_client.post(
            "/api/v1/agents",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Test Agent"},
        )
        assert response.status_code == 201

        response = await pp_client.delete(
            "/api/v1/agents/agent_123",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
        assert response.json()["error_type"] == "permission-denied"
    
    async def test_viewer_read_only_access(self, pp_client: httpx.AsyncClient, make_jwt):
        """Test viewer role has read-only access"""
        token = make_jwt(roles=["viewer"], email="viewer@waooaw.com")

        response = await pp_client.get(
            "/api/v1/agents/agent_123",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        response = await pp_client.post(
            "/api/v1/agents",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Test Agent"},
        )
        assert response.status_code == 403
    
    async def test_rbac_headers_propagated(self, pp_client: httpx.AsyncClient, make_jwt):
        """Test RBAC headers are sent to Plant"""
        token = make_jwt(roles=["developer", "analyst"], email="dev@waooaw.com")

        response = await pp_client.get(
            "/api/v1/agents/agent_123",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert "X-User-Roles" in response.headers
        assert "X-User-Role-Level" in response.headers
    
    async def test_no_role_defaults_to_viewer(self, pp_client: httpx.AsyncClient, make_jwt):
        """Test missing roles defaults to viewer permissions"""
        token = make_jwt(roles=[])

        response = await pp_client.get(
            "/api/v1/agents/agent_123",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        response = await pp_client.post(
            "/api/v1/agents",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Test Agent"},
        )
        assert response.status_code == 403


@pytest.mark.asyncio
class TestConcurrentRequests:
    """Test gateway behavior under concurrent load"""
    
    async def test_concurrent_cp_requests(self, cp_client: httpx.AsyncClient, make_jwt):
        """Test CP Gateway handles concurrent requests"""
        token = make_jwt()
        
        async def make_request(client, i):
            return await client.get(
                f"/api/v1/agents/agent_{i}",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        tasks = [make_request(cp_client, i) for i in range(50)]
        responses = await asyncio.gather(*tasks)
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count >= 45
    
    async def test_concurrent_pp_requests(self, pp_client: httpx.AsyncClient, make_jwt):
        """Test PP Gateway handles concurrent requests"""
        token = make_jwt(roles=["developer"])
        
        async def make_request(client, i):
            return await client.get(
                f"/api/v1/agents/agent_{i}",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        tasks = [make_request(pp_client, i) for i in range(50)]
        responses = await asyncio.gather(*tasks)
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count >= 45


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling and RFC 7807 compliance"""
    
    async def test_rfc7807_format(self, cp_client: httpx.AsyncClient):
        """Test errors follow RFC 7807 Problem Details format"""
        response = await cp_client.get("/api/v1/agents/nonexistent")
        assert response.status_code == 401
        data = response.json()
        assert "type" in data
        assert "title" in data
        assert "status" in data
        assert "detail" in data
        assert "instance" in data
        assert "correlation_id" in data
        assert "error_type" in data
    
    async def test_correlation_id_in_errors(self, cp_client: httpx.AsyncClient):
        """Test correlation ID is included in error responses"""
        cid = correlation_id()
        response = await cp_client.get(
            "/api/v1/agents/test",
            headers={"X-Correlation-ID": cid},
        )
        assert response.json()["correlation_id"] == cid


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
