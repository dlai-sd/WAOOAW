"""
Tests for JWTClaims class.

Verifies that the JWTClaims class correctly initializes and validates claims.
"""

from datetime import datetime, timedelta, timezone

import pytest
from src.gateway.middleware.auth import JWTClaims

def test_jwt_claims_initialization():
    """Test JWTClaims initialization with valid payload."""
    payload = {
        "user_id": "user-123",
        "email": "test@waooaw.com",
        "customer_id": "cust-456",
        "roles": ["user"],
        "iat": 1705485600,
        "exp": 1705489200,
        "iss": "waooaw.com",
        "sub": "user-123",
    }
    
    claims = JWTClaims(payload)
    
    assert claims.user_id == "user-123"
    assert claims.email == "test@waooaw.com"
    assert claims.customer_id == "cust-456"
    assert claims.roles == ["user"]

def test_jwt_claims_missing_user_id():
    """Test missing user_id raises ValueError."""
    payload = {
        "email": "test@waooaw.com",
        "customer_id": "cust-456",
        "roles": ["user"],
        "iat": 1705485600,
        "exp": 1705489200,
        "iss": "waooaw.com",
        "sub": "user-123",
    }
    
    with pytest.raises(ValueError, match="Missing required claim: user_id"):
        JWTClaims(payload)

def test_jwt_claims_missing_email():
    """Test missing email raises ValueError."""
    payload = {
        "user_id": "user-123",
        "customer_id": "cust-456",
        "roles": ["user"],
        "iat": 1705485600,
        "exp": 1705489200,
        "iss": "waooaw.com",
        "sub": "user-123",
    }
    
    with pytest.raises(ValueError, match="Missing required claim: email"):
        JWTClaims(payload)

def test_jwt_claims_missing_roles():
    """Test missing roles raises ValueError."""
    payload = {
        "user_id": "user-123",
        "email": "test@waooaw.com",
        "iat": 1705485600,
        "exp": 1705489200,
        "iss": "waooaw.com",
        "sub": "user-123",
    }
    
    with pytest.raises(ValueError, match="Missing required claim: roles"):
        JWTClaims(payload)

def test_jwt_claims_trial_mode_expired():
    """Test trial mode expiration."""
    expired_at = (datetime.now(timezone.utc) - timedelta(days=1)).replace(microsecond=0)
    payload = {
        "user_id": "user-trial",
        "email": "trial@waooaw.com",
        "customer_id": "cust-789",
        "roles": ["user"],
        "trial_mode": True,
        "trial_expires_at": expired_at.isoformat().replace("+00:00", "Z"),
        "iat": 1705485600,
        "exp": 1705489200,
        "iss": "waooaw.com",
        "sub": "user-trial",
    }
    
    claims = JWTClaims(payload)
    assert claims.is_trial_expired() is True

def test_jwt_claims_trial_mode_not_expired():
    """Test trial mode not expired."""
    not_expired_at = (datetime.now(timezone.utc) + timedelta(days=1)).replace(microsecond=0)
    payload = {
        "user_id": "user-trial",
        "email": "trial@waooaw.com",
        "customer_id": "cust-789",
        "roles": ["user"],
        "trial_mode": True,
        "trial_expires_at": not_expired_at.isoformat().replace("+00:00", "Z"),
        "iat": 1705485600,
        "exp": 1705489200,
        "iss": "waooaw.com",
        "sub": "user-trial",
    }
    
    claims = JWTClaims(payload)
    assert claims.is_trial_expired() is False
