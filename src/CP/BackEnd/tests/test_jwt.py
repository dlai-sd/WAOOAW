"""
Unit tests for JWT token handling
"""
import pytest
from core.jwt_handler import JWTHandler


@pytest.mark.unit
def test_create_access_token():
    """Test access token creation"""
    user_id = "test-user-123"
    email = "test@example.com"
    
    token = JWTHandler.create_access_token(user_id=user_id, email=email)
    
    assert isinstance(token, str)
    assert len(token) > 0


@pytest.mark.unit
def test_create_refresh_token():
    """Test refresh token creation"""
    user_id = "test-user-123"
    email = "test@example.com"
    
    token = JWTHandler.create_refresh_token(user_id=user_id, email=email)
    
    assert isinstance(token, str)
    assert len(token) > 0


@pytest.mark.unit
def test_tokens_are_different():
    """Test that access and refresh tokens are different"""
    user_id = "test-user-123"
    email = "test@example.com"
    
    access_token = JWTHandler.create_access_token(user_id=user_id, email=email)
    refresh_token = JWTHandler.create_refresh_token(user_id=user_id, email=email)
    
    assert access_token != refresh_token
