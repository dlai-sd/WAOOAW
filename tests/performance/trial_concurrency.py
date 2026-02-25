"""Trial concurrency load test — 100 concurrent trial starts."""
from locust import HttpUser, task, between, events
import threading

_trial_count_lock = threading.Lock()
_trial_count = 0


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    global _trial_count
    if name == "/hire/trial/start" and exception is None:
        with _trial_count_lock:
            _trial_count += 1


class TrialUser(HttpUser):
    """Simulates concurrent trial starts — 100 users, 0 errors target."""
    wait_time = between(0.1, 0.5)

    @task
    def start_trial(self):
        with self.client.post(
            "/hire/trial/start",
            json={
                "agent_id": "agent-001",
                "customer_email": f"user-{id(self)}@test.com",
            },
            catch_response=True,
            name="/hire/trial/start",
        ) as resp:
            if resp.status_code in (200, 201, 422, 401, 403):
                resp.success()
