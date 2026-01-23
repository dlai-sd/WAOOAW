"""
Python client SDK for WAOOAW API
"""

import requests
from fastapi import HTTPException
import time  # Importing the time module

class WAOOAWClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def login(self, email, password):
        return self._retry_request(self._login_request, email, password)

    def _login_request(self, email, password):
        response = requests.post(f"{self.base_url}/api/token", json={"email": email, "password": password})
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.json().get("detail", "Login failed"))
        return response.json()

    def _retry_request(self, func, *args, max_attempts=3):
        for attempt in range(max_attempts):
            try:
                return func(*args)
            except HTTPException as e:
                if attempt < max_attempts - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise e

# Example usage
if __name__ == "__main__":
    client = WAOOAWClient("http://localhost:8015")
    print(client.login("test@example.com", "password"))
