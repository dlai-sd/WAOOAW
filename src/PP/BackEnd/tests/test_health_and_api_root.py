from __future__ import annotations


async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("healthy", "degraded")
    assert data["service"] == "pp-backend"
    assert "components" in data


async def test_api_root(client):
    resp = await client.get("/api")
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "proxy"
    assert data["service"]


async def test_metrics_endpoint_never_500(client):
    """GET /metrics returns 200 (if prometheus-client installed) or 501 — never 500."""
    resp = await client.get("/metrics")
    assert resp.status_code in (200, 501)

