"""
Advanced JWT handler tests for coverage
"""

import pytest
from datetime import datetime, timedelta
from fastapi import HTTPException
import jwt

from core.jwt_handler import JWTHandler, create_tokens, verify_token
from core.config import settings
from models.user import TokenData


pytestmark = pytest.mark.unit


def test_create_token_pair():
    """Test creating both access and refresh tokens"""
    result = JWTHandler.create_token_pair("user123", "test@example.com")
    
    assert "access_token" in result
    assert "refresh_token" in result
    assert "token_type" in result
    assert "expires_in" in result
    assert result["token_type"] == "bearer"
    assert result["expires_in"] == settings.access_token_expire_seconds


def test_decode_token_expired():
    """Test decoding expired token"""
    # Create token with negative expiry (already expired)
    past_time = datetime.utcnow() - timedelta(hours=1)
    payload = {
        "user_id": "user123",
        "email": "test@example.com",
        "token_type": "access",
        "exp": past_time.timestamp(),
        "iat": (past_time - timedelta(minutes=5)).timestamp()
    }
    
    expired_token = jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )
    
    with pytest.raises(HTTPException) as exc_info:
        JWTHandler.decode_token(expired_token)
    
    assert exc_info.value.status_code == 401
    assert "Could not validate credentials" in exc_info.value.detail


def test_decode_token_invalid_signature():
    """Test decoding token with invalid signature"""
    # Create token with wrong secret
    payload = {
        "user_id": "user123",
        "email": "test@example.com",
        "token_type": "access",
        "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp()
    }
    
    invalid_token = jwt.encode(
        payload,
        "wrong-secret",
        algorithm=settings.JWT_ALGORITHM
    )
    
    with pytest.raises(HTTPException) as exc_info:
        JWTHandler.decode_token(invalid_token)
    
    assert exc_info.value.status_code == 401


def test_decode_token_missing_user_id():
    """Test decoding token without user_id"""
    payload = {
        "email": "test@example.com",
        "token_type": "access",
        "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp()
    }
    
    invalid_token = jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )
    
    with pytest.raises(HTTPException) as exc_info:
        JWTHandler.decode_token(invalid_token)
    
    assert exc_info.value.status_code == 401


def test_decode_token_missing_email():
    """Test decoding token without email"""
    payload = {
        "user_id": "user123",
        "token_type": "access",
        "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp()
    }
    
    invalid_token = jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )
    
    with pytest.raises(HTTPException) as exc_info:
        JWTHandler.decode_token(invalid_token)
    
    assert exc_info.value.status_code == 401


def test_decode_token_malformed():
    """Test decoding malformed token"""
    with pytest.raises(HTTPException) as exc_info:
        JWTHandler.decode_token("not.a.valid.jwt.token")
    
    assert exc_info.value.status_code == 401


def test_create_tokens_convenience_function():
    """Test convenience function for creating tokens"""
    result = create_tokens("user123", "test@example.com")
    
    assert "access_token" in result
    assert "refresh_token" in result


def test_verify_token_convenience_function():
    """Test convenience function for verifying token"""
    tokens = create_tokens("user123", "test@example.com")
    token_data = verify_token(tokens["access_token"])
    
    assert token_data.user_id == "user123"
    assert token_data.email == "test@example.com"
    assert token_data.token_type == "access"


def test_token_data_model():
    """Test TokenData model"""
    token_data = TokenData(
        user_id="user123",
        email="test@example.com",
        token_type="access"
    )
    
    assert token_data.user_id == "user123"
    assert token_data.email == "test@example.com"
    assert token_data.token_type == "access"


def test_access_token_expiry():
    """Test access token has correct expiry"""
    tokens = create_tokens("user123", "test@example.com")
    
    # Decode without verification to check expiry
    payload = jwt.decode(
        tokens["access_token"],
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM]
    )
    
    exp_time = datetime.fromtimestamp(payload["exp"])
    iat_time = datetime.fromtimestamp(payload["iat"])
    
    # Should be approximately equal to access token expire seconds
    duration = (exp_time - iat_time).total_seconds()
    assert abs(duration - settings.access_token_expire_seconds) < 2


def test_refresh_token_expiry():
    """Test refresh token has correct expiry"""
    tokens = create_tokens("user123", "test@example.com")
    
    # Decode without verification to check expiry
    payload = jwt.decode(
        tokens["refresh_token"],
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM]
    )
    
    exp_time = datetime.fromtimestamp(payload["exp"])
    iat_time = datetime.fromtimestamp(payload["iat"])
    
    # Should be approximately equal to refresh token expire seconds
    duration = (exp_time - iat_time).total_seconds()
    assert abs(duration - settings.refresh_token_expire_seconds) < 2
