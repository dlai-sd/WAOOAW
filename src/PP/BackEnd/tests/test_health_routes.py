from __future__ import annotations


async def test_api_health_returns_200(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") == "healthy"
    assert body.get("service") == "pp-proxy"


async def test_api_health_is_not_proxied(client, monkeypatch):
    import main_proxy

    async def fail_proxy_request(*args, **kwargs):
        raise AssertionError("/api/health should not be proxied")

    monkeypatch.setattr(main_proxy.http_client, "request", fail_proxy_request)

    resp = await client.get("/api/health")
    assert resp.status_code == 200
