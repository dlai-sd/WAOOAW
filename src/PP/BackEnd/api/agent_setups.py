"""AgentSetup endpoints (PP).

Phase 1: admin config that ties a customer + agent to channel allowlist and
credential references.

These values are PP-owned; Plant should only ever receive *references*.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field

from services.agent_setups import AgentSetup, FileAgentSetupStore, get_agent_setup_store


from core.authorization import require_role
from core.routing import waooaw_router  # PP-N3b
from services.audit_dependency import AuditLogger, get_audit_logger  # PP-N4

router = waooaw_router(prefix="/agent-setups", tags=["agent-setups"])


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
    audit: AuditLogger = Depends(get_audit_logger),
) -> AgentSetupResponse:
    setup = AgentSetup(
        customer_id=body.customer_id,
        agent_id=body.agent_id,
        channels=body.channels,
        posting_identity=body.posting_identity,
        credential_refs=body.credential_refs,
    )
    saved = store.upsert(setup)
    await audit.log(
        screen="pp_agent_setups",
        action="agent_setup_upserted",
        outcome="success",
        detail=f"customer_id={body.customer_id} agent_id={body.agent_id}",
    )
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


class ConstraintPolicyPatch(BaseModel):
    """Partial update for ConstraintPolicy — all fields optional."""

    approval_mode: Optional[str] = None
    max_tasks_per_day: Optional[int] = None
    max_position_size_inr: Optional[float] = None
    trial_task_limit: Optional[int] = None


@router.patch("/{agent_setup_id}/constraint-policy", response_model=dict)
async def update_constraint_policy(
    agent_setup_id: str,
    patch: ConstraintPolicyPatch,
    _auth=Depends(require_role("admin")),
    audit: AuditLogger = Depends(get_audit_logger),
    store: FileAgentSetupStore = Depends(get_agent_setup_store),
) -> dict:
    """Update ConstraintPolicy fields for an agent setup.

    Uses partial update (PATCH semantics) — only provided fields are changed.
    Writes mandatory audit record including agent_setup_id and changed fields.
    Requires admin role.
    """
    patch_data = patch.model_dump(exclude_none=True)
    if not patch_data:
        raise HTTPException(status_code=422, detail="No fields provided to update")

    updated = store.patch_constraint_policy(agent_setup_id, patch_data)
    if updated is None:
        raise HTTPException(status_code=404, detail="AgentSetup not found")

    await audit.log(
        screen="agent_setups",
        action="constraint_policy_patch",
        outcome="success",
        metadata={
            "agent_setup_id": agent_setup_id,
            "changed_fields": list(patch_data.keys()),
        },
    )
    return {
        "agent_setup_id": agent_setup_id,
        "constraint_policy": updated.constraint_policy or {},
    }


@router.get("/{agent_setup_id}/constraint-policy", response_model=dict)
async def get_constraint_policy(
    agent_setup_id: str,
    _auth=Depends(require_role("developer")),
    store: FileAgentSetupStore = Depends(get_agent_setup_store),
) -> dict:
    """Returns current ConstraintPolicy for the given agent type setup.

    developer+ can READ; admin required to PATCH.
    agent_setup_id must be in '{customer_id}:{agent_id}' format.
    """
    setup = store.get_by_composite_id(agent_setup_id)
    if setup is None:
        raise HTTPException(status_code=404, detail="AgentSetup not found")
    return {
        "agent_setup_id": agent_setup_id,
        "constraint_policy": setup.constraint_policy or {},
    }
