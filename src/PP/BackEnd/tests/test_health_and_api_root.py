from __future__ import annotations


async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "pp-proxy"


async def test_api_root(client):
    resp = await client.get("/api")
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "proxy"
    assert data["service"]
