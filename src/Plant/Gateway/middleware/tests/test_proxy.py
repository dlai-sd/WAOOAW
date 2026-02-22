"""Tests for the Gateway proxy route.

Validates that the Plant Gateway forwards catalog requests to Plant Backend,
while preventing caller Authorization header forwarding.
"""

import time
import sys
import json
from pathlib import Path

import httpx
import jwt
import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_proxy_forwards_get_and_strips_authorization(monkeypatch, jwt_keys):
    gateway_root = Path(__file__).resolve().parents[2]
    if str(gateway_root) not in sys.path:
        sys.path.insert(0, str(gateway_root))

    import main as gateway_main

    now = int(time.time())
    token = jwt.encode(
        {
            "user_id": "user-1",
            "email": "user@example.com",
            "customer_id": "customer-1",
            "roles": ["user"],
            "trial_mode": False,
            "iat": now,
            "exp": now + 3600,
            "iss": "waooaw.com",
            "sub": "user-1",
        },
        jwt_keys["private"],
        algorithm="RS256",
    )

    captured = {}

    class DummyClient:
        async def request(self, method, url, headers, content, follow_redirects):
            captured["method"] = method
            captured["url"] = url
            captured["headers"] = headers
            captured["content"] = content

            return httpx.Response(
                200,
                json={"agents": [{"id": "agent-1"}]},
                headers={"content-type": "application/json"},
            )

    monkeypatch.setattr(gateway_main, "http_client", DummyClient())

    client = TestClient(gateway_main.app)
    res = client.get(
        "/api/v1/agents?industry=marketing",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200
    assert res.json()["agents"][0]["id"] == "agent-1"

    lowered = {k.lower(): v for k, v in captured["headers"].items()}
    assert captured["method"] == "GET"
    assert "/api/v1/agents" in captured["url"]
    assert "industry=marketing" in captured["url"]

    # Gateway must not forward caller Authorization upstream.
    assert "authorization" not in lowered
    assert lowered.get("x-original-authorization") == f"Bearer {token}"


@pytest.mark.unit
def test_proxy_forces_customer_id_on_subscription_cancel(monkeypatch, jwt_keys):
    gateway_root = Path(__file__).resolve().parents[2]
    if str(gateway_root) not in sys.path:
        sys.path.insert(0, str(gateway_root))

    import main as gateway_main

    now = int(time.time())
    token = jwt.encode(
        {
            "user_id": "user-123",
            "email": "user123@example.com",
            "customer_id": "customer-abc",
            "roles": ["user"],
            "trial_mode": False,
            "iat": now,
            "exp": now + 3600,
            "iss": "waooaw.com",
            "sub": "user-123",
        },
        jwt_keys["private"],
        algorithm="RS256",
    )

    captured = {}

    class DummyClient:
        async def request(self, method, url, headers, content, follow_redirects):
            captured["method"] = method
            captured["url"] = url
            captured["headers"] = headers
            captured["content"] = content

            return httpx.Response(
                200,
                json={"subscription_id": "SUB-123", "cancel_at_period_end": True},
                headers={"content-type": "application/json"},
            )

    monkeypatch.setattr(gateway_main, "http_client", DummyClient())

    client = TestClient(gateway_main.app)
    res = client.post(
        "/api/v1/payments/subscriptions/SUB-123/cancel?customer_id=evil-customer",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200
    assert res.json()["cancel_at_period_end"] is True

    assert captured["method"] == "POST"
    assert "/api/v1/payments/subscriptions/SUB-123/cancel" in captured["url"]
    assert "customer_id=customer-abc" in captured["url"]
    assert "evil-customer" not in captured["url"]


@pytest.mark.unit
def test_proxy_subscription_cancel_requires_customer_id(monkeypatch, jwt_keys):
    gateway_root = Path(__file__).resolve().parents[2]
    if str(gateway_root) not in sys.path:
        sys.path.insert(0, str(gateway_root))

    import main as gateway_main

    now = int(time.time())
    token = jwt.encode(
        {
            "user_id": "user-nocust",
            "email": "nocust@example.com",
            "roles": ["user"],
            "trial_mode": False,
            "iat": now,
            "exp": now + 3600,
            "iss": "waooaw.com",
            "sub": "user-nocust",
        },
        jwt_keys["private"],
        algorithm="RS256",
    )

    called = {"count": 0}

    class DummyClient:
        async def request(self, method, url, headers, content, follow_redirects):
            called["count"] += 1
            return httpx.Response(200, json={}, headers={"content-type": "application/json"})

    monkeypatch.setattr(gateway_main, "http_client", DummyClient())

    client = TestClient(gateway_main.app)
    res = client.post(
        "/api/v1/payments/subscriptions/SUB-XYZ/cancel?customer_id=evil-customer",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 401
    assert called["count"] == 0


@pytest.mark.unit
def test_proxy_forces_customer_id_on_invoice_routes(monkeypatch, jwt_keys):
    gateway_root = Path(__file__).resolve().parents[2]
    if str(gateway_root) not in sys.path:
        sys.path.insert(0, str(gateway_root))

    import main as gateway_main

    now = int(time.time())
    token = jwt.encode(
        {
            "user_id": "user-999",
            "email": "user999@example.com",
            "customer_id": "customer-inv",
            "roles": ["user"],
            "trial_mode": False,
            "iat": now,
            "exp": now + 3600,
            "iss": "waooaw.com",
            "sub": "user-999",
        },
        jwt_keys["private"],
        algorithm="RS256",
    )

    captured = {}

    class DummyClient:
        async def request(self, method, url, headers, content, follow_redirects):
            captured["method"] = method
            captured["url"] = url
            captured["headers"] = headers
            captured["content"] = content

            return httpx.Response(
                200,
                json={"invoices": []},
                headers={"content-type": "application/json"},
            )

    monkeypatch.setattr(gateway_main, "http_client", DummyClient())

    client = TestClient(gateway_main.app)
    res = client.get(
        "/api/v1/invoices?customer_id=evil-customer",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200
    assert captured["method"] == "GET"
    assert "/api/v1/invoices" in captured["url"]
    assert "customer_id=customer-inv" in captured["url"]
    assert "evil-customer" not in captured["url"]


@pytest.mark.unit
def test_proxy_forces_customer_id_on_receipt_routes(monkeypatch, jwt_keys):
    gateway_root = Path(__file__).resolve().parents[2]
    if str(gateway_root) not in sys.path:
        sys.path.insert(0, str(gateway_root))

    import main as gateway_main

    now = int(time.time())
    token = jwt.encode(
        {
            "user_id": "user-555",
            "email": "user555@example.com",
            "customer_id": "customer-rct",
            "roles": ["user"],
            "trial_mode": False,
            "iat": now,
            "exp": now + 3600,
            "iss": "waooaw.com",
            "sub": "user-555",
        },
        jwt_keys["private"],
        algorithm="RS256",
    )

    captured = {}

    class DummyClient:
        async def request(self, method, url, headers, content, follow_redirects):
            captured["method"] = method
            captured["url"] = url
            captured["headers"] = headers
            captured["content"] = content

            return httpx.Response(
                200,
                json={"receipts": []},
                headers={"content-type": "application/json"},
            )

    monkeypatch.setattr(gateway_main, "http_client", DummyClient())

    client = TestClient(gateway_main.app)
    res = client.get(
        "/api/v1/receipts?customer_id=evil-customer",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200
    assert captured["method"] == "GET"
    assert "/api/v1/receipts" in captured["url"]
    assert "customer_id=customer-rct" in captured["url"]
    assert "evil-customer" not in captured["url"]


@pytest.mark.unit
def test_proxy_rewrites_auth_google_verify_to_api_v1(monkeypatch):
    gateway_root = Path(__file__).resolve().parents[2]
    if str(gateway_root) not in sys.path:
        sys.path.insert(0, str(gateway_root))

    import main as gateway_main

    captured = {}

    class DummyClient:
        async def request(self, method, url, headers, content, follow_redirects):
            captured["method"] = method
            captured["url"] = url
            captured["headers"] = headers
            captured["content"] = content

            return httpx.Response(
                200,
                json={"access_token": "test", "refresh_token": "test"},
                headers={"content-type": "application/json"},
            )

    monkeypatch.setattr(gateway_main, "http_client", DummyClient())

    client = TestClient(gateway_main.app)
    res = client.post(
        "/auth/google/verify",
        json={"id_token": "mock", "source": "mobile"},
    )

    assert res.status_code == 200
    assert captured["method"] == "POST"
    assert captured["url"].endswith("/api/v1/auth/google/verify")


@pytest.mark.unit
def test_proxy_forces_customer_id_on_trial_status_routes(monkeypatch, jwt_keys):
    gateway_root = Path(__file__).resolve().parents[2]
    if str(gateway_root) not in sys.path:
        sys.path.insert(0, str(gateway_root))

    import main as gateway_main

    now = int(time.time())
    token = jwt.encode(
        {
            "user_id": "user-777",
            "email": "user777@example.com",
            "customer_id": "customer-trial",
            "roles": ["user"],
            "trial_mode": False,
            "iat": now,
            "exp": now + 3600,
            "iss": "waooaw.com",
            "sub": "user-777",
        },
        jwt_keys["private"],
        algorithm="RS256",
    )

    captured = {}

    class DummyClient:
        async def request(self, method, url, headers, content, follow_redirects):
            captured["method"] = method
            captured["url"] = url
            captured["headers"] = headers
            captured["content"] = content

            return httpx.Response(
                200,
                json={"trials": []},
                headers={"content-type": "application/json"},
            )

    monkeypatch.setattr(gateway_main, "http_client", DummyClient())

    client = TestClient(gateway_main.app)
    res = client.get(
        "/api/v1/trial-status?customer_id=evil-customer",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200
    assert captured["method"] == "GET"
    assert "/api/v1/trial-status" in captured["url"]
    assert "customer_id=customer-trial" in captured["url"]
    assert "evil-customer" not in captured["url"]


@pytest.mark.unit
def test_proxy_forces_customer_id_on_coupon_checkout_body(monkeypatch, jwt_keys):
    gateway_root = Path(__file__).resolve().parents[2]
    if str(gateway_root) not in sys.path:
        sys.path.insert(0, str(gateway_root))

    import main as gateway_main

    now = int(time.time())
    token = jwt.encode(
        {
            "user_id": "user-pay",
            "email": "pay@example.com",
            "customer_id": "customer-pay",
            "roles": ["user"],
            "trial_mode": False,
            "iat": now,
            "exp": now + 3600,
            "iss": "waooaw.com",
            "sub": "user-pay",
        },
        jwt_keys["private"],
        algorithm="RS256",
    )

    captured = {}

    class DummyClient:
        async def request(self, method, url, headers, content, follow_redirects):
            captured["method"] = method
            captured["url"] = url
            captured["headers"] = headers
            captured["content"] = content

            return httpx.Response(
                200,
                json={"order_id": "ORDER-1", "subscription_id": "SUB-1"},
                headers={"content-type": "application/json"},
            )

    monkeypatch.setattr(gateway_main, "http_client", DummyClient())

    client = TestClient(gateway_main.app)
    res = client.post(
        "/api/v1/payments/coupon/checkout",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "coupon_code": "WAOOAW100",
            "agent_id": "agent-123",
            "duration": "monthly",
            "customer_id": "evil-customer",
        },
    )

    assert res.status_code == 200
    assert captured["method"] == "POST"
    assert "/api/v1/payments/coupon/checkout" in captured["url"]

    forwarded = json.loads(captured["content"] or b"{}")
    assert forwarded["customer_id"] == "customer-pay"
    assert forwarded["customer_id"] != "evil-customer"


@pytest.mark.unit
def test_proxy_forces_customer_id_on_subscriptions_by_customer_path(monkeypatch, jwt_keys):
    gateway_root = Path(__file__).resolve().parents[2]
    if str(gateway_root) not in sys.path:
        sys.path.insert(0, str(gateway_root))

    import main as gateway_main

    now = int(time.time())
    token = jwt.encode(
        {
            "user_id": "user-sub",
            "email": "sub@example.com",
            "customer_id": "customer-scope",
            "roles": ["user"],
            "trial_mode": False,
            "iat": now,
            "exp": now + 3600,
            "iss": "waooaw.com",
            "sub": "user-sub",
        },
        jwt_keys["private"],
        algorithm="RS256",
    )

    captured = {}

    class DummyClient:
        async def request(self, method, url, headers, content, follow_redirects):
            captured["method"] = method
            captured["url"] = url
            captured["headers"] = headers
            captured["content"] = content

            return httpx.Response(
                200,
                json=[],
                headers={"content-type": "application/json"},
            )

    monkeypatch.setattr(gateway_main, "http_client", DummyClient())

    client = TestClient(gateway_main.app)
    res = client.get(
        "/api/v1/payments/subscriptions/by-customer/evil-customer",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200
    assert captured["method"] == "GET"
    assert "/api/v1/payments/subscriptions/by-customer/customer-scope" in captured["url"]
    assert "evil-customer" not in captured["url"]


@pytest.mark.unit
def test_proxy_forces_customer_id_on_hired_agents_by_subscription(monkeypatch, jwt_keys):
    gateway_root = Path(__file__).resolve().parents[2]
    if str(gateway_root) not in sys.path:
        sys.path.insert(0, str(gateway_root))

    import main as gateway_main

    now = int(time.time())
    token = jwt.encode(
        {
            "user_id": "user-hire",
            "email": "hire@example.com",
            "customer_id": "customer-hire",
            "roles": ["user"],
            "trial_mode": False,
            "iat": now,
            "exp": now + 3600,
            "iss": "waooaw.com",
            "sub": "user-hire",
        },
        jwt_keys["private"],
        algorithm="RS256",
    )

    captured = {}

    class DummyClient:
        async def request(self, method, url, headers, content, follow_redirects):
            captured["method"] = method
            captured["url"] = url
            captured["headers"] = headers
            captured["content"] = content

            return httpx.Response(
                200,
                json={"hired_instance_id": "HIRE-1"},
                headers={"content-type": "application/json"},
            )

    monkeypatch.setattr(gateway_main, "http_client", DummyClient())

    client = TestClient(gateway_main.app)
    res = client.get(
        "/api/v1/hired-agents/by-subscription/SUB-1?customer_id=evil-customer",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200
    assert captured["method"] == "GET"
    assert "/api/v1/hired-agents/by-subscription/SUB-1" in captured["url"]
    assert "customer_id=customer-hire" in captured["url"]
    assert "evil-customer" not in captured["url"]


@pytest.mark.unit
def test_proxy_forces_customer_id_on_hired_agents_draft_body(monkeypatch, jwt_keys):
    gateway_root = Path(__file__).resolve().parents[2]
    if str(gateway_root) not in sys.path:
        sys.path.insert(0, str(gateway_root))

    import main as gateway_main

    now = int(time.time())
    token = jwt.encode(
        {
            "user_id": "user-hire-draft",
            "email": "hire-draft@example.com",
            "customer_id": "customer-hire",
            "roles": ["user"],
            "trial_mode": False,
            "iat": now,
            "exp": now + 3600,
            "iss": "waooaw.com",
            "sub": "user-hire-draft",
        },
        jwt_keys["private"],
        algorithm="RS256",
    )

    captured = {}

    class DummyClient:
        async def request(self, method, url, headers, content, follow_redirects):
            captured["method"] = method
            captured["url"] = url
            captured["headers"] = headers
            captured["content"] = content

            return httpx.Response(
                200,
                json={"hired_instance_id": "HIRE-1"},
                headers={"content-type": "application/json"},
            )

    monkeypatch.setattr(gateway_main, "http_client", DummyClient())

    client = TestClient(gateway_main.app)
    res = client.put(
        "/api/v1/hired-agents/draft",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "subscription_id": "SUB-1",
            "agent_id": "agent-123",
            "customer_id": "evil-customer",
            "nickname": "N",
            "theme": "dark",
        },
    )

    assert res.status_code == 200
    assert captured["method"] == "PUT"
    assert "/api/v1/hired-agents/draft" in captured["url"]

    forwarded = json.loads(captured["content"] or b"{}")
    assert forwarded["customer_id"] == "customer-hire"
    assert forwarded["customer_id"] != "evil-customer"


@pytest.mark.unit
def test_proxy_forces_customer_id_on_hired_agents_finalize_body(monkeypatch, jwt_keys):
    gateway_root = Path(__file__).resolve().parents[2]
    if str(gateway_root) not in sys.path:
        sys.path.insert(0, str(gateway_root))

    import main as gateway_main

    now = int(time.time())
    token = jwt.encode(
        {
            "user_id": "user-hire-finalize",
            "email": "hire-finalize@example.com",
            "customer_id": "customer-hire",
            "roles": ["user"],
            "trial_mode": False,
            "iat": now,
            "exp": now + 3600,
            "iss": "waooaw.com",
            "sub": "user-hire-finalize",
        },
        jwt_keys["private"],
        algorithm="RS256",
    )

    captured = {}

    class DummyClient:
        async def request(self, method, url, headers, content, follow_redirects):
            captured["method"] = method
            captured["url"] = url
            captured["headers"] = headers
            captured["content"] = content

            return httpx.Response(
                200,
                json={"hired_instance_id": "HIRE-1"},
                headers={"content-type": "application/json"},
            )

    monkeypatch.setattr(gateway_main, "http_client", DummyClient())

    client = TestClient(gateway_main.app)
    res = client.post(
        "/api/v1/hired-agents/HIRE-1/finalize",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "customer_id": "evil-customer",
            "goals_completed": True,
        },
    )

    assert res.status_code == 200
    assert captured["method"] == "POST"
    assert "/api/v1/hired-agents/HIRE-1/finalize" in captured["url"]

    forwarded = json.loads(captured["content"] or b"{}")
    assert forwarded["customer_id"] == "customer-hire"
    assert forwarded["customer_id"] != "evil-customer"
