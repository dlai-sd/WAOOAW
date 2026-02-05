from __future__ import annotations


async def test_api_health_returns_200(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") == "healthy"
    assert body.get("service") == "pp-proxy"
