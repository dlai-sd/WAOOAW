from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from agent_mold.skills.content_models import Campaign, CampaignWorkflowState, DailyThemeItem, estimate_cost
from agent_mold.skills.grok_client import GrokClientError, get_grok_client, grok_complete
from api.v1 import campaigns as campaigns_module
from api.v1 import hired_agents_simple
from api.v1.platform_connections import get_connected_platform_connection
from core.logging import PiiMaskingFilter
from core.routing import waooaw_router
from repositories.campaign_repository import CampaignRepository
from repositories.hired_agent_repository import HiredAgentRepository


router = waooaw_router(prefix="/hired-agents", tags=["digital-marketing-activation"])
theme_router = waooaw_router(prefix="/digital-marketing-activation", tags=["digital-marketing-activation"])

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())

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


class ThemePlanGenerateRequest(BaseModel):
    customer_id: str | None = None
    campaign_setup: dict[str, Any] = Field(default_factory=dict)


class ThemePlanUpdateRequest(BaseModel):
    customer_id: str | None = None
    master_theme: str = Field(..., min_length=1)
    derived_themes: list[dict[str, Any]] = Field(default_factory=list)
    campaign_setup: dict[str, Any] = Field(default_factory=dict)


class ThemePlanResponse(BaseModel):
    campaign_id: str | None = None
    master_theme: str
    derived_themes: list[dict[str, Any]] = Field(default_factory=list)
    workspace: dict[str, Any] = Field(default_factory=dict)


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


def _require_auth(authorization: Optional[str]) -> None:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required.")


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


def _theme_prompt(workspace: dict[str, Any], campaign_setup: dict[str, Any]) -> str:
    return json.dumps(
        {
            "brand_name": workspace.get("brand_name") or "",
            "offerings_services": workspace.get("offerings_services") or [],
            "location": workspace.get("location") or "",
            "selected_platforms": _selected_platforms(workspace),
            "schedule": dict(campaign_setup.get("schedule") or {}),
            "business_context": workspace.get("business_context") or "",
        },
        ensure_ascii=False,
    )


def _normalize_derived_themes(raw_derived: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_derived, list):
        return []

    normalized: list[dict[str, Any]] = []
    for row in raw_derived:
        row_dict = dict(row or {})
        title = str(row_dict.get("title") or "").strip()
        if not title:
            continue
        normalized.append(
            {
                "title": title,
                "description": str(row_dict.get("description") or "").strip(),
                "frequency": str(row_dict.get("frequency") or "weekly").strip() or "weekly",
            }
        )
    return normalized


def _parse_theme_plan(raw_text: str) -> tuple[str, list[dict[str, Any]]]:
    cleaned = str(raw_text or "").strip()
    if not cleaned:
        return "Digital marketing activation plan", []
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        return cleaned.splitlines()[0][:120] or "Digital marketing activation plan", []

    if not isinstance(payload, dict):
        return "Digital marketing activation plan", []

    master_theme = str(payload.get("master_theme") or payload.get("theme") or "Digital marketing activation plan").strip()
    return master_theme or "Digital marketing activation plan", _normalize_derived_themes(payload.get("derived_themes"))


def _build_theme_plan_workspace(
    *,
    workspace: dict[str, Any],
    campaign_setup: dict[str, Any],
    campaign_id: str,
    master_theme: str,
    derived_themes: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        **workspace,
        "campaign_setup": {
            **campaign_setup,
            "campaign_id": campaign_id,
            "master_theme": master_theme,
            "derived_themes": derived_themes,
        },
    }


async def _persist_workspace_state(
    *,
    record: hired_agents_simple._HiredAgentRecord,
    workspace: dict[str, Any],
    db: AsyncSession | None,
) -> hired_agents_simple._HiredAgentRecord:
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
        hired_agents_simple._by_id[record.hired_instance_id] = updated
        return updated

    repo = HiredAgentRepository(db)
    model = await repo.update_config(
        record.hired_instance_id,
        config=materialized_config,
        configured=configured,
    )
    return hired_agents_simple._db_model_to_record(model)


