from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1 import hired_agents_simple
from api.v1.platform_connections import get_connected_platform_connection
from core.routing import waooaw_router
from repositories.hired_agent_repository import HiredAgentRepository


router = waooaw_router(prefix="/hired-agents", tags=["digital-marketing-activation"])

_WORKSPACE_KEY = "digital_marketing_activation"
_DIGITAL_MARKETING_AGENT_TYPE = "marketing.digital_marketing.v1"


class ActivationWorkspaceUpsertRequest(BaseModel):
    customer_id: str = Field(..., min_length=1)
    workspace: dict[str, Any] = Field(default_factory=dict)


class ActivationReadinessResponse(BaseModel):
    brief_complete: bool
    youtube_selected: bool
    youtube_connection_ready: bool
    configured: bool
    can_finalize: bool
    missing_requirements: list[str] = Field(default_factory=list)


class ActivationWorkspaceResponse(BaseModel):
    hired_instance_id: str
    customer_id: str | None = None
    agent_type_id: str
    workspace: dict[str, Any] = Field(default_factory=dict)
    readiness: ActivationReadinessResponse
    updated_at: datetime


def _workspace_from_config(config: dict[str, Any] | None) -> dict[str, Any]:
    raw = (config or {}).get(_WORKSPACE_KEY)
    return dict(raw) if isinstance(raw, dict) else {}


def _selected_platforms(workspace: dict[str, Any]) -> list[str]:
    raw = workspace.get("platforms_enabled") or workspace.get("selected_platforms") or []
    selected: list[str] = []
    if isinstance(raw, list):
        for value in raw:
            platform = str(value or "").strip().lower()
            if platform:
                selected.append(platform)
    return selected


