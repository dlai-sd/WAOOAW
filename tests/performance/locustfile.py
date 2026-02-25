"""
Locust load test for Plant Gateway.

Users:
  AuthUser   — simulates OTP start + verify flow
  BrowseUser — simulates browsing the agent marketplace

Run headless:
  locust -f locustfile.py --headless -u 50 -r 5 --run-time 60s \
         --html /mnt/locust/reports/report.html \
         --host http://plant-gateway-test:8000
"""

import random

from locust import HttpUser, between, task


class AuthUser(HttpUser):
    """Simulates users going through the OTP authentication flow."""

    wait_time = between(1, 3)
    phone_numbers = [
        "+919876543210",
        "+919123456789",
        "+917890123456",
        "+918765432109",
    ]

    @task(3)
    def otp_start(self):
        phone = random.choice(self.phone_numbers)
        with self.client.post(
            "/auth/otp/start",
            json={"phone": phone},
            catch_response=True,
            name="/auth/otp/start",
        ) as response:
            if response.status_code not in (200, 201, 429):
                response.failure(f"Unexpected status: {response.status_code}")

    @task(1)
    def otp_verify(self):
        with self.client.post(
            "/auth/otp/verify",
            json={
                "phone": "+919876543210",
                "otp": "123456",
                "otp_id": "perf-test-otp",
            },
            catch_response=True,
            name="/auth/otp/verify",
        ) as response:
            if response.status_code not in (200, 201, 401, 422):
                response.failure(f"Unexpected status: {response.status_code}")


class BrowseUser(HttpUser):
    """Simulates users browsing the agent marketplace."""

    wait_time = between(1, 5)

    @task(5)
    def browse_agents(self):
        with self.client.get(
            "/agents",
            catch_response=True,
            name="/agents",
        ) as response:
            if response.status_code not in (200, 401):
                response.failure(f"Unexpected status: {response.status_code}")

    @task(2)
    def get_agent_detail(self):
        agent_id = random.choice(["agent-001", "agent-002", "agent-003"])
        with self.client.get(
            f"/agents/{agent_id}",
            catch_response=True,
            name="/agents/[id]",
        ) as response:
            if response.status_code not in (200, 404, 401):
                response.failure(f"Unexpected status: {response.status_code}")

    @task(1)
    def health_check(self):
        self.client.get("/health", name="/health")
