import httpx
import pytest

from services.credential_resolver import CredentialResolutionError, PPCredentialResolver


@pytest.mark.asyncio
async def test_credential_resolver_errors_on_non_200():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"detail": "forbidden"})

    resolver = PPCredentialResolver(
        pp_base_url="https://pp.test",
        bearer_token="t",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(CredentialResolutionError):
        await resolver.resolve_delta(exchange_account_id="EXCH-1", correlation_id="cid-1")


@pytest.mark.asyncio
async def test_credential_resolver_returns_credentials():
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url).endswith("/api/pp/exchange-credentials/EXCH-1")
        assert request.headers.get("Authorization") == "Bearer t"
        assert request.headers.get("X-Correlation-ID") == "cid-2"
        return httpx.Response(200, json={"api_key": "k", "api_secret": "s"})

    resolver = PPCredentialResolver(
        pp_base_url="https://pp.test",
        bearer_token="t",
        transport=httpx.MockTransport(handler),
    )

    creds = await resolver.resolve_delta(exchange_account_id="EXCH-1", correlation_id="cid-2")
    assert creds.api_key == "k"
    assert creds.api_secret == "s"
