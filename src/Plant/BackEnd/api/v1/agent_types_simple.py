"""Agent Type Definition APIs (Phase-1 simple implementation).

AGP1-PLANT-1:
- Provide versioned AgentTypeDefinitions to CP so CP can render Configure + Goal Setting
  without hard-coding agent-specific schemas.

Phase-1 scope: simple in-memory store with two definitions:
- marketing.healthcare.v1
- trading.delta_futures.v1
"""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


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
    version: str = Field(..., min_length=1)

    config_schema: JsonSchemaDefinition = Field(default_factory=JsonSchemaDefinition)
    goal_templates: list[GoalTemplateDefinition] = Field(default_factory=list)
    enforcement_defaults: EnforcementDefaults = Field(default_factory=EnforcementDefaults)


router = APIRouter(prefix="/agent-types", tags=["agent-types"])


def _marketing_definition() -> AgentTypeDefinition:
    return AgentTypeDefinition(
        agent_type_id="marketing.healthcare.v1",
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
        agent_type_id="trading.delta_futures.v1",
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
    "marketing.healthcare.v1": _marketing_definition(),
    "trading.delta_futures.v1": _trading_definition(),
}


def get_agent_type_definition(agent_type_id: str) -> AgentTypeDefinition | None:
    """Return the AgentTypeDefinition for a given id, if available."""

    return _DEFINITIONS.get(str(agent_type_id or "").strip())


@router.get("", response_model=list[AgentTypeDefinition])
@router.get("/", response_model=list[AgentTypeDefinition])
async def list_agent_types() -> list[AgentTypeDefinition]:
    return list(_DEFINITIONS.values())


@router.get("/{agent_type_id}", response_model=AgentTypeDefinition)
async def get_agent_type(agent_type_id: str) -> AgentTypeDefinition:
    key = (agent_type_id or "").strip()
    if not key:
        raise HTTPException(status_code=400, detail="agent_type_id is required")

    definition = _DEFINITIONS.get(key)
    if not definition:
        raise HTTPException(status_code=404, detail="Agent type not found")

    return definition


@router.put("/{agent_type_id}", response_model=AgentTypeDefinition)
async def upsert_agent_type(agent_type_id: str, body: AgentTypeDefinition) -> AgentTypeDefinition:
    key = (agent_type_id or "").strip()
    if not key:
        raise HTTPException(status_code=400, detail="agent_type_id is required")

    if (body.agent_type_id or "").strip() != key:
        raise HTTPException(status_code=400, detail="agent_type_id mismatch")

    _DEFINITIONS[key] = body
    return body
