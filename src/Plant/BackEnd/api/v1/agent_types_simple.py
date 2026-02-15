"""Agent Type Definition APIs (Phase-1 simple implementation).

AGP1-PLANT-1:
- Provide versioned AgentTypeDefinitions to CP so CP can render Configure + Goal Setting
    without hard-coding agent-specific schemas.

Phase-1 scope: simple in-memory store with exactly two canonical definitions:
- marketing.digital_marketing.v1 ("Digital Marketing")
- trading.share_trader.v1 ("Share Trader")

Legacy IDs are accepted as aliases for backwards compatibility:
- marketing.healthcare.v1 -> marketing.digital_marketing.v1
- trading.delta_futures.v1 -> trading.share_trader.v1
"""

from __future__ import annotations

import os
from typing import Any, AsyncGenerator, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import JSONResponse

from core.database import get_db_session
from models.skill import Skill


FieldType = Literal["text", "enum", "list", "object", "boolean", "number"]


class SchemaFieldDefinition(BaseModel):
    key: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    type: FieldType
    required: bool = False
    description: str | None = None

    options: list[str] | None = None
    item_type: FieldType | None = None


class JsonSchemaDefinition(BaseModel):
    fields: list[SchemaFieldDefinition] = Field(default_factory=list)


class GoalTemplateDefinition(BaseModel):
    goal_template_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    default_frequency: str = Field(..., min_length=1)
    settings_schema: JsonSchemaDefinition = Field(default_factory=JsonSchemaDefinition)
    skill_binding: str | None = None


class EnforcementDefaults(BaseModel):
    approval_required: bool = True
    deterministic: bool = False


class AgentTypeDefinition(BaseModel):
    agent_type_id: str = Field(..., min_length=1)
    # Customer-facing name for the catalog row.
    display_name: str | None = None
    version: str = Field(..., min_length=1)

    # SK-3.2: stable skill composition contract.
    # Keys map to Genesis Skill.external_id (aka skill_key).
    required_skill_keys: list[str] = Field(default_factory=list)

    config_schema: JsonSchemaDefinition = Field(default_factory=JsonSchemaDefinition)
    goal_templates: list[GoalTemplateDefinition] = Field(default_factory=list)
    enforcement_defaults: EnforcementDefaults = Field(default_factory=EnforcementDefaults)


router = APIRouter(prefix="/agent-types", tags=["agent-types"])


_LEGACY_AGENT_TYPE_ID_ALIASES: dict[str, str] = {
    "marketing.healthcare.v1": "marketing.digital_marketing.v1",
    "trading.delta_futures.v1": "trading.share_trader.v1",
}


def _canonical_agent_type_id(agent_type_id: str) -> str:
    key = str(agent_type_id or "").strip()
    return _LEGACY_AGENT_TYPE_ID_ALIASES.get(key, key)


def _persistence_mode() -> str:
    # Feature flag: PERSISTENCE_MODE (default: "memory" for Phase 1 compatibility)
    return os.getenv("PERSISTENCE_MODE", "memory").strip().lower()


async def _get_agent_types_db_session() -> AsyncGenerator[AsyncSession | None, None]:
    """DB session for SK-3.2 validations.

    Keep Phase-1 compatibility by yielding None unless PERSISTENCE_MODE=db.
    """

    if _persistence_mode() != "db":
        yield None
        return

    async for session in get_db_session():
        yield session


async def _validate_required_skill_keys(
    required_skill_keys: list[str],
    db: AsyncSession | None,
    *,
    instance: str,
) -> JSONResponse | None:
    """Validate SK-3.2 required_skill_keys -> certified Genesis Skills.

    Returns a JSONResponse(422) on validation failure; otherwise None.
    """

    normalized = [str(k or "").strip() for k in (required_skill_keys or [])]
    normalized = [k for k in normalized if k]

    if not normalized:
        return None

    if db is None:
        # Phase-1 compatibility: in-memory mode does not have DB-backed
        # Genesis Skill certification data, so we accept required_skill_keys
        # without validation.
        return None

    unique_keys = sorted(set(normalized))

    result = await db.execute(select(Skill).where(Skill.external_id.in_(unique_keys)))
    skills = result.scalars().all()

    found_by_key: dict[str, Skill] = {
        str(s.external_id): s for s in skills if getattr(s, "external_id", None)
    }

    missing = [k for k in unique_keys if k not in found_by_key]
    uncertified = [
        k for k, s in found_by_key.items() if str(getattr(s, "status", "")).lower() != "certified"
    ]

    if not missing and not uncertified:
        return None

    violations: list[str] = []
    if missing:
        violations.append(f"Unknown skill_key(s): {', '.join(missing)}")
    if uncertified:
        violations.append(f"Uncertified skill_key(s): {', '.join(uncertified)}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "type": "https://waooaw.com/errors/validation-error",
            "title": "Validation Error",
            "status": 422,
            "detail": "AgentTypeDefinition.required_skill_keys must reference certified skills",
            "instance": instance,
            "violations": violations,
            "missing_required_skill_keys": missing,
            "uncertified_required_skill_keys": uncertified,
        },
    )


