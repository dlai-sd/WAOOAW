"""
Load Testing for Gateway Middleware

Uses locust for load testing with target of 1000 RPS.
Tests middleware performance under load.
"""

from __future__ import annotations

import os
import random
from datetime import datetime, timedelta

import jwt
from locust import HttpUser, between, events, task


# Configuration
JWT_PRIVATE_KEY = os.getenv("JWT_PRIVATE_KEY", "")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ISSUER = os.getenv("JWT_ISSUER", "waooaw.com")
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8000")


def generate_token(user_id: str | None = None, role: str = "customer") -> str:
    """Generate JWT token for load testing.

    Matches gateway auth expectations (iss + required claims) and defaults to
    HS256 for local/dev environments.
    """

    if not JWT_PRIVATE_KEY:
        raise RuntimeError(
            "JWT_PRIVATE_KEY must be set for authenticated gateway load tests"
        )

    if not user_id:
        user_id = f"load-test-user-{random.randint(1000, 9999)}"

    now = datetime.utcnow()
    payload = {
        "sub": user_id,
        "user_id": user_id,
        "email": f"{user_id}@example.com",
        "roles": [role],
        "iss": JWT_ISSUER,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
    }

    return jwt.encode(payload, JWT_PRIVATE_KEY, algorithm=JWT_ALGORITHM)


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

    target_rps = os.getenv("LOCUST_TARGET_RPS")
    target_p95_ms = os.getenv("LOCUST_TARGET_P95_MS")
    
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

    if target_rps or target_p95_ms:
        print("\n" + "=" * 60)
        print(
            "TARGETS:"
            + (f" RPS>={target_rps}" if target_rps else "")
            + (f", p95<={target_p95_ms}ms" if target_p95_ms else "")
        )

        if target_rps:
            required_rps = float(target_rps)
            if stats.total.total_rps >= required_rps:
                print("✅ RPS Target: PASSED")
            else:
                print(
                    f"❌ RPS Target: FAILED ({stats.total.total_rps:.2f} < {required_rps:.2f})"
                )

        if target_p95_ms:
            required_p95 = float(target_p95_ms)
            measured_p95 = stats.total.get_response_time_percentile(0.95)
            if measured_p95 <= required_p95:
                print("✅ p95 Target: PASSED")
            else:
                print(
                    f"❌ p95 Target: FAILED ({measured_p95:.2f}ms > {required_p95:.2f}ms)"
                )

        print("=" * 60)


if __name__ == "__main__":
    import sys
    print("Run with: locust -f locustfile.py --host http://localhost:8000")
    print("For headless: locust -f locustfile.py --host http://localhost:8000 --users 100 --spawn-rate 10 --run-time 60s --headless")
