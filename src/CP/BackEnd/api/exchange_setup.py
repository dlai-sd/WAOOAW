"""CP exchange setup routes.

Story TR-CP-1.1: Customer connects Delta Exchange keys and sets basic
parameters (coins + risk limits). CP returns an opaque `credential_ref` and
never returns secrets.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from api.auth.dependencies import get_current_user
from models.user import User
from services.exchange_setup import (
    ExchangeSetupPublic,
    FileExchangeSetupStore,
    RiskLimits,
    get_exchange_setup_store,
)


router = APIRouter(prefix="/cp/exchange-setup", tags=["cp-exchange-setup"])


def _customer_id_from_user(user: User) -> str:
    return f"CUST-{user.id}"


def _normalize_coin(value: str) -> str:
    return str(value or "").strip().upper()


def _normalize_coins(values: List[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for raw in values or []:
        coin = _normalize_coin(raw)
        if not coin:
            continue
        if coin in seen:
            continue
        seen.add(coin)
        out.append(coin)
    return out


class UpsertExchangeSetupRequest(BaseModel):
    credential_ref: Optional[str] = None
    exchange_provider: str = Field(default="delta_exchange_india", min_length=1)

    api_key: str = Field(..., min_length=1)
    api_secret: str = Field(..., min_length=1)

    default_coin: str = Field(..., min_length=1)
    allowed_coins: Optional[List[str]] = None

    max_units_per_order: float = Field(..., gt=0)
    max_notional_inr: Optional[float] = Field(default=None, gt=0)


class ExchangeSetupResponse(ExchangeSetupPublic):
    pass


@router.put("", response_model=ExchangeSetupResponse)
async def upsert_exchange_setup(
    body: UpsertExchangeSetupRequest,
    current_user: User = Depends(get_current_user),
    store: FileExchangeSetupStore = Depends(get_exchange_setup_store),
) -> ExchangeSetupResponse:
    default_coin = _normalize_coin(body.default_coin)
    allowed = _normalize_coins(body.allowed_coins or [])
    if not allowed:
        allowed = [default_coin]
    if default_coin and default_coin not in allowed:
        allowed = [default_coin, *allowed]

    model = store.upsert(
        customer_id=_customer_id_from_user(current_user),
        exchange_provider=body.exchange_provider,
        api_key=body.api_key,
        api_secret=body.api_secret,
        default_coin=default_coin,
        allowed_coins=allowed,
        risk_limits=RiskLimits(
            max_units_per_order=body.max_units_per_order,
            max_notional_inr=body.max_notional_inr,
        ),
        metadata={},
        credential_ref=(body.credential_ref or None),
    )

    return ExchangeSetupResponse(**model.model_dump())


@router.get("", response_model=List[ExchangeSetupResponse])
async def list_exchange_setups(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    store: FileExchangeSetupStore = Depends(get_exchange_setup_store),
) -> List[ExchangeSetupResponse]:
    rows = store.list(customer_id=_customer_id_from_user(current_user), limit=limit)
    return [ExchangeSetupResponse(**r.model_dump()) for r in rows]
