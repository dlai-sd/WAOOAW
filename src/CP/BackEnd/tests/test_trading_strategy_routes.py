from __future__ import annotations

from pathlib import Path


def test_trading_strategy_upsert_and_list(client, auth_headers, monkeypatch, tmp_path: Path):
    store_path = tmp_path / "cp_trading_strategy.jsonl"
    monkeypatch.setenv("CP_TRADING_STRATEGY_STORE_PATH", str(store_path))

    from services import trading_strategy as svc

    svc.default_trading_strategy_config_store.cache_clear()

    upsert = client.put(
        "/api/cp/trading-strategy",
        headers=auth_headers,
        json={
            "agent_id": "AGT-TRD-DELTA-001",
            "interval_seconds": 300,
            "active_window_start": "09:15",
            "active_window_end": "15:30",
            "strategy_params": {"mode": "paper", "risk_profile": "low"},
        },
    )
    assert upsert.status_code == 200
    body = upsert.json()
    assert body["config_ref"].startswith("STRAT-")
    assert body["agent_id"] == "AGT-TRD-DELTA-001"
    assert body["interval_seconds"] == 300
    assert body["active_window"]["start"] == "09:15"
    assert body["metadata"]["strategy_params"]["mode"] == "paper"

    listed = client.get("/api/cp/trading-strategy", headers=auth_headers)
    assert listed.status_code == 200
    rows = listed.json()
    assert isinstance(rows, list)
    assert len(rows) == 1
    assert rows[0]["config_ref"] == body["config_ref"]
    assert rows[0]["metadata"]["strategy_params"]["risk_profile"] == "low"
