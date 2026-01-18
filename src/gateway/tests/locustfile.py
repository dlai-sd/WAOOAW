"""
Load Testing for Gateway Middleware

Uses locust for load testing with target of 1000 RPS.
Tests middleware performance under load.
"""

from locust import HttpUser, task, between, events
import random
import jwt
import os
from datetime import datetime, timedelta


# Configuration
JWT_PRIVATE_KEY = os.getenv("JWT_PRIVATE_KEY", "")
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8000")


def generate_token(user_id: str = None, role: str = "customer") -> str:
    """Generate JWT token for load testing"""
    if not user_id:
        user_id = f"load-test-user-{random.randint(1000, 9999)}"
    
    payload = {
        "sub": user_id,
        "role": role,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    
    return jwt.encode(payload, JWT_PRIVATE_KEY, algorithm="RS256")


class GatewayUser(HttpUser):
    """
    Simulated user for load testing
    """
    wait_time = between(0.1, 0.5)  # Wait 100-500ms between requests
    
    def on_start(self):
        """Generate token when user starts"""
        self.token = generate_token()
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(10)
    def list_agents(self):
        """List all agents (most common operation)"""
        self.client.get(
            "/api/v1/agents",
            headers=self.headers,
            name="GET /api/v1/agents"
        )
    
    @task(5)
    def get_agent(self):
        """Get specific agent details"""
        agent_ids = ["agent-001", "agent-002", "agent-003"]
        agent_id = random.choice(agent_ids)
        self.client.get(
            f"/api/v1/agents/{agent_id}",
            headers=self.headers,
            name="GET /api/v1/agents/{id}"
        )
    
    @task(3)
    def hire_agent(self):
        """Hire an agent (POST operation)"""
        agent_ids = ["agent-001", "agent-002", "agent-003"]
        agent_id = random.choice(agent_ids)
        self.client.post(
            f"/api/v1/agents/{agent_id}/hire",
            headers=self.headers,
            name="POST /api/v1/agents/{id}/hire"
        )
    
    @task(2)
    def search_agents(self):
        """Search agents with filters"""
        industries = ["marketing", "education", "sales"]
        industry = random.choice(industries)
        self.client.get(
            f"/api/v1/agents?industry={industry}",
            headers=self.headers,
            name="GET /api/v1/agents?industry={industry}"
        )
    
    @task(1)
    def health_check(self):
        """Health check (no auth required)"""
        self.client.get("/health", name="GET /health")


class AdminUser(HttpUser):
    """Admin user performing privileged operations"""
    wait_time = between(1, 3)  # Admin operations less frequent
    
    def on_start(self):
        """Generate admin token"""
        self.token = generate_token(role="admin")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(5)
    def list_agents(self):
        """Admin listing agents"""
        self.client.get(
            "/api/v1/agents",
            headers=self.headers,
            name="ADMIN GET /api/v1/agents"
        )
    
    @task(2)
    def admin_endpoint(self):
        """Access admin-only endpoint"""
        self.client.post(
            "/api/v1/admin/settings",
            headers=self.headers,
            name="POST /api/v1/admin/settings"
        )
    
    @task(1)
    def delete_agent(self):
        """Delete agent (requires governor approval)"""
        agent_id = f"agent-{random.randint(100, 999)}"
        self.client.delete(
            f"/api/v1/agents/{agent_id}",
            headers=self.headers,
            name="DELETE /api/v1/agents/{id}"
        )


# Performance metrics collection
@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Initialize performance metrics"""
    print("=" * 60)
    print("Gateway Load Testing Initialized")
    print(f"Target: {GATEWAY_URL}")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print final performance report"""
    stats = environment.stats
    
    print("\n" + "=" * 60)
    print("LOAD TEST RESULTS")
    print("=" * 60)
    
    print(f"\nTotal Requests: {stats.total.num_requests}")
    print(f"Total Failures: {stats.total.num_failures}")
    print(f"Failure Rate: {stats.total.fail_ratio * 100:.2f}%")
    print(f"RPS: {stats.total.total_rps:.2f}")
    
    print(f"\nResponse Times:")
    print(f"  p50 (median): {stats.total.get_response_time_percentile(0.5):.2f}ms")
    print(f"  p75: {stats.total.get_response_time_percentile(0.75):.2f}ms")
    print(f"  p90: {stats.total.get_response_time_percentile(0.90):.2f}ms")
    print(f"  p95: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    print(f"  p99: {stats.total.get_response_time_percentile(0.99):.2f}ms")
    print(f"  Max: {stats.total.max_response_time:.2f}ms")
    print(f"  Min: {stats.total.min_response_time:.2f}ms")
    print(f"  Average: {stats.total.avg_response_time:.2f}ms")
    
    print("\n" + "=" * 60)
    print("TARGET: 1000 RPS, p95 < 100ms")
    
    # Check if targets met
    if stats.total.total_rps >= 900:  # Allow 10% tolerance
        print("✅ RPS Target: PASSED")
    else:
        print(f"❌ RPS Target: FAILED ({stats.total.total_rps:.2f} < 900)")
    
    if stats.total.get_response_time_percentile(0.95) < 100:
        print("✅ Latency Target: PASSED")
    else:
        print(f"❌ Latency Target: FAILED ({stats.total.get_response_time_percentile(0.95):.2f}ms >= 100ms)")
    
    print("=" * 60)


if __name__ == "__main__":
    import sys
    print("Run with: locust -f locustfile.py --host http://localhost:8000")
    print("For headless: locust -f locustfile.py --host http://localhost:8000 --users 100 --spawn-rate 10 --run-time 60s --headless")
