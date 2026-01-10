"""
Tests for configuration settings
"""

import pytest

from core.config import settings, get_settings


pytestmark = pytest.mark.unit


def test_cors_origins_list_wildcard():
    """Test CORS origins list parsing"""
    result = settings.cors_origins_list
    assert isinstance(result, list)
    assert len(result) > 0


def test_access_token_expire_seconds():
    """Test access token expiry conversion to seconds"""
    result = settings.access_token_expire_seconds
    expected = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    assert result == expected


def test_refresh_token_expire_seconds():
    """Test refresh token expiry conversion to seconds"""
    result = settings.refresh_token_expire_seconds
    expected = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    assert result == expected


def test_get_settings_returns_singleton():
    """Test get_settings returns the same instance"""
    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2
