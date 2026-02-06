"""Deterministic trading executor (MVP).

Produces a draft order intent plan, and can optionally execute the action
when an explicit intent_action is provided *and* an approval_id is present.

External side effects are expected to be approval-gated by hooks in later stories.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol

from pydantic import BaseModel, Field

from agent_mold.skills.playbook import SkillPlaybook


class TradingIntentAction(str):
    PLACE_ORDER = "place_order"
    CLOSE_POSITION = "close_position"


class TradingOrderIntent(BaseModel):
    exchange_provider: str = Field(..., min_length=1)
    exchange_account_id: str = Field(..., min_length=1)
    coin: str = Field(..., min_length=1)
    units: float = Field(..., gt=0)
    side: str = Field(..., min_length=1)  # long|short
    action: str = Field(..., min_length=1)  # enter|exit
    order_type: str = Field(..., min_length=1)  # market|limit
    limit_price: Optional[float] = Field(default=None, gt=0)


class TradingExecutionResult(BaseModel):
    playbook_id: str
    draft_only: bool
    intent: TradingOrderIntent
    executed: bool = False
    execution: Optional[Dict[str, Any]] = None
    debug: Dict[str, Any] = Field(default_factory=dict)


class DeltaClient(Protocol):
    def place_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def close_position(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError


@dataclass(frozen=True)
class TradingExecutionContext:
    intent_action: Optional[str] = None
    approval_id: Optional[str] = None


def execute_trading_delta_futures_manual_v1(
    playbook: SkillPlaybook,
    *,
    exchange_provider: str,
    exchange_account_id: str,
    coin: str,
    units: float,
    side: str,
    action: str,
    market: bool,
    limit_price: Optional[float],
    ctx: TradingExecutionContext,
    delta_client: Optional[DeltaClient] = None,
) -> TradingExecutionResult:
    coin_norm = coin.strip().upper()
    side_norm = side.strip().lower()
    action_norm = action.strip().lower()

    if side_norm not in {"long", "short"}:
        raise ValueError("side must be one of ['long','short']")
    if action_norm not in {"enter", "exit"}:
        raise ValueError("action must be one of ['enter','exit']")

    order_type = "market" if market else "limit"
    if not market:
        if limit_price is None:
            raise ValueError("limit_price is required when market=false")
        if float(limit_price) <= 0:
            raise ValueError("limit_price must be > 0")

    intent = TradingOrderIntent(
        exchange_provider=exchange_provider,
        exchange_account_id=exchange_account_id,
        coin=coin_norm,
        units=float(units),
        side=side_norm,
        action=action_norm,
        order_type=order_type,
        limit_price=None if market else float(limit_price),
    )

    # Draft-only by default.
    should_execute = bool(ctx.intent_action and ctx.approval_id)
    if not should_execute:
        return TradingExecutionResult(
            playbook_id=playbook.metadata.playbook_id,
            draft_only=True,
            intent=intent,
            executed=False,
            execution=None,
            debug={"mode": "draft"},
        )

    if delta_client is None:
        raise ValueError("delta_client is required for execution")

    payload = intent.model_dump(mode="json")
    payload["approval_id"] = ctx.approval_id

    if ctx.intent_action == TradingIntentAction.PLACE_ORDER:
        execution = delta_client.place_order(payload)
    elif ctx.intent_action == TradingIntentAction.CLOSE_POSITION:
        execution = delta_client.close_position(payload)
    else:
        raise ValueError("Unsupported intent_action")

    return TradingExecutionResult(
        playbook_id=playbook.metadata.playbook_id,
        draft_only=False,
        intent=intent,
        executed=True,
        execution=execution,
        debug={"mode": "executed", "intent_action": ctx.intent_action},
    )