def _platform_bindings(workspace: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = workspace.get("platform_bindings")
    if not isinstance(raw, dict):
        return {}

    bindings: dict[str, dict[str, Any]] = {}
    for platform_key, value in raw.items():
        if not isinstance(value, dict):
            continue
        normalized_key = str(platform_key or "").strip().lower()
        if normalized_key:
            bindings[normalized_key] = dict(value)
    return bindings


def _materialize_marketing_config(
    *,
    existing_config: dict[str, Any],
    workspace: dict[str, Any],
) -> dict[str, Any]:
    config = dict(existing_config or {})
    config[_WORKSPACE_KEY] = workspace

    for field_name in (
        "brand_name",
        "location",
        "primary_language",
        "timezone",
        "business_context",
    ):
        value = workspace.get(field_name)
        if value is not None:
            config[field_name] = value

    offerings = workspace.get("offerings_services")
    if isinstance(offerings, list):
        config["offerings_services"] = offerings

    selected_platforms = _selected_platforms(workspace)
    if selected_platforms:
        config["platforms_enabled"] = selected_platforms

    bindings = _platform_bindings(workspace)
    platform_credentials: dict[str, dict[str, str]] = {}
    for platform in selected_platforms:
        binding = bindings.get(platform) or {}
        credential_ref = (
            binding.get("credential_ref")
            or binding.get("customer_platform_credential_id")
            or binding.get("credential_id")
        )
        if isinstance(credential_ref, str) and credential_ref.strip():
            platform_credentials[platform] = {"credential_ref": credential_ref.strip()}
    if platform_credentials:
        config["platform_credentials"] = platform_credentials

    return config


def _ensure_supported_record(record: hired_agents_simple._HiredAgentRecord) -> None:
    if hired_agents_simple._canonical_agent_type_id_or_400(record.agent_type_id) != _DIGITAL_MARKETING_AGENT_TYPE:
        raise HTTPException(status_code=409, detail="Digital marketing activation is only supported for marketing.digital_marketing.v1")


async def _youtube_connection_ready(
    *,
    hired_instance_id: str,
    workspace: dict[str, Any],
    db: AsyncSession | None,
) -> bool:
    if "youtube" not in _selected_platforms(workspace):
        return True

    bindings = _platform_bindings(workspace)
    youtube_binding = bindings.get("youtube") or {}
    if db is None:
        return bool(youtube_binding.get("connected"))

    skill_id = str(youtube_binding.get("skill_id") or "").strip()
    if not skill_id:
        return False

    connection = await get_connected_platform_connection(
        db,
        hired_instance_id=hired_instance_id,
        skill_id=skill_id,
        platform_key="youtube",
    )
    return connection is not None


async def _build_response(
    *,
    record: hired_agents_simple._HiredAgentRecord,
    db: AsyncSession | None,
) -> ActivationWorkspaceResponse:
    workspace = _workspace_from_config(record.config)
    youtube_selected = "youtube" in _selected_platforms(workspace)
    youtube_connection_ready = await _youtube_connection_ready(
        hired_instance_id=record.hired_instance_id,
        workspace=workspace,
        db=db,
    )
    configured = hired_agents_simple._compute_agent_configured(
        record.nickname,
        record.theme,
        agent_id=record.agent_id,
        config=record.config,
    )
    brief_complete = hired_agents_simple._marketing_config_complete(record.config)

    missing_requirements: list[str] = []
    if not brief_complete:
        missing_requirements.append("business_profile")
    if youtube_selected and not youtube_connection_ready:
        missing_requirements.append("youtube_connection")
    if not configured:
        missing_requirements.append("agent_configuration")

    return ActivationWorkspaceResponse(
        hired_instance_id=record.hired_instance_id,
        customer_id=record.customer_id,
        agent_type_id=hired_agents_simple._canonical_agent_type_id_or_400(record.agent_type_id),
        workspace=workspace,
        readiness=ActivationReadinessResponse(
            brief_complete=brief_complete,
            youtube_selected=youtube_selected,
            youtube_connection_ready=youtube_connection_ready,
            configured=configured,
            can_finalize=brief_complete and youtube_connection_ready and configured,
            missing_requirements=missing_requirements,
        ),
        updated_at=record.updated_at,
    )


@router.get("/{hired_instance_id}/digital-marketing-activation", response_model=ActivationWorkspaceResponse)
async def get_activation_workspace(
    hired_instance_id: str,
    customer_id: str,
    db: AsyncSession | None = Depends(hired_agents_simple._get_read_hired_agents_db_session),
) -> ActivationWorkspaceResponse:
    record = await hired_agents_simple._get_record_by_id(hired_instance_id=hired_instance_id, db=db)
    if record is None:
        raise HTTPException(status_code=404, detail="Hired agent instance not found.")

    hired_agents_simple._assert_customer_owns_record(record, customer_id)
    _ensure_supported_record(record)
    await hired_agents_simple._assert_readable(record, db=db)
    return await _build_response(record=record, db=db)


@router.put("/{hired_instance_id}/digital-marketing-activation", response_model=ActivationWorkspaceResponse)
async def upsert_activation_workspace(
    hired_instance_id: str,
    body: ActivationWorkspaceUpsertRequest,
    db: AsyncSession | None = Depends(hired_agents_simple._get_hired_agents_db_session),
) -> ActivationWorkspaceResponse:
    record = await hired_agents_simple._get_record_by_id(hired_instance_id=hired_instance_id, db=db)
    if record is None:
        raise HTTPException(status_code=404, detail="Hired agent instance not found.")

    hired_agents_simple._assert_customer_owns_record(record, body.customer_id)
    _ensure_supported_record(record)
    await hired_agents_simple._assert_writable(record, db=db)

    existing_workspace = _workspace_from_config(record.config)
    workspace = {**existing_workspace, **dict(body.workspace or {})}
    materialized_config = _materialize_marketing_config(
        existing_config=dict(record.config or {}),
        workspace=workspace,
    )
    configured = hired_agents_simple._compute_agent_configured(
        record.nickname,
        record.theme,
        agent_id=record.agent_id,
        config=materialized_config,
    )
    now = datetime.now(timezone.utc)

    if db is None:
        updated = record.model_copy(
            update={
                "config": materialized_config,
                "configured": configured,
                "updated_at": now,
            }
        )
        hired_agents_simple._by_id[hired_instance_id] = updated
        return await _build_response(record=updated, db=db)

    repo = HiredAgentRepository(db)
    model = await repo.update_config(
        hired_instance_id,
        config=materialized_config,
        configured=configured,
    )
    await db.commit()
    refreshed = hired_agents_simple._db_model_to_record(model)
    return await _build_response(record=refreshed, db=db)