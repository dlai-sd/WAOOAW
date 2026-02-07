"""Trading strategy configuration routes (CP).

Story TR-CP-3.1: Store interval/time-window strategy parameters. No execution
happens here; trading execution remains approval-gated.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from api.auth.dependencies import get_current_user
from models.user import User
from services.trading_strategy import (
    ActiveWindow,
    FileTradingStrategyConfigStore,
    TradingStrategyConfigPublic,
    get_trading_strategy_config_store,
)


router = APIRouter(prefix="/cp/trading-strategy", tags=["cp-trading-strategy"])


def _customer_id_from_user(user: User) -> str:
    return f"CUST-{user.id}"


class UpsertTradingStrategyConfigRequest(BaseModel):
    config_ref: Optional[str] = None
    agent_id: str = Field(default="AGT-TRD-DELTA-001", min_length=1)

    interval_seconds: Optional[int] = Field(default=None, gt=0)
    active_window_start: Optional[str] = None
    active_window_end: Optional[str] = None

    strategy_params: Optional[Dict[str, Any]] = None


class TradingStrategyConfigResponse(TradingStrategyConfigPublic):
    pass


@router.put("", response_model=TradingStrategyConfigResponse)
async def upsert_trading_strategy_config(
    body: UpsertTradingStrategyConfigRequest,
    current_user: User = Depends(get_current_user),
    store: FileTradingStrategyConfigStore = Depends(get_trading_strategy_config_store),
) -> TradingStrategyConfigResponse:
    active_window: Optional[ActiveWindow] = None
    if body.active_window_start and body.active_window_end:
        active_window = ActiveWindow(start=body.active_window_start, end=body.active_window_end)

    model = store.upsert(
        customer_id=_customer_id_from_user(current_user),
        agent_id=body.agent_id,
        interval_seconds=body.interval_seconds,
        active_window=active_window,
        metadata={"strategy_params": body.strategy_params} if body.strategy_params is not None else {},
        config_ref=(body.config_ref or None),
    )
    return TradingStrategyConfigResponse(**model.model_dump())


@router.get("", response_model=List[TradingStrategyConfigResponse])
async def list_trading_strategy_configs(
    agent_id: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    store: FileTradingStrategyConfigStore = Depends(get_trading_strategy_config_store),
) -> List[TradingStrategyConfigResponse]:
    rows = store.list(customer_id=_customer_id_from_user(current_user), agent_id=agent_id, limit=limit)
    return [TradingStrategyConfigResponse(**r.model_dump()) for r in rows]
