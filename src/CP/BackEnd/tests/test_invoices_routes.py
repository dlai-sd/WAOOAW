import os

import httpx
import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_cp_invoices_list_proxies_to_plant(monkeypatch):
    from main import app
    from api.auth.dependencies import get_current_user
    from models.user import User

    app.dependency_overrides[get_current_user] = lambda: User(
        id="user-1",
        email="user@example.com",
        name="User",
        picture=None,
        provider="test",
        provider_id="test",
        created_at=__import__("datetime").datetime.utcnow(),
        last_login_at=None,
    )

    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway")

    class DummyClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, headers=None, params=None):
            assert url == "http://plant-gateway/api/v1/invoices"
            # CP passes through query params but Gateway enforces customer_id.
            return httpx.Response(200, json={"invoices": [{"invoice_id": "inv-1"}]})

    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout: DummyClient())

    client = TestClient(app)
    res = client.get(
        "/api/cp/invoices",
        headers={"Authorization": "Bearer test"},
    )
    assert res.status_code == 200
    assert res.json()["invoices"][0]["invoice_id"] == "inv-1"

    app.dependency_overrides.clear()
