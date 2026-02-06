"""AgentSetup endpoints (PP).

Phase 1: admin config that ties a customer + agent to channel allowlist and
credential references.

These values are PP-owned; Plant should only ever receive *references*.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from services.agent_setups import AgentSetup, FileAgentSetupStore, get_agent_setup_store


router = APIRouter(prefix="/agent-setups", tags=["agent-setups"])


class UpsertAgentSetupRequest(BaseModel):
    customer_id: str = Field(..., min_length=1)
    agent_id: str = Field(..., min_length=1)

    channels: List[str] = Field(default_factory=list)
    posting_identity: Optional[str] = None

    credential_refs: Dict[str, str] = Field(default_factory=dict)


class AgentSetupResponse(BaseModel):
    customer_id: str
    agent_id: str
    channels: List[str]
    posting_identity: Optional[str] = None
    credential_refs: Dict[str, str]
    created_at: str
    updated_at: str


def _to_response(model: AgentSetup) -> AgentSetupResponse:
    return AgentSetupResponse(
        customer_id=model.customer_id,
        agent_id=model.agent_id,
        channels=list(model.channels or []),
        posting_identity=model.posting_identity,
        credential_refs=dict(model.credential_refs or {}),
        created_at=model.created_at.isoformat(),
        updated_at=model.updated_at.isoformat(),
    )


@router.put("", response_model=AgentSetupResponse)
async def upsert_agent_setup(
    body: UpsertAgentSetupRequest,
    store: FileAgentSetupStore = Depends(get_agent_setup_store),
) -> AgentSetupResponse:
    setup = AgentSetup(
        customer_id=body.customer_id,
        agent_id=body.agent_id,
        channels=body.channels,
        posting_identity=body.posting_identity,
        credential_refs=body.credential_refs,
    )
    saved = store.upsert(setup)
    return _to_response(saved)


class AgentSetupListResponse(BaseModel):
    count: int
    setups: List[Dict[str, Any]]


@router.get("", response_model=AgentSetupListResponse)
async def list_agent_setups(
    customer_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    limit: int = 100,
    store: FileAgentSetupStore = Depends(get_agent_setup_store),
) -> AgentSetupListResponse:
    setups = store.list(customer_id=customer_id, agent_id=agent_id, limit=limit)
    return AgentSetupListResponse(count=len(setups), setups=[_to_response(s).model_dump(mode="json") for s in setups])