async def _persist_theme_plan_to_campaign(
    *,
    record: hired_agents_simple._HiredAgentRecord,
    workspace: dict[str, Any],
    master_theme: str,
    derived_themes: list[dict[str, Any]],
    campaign_setup: dict[str, Any],
    db: AsyncSession | None,
) -> str:
    activation_payload = {
        "induction": {
            "nickname": record.nickname,
            "theme": record.theme,
            "primary_language": workspace.get("primary_language") or dict(record.config or {}).get("primary_language") or "en",
            "timezone": workspace.get("timezone") or dict(record.config or {}).get("timezone") or "",
            "brand_name": workspace.get("brand_name") or dict(record.config or {}).get("brand_name") or "",
            "offerings_services": workspace.get("offerings_services") or dict(record.config or {}).get("offerings_services") or [],
            "location": workspace.get("location") or dict(record.config or {}).get("location") or "",
            "target_audience": workspace.get("target_audience") or "",
            "notes": workspace.get("business_context") or "",
        },
        "selected_platforms": _selected_platforms(workspace),
        "theme_plan": {
            "master_theme": master_theme,
            "derived_themes": derived_themes,
        },
        "schedule": dict(campaign_setup.get("schedule") or {}),
    }
    brief = campaigns_module.build_campaign_brief_from_activation_payload(activation_payload)
    cost_estimate = estimate_cost(brief, model_used="grok-3-latest")

    if db is None or campaigns_module.CAMPAIGN_PERSISTENCE_MODE != "db":
        existing = next(
            (
                campaign
                for campaign in campaigns_module._campaigns.values()
                if campaign.hired_instance_id == record.hired_instance_id
                and campaign.status == campaigns_module.CampaignStatus.DRAFT
            ),
            None,
        )
        if existing is None:
            campaign = Campaign(
                hired_instance_id=record.hired_instance_id,
                customer_id=str(record.customer_id or ""),
                brief=brief,
                cost_estimate=cost_estimate,
            )
        else:
            campaign = existing.model_copy(
                update={
                    "brief": brief,
                    "cost_estimate": cost_estimate,
                    "workflow_state": CampaignWorkflowState.BRIEF_CAPTURED,
                    "updated_at": datetime.now(timezone.utc),
                }
            )

        theme_items = [
            DailyThemeItem.model_validate(item)
            for item in campaigns_module.build_theme_items_from_activation_payload(
                campaign_id=campaign.campaign_id,
                payload=activation_payload,
            )
        ]
        campaigns_module._campaigns[campaign.campaign_id] = campaigns_module._enrich_campaign_runtime(
            campaign,
            theme_items=theme_items,
            posts=[],
        )
        campaigns_module._theme_items[campaign.campaign_id] = {
            item.theme_item_id: item for item in theme_items
        }
        campaigns_module._posts[campaign.campaign_id] = {}
        return campaign.campaign_id

    repo = CampaignRepository(db)
    draft_campaign = await repo.get_active_draft_campaign_by_hired_instance(record.hired_instance_id)
    existing_campaign = await repo.upsert_draft_campaign_with_theme_items(
        hired_instance_id=record.hired_instance_id,
        customer_id=str(record.customer_id or ""),
        brief=brief.model_dump(mode="json"),
        cost_estimate=cost_estimate.model_dump(mode="json"),
        workflow_state=CampaignWorkflowState.BRIEF_CAPTURED.value,
        brief_summary=campaigns_module._build_brief_summary(brief).model_dump(mode="json"),
        theme_items=campaigns_module.build_theme_items_from_activation_payload(
            campaign_id=draft_campaign.campaign_id if draft_campaign is not None else "pending-draft-campaign",
            payload=activation_payload,
        ),
    )
    await campaigns_module._persist_campaign_runtime(repo, existing_campaign.campaign_id)
    return existing_campaign.campaign_id


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


