from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import Body, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from agent_mold.skills.content_models import Campaign, CampaignWorkflowState, DailyThemeItem, estimate_cost
from agent_mold.skills.grok_client import GrokClientError, get_grok_client, grok_complete
from api.v1 import campaigns as campaigns_module
from api.v1.hired_agents_simple import (
    _HiredAgentRecord,
    _by_id,
    _db_model_to_record,
    _get_hired_agents_db_session,
    _get_read_hired_agents_db_session,
    _get_record_by_id,
)
from core.logging import PiiMaskingFilter
from core.routing import waooaw_router
from repositories.campaign_repository import CampaignRepository
from repositories.hired_agent_repository import HiredAgentRepository

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())

router = waooaw_router(
    prefix="/digital-marketing-activation",
    tags=["digital-marketing-activation"],
)


class DerivedThemeItemResponse(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = ""
    frequency: str = "weekly"


class PlatformStepResponse(BaseModel):
    platform_key: str = Field(..., min_length=1)
    complete: bool = False
    status: str = "pending"


class InductionStateResponse(BaseModel):
    nickname: str = ""
    theme: str = "default"
    primary_language: str = "en"
    timezone: str = ""
    brand_name: str = ""
    offerings_services: list[str] = Field(default_factory=list)
    location: str = ""
    target_audience: str = ""
    notes: str = ""


class PrepareAgentStateResponse(BaseModel):
    selected_platforms: list[str] = Field(default_factory=list)
    platform_steps: list[PlatformStepResponse] = Field(default_factory=list)
    all_selected_platforms_completed: bool = False


class CampaignScheduleResponse(BaseModel):
    start_date: str = ""
    posts_per_week: int = 0
    preferred_days: list[str] = Field(default_factory=list)
    preferred_hours_utc: list[int] = Field(default_factory=list)


class CampaignSetupStateResponse(BaseModel):
    campaign_id: str | None = None
    master_theme: str = ""
    derived_themes: list[DerivedThemeItemResponse] = Field(default_factory=list)
    schedule: CampaignScheduleResponse = Field(default_factory=CampaignScheduleResponse)


class DigitalMarketingActivationWorkspaceResponse(BaseModel):
    hired_instance_id: str
    help_visible: bool = False
    activation_complete: bool = False
    induction: InductionStateResponse = Field(default_factory=InductionStateResponse)
    prepare_agent: PrepareAgentStateResponse = Field(default_factory=PrepareAgentStateResponse)
    campaign_setup: CampaignSetupStateResponse = Field(default_factory=CampaignSetupStateResponse)
    updated_at: datetime


class ThemePlanResponse(BaseModel):
    campaign_id: str | None = None
    master_theme: str
    derived_themes: list[DerivedThemeItemResponse] = Field(default_factory=list)
    workspace: DigitalMarketingActivationWorkspaceResponse


def _require_auth(authorization: Optional[str]) -> None:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(dict(merged[key]), value)
        else:
            merged[key] = value
    return merged


def _normalize_platform_steps(
    selected_platforms: list[str],
    existing_steps: list[dict[str, Any]] | list[PlatformStepResponse] | None,
) -> list[dict[str, Any]]:
    normalized_selected = []
    for platform in selected_platforms:
        candidate = str(platform or "").strip().lower()
        if candidate and candidate not in normalized_selected:
            normalized_selected.append(candidate)

    step_map: dict[str, dict[str, Any]] = {}
    for step in existing_steps or []:
        raw = step.model_dump(mode="json") if hasattr(step, "model_dump") else dict(step or {})
        platform_key = str(raw.get("platform_key") or "").strip().lower()
        if platform_key:
            step_map[platform_key] = {
                "platform_key": platform_key,
                "complete": bool(raw.get("complete", False)),
                "status": str(raw.get("status") or ("complete" if raw.get("complete") else "pending")),
            }

    steps: list[dict[str, Any]] = []
    for platform in normalized_selected:
        existing = step_map.get(platform) or {}
        complete = bool(existing.get("complete", False))
        steps.append(
            {
                "platform_key": platform,
                "complete": complete,
                "status": str(existing.get("status") or ("complete" if complete else "pending")),
            }
        )
    return steps


def _build_workspace(record: _HiredAgentRecord) -> DigitalMarketingActivationWorkspaceResponse:
    config = dict(record.config or {})
    activation = dict(config.get("digital_marketing_activation") or {})
    induction = dict(activation.get("induction") or {})
    prepare_agent = dict(activation.get("prepare_agent") or {})
    campaign_setup = dict(activation.get("campaign_setup") or {})

    selected_platforms_raw = prepare_agent.get("selected_platforms")
    if not isinstance(selected_platforms_raw, list):
        selected_platforms_raw = list(config.get("platforms_enabled") or [])

    selected_platforms = [
        str(platform or "").strip().lower()
        for platform in selected_platforms_raw
        if str(platform or "").strip()
    ]
    selected_platforms = list(dict.fromkeys(selected_platforms))

    platform_steps = _normalize_platform_steps(
        selected_platforms,
        prepare_agent.get("platform_steps") if isinstance(prepare_agent.get("platform_steps"), list) else None,
    )
    all_selected_platforms_completed = bool(platform_steps) and all(
        bool(step.get("complete", False)) for step in platform_steps
    )

    return DigitalMarketingActivationWorkspaceResponse.model_validate(
        {
            "hired_instance_id": record.hired_instance_id,
            "help_visible": bool(activation.get("help_visible", False)),
            "activation_complete": bool(activation.get("activation_complete", False)),
            "induction": {
                "nickname": str(induction.get("nickname") or record.nickname or ""),
                "theme": str(induction.get("theme") or record.theme or "default"),
                "primary_language": str(induction.get("primary_language") or config.get("primary_language") or "en"),
                "timezone": str(induction.get("timezone") or config.get("timezone") or ""),
                "brand_name": str(induction.get("brand_name") or config.get("brand_name") or ""),
                "offerings_services": list(induction.get("offerings_services") or config.get("offerings_services") or []),
                "location": str(induction.get("location") or config.get("location") or ""),
                "target_audience": str(induction.get("target_audience") or ""),
                "notes": str(induction.get("notes") or ""),
            },
            "prepare_agent": {
                "selected_platforms": selected_platforms,
                "platform_steps": platform_steps,
                "all_selected_platforms_completed": all_selected_platforms_completed,
            },
            "campaign_setup": {
                "campaign_id": campaign_setup.get("campaign_id"),
                "master_theme": str(campaign_setup.get("master_theme") or ""),
                "derived_themes": list(campaign_setup.get("derived_themes") or []),
                "schedule": {
                    "start_date": str(dict(campaign_setup.get("schedule") or {}).get("start_date") or ""),
                    "posts_per_week": int(dict(campaign_setup.get("schedule") or {}).get("posts_per_week") or 0),
                    "preferred_days": list(dict(campaign_setup.get("schedule") or {}).get("preferred_days") or []),
                    "preferred_hours_utc": list(dict(campaign_setup.get("schedule") or {}).get("preferred_hours_utc") or []),
                },
            },
            "updated_at": record.updated_at,
        }
    )


async def _persist_workspace(
    *,
    record: _HiredAgentRecord,
    workspace: DigitalMarketingActivationWorkspaceResponse,
    db: AsyncSession | None,
) -> _HiredAgentRecord:
    serialized_workspace = workspace.model_dump(mode="json")
    next_config = dict(record.config or {})
    next_config["digital_marketing_activation"] = serialized_workspace
    now = datetime.now(timezone.utc)

    if db is None:
        updated = record.model_copy(
            update={
                "nickname": workspace.induction.nickname or record.nickname,
                "theme": workspace.induction.theme or record.theme,
                "config": next_config,
                "configured": bool(record.configured or workspace.activation_complete),
                "goals_completed": bool(record.goals_completed or workspace.activation_complete),
                "updated_at": now,
            }
        )
        _by_id[record.hired_instance_id] = updated
        return updated

    repo = HiredAgentRepository(db)
    model = await repo.get_by_id(record.hired_instance_id)
    if model is None:
        raise HTTPException(status_code=404, detail="Hired agent not found.")
    model.nickname = workspace.induction.nickname or model.nickname
    model.theme = workspace.induction.theme or model.theme
    model.config = next_config
    model.configured = bool(model.configured or workspace.activation_complete)
    model.goals_completed = bool(model.goals_completed or workspace.activation_complete)
    model.updated_at = now
    await db.flush()
    await db.refresh(model)
    return _db_model_to_record(model)


def _theme_prompt(workspace: DigitalMarketingActivationWorkspaceResponse) -> str:
    induction = workspace.induction
    schedule = workspace.campaign_setup.schedule
    return json.dumps(
        {
            "brand_name": induction.brand_name,
            "offerings_services": induction.offerings_services,
            "location": induction.location,
            "target_audience": induction.target_audience,
            "selected_platforms": workspace.prepare_agent.selected_platforms,
            "posts_per_week": schedule.posts_per_week,
            "preferred_days": schedule.preferred_days,
            "preferred_hours_utc": schedule.preferred_hours_utc,
        },
        ensure_ascii=False,
    )


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
    derived = payload.get("derived_themes")
    if not isinstance(derived, list):
        derived = []
    normalized = []
    for row in derived:
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
    return master_theme or "Digital marketing activation plan", normalized


async def _persist_theme_plan_to_campaign(
    *,
    record: _HiredAgentRecord,
    workspace: DigitalMarketingActivationWorkspaceResponse,
    db: AsyncSession | None,
) -> str:
    activation_payload = {
        "induction": workspace.induction.model_dump(mode="json"),
        "selected_platforms": workspace.prepare_agent.selected_platforms,
        "theme_plan": {
            "master_theme": workspace.campaign_setup.master_theme,
            "derived_themes": [item.model_dump(mode="json") for item in workspace.campaign_setup.derived_themes],
        },
        "schedule": workspace.campaign_setup.schedule.model_dump(mode="json"),
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
    existing_campaign = await repo.get_active_draft_campaign_by_hired_instance(record.hired_instance_id)
    if existing_campaign is None:
        existing_campaign = await repo.create_campaign(
            hired_instance_id=record.hired_instance_id,
            customer_id=str(record.customer_id or ""),
            brief=brief.model_dump(mode="json"),
            cost_estimate=cost_estimate.model_dump(mode="json"),
        )
    else:
        existing_campaign = await repo.update_campaign_brief(
            existing_campaign.campaign_id,
            brief=brief.model_dump(mode="json"),
            cost_estimate=cost_estimate.model_dump(mode="json"),
            workflow_state=CampaignWorkflowState.BRIEF_CAPTURED.value,
            brief_summary=campaigns_module._build_brief_summary(brief).model_dump(mode="json"),
        )
    await repo.replace_theme_items(
        existing_campaign.campaign_id,
        campaigns_module.build_theme_items_from_activation_payload(
            campaign_id=existing_campaign.campaign_id,
            payload=activation_payload,
        ),
    )
    await campaigns_module._persist_campaign_runtime(repo, existing_campaign.campaign_id)
    return existing_campaign.campaign_id


def _response_from_workspace(workspace: DigitalMarketingActivationWorkspaceResponse) -> ThemePlanResponse:
    return ThemePlanResponse(
        campaign_id=workspace.campaign_setup.campaign_id,
        master_theme=workspace.campaign_setup.master_theme,
        derived_themes=workspace.campaign_setup.derived_themes,
        workspace=workspace,
    )


@router.get("/{hired_instance_id}", response_model=DigitalMarketingActivationWorkspaceResponse)
async def get_workspace(
    hired_instance_id: str,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    db: AsyncSession | None = Depends(_get_read_hired_agents_db_session),
) -> DigitalMarketingActivationWorkspaceResponse:
    _require_auth(authorization)
    record = await _get_record_by_id(hired_instance_id=hired_instance_id, db=db)
    if record is None:
        raise HTTPException(status_code=404, detail="Hired agent not found.")
    return _build_workspace(record)


@router.patch("/{hired_instance_id}", response_model=DigitalMarketingActivationWorkspaceResponse)
async def patch_workspace(
    hired_instance_id: str,
    body: dict[str, Any] = Body(default_factory=dict),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    db: AsyncSession | None = Depends(_get_hired_agents_db_session),
) -> DigitalMarketingActivationWorkspaceResponse:
    _require_auth(authorization)
    record = await _get_record_by_id(hired_instance_id=hired_instance_id, db=db)
    if record is None:
        raise HTTPException(status_code=404, detail="Hired agent not found.")

    current = _build_workspace(record)
    merged_dict = _deep_merge(current.model_dump(mode="json"), body)
    merged_dict["hired_instance_id"] = hired_instance_id
    selected_platforms = list(
        merged_dict.get("prepare_agent", {}).get("selected_platforms")
        or current.prepare_agent.selected_platforms
    )
    merged_dict.setdefault("prepare_agent", {})
    merged_dict["prepare_agent"]["platform_steps"] = _normalize_platform_steps(
        selected_platforms,
        merged_dict["prepare_agent"].get("platform_steps"),
    )
    merged_dict["prepare_agent"]["all_selected_platforms_completed"] = bool(
        merged_dict["prepare_agent"]["platform_steps"]
    ) and all(bool(step.get("complete", False)) for step in merged_dict["prepare_agent"]["platform_steps"])
    merged_dict["updated_at"] = datetime.now(timezone.utc).isoformat()

    workspace = DigitalMarketingActivationWorkspaceResponse.model_validate(merged_dict)
    persisted = await _persist_workspace(record=record, workspace=workspace, db=db)
    if db is not None:
        await db.commit()
    return _build_workspace(persisted)


@router.post("/{hired_instance_id}/generate-theme-plan", response_model=ThemePlanResponse)
async def generate_theme_plan(
    hired_instance_id: str,
    body: dict[str, Any] = Body(default_factory=dict),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    db: AsyncSession | None = Depends(_get_hired_agents_db_session),
) -> ThemePlanResponse:
    _require_auth(authorization)
    record = await _get_record_by_id(hired_instance_id=hired_instance_id, db=db)
    if record is None:
        raise HTTPException(status_code=404, detail="Hired agent not found.")

    current = _build_workspace(record)
    merged_dict = _deep_merge(current.model_dump(mode="json"), body)
    merged_dict["hired_instance_id"] = hired_instance_id
    merged_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    workspace = DigitalMarketingActivationWorkspaceResponse.model_validate(merged_dict)

    try:
        client = get_grok_client()
        proposal = grok_complete(
            client,
            system="You are a digital marketing strategist creating one master theme and a short list of derived campaign themes. Return JSON with master_theme and derived_themes.",
            user=_theme_prompt(workspace),
            model="grok-3-latest",
            temperature=0.7,
        )
    except GrokClientError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    master_theme, derived_themes = _parse_theme_plan(proposal)
    workspace = DigitalMarketingActivationWorkspaceResponse.model_validate(
        {
            **workspace.model_dump(mode="json"),
            "campaign_setup": {
                **workspace.campaign_setup.model_dump(mode="json"),
                "master_theme": master_theme,
                "derived_themes": derived_themes,
            },
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    campaign_id = await _persist_theme_plan_to_campaign(record=record, workspace=workspace, db=db)
    workspace = DigitalMarketingActivationWorkspaceResponse.model_validate(
        {
            **workspace.model_dump(mode="json"),
            "campaign_setup": {
                **workspace.campaign_setup.model_dump(mode="json"),
                "campaign_id": campaign_id,
            },
        }
    )
    persisted = await _persist_workspace(record=record, workspace=workspace, db=db)
    if db is not None:
        await db.commit()
    return _response_from_workspace(_build_workspace(persisted))


@router.patch("/{hired_instance_id}/theme-plan", response_model=ThemePlanResponse)
async def patch_theme_plan(
    hired_instance_id: str,
    body: dict[str, Any] = Body(default_factory=dict),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    db: AsyncSession | None = Depends(_get_hired_agents_db_session),
) -> ThemePlanResponse:
    _require_auth(authorization)
    record = await _get_record_by_id(hired_instance_id=hired_instance_id, db=db)
    if record is None:
        raise HTTPException(status_code=404, detail="Hired agent not found.")

    current = _build_workspace(record)
    merged_dict = _deep_merge(current.model_dump(mode="json"), {"campaign_setup": body})
    merged_dict["hired_instance_id"] = hired_instance_id
    merged_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    workspace = DigitalMarketingActivationWorkspaceResponse.model_validate(merged_dict)
    campaign_id = await _persist_theme_plan_to_campaign(record=record, workspace=workspace, db=db)
    workspace = DigitalMarketingActivationWorkspaceResponse.model_validate(
        {
            **workspace.model_dump(mode="json"),
            "campaign_setup": {
                **workspace.campaign_setup.model_dump(mode="json"),
                "campaign_id": campaign_id,
            },
        }
    )
    persisted = await _persist_workspace(record=record, workspace=workspace, db=db)
    if db is not None:
        await db.commit()
    return _response_from_workspace(_build_workspace(persisted))
