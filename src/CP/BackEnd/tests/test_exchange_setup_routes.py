from __future__ import annotations

from pathlib import Path


def test_exchange_setup_upsert_and_list(client, auth_headers, monkeypatch, tmp_path: Path):
    store_path = tmp_path / "cp_exchange_setups.jsonl"
    monkeypatch.setenv("CP_EXCHANGE_SETUP_STORE_PATH", str(store_path))
    monkeypatch.setenv("CP_EXCHANGE_SETUP_SECRET", "test-secret")

    from services import exchange_setup as svc

    svc.default_exchange_setup_store.cache_clear()

    upsert = client.put(
        "/api/cp/exchange-setup",
        headers=auth_headers,
        json={
            "exchange_provider": "delta_exchange_india",
            "api_key": "k1",
            "api_secret": "s1",
            "default_coin": "btc",
            "allowed_coins": ["btc", "eth"],
            "max_units_per_order": 2,
            "max_notional_inr": 100000,
        },
    )
    assert upsert.status_code == 200
    body = upsert.json()
    assert body["exchange_provider"] == "delta_exchange_india"
    assert body["credential_ref"].startswith("EXCH-")
    assert body["default_coin"] == "BTC"
    assert body["allowed_coins"] == ["BTC", "ETH"]
    assert body["risk_limits"]["max_units_per_order"] == 2
    assert body["risk_limits"]["max_notional_inr"] == 100000

    # Secrets must never be returned.
    assert "api_key" not in body
    assert "api_secret" not in body

    listed = client.get("/api/cp/exchange-setup", headers=auth_headers)
    assert listed.status_code == 200
    rows = listed.json()
    assert isinstance(rows, list)
    assert len(rows) == 1
    assert rows[0]["credential_ref"] == body["credential_ref"]