@theme_router.post("/{hired_instance_id}/generate-theme-plan", response_model=ThemePlanResponse)
async def generate_theme_plan(
    hired_instance_id: str,
    body: ThemePlanGenerateRequest,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    db: AsyncSession | None = Depends(hired_agents_simple._get_hired_agents_db_session),
) -> ThemePlanResponse:
    _require_auth(authorization)
    record = await hired_agents_simple._get_record_by_id(hired_instance_id=hired_instance_id, db=db)
    if record is None:
        raise HTTPException(status_code=404, detail="Hired agent not found.")

    if body.customer_id is not None:
        hired_agents_simple._assert_customer_owns_record(record, body.customer_id)
    _ensure_supported_record(record)

    workspace = _workspace_from_config(record.config)
    campaign_setup = dict(body.campaign_setup or {})

    try:
        client = get_grok_client()
        proposal = grok_complete(
            client,
            system="You are a digital marketing strategist creating one master theme and a short list of derived campaign themes. Return JSON with master_theme and derived_themes.",
            user=_theme_prompt(workspace, campaign_setup),
            model="grok-3-latest",
            temperature=0.7,
        )
    except GrokClientError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    master_theme, derived_themes = _parse_theme_plan(proposal)
    logger.info("Generated DMA theme plan for hired_instance_id=%s", hired_instance_id)
    campaign_id = await _persist_theme_plan_to_campaign(
        record=record,
        workspace=workspace,
        master_theme=master_theme,
        derived_themes=derived_themes,
        campaign_setup=campaign_setup,
        db=db,
    )
    persisted_workspace = _build_theme_plan_workspace(
        workspace=workspace,
        campaign_setup=campaign_setup,
        campaign_id=campaign_id,
        master_theme=master_theme,
        derived_themes=derived_themes,
    )
    await _persist_workspace_state(
        record=record,
        workspace=persisted_workspace,
        db=db,
    )
    if db is not None:
        await db.commit()

    return ThemePlanResponse(
        campaign_id=campaign_id,
        master_theme=master_theme,
        derived_themes=derived_themes,
        workspace=persisted_workspace,
    )


@theme_router.patch("/{hired_instance_id}/theme-plan", response_model=ThemePlanResponse)
async def update_theme_plan(
    hired_instance_id: str,
    body: ThemePlanUpdateRequest,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    db: AsyncSession | None = Depends(hired_agents_simple._get_hired_agents_db_session),
) -> ThemePlanResponse:
    _require_auth(authorization)
    record = await hired_agents_simple._get_record_by_id(hired_instance_id=hired_instance_id, db=db)
    if record is None:
        raise HTTPException(status_code=404, detail="Hired agent not found.")

    if body.customer_id is not None:
        hired_agents_simple._assert_customer_owns_record(record, body.customer_id)
    _ensure_supported_record(record)

    workspace = _workspace_from_config(record.config)
    campaign_setup = dict(body.campaign_setup or {})
    master_theme = str(body.master_theme or "").strip()
    if not master_theme:
        raise HTTPException(status_code=422, detail="master_theme is required")
    derived_themes = _normalize_derived_themes(body.derived_themes)

    campaign_id = await _persist_theme_plan_to_campaign(
        record=record,
        workspace=workspace,
        master_theme=master_theme,
        derived_themes=derived_themes,
        campaign_setup=campaign_setup,
        db=db,
    )
    persisted_workspace = _build_theme_plan_workspace(
        workspace=workspace,
        campaign_setup=campaign_setup,
        campaign_id=campaign_id,
        master_theme=master_theme,
        derived_themes=derived_themes,
    )
    await _persist_workspace_state(
        record=record,
        workspace=persisted_workspace,
        db=db,
    )
    if db is not None:
        await db.commit()

    logger.info("Updated DMA theme plan for hired_instance_id=%s", hired_instance_id)
    return ThemePlanResponse(
        campaign_id=campaign_id,
        master_theme=master_theme,
        derived_themes=derived_themes,
        workspace=persisted_workspace,
    )