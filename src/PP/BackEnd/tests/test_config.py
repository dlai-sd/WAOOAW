from __future__ import annotations

import pytest


@pytest.mark.unit
def test_settings_helpers_parse_cors_and_expiries():
    from core.config import Settings

    settings = Settings(CORS_ORIGINS="http://a.example, http://b.example", ACCESS_TOKEN_EXPIRE_MINUTES=2, REFRESH_TOKEN_EXPIRE_DAYS=1)

    assert settings.cors_origins_list == ["http://a.example", "http://b.example"]
    assert settings.access_token_expire_seconds == 120
    assert settings.refresh_token_expire_seconds == 86400


@pytest.mark.unit
def test_startup_fails_when_jwt_secret_empty_in_live_env():
    """E1-S1-T1: Settings raises ValueError in live env with empty JWT_SECRET."""
    from core.config import Settings

    with pytest.raises(ValueError, match="JWT_SECRET must be set"):
        Settings(ENVIRONMENT="uat", JWT_SECRET="")


@pytest.mark.unit
def test_startup_succeeds_when_jwt_secret_empty_in_codespace():
    """E1-S1-T2: Settings does NOT raise in codespace with empty JWT_SECRET."""
    from core.config import Settings

    s = Settings(ENVIRONMENT="codespace", JWT_SECRET="")
    assert s.JWT_SECRET == ""


@pytest.mark.unit
def test_startup_succeeds_with_jwt_secret_in_demo():
    """E1-S1-T3: Settings does NOT raise in demo with a real JWT_SECRET."""
    from core.config import Settings

    s = Settings(ENVIRONMENT="demo", JWT_SECRET="real-secret-value")
    assert s.JWT_SECRET == "real-secret-value"
