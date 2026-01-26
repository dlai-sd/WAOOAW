from __future__ import annotations

import pytest


@pytest.mark.unit
def test_settings_helpers_parse_cors_and_expiries():
    from core.config import Settings

    settings = Settings(CORS_ORIGINS="http://a.example, http://b.example", ACCESS_TOKEN_EXPIRE_MINUTES=2, REFRESH_TOKEN_EXPIRE_DAYS=1)

    assert settings.cors_origins_list == ["http://a.example", "http://b.example"]
    assert settings.access_token_expire_seconds == 120
    assert settings.refresh_token_expire_seconds == 86400
