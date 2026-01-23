"""
Python client SDK for WAOOAW API
"""

import requests

class WAOOAWClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def login(self, email, password):
        response = requests.post(f"{self.base_url}/api/token", json={"email": email, "password": password})
        return response.json()

# Example usage
if __name__ == "__main__":
    client = WAOOAWClient("http://localhost:8015")
    print(client.login("test@example.com", "password"))
