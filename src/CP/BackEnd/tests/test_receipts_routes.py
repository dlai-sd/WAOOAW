import httpx
import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_cp_receipts_list_proxies_to_plant(monkeypatch):
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
            assert url == "http://plant-gateway/api/v1/receipts"
            return httpx.Response(200, json={"receipts": [{"receipt_id": "rct-1"}]})

    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout: DummyClient())

    client = TestClient(app)
    res = client.get(
        "/api/cp/receipts",
        headers={"Authorization": "Bearer test"},
    )
    assert res.status_code == 200
    assert res.json()["receipts"][0]["receipt_id"] == "rct-1"

    app.dependency_overrides.clear()


@pytest.mark.unit
def test_cp_receipts_get_by_order_proxies_to_plant(monkeypatch):
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
            assert "/by-order/order-456" in url
            return httpx.Response(200, json={"receipt_id": "rct-order-456"})

    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout: DummyClient())

    client = TestClient(app)
    res = client.get(
        "/api/cp/receipts/by-order/order-456",
        headers={"Authorization": "Bearer test"},
    )
    assert res.status_code == 200
    assert res.json()["receipt_id"] == "rct-order-456"

    app.dependency_overrides.clear()


@pytest.mark.unit
def test_cp_receipts_get_single_proxies_to_plant(monkeypatch):
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
            assert "receipts/rct-789" in url
            return httpx.Response(200, json={"receipt_id": "rct-789", "amount": 5000})

    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout: DummyClient())

    client = TestClient(app)
    res = client.get(
        "/api/cp/receipts/rct-789",
        headers={"Authorization": "Bearer test"},
    )
    assert res.status_code == 200
    assert res.json()["receipt_id"] == "rct-789"

    app.dependency_overrides.clear()


@pytest.mark.unit
def test_cp_receipts_download_html(monkeypatch):
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
            assert "/html" in url
            return httpx.Response(
                200,
                text="<html><body>Receipt HTML</body></html>",
                headers={"content-disposition": "attachment; filename=rct.html"},
            )

    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout: DummyClient())

    client = TestClient(app)
    res = client.get(
        "/api/cp/receipts/rct-999/html",
        headers={"Authorization": "Bearer test"},
    )
    assert res.status_code == 200
    assert res.text == "<html><body>Receipt HTML</body></html>"
    assert "content-disposition" in res.headers

    app.dependency_overrides.clear()


@pytest.mark.unit
def test_cp_receipts_plant_unavailable_fallback(monkeypatch):
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

    monkeypatch.setenv("PLANT_GATEWAY_URL", "")

    client = TestClient(app)
    res = client.get(
        "/api/cp/receipts",
        headers={"Authorization": "Bearer test"},
    )
    assert res.status_code == 200
    assert res.json()["receipts"] == []

    app.dependency_overrides.clear()
