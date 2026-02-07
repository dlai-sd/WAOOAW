"""Customer-scoped trading approval routes (CP).

Story TR-CP-2.1: Customer reviews a proposed trade plan, then approves execution.

Implementation notes:
- CP injects customer_id derived from authenticated user.
- CP mints an approval_id locally and forwards it to Plant.
- CP never forwards raw exchange credentials to Plant (only an opaque ref).
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from api.auth.dependencies import get_current_user
from models.user import User
from services.cp_approvals import FileCPApprovalStore, get_cp_approval_store
from services.plant_gateway_client import PlantGatewayClient


router = APIRouter(prefix="/cp/trading", tags=["cp-trading"])


def _customer_id_from_user(user: User) -> str:
    return f"CUST-{user.id}"


def get_plant_gateway_client() -> PlantGatewayClient:
    base_url = os.getenv("PLANT_GATEWAY_URL", "http://localhost:8000")
    return PlantGatewayClient(base_url=base_url)


def _forward_headers(request: Request) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    auth = request.headers.get("authorization")
    if auth:
        headers["Authorization"] = auth
    correlation = request.headers.get("x-correlation-id")
    if correlation:
        headers["X-Correlation-ID"] = correlation
    debug = request.headers.get("x-debug-trace")
    if debug:
        headers["X-Debug-Trace"] = debug
    return headers


class DraftTradePlanRequest(BaseModel):
    agent_id: str = Field(default="AGT-TRD-DELTA-001", min_length=1)

    exchange_account_id: str = Field(..., min_length=1)
    coin: str = Field(..., min_length=1)
    units: float = Field(..., gt=0)
    side: str = Field(..., min_length=1)  # long|short
    action: str = Field(..., min_length=1)  # enter|exit

    market: Optional[bool] = None
    limit_price: Optional[float] = Field(default=None, gt=0)


class ApproveAndExecuteTradeRequest(DraftTradePlanRequest):
    intent_action: str = Field(..., min_length=1)  # place_order|close_position


@router.post("/draft-plan", response_model=Dict[str, Any])
async def draft_trade_plan(
    body: DraftTradePlanRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    plant: PlantGatewayClient = Depends(get_plant_gateway_client),
) -> Dict[str, Any]:
    customer_id = _customer_id_from_user(current_user)

    resp = await plant.request_json(
        method="POST",
        path=f"api/v1/reference-agents/{body.agent_id}/run",
        headers=_forward_headers(request),
        json_body={
            "customer_id": customer_id,
            "exchange_account_id": body.exchange_account_id,
            "coin": body.coin,
            "units": body.units,
            "side": body.side,
            "action": body.action,
            "market": body.market,
            "limit_price": body.limit_price,
        },
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json)

    if isinstance(resp.json, dict):
        return resp.json
    return {"status": "unknown", "draft": resp.json}


@router.post("/approve-execute", response_model=Dict[str, Any])
async def approve_and_execute_trade(
    body: ApproveAndExecuteTradeRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    plant: PlantGatewayClient = Depends(get_plant_gateway_client),
    approvals: FileCPApprovalStore = Depends(get_cp_approval_store),
) -> Dict[str, Any]:
    customer_id = _customer_id_from_user(current_user)

    approval = approvals.append(
        customer_id=customer_id,
        subject_type="trading_intent",
        subject_id=f"{body.agent_id}:{body.exchange_account_id}:{body.coin}:{body.side}:{body.action}",
        action=body.intent_action,
        decision="approved",
    )

    resp = await plant.request_json(
        method="POST",
        path=f"api/v1/reference-agents/{body.agent_id}/run",
        headers=_forward_headers(request),
        json_body={
            "customer_id": customer_id,
            "intent_action": body.intent_action,
            "approval_id": approval.approval_id,
            "exchange_account_id": body.exchange_account_id,
            "coin": body.coin,
            "units": body.units,
            "side": body.side,
            "action": body.action,
            "market": body.market,
            "limit_price": body.limit_price,
        },
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json)

    if isinstance(resp.json, dict):
        return resp.json
    return {"status": "unknown", "draft": resp.json, "approval_id": approval.approval_id}
