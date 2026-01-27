"""Unit tests for Google OAuth helpers.

These tests intentionally avoid real HTTP/network calls.
"""

import pytest
from fastapi import HTTPException

from api.auth.google_oauth import GoogleOAuth, get_user_from_google
from core.config import settings


pytestmark = pytest.mark.unit


class _DummyResponse:
    def __init__(self, status_code: int, json_data):
        self.status_code = status_code
        self._json_data = json_data

    def json(self):
        return self._json_data


class _DummyAsyncClient:
    def __init__(self, *, post_response: _DummyResponse | None = None, get_response: _DummyResponse | None = None):
        self._post_response = post_response
        self._get_response = get_response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, data=None, headers=None):
        assert self._post_response is not None
        return self._post_response

    async def get(self, url, headers=None):
        assert self._get_response is not None
        return self._get_response


def test_get_authorization_url_contains_expected_params() -> None:
    url = GoogleOAuth.get_authorization_url(
        redirect_uri="http://localhost:3000/auth/callback",
        state="state-123",
    )

    assert url.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert "redirect_uri=http://localhost:3000/auth/callback" in url
    assert "state=state-123" in url


@pytest.mark.asyncio
async def test_exchange_code_for_token_raises_on_non_200(mocker) -> None:
    mocker.patch(
        "api.auth.google_oauth.httpx.AsyncClient",
        return_value=_DummyAsyncClient(post_response=_DummyResponse(400, {"error": "bad"})),
    )

    with pytest.raises(HTTPException) as exc_info:
        await GoogleOAuth.exchange_code_for_token(code="code", redirect_uri="http://localhost/callback")

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_verify_id_token_happy_path(mocker) -> None:
    token_info = {"aud": settings.GOOGLE_CLIENT_ID, "email": "test@example.com"}
    mocker.patch(
        "api.auth.google_oauth.httpx.AsyncClient",
        return_value=_DummyAsyncClient(get_response=_DummyResponse(200, token_info)),
    )

    result = await GoogleOAuth.verify_id_token(id_token="id-token")
    assert result == token_info


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
