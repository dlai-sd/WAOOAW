"""
Locust load testing configuration for Plant Backend API.

This file defines load testing scenarios for the backend API endpoints.
Supports multiple test scenarios: health checks, authentication, agent operations.

Usage:
  # Inside Docker container:
  locust -f tests/performance/locustfile.py --host=http://localhost:8001

  # With web UI (default):
  locust -f tests/performance/locustfile.py --host=http://plant-backend-local:8001

  # Headless mode (for CI):
  locust -f tests/performance/locustfile.py --host=http://plant-backend-local:8001 \
    --users 10 --spawn-rate 2 --run-time 60s --headless
"""

import random
import time
from typing import Optional
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner


# Test data for realistic scenarios
CUSTOMER_IDS = [
    "test-customer-001",
    "test-customer-002",
    "test-customer-003",
    "test-customer-004",
    "test-customer-005",
]

AGENT_TYPES = [
    "marketing_content_creator",
    "marketing_social_media_manager",
    "trading_delta_exchange",
]

INDUSTRY_FILTERS = ["marketing", "education", "sales"]


class PlantBackendUser(HttpUser):
    """
    Simulates a typical customer interacting with the Plant Backend API.
    
    Includes realistic wait times between requests and weighted task distribution.
    """
    
    # Wait 1-3 seconds between tasks (realistic user behavior)
    wait_time = between(1, 3)
    
    def on_start(self):
        """Initialize user session with authentication."""
        self.customer_id = random.choice(CUSTOMER_IDS)
        self.agent_id: Optional[str] = None
        self.access_token: Optional[str] = None
        
        # Authenticate (in real scenario, would get JWT token)
        # For now, we'll use API key auth or mock token
        self.headers = {
            "X-Customer-ID": self.customer_id,
            "Content-Type": "application/json",
        }
    
    @task(10)
    def health_check(self):
        """
        Health check endpoint - highest frequency (10x weight).
        
        Expected: P50 < 50ms, P95 < 100ms, P99 < 200ms
        """
        with self.client.get(
            "/health",
            catch_response=True,
            name="GET /health"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(8)
    def list_agents(self):
        """
        List all available agents - high frequency (8x weight).
        
        Expected: P50 < 100ms, P95 < 300ms, P99 < 500ms
        """
        with self.client.get(
            "/api/v1/agents",
            headers=self.headers,
            catch_response=True,
            name="GET /api/v1/agents"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        response.success()
                    else:
                        response.failure("Response not a list")
                except Exception as e:
                    response.failure(f"JSON parse error: {e}")
            else:
                response.failure(f"List agents failed: {response.status_code}")
    
    @task(5)
    def filter_agents_by_industry(self):
        """
        Filter agents by industry - medium frequency (5x weight).
        
        Expected: P50 < 100ms, P95 < 300ms, P99 < 500ms
        """
        industry = random.choice(INDUSTRY_FILTERS)
        with self.client.get(
            f"/api/v1/agents?industry={industry}",
            headers=self.headers,
            catch_response=True,
            name="GET /api/v1/agents?industry=*"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Filter agents failed: {response.status_code}")
    
    @task(6)
    def get_customer_agents(self):
        """
        Get customer's hired agents - high frequency (6x weight).
        
        Expected: P50 < 150ms, P95 < 400ms, P99 < 600ms
        """
        with self.client.get(
            f"/api/v1/customers/{self.customer_id}/agents",
            headers=self.headers,
            catch_response=True,
            name="GET /api/v1/customers/:id/agents"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0:
                        # Cache an agent ID for subsequent requests
                        self.agent_id = data[0].get("id")
                    response.success()
                except Exception as e:
                    response.failure(f"JSON parse error: {e}")
            elif response.status_code == 404:
                # No agents hired yet - acceptable
                response.success()
            else:
                response.failure(f"Get customer agents failed: {response.status_code}")
    
    @task(4)
    def get_agent_configuration(self):
        """
        Get agent configuration - medium frequency (4x weight).
        Requires agent_id from previous get_customer_agents call.
        
        Expected: P50 < 150ms, P95 < 400ms, P99 < 600ms
        """
        if not self.agent_id:
            # Skip if no agent ID available yet
            return
        
        with self.client.get(
            f"/api/v1/agents/{self.agent_id}/configuration",
            headers=self.headers,
            catch_response=True,
            name="GET /api/v1/agents/:id/configuration"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Agent not found - acceptable in test
                response.success()
            else:
                response.failure(f"Get configuration failed: {response.status_code}")
    
    @task(3)
    def list_goals(self):
        """
        List agent goals - medium frequency (3x weight).
        
        Expected: P50 < 200ms, P95 < 500ms, P99 < 800ms
        """
        if not self.agent_id:
            return
        
        with self.client.get(
            f"/api/v1/agents/{self.agent_id}/goals",
            headers=self.headers,
            catch_response=True,
            name="GET /api/v1/agents/:id/goals"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.success()
            else:
                response.failure(f"List goals failed: {response.status_code}")
    
    @task(2)
    def get_deliverables(self):
        """
        Get agent deliverables - lower frequency (2x weight).
        
        Expected: P50 < 200ms, P95 < 600ms, P99 < 1000ms
        """
        if not self.agent_id:
            return
        
        with self.client.get(
            f"/api/v1/agents/{self.agent_id}/deliverables",
            headers=self.headers,
            catch_response=True,
            name="GET /api/v1/agents/:id/deliverables"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.success()
            else:
                response.failure(f"Get deliverables failed: {response.status_code}")
    
    @task(1)
    def create_goal(self):
        """
        Create a new goal - lowest frequency (1x weight).
        This is a write operation, so less frequent.
        
        Expected: P50 < 300ms, P95 < 800ms, P99 < 1500ms
        """
        if not self.agent_id:
            return
        
        goal_data = {
            "title": f"Test Goal {random.randint(1000, 9999)}",
            "description": "Load testing goal - automated creation",
            "schedule": "daily",
            "enabled": False,  # Don't actually run these test goals
        }
        
        with self.client.post(
            f"/api/v1/agents/{self.agent_id}/goals",
            headers=self.headers,
            json=goal_data,
            catch_response=True,
            name="POST /api/v1/agents/:id/goals"
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            elif response.status_code == 404:
                response.success()
            else:
                response.failure(f"Create goal failed: {response.status_code}")


class HealthCheckUser(HttpUser):
    """
    Lightweight user that only hits health check endpoint.
    Useful for smoke testing and basic availability checks.
    """
    wait_time = between(0.5, 1.5)
    
    @task
    def health_check(self):
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")


# Performance SLA thresholds (from AGP2-PERF-1_Implementation_Plan.md)
PERFORMANCE_THRESHOLDS = {
    "health": {"p50": 50, "p95": 100, "p99": 200},
    "read_light": {"p50": 100, "p95": 300, "p99": 500},
    "read_medium": {"p50": 150, "p95": 400, "p99": 600},
    "read_heavy": {"p50": 200, "p95": 500, "p99": 800},
    "write_light": {"p50": 200, "p95": 600, "p99": 1000},
    "write_heavy": {"p50": 300, "p95": 800, "p99": 1500},
}


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts."""
    print("=" * 80)
    print("Plant Backend Load Testing - Starting")
    print("=" * 80)
    print(f"Host: {environment.host}")
    if isinstance(environment.runner, MasterRunner):
        print(f"Mode: Master (distributed)")
    else:
        print(f"Mode: Standalone")
    print(f"Users: {environment.runner.target_user_count if environment.runner else 'N/A'}")
    print("=" * 80)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops - validate SLAs."""
    print("\n" + "=" * 80)
    print("Plant Backend Load Testing - Complete")
    print("=" * 80)
    
    stats = environment.stats
    
    print("\n📊 Request Summary:")
    print(f"  Total Requests: {stats.total.num_requests}")
    print(f"  Total Failures: {stats.total.num_failures}")
    print(f"  Failure Rate: {stats.total.fail_ratio * 100:.2f}%")
    print(f"  RPS: {stats.total.total_rps:.2f}")
    print(f"  Avg Response Time: {stats.total.avg_response_time:.2f}ms")
    
    print("\n🎯 Performance Targets:")
    for name, entry in stats.entries.items():
        print(f"\n  {name}:")
        print(f"    Requests: {entry.num_requests}, Failures: {entry.num_failures}")
        print(f"    Avg: {entry.avg_response_time:.2f}ms")
        print(f"    P50: {entry.get_response_time_percentile(0.50):.2f}ms")
        print(f"    P95: {entry.get_response_time_percentile(0.95):.2f}ms")
        print(f"    P99: {entry.get_response_time_percentile(0.99):.2f}ms")
        print(f"    RPS: {entry.total_rps:.2f}")
    
    print("\n" + "=" * 80)
    
    # Check if we meet SLA thresholds
    sla_violations = []
    for name, entry in stats.entries.items():
        p95 = entry.get_response_time_percentile(0.95)
        # name is a tuple (path, method), extract path
        endpoint = name[0] if isinstance(name, tuple) else str(name)
        if "health" in endpoint.lower() and p95 > PERFORMANCE_THRESHOLDS["health"]["p95"]:
            sla_violations.append(f"{endpoint}: P95 {p95:.0f}ms > {PERFORMANCE_THRESHOLDS['health']['p95']}ms")
        elif "/agents" in endpoint and p95 > PERFORMANCE_THRESHOLDS["read_light"]["p95"]:
            sla_violations.append(f"{endpoint}: P95 {p95:.0f}ms > {PERFORMANCE_THRESHOLDS['read_light']['p95']}ms")
    
    if sla_violations:
        print("\n⚠️  SLA VIOLATIONS:")
        for violation in sla_violations:
            print(f"  • {violation}")
    else:
        print("\n✅ All SLA thresholds met!")
    
    print("=" * 80 + "\n")
