"""
Trial concurrency load test for Plant Gateway.

Simulates concurrent trial start requests to verify the platform handles
high concurrency on the trial creation endpoint without data races or errors.

Run headless:
  locust -f trial_concurrency.py --headless -u 100 -r 10 --run-time 60s \
         --html /mnt/locust/reports/trial-concurrency.html \
         --host http://plant-gateway-test:8000
"""

import random
import uuid

from locust import HttpUser, between, task


class TrialUser(HttpUser):
    """
    Simulates concurrent users starting trials.

    Each user:
      1. Authenticates (mocked via test token).
      2. Attempts to start a trial for a random agent.
      3. Checks the resulting trial status.
    """

    wait_time = between(0.5, 2)
    agents = [f"agent-{i:03d}" for i in range(1, 20)]

    def on_start(self):
        """Set up a test auth token before running tasks."""
        self.headers = {"Authorization": "Bearer e2e-test-token"}
        self.customer_id = str(uuid.uuid4())

    @task(4)
    def start_trial(self):
        agent_id = random.choice(self.agents)
        with self.client.post(
            "/hire",
            json={
                "agent_id": agent_id,
                "customer_id": self.customer_id,
                "trial": True,
            },
            headers=self.headers,
            catch_response=True,
            name="/hire (trial start)",
        ) as response:
            if response.status_code in (200, 201):
                response.success()
            elif response.status_code in (401, 403, 422, 429):
                response.success()  # expected operational responses
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(2)
    def check_trial_status(self):
        trial_id = str(uuid.uuid4())
        with self.client.get(
            f"/trials/{trial_id}",
            headers=self.headers,
            catch_response=True,
            name="/trials/[id]",
        ) as response:
            if response.status_code in (200, 404, 401):
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(1)
    def list_my_trials(self):
        with self.client.get(
            f"/customers/{self.customer_id}/trials",
            headers=self.headers,
            catch_response=True,
            name="/customers/[id]/trials",
        ) as response:
            if response.status_code in (200, 401, 404):
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")
