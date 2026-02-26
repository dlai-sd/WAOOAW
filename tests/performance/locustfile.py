"""Locust load test for Plant Gateway — AuthUser and BrowseUser behaviours."""
from locust import HttpUser, task, between


class AuthUser(HttpUser):
    """Simulates authentication-heavy users hitting OTP endpoints."""
    wait_time = between(1, 3)

    @task(3)
    def otp_start(self):
        self.client.post(
            "/auth/otp/start",
            json={"phone": "+911234567890", "channel": "sms"},
            catch_response=True,
        )

    @task(1)
    def health_check(self):
        with self.client.get("/health", catch_response=True) as resp:
            if resp.status_code in (200, 404):
                resp.success()


class BrowseUser(HttpUser):
    """Simulates users browsing the agent catalog."""
    wait_time = between(1, 5)

    @task(5)
    def browse_agents(self):
        with self.client.get("/agents", catch_response=True) as resp:
            if resp.status_code in (200, 401, 403):
                resp.success()

    @task(2)
    def browse_agent_types(self):
        with self.client.get("/agent-types", catch_response=True) as resp:
            if resp.status_code in (200, 401, 403, 404):
                resp.success()

    @task(1)
    def health_check(self):
        with self.client.get("/health", catch_response=True) as resp:
            if resp.status_code in (200, 404):
                resp.success()
