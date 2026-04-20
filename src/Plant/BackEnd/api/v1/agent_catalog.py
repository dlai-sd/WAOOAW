"""Plant-owned catalog lifecycle API for hire-ready agents."""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.agent_types_simple import get_agent_type_definition
from core.database import get_db_session, get_read_db_session
from core.routing import waooaw_router
from models.agent import Agent
from models.industry import Industry
from models.job_role import JobRole
from models.agent_catalog import AgentCatalogReleaseModel
from repositories.agent_catalog_repository import AgentCatalogRepository
from repositories.agent_type_repository import AgentTypeDefinitionRepository


router = waooaw_router(prefix="/catalog", tags=["catalog"])

DEFAULT_TRIAL_DAYS = 7
DEFAULT_ALLOWED_DURATIONS = ["monthly", "quarterly"]


class CatalogReleaseUpsertRequest(BaseModel):
    public_name: Optional[str] = None
    short_description: Optional[str] = None
    monthly_price_inr: Optional[int] = Field(default=None, ge=0)
    trial_days: Optional[int] = Field(default=None, ge=0)
    allowed_durations: Optional[list[str]] = None
    supported_channels: Optional[list[str]] = None
    approval_mode: Optional[str] = None
    external_catalog_version: Optional[str] = None
    agent_type_id: Optional[str] = None
    internal_definition_version_id: Optional[str] = None


class CatalogAgentResponse(BaseModel):
    release_id: str
    id: str
    public_name: str
    short_description: str
    industry_name: str
    job_role_label: str
    monthly_price_inr: int
    trial_days: int
    allowed_durations: list[str]
    supported_channels: list[str]
    approval_mode: str
    agent_type_id: str
    internal_definition_version_id: str | None = None
    external_catalog_version: str
    lifecycle_state: str
    approved_for_new_hire: bool
    retired_from_catalog_at: str | None = None


def _compute_monthly_price_inr(industry_display_name: Optional[str]) -> int:
    industry_key = (industry_display_name or "").strip().lower()
    if industry_key == "marketing":
        return 12000
    if industry_key == "education":
        return 8000
    if industry_key == "sales":
        return 15000
    return 12000


def _default_short_description(public_name: str, job_role_label: str, industry_name: str) -> str:
    return f"{public_name} for {industry_name.lower()} workflows, packaged as a hire-ready {job_role_label.lower()} release."


def _infer_agent_type_id(agent_ref: str) -> str | None:
    normalized = str(agent_ref or "").strip().upper()
    if normalized.startswith("AGT-MKT-"):
        return "marketing.digital_marketing.v1"
    if normalized.startswith("AGT-TRD-"):
        return "trading.share_trader.v1"
    return None


async def _resolve_agent_listing_row(*, agent_id: str, db: AsyncSession) -> dict[str, Any]:
    normalized_agent_id = (agent_id or "").strip()
    if not normalized_agent_id:
        raise HTTPException(status_code=400, detail="agent_id is required.")

    maybe_uuid: UUID | None = None
    try:
        maybe_uuid = UUID(normalized_agent_id)
    except Exception:
        maybe_uuid = None

    clauses = [Agent.external_id == normalized_agent_id]
    if maybe_uuid is not None:
        clauses.append(Agent.id == maybe_uuid)

    stmt = (
        select(Agent, Industry.name.label("industry_name"), JobRole.name.label("job_role_label"))
        .join(Industry, Agent.industry_id == Industry.id)
        .join(JobRole, Agent.job_role_id == JobRole.id)
        .where(Agent.status == "active")
        .where(or_(*clauses))
    )
    result = await db.execute(stmt)
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Agent not found.")

    agent_model: Agent = row[0]
    agent_ref = str(getattr(agent_model, "external_id", None) or agent_model.id)
    return {
        "agent_id": agent_ref,
        "name": agent_model.name,
        "industry_name": row[1],
        "job_role_label": row[2],
    }


async def _resolve_definition_version(*, db: AsyncSession, agent_type_id: str) -> str | None:
    repo = AgentTypeDefinitionRepository(db)
    definition = await repo.get_by_id(agent_type_id)
    if definition is not None:
        return definition.version

    in_memory = get_agent_type_definition(agent_type_id)
    if in_memory is not None:
        return in_memory.version
    return None


def _to_catalog_response(model: AgentCatalogReleaseModel) -> CatalogAgentResponse:
    retired = model.retired_from_catalog_at.isoformat() if model.retired_from_catalog_at else None
    return CatalogAgentResponse(
        release_id=model.release_id,
        id=model.agent_id,
        public_name=model.public_name,
        short_description=model.short_description,
        industry_name=model.industry_name,
        job_role_label=model.job_role_label,
        monthly_price_inr=int(model.monthly_price_inr),
        trial_days=int(model.trial_days),
        allowed_durations=list(model.allowed_durations or []),
        supported_channels=list(model.supported_channels or []),
        approval_mode=model.approval_mode,
        agent_type_id=model.agent_type_id,
        internal_definition_version_id=model.internal_definition_version_id,
        external_catalog_version=model.external_catalog_version,
        lifecycle_state=model.lifecycle_state,
        approved_for_new_hire=bool(model.approved_for_new_hire),
        retired_from_catalog_at=retired,
    )


