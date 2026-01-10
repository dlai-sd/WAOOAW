"""
Load testing with Locust
Tests API endpoints under load to identify performance bottlenecks
"""

from locust import HttpUser, task, between
import random


class CPBackendUser(HttpUser):
    """Simulates a Customer Portal user"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Called when a simulated user starts"""
        self.auth_token = None
        # In production: authenticate and get real token
        # self.login()
    
    @task(3)
    def health_check(self):
        """Check API health (most frequent)"""
        self.client.get("/health")
    
    @task(2)
    def auth_health(self):
        """Check auth service health"""
        self.client.get("/api/auth/health")
    
    @task(1)
    def api_docs(self):
        """Access API documentation"""
        self.client.get("/docs")
    
    # def login(self):
    #     """Login and get JWT token"""
    #     response = self.client.post("/api/auth/google/verify", json={
    #         "id_token": "test_token",
    #         "source": "cp"
    #     })
    #     if response.status_code == 200:
    #         self.auth_token = response.json().get("access_token")
    
    # @task(1)
    # def get_current_user(self):
    #     """Get current user info (requires auth)"""
    #     if self.auth_token:
    #         self.client.get("/api/auth/me", headers={
    #             "Authorization": f"Bearer {self.auth_token}"
    #         })


class CPStressTest(HttpUser):
    """Stress test with high concurrency"""
    
    wait_time = between(0.1, 0.5)  # Minimal wait time
    
    @task
    def rapid_health_checks(self):
        """Rapid fire health checks"""
        self.client.get("/health")
    
    @task
    def rapid_auth_checks(self):
        """Rapid fire auth health checks"""
        self.client.get("/api/auth/health")


class CPEnduranceTest(HttpUser):
    """Long-running endurance test"""
    
    wait_time = between(5, 10)  # Longer wait time
    
    @task
    def sustained_load(self):
        """Sustained API calls over long period"""
        endpoints = ["/health", "/api/auth/health", "/docs"]
        endpoint = random.choice(endpoints)
        self.client.get(endpoint)
