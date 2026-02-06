from pathlib import Path

import pytest

from agent_mold.skills.loader import load_playbook
from agent_mold.skills.trading_executor import (
    TradingExecutionContext,
    TradingIntentAction,
    execute_trading_delta_futures_manual_v1,
)


class _FakeDeltaClient:
    def __init__(self):
        self.calls = []

    def place_order(self, payload):
        self.calls.append(("place_order", payload))
        return {"ok": True, "order_id": "ORD-1"}

    def close_position(self, payload):
        self.calls.append(("close_position", payload))
        return {"ok": True, "closed": True}


def _load_trading_playbook():
    backend_root = Path(__file__).resolve().parents[2]
    playbook_path = backend_root / "agent_mold" / "playbooks" / "trading" / "delta_futures_manual_v1.md"
    return load_playbook(playbook_path)


def test_trading_executor_returns_draft_without_intent_action_or_approval():
    playbook = _load_trading_playbook()
    res = execute_trading_delta_futures_manual_v1(
        playbook,
        exchange_provider="delta_exchange_india",
        exchange_account_id="EXCH-1",
        coin="btc",
        units=1,
        side="long",
        action="enter",
        market=True,
        limit_price=None,
        ctx=TradingExecutionContext(intent_action=None, approval_id=None),
        delta_client=None,
    )

    assert res.draft_only is True
    assert res.executed is False
    assert res.intent.coin == "BTC"


def test_trading_executor_executes_when_intent_action_and_approval_present():
    playbook = _load_trading_playbook()
    client = _FakeDeltaClient()
    res = execute_trading_delta_futures_manual_v1(
        playbook,
        exchange_provider="delta_exchange_india",
        exchange_account_id="EXCH-1",
        coin="ETH",
        units=2,
        side="short",
        action="enter",
        market=True,
        limit_price=None,
        ctx=TradingExecutionContext(
            intent_action=TradingIntentAction.PLACE_ORDER,
            approval_id="APR-1",
        ),
        delta_client=client,
    )

    assert res.draft_only is False
    assert res.executed is True
    assert res.execution and res.execution.get("order_id") == "ORD-1"
    assert client.calls and client.calls[0][0] == "place_order"


@pytest.mark.parametrize(
    "side,action",
    [
        ("buy", "enter"),
        ("long", "open"),
    ],
)
def test_trading_executor_rejects_invalid_side_or_action(side, action):
    playbook = _load_trading_playbook()
    with pytest.raises(ValueError):
        execute_trading_delta_futures_manual_v1(
            playbook,
            exchange_provider="delta_exchange_india",
            exchange_account_id="EXCH-1",
            coin="BTC",
            units=1,
            side=side,
            action=action,
            market=True,
            limit_price=None,
            ctx=TradingExecutionContext(),
            delta_client=None,
        )
