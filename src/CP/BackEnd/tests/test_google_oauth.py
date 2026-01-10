"""Unit tests for Google OAuth helpers.

These tests intentionally avoid real HTTP/network calls.
"""

import pytest
from fastapi import HTTPException

from api.auth.google_oauth import GoogleOAuth, get_user_from_google


pytestmark = pytest.mark.unit


def test_get_authorization_url_contains_expected_params() -> None:
    url = GoogleOAuth.get_authorization_url(
        redirect_uri="http://localhost:3000/auth/callback",
        state="state-123",
    )

    assert url.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert "redirect_uri=http://localhost:3000/auth/callback" in url
    assert "state=state-123" in url


@pytest.mark.asyncio
async def test_get_user_from_google_raises_when_access_token_missing(mocker) -> None:
    exchange = mocker.patch(
        "api.auth.google_oauth.GoogleOAuth.exchange_code_for_token",
        new_callable=mocker.AsyncMock,
    )
    exchange.return_value = {}

    with pytest.raises(HTTPException) as exc_info:
        await get_user_from_google(code="code", redirect_uri="http://localhost/callback")

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_get_user_from_google_happy_path(mocker) -> None:
    exchange = mocker.patch(
        "api.auth.google_oauth.GoogleOAuth.exchange_code_for_token",
        new_callable=mocker.AsyncMock,
    )
    exchange.return_value = {"access_token": "access-token"}

    user_info = {"id": "123", "email": "test@example.com"}
    get_user_info = mocker.patch(
        "api.auth.google_oauth.GoogleOAuth.get_user_info",
        new_callable=mocker.AsyncMock,
    )
    get_user_info.return_value = user_info

    result = await get_user_from_google(code="code", redirect_uri="http://localhost/callback")

    assert result == user_info
    get_user_info.assert_awaited_once_with("access-token")
