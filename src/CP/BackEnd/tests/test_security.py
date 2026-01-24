import pytest
from fastapi.testclient import TestClient
from core.security import hash_password, verify_password, create_access_token, get_current_user
from core.config import settings

def test_hash_password():
    password = "test_password"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False

def test_create_access_token():
    token = create_access_token({"user_id": "test_user"})
    assert token is not None

# Add more tests for get_current_user and other functions as needed