@router.get("/agents", response_model=list[CatalogAgentResponse])
async def list_catalog_agents(
    db: AsyncSession = Depends(get_read_db_session),
) -> list[CatalogAgentResponse]:
    repo = AgentCatalogRepository(db)
    releases = await repo.list_live_releases()
    return [_to_catalog_response(release) for release in releases]


@router.get("/agents/{agent_id}", response_model=CatalogAgentResponse)
async def get_catalog_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_read_db_session),
) -> CatalogAgentResponse:
    """Return the live catalog entry for a single agent by its string catalog ID (e.g. AGT-MKT-DMA-001)."""
    repo = AgentCatalogRepository(db)
    release = await repo.get_live_release_for_agent_id(agent_id)
    if not release:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found in catalog.")
    return _to_catalog_response(release)


@router.get("/releases", response_model=list[CatalogAgentResponse])
async def list_catalog_releases(
    db: AsyncSession = Depends(get_read_db_session),
) -> list[CatalogAgentResponse]:
    repo = AgentCatalogRepository(db)
    releases = await repo.list_releases()
    return [_to_catalog_response(release) for release in releases]


@router.put("/agents/{agent_id}/release", response_model=CatalogAgentResponse)
async def upsert_catalog_release(
    agent_id: str,
    body: CatalogReleaseUpsertRequest,
    db: AsyncSession = Depends(get_db_session),
) -> CatalogAgentResponse:
    listing = await _resolve_agent_listing_row(agent_id=agent_id, db=db)
    agent_ref = listing["agent_id"]

    repo = AgentCatalogRepository(db)
    latest = await repo.get_latest_for_agent_id(agent_ref)

    resolved_agent_type_id = (
        body.agent_type_id
        or (latest.agent_type_id if latest is not None else None)
        or _infer_agent_type_id(agent_ref)
    )
    if not resolved_agent_type_id:
        raise HTTPException(status_code=422, detail="agent_type_id is required for catalog release.")

    release = await repo.upsert_release(
        agent_id=agent_ref,
        agent_type_id=resolved_agent_type_id,
        internal_definition_version_id=(
            body.internal_definition_version_id
            or (latest.internal_definition_version_id if latest is not None else None)
            or await _resolve_definition_version(db=db, agent_type_id=resolved_agent_type_id)
        ),
        external_catalog_version=(
            body.external_catalog_version
            or (latest.external_catalog_version if latest is not None else "v1")
        ),
        public_name=body.public_name or listing["name"],
        short_description=(
            body.short_description
            or (latest.short_description if latest is not None else _default_short_description(listing["name"], listing["job_role_label"], listing["industry_name"]))
        ),
        industry_name=listing["industry_name"],
        job_role_label=listing["job_role_label"],
        monthly_price_inr=(
            body.monthly_price_inr
            if body.monthly_price_inr is not None
            else (latest.monthly_price_inr if latest is not None else _compute_monthly_price_inr(listing["industry_name"]))
        ),
        trial_days=(
            body.trial_days
            if body.trial_days is not None
            else (latest.trial_days if latest is not None else DEFAULT_TRIAL_DAYS)
        ),
        allowed_durations=body.allowed_durations or (list(latest.allowed_durations or []) if latest is not None else list(DEFAULT_ALLOWED_DURATIONS)),
        supported_channels=body.supported_channels or (list(latest.supported_channels or []) if latest is not None else []),
        approval_mode=body.approval_mode or (latest.approval_mode if latest is not None else "manual_review"),
    )
    await db.commit()
    return _to_catalog_response(release)


@router.post("/agents/{agent_id}/approve", response_model=CatalogAgentResponse)
async def approve_catalog_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> CatalogAgentResponse:
    listing = await _resolve_agent_listing_row(agent_id=agent_id, db=db)
    repo = AgentCatalogRepository(db)

    release = await repo.get_latest_for_agent_id(listing["agent_id"])
    if release is None:
        inferred_type = _infer_agent_type_id(listing["agent_id"])
        if not inferred_type:
            raise HTTPException(status_code=422, detail="agent_type_id is required before approval.")
        release = await repo.upsert_release(
            agent_id=listing["agent_id"],
            agent_type_id=inferred_type,
            internal_definition_version_id=await _resolve_definition_version(db=db, agent_type_id=inferred_type),
            external_catalog_version="v1",
            public_name=listing["name"],
            short_description=_default_short_description(listing["name"], listing["job_role_label"], listing["industry_name"]),
            industry_name=listing["industry_name"],
            job_role_label=listing["job_role_label"],
            monthly_price_inr=_compute_monthly_price_inr(listing["industry_name"]),
            trial_days=DEFAULT_TRIAL_DAYS,
            allowed_durations=list(DEFAULT_ALLOWED_DURATIONS),
            supported_channels=[],
            approval_mode="manual_review",
        )

    approved = await repo.approve_release(release.release_id)
    await db.commit()
    return _to_catalog_response(approved)


@router.post("/releases/{release_id}/retire", response_model=CatalogAgentResponse)
async def retire_catalog_release(
    release_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> CatalogAgentResponse:
    repo = AgentCatalogRepository(db)
    try:
        retired = await repo.retire_release(release_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Catalog release not found.")
    await db.commit()
    return _to_catalog_response(retired)
