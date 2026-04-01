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
def test_cp_content_analytics_proxies_success(client, auth_headers):
    from main import app
    from api.cp_content_analytics import get_plant_gateway_client

    fake = _FakePlantClient(
        type(
            "Response",
            (),
            {
                "status_code": 200,
                "json": {
                    "top_dimensions": ["education"],
                    "best_posting_hours": [9, 14],
                    "avg_engagement_rate": 0.042,
                    "total_posts_analyzed": 12,
                    "recommendation_text": "Post at 9 AM and 2 PM.",
                },
                "headers": {},
            },
        )()
    )
    app.dependency_overrides[get_plant_gateway_client] = lambda: fake

    response = client.get("/api/cp/content-recommendations/HIRED-1", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["top_dimensions"] == ["education"]
    assert fake.calls[0]["path"] == "/api/v1/hired-agents/HIRED-1/content-recommendations"
    app.dependency_overrides.clear()


@pytest.mark.usefixtures("auth_headers")
def test_cp_content_analytics_returns_503_for_upstream_500(client, auth_headers):
    from main import app
    from api.cp_content_analytics import get_plant_gateway_client

    fake = _FakePlantClient(
        type("Response", (), {"status_code": 500, "json": {"detail": "boom"}, "headers": {}})()
    )
    app.dependency_overrides[get_plant_gateway_client] = lambda: fake

    response = client.get("/api/cp/content-recommendations/HIRED-2", headers=auth_headers)

    assert response.status_code == 503
    app.dependency_overrides.clear()