def _marketing_definition() -> AgentTypeDefinition:
    return AgentTypeDefinition(
        agent_type_id="marketing.digital_marketing.v1",
        display_name="Digital Marketing",
        version="1.0.0",
        # SK-3.3: runtime enforcement requires an allowlist.
        # Phase-1 default: this agent type supports the multichannel post executor.
        required_skill_keys=["marketing.multichannel-post-v1"],
        config_schema=JsonSchemaDefinition(
            fields=[
                SchemaFieldDefinition(key="nickname", label="Agent nickname", type="text", required=True),
                SchemaFieldDefinition(
                    key="theme",
                    label="Avatar/theme",
                    type="enum",
                    required=True,
                    options=["default", "dark", "light"],
                ),
                SchemaFieldDefinition(
                    key="primary_language",
                    label="Primary language",
                    type="enum",
                    required=True,
                    options=["en", "hi"],
                ),
                SchemaFieldDefinition(key="timezone", label="Timezone", type="text", required=True),
                SchemaFieldDefinition(key="brand_name", label="Brand name", type="text", required=True),
                SchemaFieldDefinition(
                    key="offerings_services",
                    label="Offerings/services",
                    type="list",
                    required=True,
                    item_type="text",
                ),
                SchemaFieldDefinition(key="location", label="Location", type="text", required=True),
                SchemaFieldDefinition(
                    key="platforms_enabled",
                    label="Platforms enabled",
                    type="list",
                    required=True,
                    item_type="enum",
                    options=["youtube", "instagram", "facebook", "linkedin", "whatsapp", "x", "twitter"],
                ),
                SchemaFieldDefinition(
                    key="platform_credentials",
                    label="Per-platform credential refs",
                    type="object",
                    required=True,
                    description="Store only credential_ref values; secrets stay in CP.",
                ),
                SchemaFieldDefinition(
                    key="posting_identity",
                    label="Posting identity",
                    type="text",
                    required=False,
                ),
                SchemaFieldDefinition(
                    key="constraints",
                    label="Constraints",
                    type="object",
                    required=False,
                ),
            ]
        ),
        goal_templates=[
            GoalTemplateDefinition(
                goal_template_id="marketing.weekly_multichannel_batch.v1",
                name="Weekly multichannel posting batch",
                default_frequency="weekly",
                settings_schema=JsonSchemaDefinition(
                    fields=[
                        SchemaFieldDefinition(key="topics", label="Topics", type="list", required=False, item_type="text"),
                        SchemaFieldDefinition(key="posts_per_platform", label="Posts per platform", type="number", required=False),
                    ]
                ),
                skill_binding="content_marketing",
            ),
            GoalTemplateDefinition(
                goal_template_id="marketing.daily_micro_post.v1",
                name="Daily patient-education micro-post",
                default_frequency="daily",
                settings_schema=JsonSchemaDefinition(
                    fields=[
                        SchemaFieldDefinition(key="topic", label="Topic", type="text", required=False),
                    ]
                ),
                skill_binding="social_media",
            ),
            GoalTemplateDefinition(
                goal_template_id="marketing.monthly_campaign_pack.v1",
                name="Monthly campaign pack",
                default_frequency="monthly",
                settings_schema=JsonSchemaDefinition(
                    fields=[
                        SchemaFieldDefinition(key="theme", label="Campaign theme", type="text", required=False),
                    ]
                ),
                skill_binding="brand_strategy",
            ),
        ],
        enforcement_defaults=EnforcementDefaults(approval_required=True, deterministic=False),
    )


