from __future__ import annotations

import pytest


class _FakePlantClient:
    def __init__(self, response):
        self.response = response
        self.calls = []

    async def request_json(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


@pytest.mark.usefixtures("auth_headers")
def test_cp_publish_receipts_proxies_success(client, auth_headers):
    from api.cp_publish_receipts import get_plant_gateway_client
    from main import app

    fake = _FakePlantClient(
        type(
            "Response",
            (),
            {
                "status_code": 200,
                "json": [
                    {
                        "id": "receipt-1",
                        "hired_instance_id": "HIRED-1",
                        "platform_key": "youtube",
                        "published_at": "2026-04-01T12:00:00Z",
                        "status": "success",
                        "platform_url": "https://youtube.com/watch?v=abc123",
                    }
                ],
                "headers": {},
            },
        )()
    )
    app.dependency_overrides[get_plant_gateway_client] = lambda: fake

    response = client.get("/api/cp/publish-receipts/HIRED-1", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()[0]["platform_key"] == "youtube"
    assert fake.calls[0]["path"] == "/api/v1/publish-receipts/HIRED-1"
    app.dependency_overrides.clear()


@pytest.mark.usefixtures("auth_headers")
def test_cp_publish_receipts_returns_503_for_upstream_500(client, auth_headers):
    from api.cp_publish_receipts import get_plant_gateway_client
    from main import app

    fake = _FakePlantClient(
        type("Response", (), {"status_code": 500, "json": {"detail": "boom"}, "headers": {}})()
    )
    app.dependency_overrides[get_plant_gateway_client] = lambda: fake

    response = client.get("/api/cp/publish-receipts/HIRED-2", headers=auth_headers)

    assert response.status_code == 503
    app.dependency_overrides.clear()
