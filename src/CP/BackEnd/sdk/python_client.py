"""
Python Client SDK for WAOOAW API
"""

import requests

class WAOOAWClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key

    def get_user(self, user_id: str):
        response = requests.get(f"{self.base_url}/api/v1/users/{user_id}", headers={"Authorization": f"Bearer {self.api_key}"})
        return response.json()

    # Add more methods as needed