def _trading_definition() -> AgentTypeDefinition:
    return AgentTypeDefinition(
        agent_type_id="trading.share_trader.v1",
        display_name="Share Trader",
        version="1.0.0",
        config_schema=JsonSchemaDefinition(
            fields=[
                SchemaFieldDefinition(key="nickname", label="Agent nickname", type="text", required=True),
                SchemaFieldDefinition(
                    key="theme",
                    label="Avatar/theme",
                    type="enum",
                    required=True,
                    options=["default", "dark", "light"],
                ),
                SchemaFieldDefinition(key="timezone", label="Timezone", type="text", required=True),
                SchemaFieldDefinition(
                    key="exchange_provider",
                    label="Exchange provider",
                    type="enum",
                    required=True,
                    options=["delta_exchange_india"],
                ),
                SchemaFieldDefinition(
                    key="exchange_credential_ref",
                    label="Exchange credential ref",
                    type="text",
                    required=True,
                    description="Ref minted by CP; Plant must never receive raw API keys.",
                ),
                SchemaFieldDefinition(
                    key="allowed_coins",
                    label="Allowed coins",
                    type="list",
                    required=True,
                    item_type="text",
                ),
                SchemaFieldDefinition(key="default_coin", label="Default coin", type="text", required=True),
                SchemaFieldDefinition(
                    key="interval_seconds",
                    label="Interval (seconds)",
                    type="number",
                    required=True,
                    description="How often the agent evaluates signals / creates draft intents.",
                ),
                SchemaFieldDefinition(
                    key="risk_limits",
                    label="Risk limits",
                    type="object",
                    required=True,
                    description="e.g., max_units_per_order, optional max_notional_inr.",
                ),
            ]
        ),
        goal_templates=[
            GoalTemplateDefinition(
                goal_template_id="trading.trade_intent_draft.v1",
                name="Trade intent draft (enter/exit)",
                default_frequency="on_demand",
                settings_schema=JsonSchemaDefinition(
                    fields=[
                        SchemaFieldDefinition(key="coin", label="Coin", type="text", required=True),
                        SchemaFieldDefinition(key="side", label="Side", type="enum", required=True, options=["buy", "sell"]),
                        SchemaFieldDefinition(key="units", label="Units", type="number", required=True),
                    ]
                ),
                skill_binding="trading_executor",
            ),
            GoalTemplateDefinition(
                goal_template_id="trading.close_position_reminder.v1",
                name="Scheduled close-position reminder",
                default_frequency="daily",
                settings_schema=JsonSchemaDefinition(
                    fields=[
                        SchemaFieldDefinition(key="window_local_time", label="Window local time", type="text", required=True),
                    ]
                ),
                skill_binding="trading_executor",
            ),
            GoalTemplateDefinition(
                goal_template_id="trading.guardrail_report.v1",
                name="Guardrail report",
                default_frequency="daily",
                settings_schema=JsonSchemaDefinition(fields=[]),
                skill_binding="trading_executor",
            ),
        ],
        enforcement_defaults=EnforcementDefaults(approval_required=True, deterministic=True),
    )


_DEFINITIONS: dict[str, AgentTypeDefinition] = {
    "marketing.digital_marketing.v1": _marketing_definition(),
    "trading.share_trader.v1": _trading_definition(),
}


def get_agent_type_definition(agent_type_id: str) -> AgentTypeDefinition | None:
    """Return the AgentTypeDefinition for a given id, if available."""

    return _DEFINITIONS.get(_canonical_agent_type_id(agent_type_id))


@router.get("", response_model=list[AgentTypeDefinition])
@router.get("/", response_model=list[AgentTypeDefinition])
async def list_agent_types() -> list[AgentTypeDefinition]:
    return list(_DEFINITIONS.values())


@router.get("/{agent_type_id}", response_model=AgentTypeDefinition)
async def get_agent_type(agent_type_id: str) -> AgentTypeDefinition:
    key = (agent_type_id or "").strip()
    if not key:
        raise HTTPException(status_code=400, detail="agent_type_id is required")

    canonical_key = _canonical_agent_type_id(key)
    definition = _DEFINITIONS.get(canonical_key)
    if not definition:
        raise HTTPException(status_code=404, detail="Agent type not found")

    return definition


@router.put("/{agent_type_id}", response_model=AgentTypeDefinition)
async def upsert_agent_type(
    agent_type_id: str,
    body: AgentTypeDefinition,
    db: AsyncSession | None = Depends(_get_agent_types_db_session),
) -> AgentTypeDefinition | JSONResponse:
    key = (agent_type_id or "").strip()
    if not key:
        raise HTTPException(status_code=400, detail="agent_type_id is required")

    canonical_key = _canonical_agent_type_id(key)
    canonical_body_key = _canonical_agent_type_id((body.agent_type_id or "").strip())
    if canonical_body_key != canonical_key:
        raise HTTPException(status_code=400, detail="agent_type_id mismatch")

    if (body.agent_type_id or "").strip() != canonical_key:
        body = body.model_copy(update={"agent_type_id": canonical_key})

    validation_error = await _validate_required_skill_keys(
        body.required_skill_keys,
        db,
        instance=f"/api/v1/agent-types/{canonical_key}",
    )
    if validation_error is not None:
        return validation_error

    _DEFINITIONS[canonical_key] = body
    return body
