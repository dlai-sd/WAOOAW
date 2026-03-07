"""Deterministic trading executor (MVP).

Produces a draft order intent plan, and can optionally execute the action
when an explicit intent_action is provided *and* an approval_id is present.

External side effects are expected to be approval-gated by hooks in later stories.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Optional, Protocol

from pydantic import BaseModel, Field

from agent_mold.processor import BaseProcessor, ProcessorInput, ProcessorOutput
from agent_mold.skills.playbook import SkillPlaybook

if TYPE_CHECKING:
    from agent_mold.hooks import HookBus


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


class TradingExecutor(BaseProcessor):
    """BaseProcessor implementation for trading agents.

    Adapter shim: unpacks ProcessorInput.goal_config and delegates to
    execute_trading_delta_futures_manual_v1 in draft-only mode (no approval_id
    present means draft). Returns ProcessorOutput wrapping TradingExecutionResult.
    """

    async def process(self, input_data: ProcessorInput, hook_bus: "HookBus") -> ProcessorOutput:
        """Execute trading logic from goal_config. Draft-only unless approval_id provided.

        Adapter shim: unpacks ProcessorInput.goal_config to build a TradingExecutionContext.
        Actual execution is delegated to execute_trading_delta_futures_manual_v1.
        """
        cfg = input_data.goal_config

        ctx = TradingExecutionContext(
            intent_action=cfg.get("intent_action"),
            approval_id=cfg.get("approval_id"),
        )

        # Build a minimal duck-typed playbook container for the legacy function
        playbook_id = cfg.get("playbook_id", "TRADING.DELTA.FUTURES.MANUAL.V1")

        class _PlaybookRef:
            class metadata:
                pass
        _PlaybookRef.metadata.playbook_id = playbook_id  # type: ignore[attr-defined]

        result = execute_trading_delta_futures_manual_v1(
            playbook=_PlaybookRef(),  # type: ignore[arg-type]
            exchange_provider=cfg.get("exchange_provider", "delta_exchange_india"),
            exchange_account_id=cfg.get("exchange_account_id", "default"),
            coin=cfg.get("coin", "BTC"),
            units=float(cfg.get("units", 1)),
            side=cfg.get("side", "long"),
            action=cfg.get("action", "enter"),
            market=bool(cfg.get("market", True)),
            limit_price=cfg.get("limit_price"),
            ctx=ctx,
            delta_client=cfg.get("delta_client"),
        )

        return ProcessorOutput(
            result=result,
            metadata={"processor_type": self.processor_type()},
            correlation_id=input_data.correlation_id,
        )

