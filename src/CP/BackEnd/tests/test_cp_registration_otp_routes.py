import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class _MockResponse:
    def __init__(self, *, status_code: int, json_data=None, text: str = "", content: bytes = b"{}"):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text
        self.content = content

    def json(self):
        if isinstance(self._json_data, Exception):
            raise self._json_data
        return self._json_data


def _mock_async_client(*, get_response: _MockResponse, post_response: _MockResponse):
    client = MagicMock()
    client.get = AsyncMock(return_value=get_response)
    client.post = AsyncMock(return_value=post_response)

    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=client)
    cm.__aexit__ = AsyncMock(return_value=None)
    return cm, client


@pytest.mark.unit
def test_cp_register_otp_start_returns_503_when_key_missing(client, monkeypatch):
    monkeypatch.delenv("CP_REGISTRATION_KEY", raising=False)

    resp = client.post(
        "/api/cp/auth/register/otp/start",
        json={"email": "test@example.com"},
    )

    assert resp.status_code == 503
    assert resp.json()["detail"] == "Registration service misconfigured (missing CP_REGISTRATION_KEY)"


@pytest.mark.unit
def test_cp_register_otp_start_returns_503_when_plant_rejects_key_on_lookup(client, monkeypatch):
    monkeypatch.setenv("CP_REGISTRATION_KEY", "test-registration-key")

    async_client_cm, async_client = _mock_async_client(
        get_response=_MockResponse(status_code=401, json_data={}, content=b"{}"),
        post_response=_MockResponse(status_code=500, json_data={}, content=b"{}"),
    )

    with patch("api.cp_registration_otp.httpx.AsyncClient", return_value=async_client_cm):
        resp = client.post(
            "/api/cp/auth/register/otp/start",
            json={"email": "test@example.com"},
        )

    assert resp.status_code == 503
    assert resp.json()["detail"] == "Registration service misconfigured (Plant rejected CP_REGISTRATION_KEY)"
    assert async_client.get.await_count == 1
    assert async_client.post.await_count == 0


@pytest.mark.unit
def test_cp_register_otp_start_happy_path_forwards_headers_and_returns_otp_id(client, monkeypatch):
    monkeypatch.setenv("CP_REGISTRATION_KEY", "test-registration-key")
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway")

    async_client_cm, async_client = _mock_async_client(
        get_response=_MockResponse(status_code=404, json_data={}, content=b"{}"),
        post_response=_MockResponse(
            status_code=201,
            json_data={
                "otp_id": "otp-123",
                "destination_masked": "t***@example.com",
                "expires_in_seconds": 300,
                "otp_code": "123456",
            },
            content=b"{\"ok\": true}",
        ),
    )

    with patch("api.cp_registration_otp.httpx.AsyncClient", return_value=async_client_cm):
        resp = client.post(
            "/api/cp/auth/register/otp/start",
            json={"email": "TEST@EXAMPLE.COM"},
        )

    assert resp.status_code == 200
    assert resp.json()["otp_id"] == "otp-123"
    assert resp.json()["destination_masked"] == "t***@example.com"
    assert resp.json()["expires_in_seconds"] == 300

    lookup_headers = async_client.get.call_args.kwargs["headers"]
    assert lookup_headers["X-CP-Registration-Key"] == "test-registration-key"
    assert "X-Correlation-ID" in lookup_headers


@pytest.mark.unit
def test_cp_register_otp_start_returns_503_when_plant_5xx_on_lookup(client, monkeypatch):
    """Plant returns 500 (e.g. missing otp_sessions table) during customer lookup → 503 UPSTREAM_ERROR."""
    monkeypatch.setenv("CP_REGISTRATION_KEY", "test-registration-key")
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway")

    async_client_cm, async_client = _mock_async_client(
        get_response=_MockResponse(
            status_code=500,
            json_data={"detail": "internal server error"},
            text="internal server error",
            content=b"{}",
        ),
        post_response=_MockResponse(status_code=500, json_data={}, content=b"{}"),
    )

    with patch("api.cp_registration_otp.httpx.AsyncClient", return_value=async_client_cm):
        resp = client.post(
            "/api/cp/auth/register/otp/start",
            json={"email": "test@example.com"},
        )

    assert resp.status_code == 503
    body = resp.json()
    assert body["error"]["code"] == "UPSTREAM_ERROR"
    assert "Retry-After" in resp.headers
    # Must not have proceeded to OTP session create
    assert async_client.post.await_count == 0


@pytest.mark.unit
def test_cp_register_otp_start_returns_503_when_plant_5xx_on_otp_create(client, monkeypatch):
    """Plant returns 500 during OTP session create (e.g. missing otp_sessions table) → 503 UPSTREAM_ERROR."""
    monkeypatch.setenv("CP_REGISTRATION_KEY", "test-registration-key")
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway")

    async_client_cm, async_client = _mock_async_client(
        get_response=_MockResponse(status_code=404, json_data={}, content=b"{}"),
        post_response=_MockResponse(
            status_code=500,
            json_data={"detail": "relation otp_sessions does not exist"},
            text="relation otp_sessions does not exist",
            content=b"{}",
        ),
    )

    with patch("api.cp_registration_otp.httpx.AsyncClient", return_value=async_client_cm):
        resp = client.post(
            "/api/cp/auth/register/otp/start",
            json={"email": "test@example.com"},
        )

    assert resp.status_code == 503
    body = resp.json()
    assert body["error"]["code"] == "UPSTREAM_ERROR"
    assert "Retry-After" in resp.headers


@pytest.mark.unit
def test_cp_register_otp_start_returns_409_when_email_exists(client, monkeypatch):
    """Plant returns 200 on lookup → email already registered → 409."""
    monkeypatch.setenv("CP_REGISTRATION_KEY", "test-registration-key")
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway")

    async_client_cm, async_client = _mock_async_client(
        get_response=_MockResponse(status_code=200, json_data={"id": "cust-123"}, content=b"{}"),
        post_response=_MockResponse(status_code=201, json_data={}, content=b"{}"),
    )

    with patch("api.cp_registration_otp.httpx.AsyncClient", return_value=async_client_cm):
        resp = client.post(
            "/api/cp/auth/register/otp/start",
            json={"email": "existing@example.com"},
        )

    assert resp.status_code == 409
    assert "already registered" in resp.json()["detail"]
    assert async_client.post.await_count == 0


@pytest.mark.unit
def test_cp_register_otp_start_returns_503_when_plant_403_on_otp_create(client, monkeypatch):
    """Plant returns 403 during OTP session create → misconfigured key error."""
    monkeypatch.setenv("CP_REGISTRATION_KEY", "test-registration-key")
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway")

    async_client_cm, _ = _mock_async_client(
        get_response=_MockResponse(status_code=404, json_data={}, content=b"{}"),
        post_response=_MockResponse(status_code=403, json_data={}, content=b"{}"),
    )

    with patch("api.cp_registration_otp.httpx.AsyncClient", return_value=async_client_cm):
        resp = client.post(
            "/api/cp/auth/register/otp/start",
            json={"email": "test@example.com"},
        )

    assert resp.status_code == 503
    assert "Plant rejected CP_REGISTRATION_KEY" in resp.json()["detail"]
