from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, List, Optional, Tuple
from uuid import uuid4

from fastapi import Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from agent_mold.reference_agents import THEME_DISCOVERY_REQUIRED_FIELDS
from agent_mold.skills.content_models import Campaign, CampaignWorkflowState, DailyThemeItem, estimate_cost
from agent_mold.skills.executor import execute_marketing_multichannel_v1
from agent_mold.skills.grok_client import GrokClientError, get_grok_client, grok_complete
from agent_mold.skills.loader import load_playbook
from agent_mold.skills.playbook import ArtifactRequest, ArtifactType, ChannelName, SkillExecutionInput
from api.v1 import campaigns as campaigns_module
from api.v1 import hired_agents_simple
from api.v1.platform_connections import get_connected_platform_connection
from core.logging import PiiMaskingFilter
from services.agent_response_validator import detect_filler
from core.routing import waooaw_router
from repositories.campaign_repository import CampaignRepository
from repositories.hired_agent_repository import HiredAgentRepository
from services.brand_voice_service import get_brand_voice
from services.content_analytics import get_content_recommendations, get_posting_time_suggestions
from services.draft_batches import DatabaseDraftBatchStore, DraftBatchRecord, DraftPostRecord


router = waooaw_router(prefix="/hired-agents", tags=["digital-marketing-activation"])
theme_router = waooaw_router(prefix="/digital-marketing-activation", tags=["digital-marketing-activation"])

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())

_WORKSPACE_KEY = "digital_marketing_activation"
_DIGITAL_MARKETING_AGENT_TYPE = "marketing.digital_marketing.v1"

# Bare-minimum fields required before the DMA can generate a rough theme draft.
# The full 11 fields are needed for approval_ready, but these 5 unlock early drafts.
CORE_REQUIRED_FIELDS: list[str] = [
    "industry",
    "locality",
    "target_audience",
    "objective",
    "offer",
]

# Human-readable purpose for each field — sent to the LLM so it can explain
# *why* each piece of information matters (not just demand it).
_FIELD_PURPOSE: dict[str, str] = {
    "business_background": "So your content reflects what you actually do, not generic marketing.",
    "objective": "So every theme drives a specific result — leads, bookings, trust — not random content.",
    "industry": "So the strategy uses the right language, trends, and competitor context for your field.",
    "locality": "So the content targets your actual catchment area and local search terms.",
    "target_audience": "So every post speaks to the right customer segment, not everyone.",
    "persona": "So the content tone and examples match your ideal customer's life-stage and motivation.",
    "tone": "So the brand voice feels consistent and intentional across all content.",
    "offer": "So each post has a clear call-to-action tied to something you actually sell.",
    "channel_intent": "So the content format and style match the platform you chose (e.g. YouTube vs Instagram).",
    "posting_cadence": "So the theme calendar has the right number of slots and pacing.",
    "success_metrics": "So we can measure whether the content is working and adjust.",
}

# Canonical mapping from THEME_DISCOVERY_REQUIRED_FIELDS to workshop summary keys.
# Defined once at module level to avoid drift between prompt construction and validation.
_FIELD_TO_SUMMARY_KEY: dict[str, str] = {
    "business_background": "business_focus",
    "objective": "business_goal",
    "industry": "profession_name",
    "locality": "location_focus",
    "target_audience": "audience",
    "persona": "customer_profile",
    "tone": "tone",
    "offer": "cta",
    "channel_intent": "youtube_angle",
    "posting_cadence": "first_content_direction",
    "success_metrics": "positioning",
}


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
    workspace: dict[str, Any] = Field(default_factory=dict)
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
    # Populated when the customer's message triggers content generation directly from chat
    auto_generated_draft: Optional[dict[str, Any]] = None
    posting_time_suggestions: list[dict[str, str]] = Field(default_factory=list)


@lru_cache(maxsize=1)
def _dma_playbook():
    path = (
        Path(__file__).resolve().parents[2]
        / "agent_mold"
        / "playbooks"
        / "marketing"
        / "multichannel_post_v1.md"
    )
    return load_playbook(path)


# ---------------------------------------------------------------------------
# Intent detection — recognises natural-language approval / generation signals
# ---------------------------------------------------------------------------

_APPROVAL_PATTERNS = re.compile(
    r"\b(approve[ds]?|yes|confirm(s|ed)?|go ahead|start|proceed|lock.?it|lock.?in|looks? good|all set|"
    r"let'?s go|move.?on|next step|finalize|finalise|done|ready|great|perfect|sounds? good|agreed)\b",
    re.IGNORECASE,
)

_ARTIFACT_KEYWORDS: List[Tuple[str, ArtifactType]] = [
    (r"\b(table|tabular|tabulate|spreadsheet|schedule|plan|calendar|list|comparison|checklist)\b", ArtifactType.TABLE),
    (r"\b(image|picture|photo|visual|graphic|thumbnail|banner|design)\b", ArtifactType.IMAGE),
    (r"\b(video|clip|reel|short|film|recording)\b", ArtifactType.VIDEO),
    (r"\b(audio|voice|narration|podcast|sound)\b", ArtifactType.AUDIO),
    (r"\b(video.?audio|narrated.?video|video.?with.?(voice|narration|audio))\b", ArtifactType.VIDEO_AUDIO),
]

_GENERATE_VERBS = re.compile(
    r"\b(show|give|create|generate|make|build|produce|draft|write|prepare|get)\b",
    re.IGNORECASE,
)


def _detect_generation_intent(
    pending_input: str,
    workshop_status: str,
) -> Tuple[bool, List[ArtifactType]]:
    """Return (should_generate_draft, artifact_types_requested).

    Fires when:
    - customer explicitly requests an artifact type (table/image/video etc.), OR
    - customer sends an approval signal AND the workshop is already approval_ready or approved.
    """
    text = pending_input.strip()
    if not text:
        return False, []

    # Detect explicit artifact mention
    requested_artifact_types: List[ArtifactType] = []
    for pattern, artifact_type in _ARTIFACT_KEYWORDS:
        if re.search(pattern, text, re.IGNORECASE):
            requested_artifact_types.append(artifact_type)

    has_generate_verb = bool(_GENERATE_VERBS.search(text))
    has_approval_signal = bool(_APPROVAL_PATTERNS.search(text))

    # Explicit "show me table/video/image" — always generate
    if requested_artifact_types and has_generate_verb:
        return True, requested_artifact_types

    # Pure approval signal when strategy is ready — generate table by default
    if has_approval_signal and workshop_status in {"approval_ready", "approved", "draft_ready"}:
        # Default to table if no specific artifact mentioned
        return True, requested_artifact_types or [ArtifactType.TABLE]

    # Conversational mention of an artifact type with approval signal
    if requested_artifact_types and has_approval_signal:
        return True, requested_artifact_types

    return False, []


async def _build_auto_draft(
    *,
    record: hired_agents_simple._HiredAgentRecord,
    workspace: dict[str, Any],
    master_theme: str,
    campaign_id: str | None,
    artifact_types: List[ArtifactType],
    db: AsyncSession | None,
) -> dict[str, Any]:
    """Build and persist a draft batch inline from the chat handler. Returns the serialisable batch dict."""
    playbook = _dma_playbook()
    # Use the customer's brand name from the workspace brief — never fall back to the
    # agent's own hire nickname (that causes the agent's personal name to appear in posts).
    # D2 fix: if brand_name is empty, fall back to workshop summary fields before giving up.
    brand_name = str(workspace.get("brand_name") or "").strip()
    if not brand_name:
        summary = (workspace.get("campaign_setup") or {}).get("strategy_workshop", {}).get("summary", {})
        brand_name = (
            str(summary.get("profession_name") or "").strip()
            or str(summary.get("business_focus") or "").strip()
            or str(workspace.get("agent_type_id") or record.agent_type_id or "").strip()
            or "Brand"
        )
    location = str(workspace.get("location") or "").strip()
    language = str(workspace.get("primary_language") or "en").strip()

    batch_id = str(uuid4())
    posts: List[DraftPostRecord] = []

    # ── TABLE artifact: build a GFM markdown table from campaign themes ──────
    if ArtifactType.TABLE in artifact_types:
        campaign_setup: dict[str, Any] = workspace.get("campaign_setup") or {}
        derived_themes: List[dict[str, Any]] = campaign_setup.get("derived_themes") or []
        master_theme_val = campaign_setup.get("master_theme") or master_theme or brand_name or "Content Plan"

        if derived_themes:
            header = f"**Master Theme:** {master_theme_val}\n\n"
            table_lines = [
                "| # | Theme | Description | Frequency |",
                "|---|-------|-------------|-----------|",
            ]
            table_preview_rows = []
            for i, theme in enumerate(derived_themes, 1):
                title = str(theme.get("title") or "").replace("|", "\\|")
                desc = str(theme.get("description") or "").replace("|", "\\|")
                freq = str(theme.get("frequency") or "").replace("|", "\\|")
                table_lines.append(f"| {i} | {title} | {desc} | {freq} |")
                # Build structured table_preview for frontend
                table_preview_rows.append({
                    "#": str(i),
                    "Theme": str(theme.get("title") or ""),
                    "Description": str(theme.get("description") or ""),
                    "Frequency": str(theme.get("frequency") or "weekly"),
                })
            table_text = header + "\n".join(table_lines)
        else:
            table_text = (
                f"**Master Theme:** {master_theme_val}\n\n"
                "| # | Theme | Description | Frequency |\n"
                "|---|-------|-------------|----------|\n"
                f"| 1 | {master_theme_val} | Content plan for {brand_name or 'your brand'} | weekly |\n"
            )
            table_preview_rows = [{
                "#": "1",
                "Theme": master_theme_val,
                "Description": f"Content plan for {brand_name or 'your brand'}",
                "Frequency": "weekly",
            }]

        posts.append(
            DraftPostRecord(
                post_id=str(uuid4()),
                channel="youtube",
                text=table_text,
                artifact_type="table",
                hashtags=[],
                artifact_metadata={
                    "table_preview": {
                        "columns": ["#", "Theme", "Description", "Frequency"],
                        "rows": table_preview_rows,
                    }
                },
            )
        )

    # ── Non-table artifacts: run the deterministic channel adapters ───────────
    non_table_types = [a for a in artifact_types if a != ArtifactType.TABLE]
    if non_table_types or not posts:
        subject = master_theme or brand_name or "the approved content plan"
        requested_artifacts = [
            ArtifactRequest(
                artifact_type=art,
                prompt=f"Create a {art.value.replace('_', ' ')} asset for: {subject}",
                metadata={"source": "dma_chat_intent", "channel": "youtube"},
            )
            for art in (non_table_types or [ArtifactType.TABLE])
        ]

        channel_brand = brand_name or "Brand"
        result = execute_marketing_multichannel_v1(
            playbook,
            SkillExecutionInput(
                theme=master_theme or channel_brand,
                brand_name=channel_brand,
                offer=None,
                location=location or None,
                audience=None,
                tone=None,
                language=language,
                channels=[ChannelName.YOUTUBE],
                requested_artifacts=requested_artifacts,
            ),
        )

        for v in result.output.variants:
            art_type: str = non_table_types[0].value if non_table_types else "text"
            posts.append(
                DraftPostRecord(
                    post_id=str(uuid4()),
                    channel=v.channel,
                    text=v.text,
                    artifact_type=art_type,
                    hashtags=v.hashtags,
                )
            )

    # E1 fix: agent_id, theme, and brand_name all have min_length=1 in DraftBatchRecord.
    # Ensure none of them can be empty strings to prevent silent Pydantic validation failures.
    safe_agent_id = str(record.agent_id or "").strip() or str(record.agent_type_id or "").strip() or "unknown-agent"
    safe_theme = (master_theme or brand_name or "Content Plan").strip() or "Content Plan"

    batch = DraftBatchRecord(
        batch_id=batch_id,
        agent_id=safe_agent_id,
        hired_instance_id=record.hired_instance_id,
        campaign_id=campaign_id,
        customer_id=str(record.customer_id or "") if record.customer_id else None,
        theme=safe_theme,
        brand_name=brand_name,
        brief_summary=None,
        created_at=datetime.utcnow(),
        posts=posts,
    )

    if db is not None:
        store = DatabaseDraftBatchStore(db)
        await store.save_batch(batch)
        # Caller commits after this returns

    return batch.model_dump(mode="json")


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


def _normalize_workshop_messages(raw_messages: Any) -> list[dict[str, str]]:
    if not isinstance(raw_messages, list):
        return []

    normalized: list[dict[str, str]] = []
    for item in raw_messages:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").strip().lower()
        content = str(item.get("content") or "").strip()
        if role not in {"assistant", "user"} or not content:
            continue
        normalized.append({"role": role, "content": content})
    return normalized[-12:]


def _normalize_string_list(raw_items: Any) -> list[str]:
    if not isinstance(raw_items, list):
        return []
    return [str(item or "").strip() for item in raw_items if str(item or "").strip()]


def _complete_or_fallback_text(value: Any, fallback: str, *, max_length: int = 320) -> str:
    text = str(value or "").strip()
    if not text:
        return fallback

    compact = " ".join(text.split())[:max_length].strip()
    if not compact:
        return fallback

    if compact[-1:] in {".", "!", "?"}:
        return compact

    sentence_end = max(compact.rfind("."), compact.rfind("!"), compact.rfind("?"))
    if sentence_end >= 24:
        return compact[: sentence_end + 1].strip()

    if compact.endswith((" can we", " shall we", " should we", " let us", " let's")):
        return fallback

    last_word = compact.split(" ")[-1]
    if len(last_word) <= 2:
        return fallback

    return compact


def _base_workshop_summary(workspace: dict[str, Any]) -> dict[str, Any]:
    return {
        "profession_name": "",
        "location_focus": str(workspace.get("location") or "").strip(),
        "customer_profile": str(workspace.get("target_audience") or "").strip(),
        "service_focus": ", ".join(_normalize_string_list(workspace.get("offerings_services"))),
        "signature_differentiator": "",
        "business_goal": "",
        "first_content_direction": "",
        "business_focus": str(workspace.get("offerings_services") or "").strip() if isinstance(workspace.get("offerings_services"), str) else ", ".join(
            _normalize_string_list(workspace.get("offerings_services"))
        ),
        "audience": str(workspace.get("target_audience") or "").strip(),
        "positioning": "",
        "tone": "",
        "content_pillars": [],
        "youtube_angle": "",
        "cta": "",
    }


def _normalize_workshop_summary(raw_summary: Any, workspace: dict[str, Any]) -> dict[str, Any]:
    summary = _base_workshop_summary(workspace)
    if not isinstance(raw_summary, dict):
        return summary

    for field in (
        "profession_name",
        "location_focus",
        "customer_profile",
        "service_focus",
        "signature_differentiator",
        "business_goal",
        "first_content_direction",
        "business_focus",
        "audience",
        "positioning",
        "tone",
        "youtube_angle",
        "cta",
    ):
        value = str(raw_summary.get(field) or "").strip()
        if value:
            summary[field] = value
    summary["content_pillars"] = _normalize_string_list(raw_summary.get("content_pillars"))
    return summary


def _normalize_strategy_workshop(raw_workshop: Any, workspace: dict[str, Any]) -> dict[str, Any]:
    workshop = dict(raw_workshop or {}) if isinstance(raw_workshop, dict) else {}
    status = str(workshop.get("status") or "not_started").strip().lower()
    if status not in {"not_started", "discovery", "draft_ready", "approval_ready", "approved"}:
        status = "not_started"

    approved_at = workshop.get("approved_at")
    approved_at_value = str(approved_at).strip() if approved_at else None
    return {
        "status": status,
        "assistant_message": str(workshop.get("assistant_message") or "").strip(),
        "checkpoint_summary": str(workshop.get("checkpoint_summary") or "").strip(),
        "current_focus_question": str(workshop.get("current_focus_question") or "").strip(),
        "next_step_options": _normalize_string_list(workshop.get("next_step_options")),
        "time_saving_note": str(workshop.get("time_saving_note") or "").strip(),
        "follow_up_questions": _normalize_string_list(workshop.get("follow_up_questions")),
        "messages": _normalize_workshop_messages(workshop.get("messages")),
        "summary": _normalize_workshop_summary(workshop.get("summary"), workspace),
        "approved_at": approved_at_value,
    }


def _infer_profession_label(workspace: dict[str, Any], workshop: dict[str, Any]) -> str:
    summary = dict(workshop.get("summary") or {})
    explicit = str(summary.get("profession_name") or "").strip()
    if explicit:
        return explicit

    haystack = " ".join(
        [
            str(workspace.get("brand_name") or ""),
            str(workspace.get("business_context") or ""),
            " ".join(_normalize_string_list(workspace.get("offerings_services"))),
        ]
    ).lower()

    profession_keywords = {
        "Beauty Artist": ["beauty", "makeup", "salon", "hair", "nail", "bridal", "cosmetic"],
        "Doctor": ["doctor", "clinic", "hospital", "dental", "dentist", "skin", "medical"],
        "Share Trader": ["trader", "trading", "stocks", "equity", "market", "investment"],
        "Tutor": ["tutor", "coaching", "teaching", "education", "exam", "class"],
    }
    for label, keywords in profession_keywords.items():
        if any(keyword in haystack for keyword in keywords):
            return label
    return "Digital Business Expert"


def _profession_flavor(label: str) -> str:
    normalized = str(label or "").strip().lower()
    if "beauty" in normalized or "artist" in normalized or "salon" in normalized:
        return (
            "Think like a premium beauty growth strategist. Focus on trust, visual proof, occasion-led demand, local reputation, "
            "repeat bookings, health-conscious product choices, and confidence outcomes for women deciding where to spend on grooming or event looks."
        )
    if "doctor" in normalized or "clinic" in normalized or "dental" in normalized:
        return (
            "Think like a healthcare content strategist. Focus on trust, expertise, patient hesitation, local credibility, ethical education, "
            "and helping cautious patients move from fear or confusion to informed action."
        )
    if "trader" in normalized or "share" in normalized or "market" in normalized:
        return (
            "Think like a finance educator strategist. Focus on trust, clarity, risk awareness, disciplined decision-making, audience sophistication, "
            "and converting curiosity into advisory credibility without hype."
        )
    if "tutor" in normalized or "education" in normalized or "coaching" in normalized:
        return (
            "Think like an education growth strategist. Focus on parent/student anxieties, outcomes, pedagogy credibility, exam confidence, local trust, "
            "and proving teaching quality through helpful explanations and structured guidance."
        )
    return (
        "Think like a premium local-business content strategist. Focus on trust, differentiation, customer motivations, local proof, "
        "and the fastest path from curiosity to serious inquiry."
    )


def _theme_workshop_prompt(
    workspace: dict[str, Any],
    campaign_setup: dict[str, Any],
    brand_voice_section: dict[str, Any] | None = None,
    performance_insights: dict[str, Any] | None = None,
) -> str:
    workshop = _normalize_strategy_workshop(campaign_setup.get("strategy_workshop"), workspace)
    profession_label = _infer_profession_label(workspace, workshop)
    pending_input = str(campaign_setup.get("strategy_workshop", {}).get("pending_input") or "").strip() if isinstance(campaign_setup.get("strategy_workshop"), dict) else ""
    
    # Compute locked and missing fields
    summary = workshop["summary"]
    locked_fields = {}
    missing_fields = []
    for req_field in THEME_DISCOVERY_REQUIRED_FIELDS:
        summary_key = _FIELD_TO_SUMMARY_KEY.get(req_field, req_field)
        value = str(summary.get(summary_key) or "").strip()
        if value:
            locked_fields[req_field] = value
        else:
            missing_fields.append(req_field)
    
    return json.dumps(
        {
            "operating_mode": {
                "profession_label": profession_label,
                "profession_flavor": _profession_flavor(profession_label),
                "free_model_rules": [
                    "Keep the strategist response under 90 words and usually within 1-2 short sentences.",
                    "Do not repeat the user's last answer in full.",
                    "Do not restart the conversation or ask the customer to repeat context already present in the thread.",
                    "Give one insight, one recommendation, and one next question only if still needed.",
                    "Provide 2-3 short next-step options that save the customer's time.",
                    "Sound like a premium strategist in live chat, not a setup wizard, checklist, or intake form.",
                    "Keep the tone consultative, targeted, commercially sharp, and calm.",
                    "Lead the conversation with confidence and warmth so the customer feels guided, not processed.",
                    "Move to approval_ready as soon as the strategy is coherent enough.",
                ],
            },
            "business_profile": {
                "brand_name": workspace.get("brand_name") or "",
                "offerings_services": workspace.get("offerings_services") or [],
                "location": workspace.get("location") or "",
                "primary_language": workspace.get("primary_language") or "",
                "timezone": workspace.get("timezone") or "",
                "business_context": workspace.get("business_context") or "",
                "selected_platforms": _selected_platforms(workspace),
            },
            "campaign_setup": {
                "schedule": dict(campaign_setup.get("schedule") or {}),
            },
            "workshop_state": {
                "status": workshop["status"],
                "messages": workshop["messages"],
                "summary": workshop["summary"],
                "follow_up_questions": workshop["follow_up_questions"],
                "required_fields_checklist": {
                    "total": len(THEME_DISCOVERY_REQUIRED_FIELDS),
                    "filled": len(locked_fields),
                    "missing": len(missing_fields),
                    "locked_fields": locked_fields,
                    "missing_fields": missing_fields,
                    "core_fields": CORE_REQUIRED_FIELDS,
                    "core_filled": [f for f in CORE_REQUIRED_FIELDS if f in locked_fields],
                    "core_missing": [f for f in CORE_REQUIRED_FIELDS if f not in locked_fields],
                    "can_generate_draft": len([f for f in CORE_REQUIRED_FIELDS if f in locked_fields]) >= 5,
                    "field_purposes": {f: _FIELD_PURPOSE.get(f, "") for f in missing_fields},
                },
            },
            "pending_customer_input": pending_input,
            "brand_voice_context": brand_voice_section or {},
            "performance_insights": performance_insights or {},
            "response_contract": {
                "assistant_message": "One compact, high-conviction, thread-aware strategist reply in plain English. It should feel like premium live chat: warm, commercially sharp, and easy to respond to.",
                "checkpoint_summary": "One short paragraph summarizing what is now locked.",
                "current_focus_question": "At most one high-value question. Empty string if not needed.",
                "next_step_options": ["Two or three short suggested next moves."],
                "time_saving_note": "One sentence that makes it explicit how you are saving the customer's time.",
                "status": "One of discovery or approval_ready.",
                "summary": {
                    "profession_name": "Beauty Artist / Doctor / Share Trader / Tutor / etc.  [canonical: industry]",
                    "location_focus": "Locality or geography to prioritize.  [canonical: locality]",
                    "customer_profile": "Age, life-stage, income, event, or motivation summary.  [canonical: persona]",
                    "service_focus": "Key services or offer cluster.",
                    "signature_differentiator": "What makes the business distinct.",
                    "business_goal": "Primary commercial goal from content.  [canonical: objective]",
                    "first_content_direction": "Recommended first angle or series to start with.  [canonical: posting_cadence]",
                    "business_focus": "Short sentence.  [canonical: business_background]",
                    "audience": "Short sentence.  [canonical: target_audience]",
                    "positioning": "Short sentence.  [canonical: success_metrics]",
                    "tone": "Short sentence.  [canonical: tone]",
                    "content_pillars": ["Three concise pillars."],
                    "competitor_names": ["2-5 competitor or peer names."],
                    "niche_keywords": ["5-10 niche keywords or trending topics."],
                    "youtube_angle": "Short sentence.  [canonical: channel_intent]",
                    "cta": "Short sentence.  [canonical: offer]",
                },
                "master_theme": "A clear approved-ready master theme statement.",
                "derived_themes": [
                    {
                        "title": "Theme title",
                        "description": "What this content lane covers",
                        "frequency": "weekly",
                        "pillar": "Content pillar name",
                    }
                ],
            },
        },
        ensure_ascii=False,
    )


def _normalize_derived_themes(raw_derived: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_derived, list):
        return []

    normalized: list[dict[str, Any]] = []
    for row in raw_derived:
        if isinstance(row, str):
            title = row.strip()
            if title:
                normalized.append({"title": title, "description": "", "frequency": "weekly"})
            continue
        if not isinstance(row, dict):
            continue
        title = str(row.get("title") or "").strip()
        if not title:
            continue
        normalized.append(
            {
                "title": title,
                "description": str(row.get("description") or "").strip(),
                "frequency": str(row.get("frequency") or "weekly").strip() or "weekly",
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
        candidate = cleaned.splitlines()[0] if cleaned.splitlines() else cleaned
        return _complete_or_fallback_text(candidate, "Digital marketing activation plan", max_length=180), []

    if not isinstance(payload, dict):
        return "Digital marketing activation plan", []

    master_theme = _complete_or_fallback_text(
        payload.get("master_theme") or payload.get("theme"),
        "Digital marketing activation plan",
        max_length=180,
    )
    return master_theme or "Digital marketing activation plan", _normalize_derived_themes(payload.get("derived_themes"))


def _parse_theme_workshop_response(
    raw_text: str,
    *,
    workspace: dict[str, Any],
    existing_workshop: dict[str, Any],
    pending_input: str,
) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    cleaned = str(raw_text or "").strip()
    fallback_message = "I can take this forward quickly. Tell me the one business result this content must drive first, and I will turn that into a sharper direction."

    if not cleaned:
        workshop = _normalize_strategy_workshop(existing_workshop, workspace)
        workshop["status"] = "discovery"
        workshop["assistant_message"] = fallback_message
        workshop["checkpoint_summary"] = "We have the business basics, but the commercial priority is still too broad to lock the theme."
        workshop["time_saving_note"] = "I am narrowing this to the one decision that most changes the content direction."
        if pending_input:
            workshop["messages"] = [*workshop["messages"], {"role": "user", "content": pending_input}]
        workshop["messages"] = [*workshop["messages"], {"role": "assistant", "content": fallback_message}]
        workshop["current_focus_question"] = "What is the first business result this content should drive: trust, leads, repeat bookings, or direct sales?"
        workshop["next_step_options"] = ["Refine the audience", "Clarify the core offer", "Choose the first content angle"]
        return "Digital marketing activation plan", [], workshop

    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        master_theme, derived_themes = _parse_theme_plan(cleaned)
        workshop = _normalize_strategy_workshop(existing_workshop, workspace)
        if pending_input:
            workshop["messages"] = [*workshop["messages"], {"role": "user", "content": pending_input}]
        assistant_message = _complete_or_fallback_text(master_theme, fallback_message)
        workshop["assistant_message"] = assistant_message
        workshop["status"] = "approval_ready" if derived_themes else "discovery"
        workshop["checkpoint_summary"] = _complete_or_fallback_text(
            master_theme,
            "The core strategy is taking shape, but it still needs one stronger decision.",
        )
        workshop["current_focus_question"] = ""
        workshop["next_step_options"] = ["Approve this direction", "Sharpen the audience", "Suggest a different first angle"]
        workshop["time_saving_note"] = "I have collapsed your earlier answers into one working direction so we do not keep restating the same inputs."
        workshop["messages"] = [*workshop["messages"], {"role": "assistant", "content": assistant_message}]
        return master_theme, derived_themes, workshop

    if not isinstance(payload, dict):
        return _parse_theme_workshop_response("", workspace=workspace, existing_workshop=existing_workshop, pending_input=pending_input)

    master_theme = _complete_or_fallback_text(
        payload.get("master_theme") or payload.get("theme") or existing_workshop.get("master_theme"),
        "Digital marketing activation plan",
        max_length=180,
    )
    derived_themes = _normalize_derived_themes(payload.get("derived_themes"))
    assistant_message = _complete_or_fallback_text(
        payload.get("assistant_message") or (master_theme if derived_themes else fallback_message),
        fallback_message,
    )
    # Filler gate: if the LLM returned conversational fluff instead of actionable
    # guidance, replace with the deterministic fallback so the user gets a real
    # next-step instead of "I'm thrilled to present…" prose.
    if detect_filler(assistant_message):
        logger.info("Filler detected in LLM assistant_message, using fallback")
        assistant_message = fallback_message
    workshop = _normalize_strategy_workshop(payload.get("strategy_workshop") or payload, workspace)

    if pending_input:
        workshop["messages"] = [*existing_workshop.get("messages", []), {"role": "user", "content": pending_input}]
    else:
        workshop["messages"] = list(existing_workshop.get("messages", []))

    workshop["assistant_message"] = assistant_message
    workshop["messages"] = [*workshop["messages"], {"role": "assistant", "content": assistant_message}]
    workshop["checkpoint_summary"] = _complete_or_fallback_text(
        payload.get("checkpoint_summary") or workshop.get("checkpoint_summary"),
        "The core strategy is taking shape, but it still needs one stronger decision.",
    )
    workshop["current_focus_question"] = _complete_or_fallback_text(
        payload.get("current_focus_question") or workshop.get("current_focus_question"),
        "",
        max_length=220,
    )
    workshop["time_saving_note"] = str(payload.get("time_saving_note") or workshop.get("time_saving_note") or "").strip()
    if payload.get("next_step_options"):
        workshop["next_step_options"] = _normalize_string_list(payload.get("next_step_options"))
    if not workshop["follow_up_questions"] and payload.get("follow_up_questions"):
        workshop["follow_up_questions"] = _normalize_string_list(payload.get("follow_up_questions"))
    if not workshop["current_focus_question"] and workshop["follow_up_questions"]:
        workshop["current_focus_question"] = workshop["follow_up_questions"][0]
    if not workshop["status"] or workshop["status"] == "not_started":
        workshop["status"] = "approval_ready" if (master_theme and derived_themes) else "discovery"
    if workshop["status"] == "approval_ready":
        workshop["approved_at"] = None
        if not workshop["next_step_options"]:
            workshop["next_step_options"] = ["Approve this direction", "Refine the positioning", "Request another theme version"]
    
    # E1-S2: Server-side field-completeness validation gate
    filled_count = sum(
        1 for req_field in THEME_DISCOVERY_REQUIRED_FIELDS
        if str(workshop["summary"].get(_FIELD_TO_SUMMARY_KEY.get(req_field, req_field)) or "").strip()
    )
    
    # E2-S1: Add brief_progress to workshop dict
    workshop["brief_progress"] = {
        "filled": filled_count,
        "total": len(THEME_DISCOVERY_REQUIRED_FIELDS),
        "missing_fields": [
            req_field for req_field in THEME_DISCOVERY_REQUIRED_FIELDS
            if not str(workshop["summary"].get(_FIELD_TO_SUMMARY_KEY.get(req_field, req_field)) or "").strip()
        ],
        "locked_fields": {
            req_field: str(workshop["summary"].get(_FIELD_TO_SUMMARY_KEY.get(req_field, req_field)) or "").strip()
            for req_field in THEME_DISCOVERY_REQUIRED_FIELDS
            if str(workshop["summary"].get(_FIELD_TO_SUMMARY_KEY.get(req_field, req_field)) or "").strip()
        },
    }
    
    # Count how many CORE fields are filled (for draft-readiness)
    core_filled_count = sum(
        1 for req_field in CORE_REQUIRED_FIELDS
        if str(workshop["summary"].get(_FIELD_TO_SUMMARY_KEY.get(req_field, req_field)) or "").strip()
    )
    workshop["brief_progress"]["core_filled_count"] = core_filled_count
    workshop["brief_progress"]["can_generate_draft"] = core_filled_count >= len(CORE_REQUIRED_FIELDS)

    if workshop["status"] == "approval_ready" and filled_count < 9:
        # If all 5 core fields are filled, allow "draft_ready" — a middle state
        # where the DMA can produce a rough theme calendar but not final approval.
        if core_filled_count >= len(CORE_REQUIRED_FIELDS):
            logger.info(
                "LLM tried approval_ready with %d/%d fields (%d/%d core) — allowing draft_ready",
                filled_count, len(THEME_DISCOVERY_REQUIRED_FIELDS),
                core_filled_count, len(CORE_REQUIRED_FIELDS),
            )
            workshop["status"] = "draft_ready"
        else:
            core_missing = [
                f for f in CORE_REQUIRED_FIELDS
                if not str(workshop["summary"].get(_FIELD_TO_SUMMARY_KEY.get(f, f)) or "").strip()
            ]
            logger.warning(
                "LLM tried approval_ready with only %d/%d fields filled (core missing: %s) — forcing discovery",
                filled_count, len(THEME_DISCOVERY_REQUIRED_FIELDS), core_missing,
            )
            workshop["status"] = "discovery"
            missing_explanations = "; ".join(
                f"{f}: {_FIELD_PURPOSE.get(f, '')}" for f in core_missing[:3]
            )
            if not workshop["current_focus_question"]:
                workshop["current_focus_question"] = (
                    f"To build your content calendar I still need: {', '.join(core_missing)}. "
                    f"{missing_explanations}. Which of these can you share first?"
                )
    
    return master_theme or "Digital marketing activation plan", derived_themes, workshop


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
    existing_campaign_setup = dict(workspace.get("campaign_setup") or {})
    campaign_setup = {
        **existing_campaign_setup,
        **dict(body.campaign_setup or {}),
    }
    existing_workshop = _normalize_strategy_workshop(campaign_setup.get("strategy_workshop"), workspace)
    pending_input = str(campaign_setup.get("strategy_workshop", {}).get("pending_input") or "").strip() if isinstance(campaign_setup.get("strategy_workshop"), dict) else ""

    # Load brand voice for this customer
    brand_voice = await get_brand_voice(customer_id=str(record.customer_id), db=db) if db is not None else None
    brand_voice_section = {}
    if brand_voice:
        brand_voice_section = {
            "tone_keywords": brand_voice.tone_keywords or [],
            "vocabulary_preferences": brand_voice.vocabulary_preferences or [],
            "messaging_patterns": brand_voice.messaging_patterns or [],
            "example_phrases": brand_voice.example_phrases or [],
            "voice_description": brand_voice.voice_description or "",
        }

    # Load performance insights for this hired agent
    performance_insights = {}
    try:
        recommendations = await get_content_recommendations(
            hired_instance_id=hired_instance_id, db=db
        ) if db is not None else None
        if recommendations and recommendations.avg_engagement_rate > 0:
            performance_insights = {
                "top_performing_dimensions": recommendations.top_dimensions,
                "best_posting_hours": recommendations.best_posting_hours,
                "avg_engagement_rate": recommendations.avg_engagement_rate,
                "recommendation_summary": recommendations.recommendation_text,
            }
    except Exception:
        logger.warning("Could not load performance insights — proceeding without")

    try:
        client = get_grok_client()
        proposal = grok_complete(
            client,
            system=(
                "You are the Digital Marketing Agent the customer has already hired, and you are running a live strategy conversation. "
                "Sound like a world-class strategist inside a premium chat product: warm, confident, commercially sharp, and easy to reply to. "
                "Do not sound like a wizard, onboarding checklist, status dashboard, or form. Lead the customer through the fewest possible questions, "
                "extract signal quickly, and make each reply feel useful enough that the customer wants to keep going. "
                "\n\nREQUIRED FIELDS COLLECTION RULES:\n"
                "Here are the 11 fields you must collect. When a field has a value, it is LOCKED — never ask about it again. "
                "The required fields are: business_background, objective, industry, locality, target_audience, persona, tone, offer, channel_intent, posting_cadence, success_metrics. "
                "When the customer gives a direct answer, lock that field and confirm in one sentence. Do NOT re-offer locked fields as next-step options. "
                "When all 11 fields are filled, you MUST set status to approval_ready and present the master theme for approval. Do not ask more questions. "
                "\n\nCONTENT PILLARS:\n"
                "During discovery, help the customer define 3-5 content pillars — recurring categories that all content should map to. "
                "Examples: Educational, Behind the scenes, Customer stories, Industry trends, Product showcase. "
                "Each derived theme must map to one pillar. Include `content_pillars` in the summary. "
                "\n\nCOMPETITOR AND NICHE CONTEXT:\n"
                "Ask the customer to name 2-5 competitors or industry peers they want to differentiate from. "
                "Also ask for 5-10 niche keywords or topics that are trending in their space. "
                "Include `competitor_names` and `niche_keywords` in the summary. "
                "\n\nBRAND VOICE:\n"
                "The customer's brand voice is provided in the context. Use this exact tone, vocabulary, and messaging patterns in all conversation responses and generated content. "
                "\n\nPERFORMANCE INSIGHTS:\n"
                "Performance insights from previous content cycles are provided below. Use these to guide theme recommendations — favor topics and formats that drove higher engagement. "
                "Reference specific performance data when making suggestions. "
                "\n\nDELIVERABLE REQUEST RULE (MANDATORY — READ CAREFULLY):\n"
                "When the customer asks for a concrete deliverable (plan, table, draft, schedule, themes, calendar):\n"
                "1. Check the required_fields_checklist in the context below.\n"
                "2. If 5 or more CORE fields are filled (industry, locality, target_audience, objective, offer), "
                "produce the deliverable NOW — return master_theme and 2-4 derived_themes in the JSON response. "
                "Use reasonable defaults for any still-missing non-core fields and note what you assumed.\n"
                "3. If fewer than 5 core fields are filled, tell the customer clearly: "
                "'To build your content calendar I need [list the missing core fields]. Here is why each matters: [one line per field from the field_purposes below].' "
                "Then ask for the most important missing field. Do NOT produce empty themes or filler text.\n"
                "4. NEVER respond with just conversational text like 'I would be happy to provide...' when a deliverable is requested. "
                "Either produce the deliverable or state exactly what is missing.\n"
                "\n\nFIELD PURPOSE REFERENCE (use when explaining why a field is needed):\n"
                "- industry: So the strategy uses the right language, trends, and competitor context.\n"
                "- locality: So content targets your actual catchment area and local search terms.\n"
                "- target_audience: So every post speaks to the right customer, not everyone.\n"
                "- objective: So every theme drives a specific result, not random content.\n"
                "- offer: So each post has a clear call-to-action tied to what you sell.\n"
                "- persona: So content matches your ideal customer's life-stage and motivation.\n"
                "- tone: So brand voice is consistent across all content.\n"
                "- channel_intent: So content format matches the chosen platform.\n"
                "- posting_cadence: So the calendar has the right pacing.\n"
                "- success_metrics: So we can measure and adjust.\n"
                "- business_background: So content reflects what you actually do.\n"
                "\n\nAsk probing questions only until the strategy is strong enough for approval, then return a clear master theme, 2-4 derived themes, and a structured summary. "
                "Always return JSON matching the requested response contract."
            ),
            user=_theme_workshop_prompt(workspace, campaign_setup, brand_voice_section, performance_insights),
            model="grok-3-latest",
            temperature=0.7,
        )
    except GrokClientError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    master_theme, derived_themes, strategy_workshop = _parse_theme_workshop_response(
        proposal,
        workspace=workspace,
        existing_workshop=existing_workshop,
        pending_input=pending_input,
    )
    logger.info("Generated DMA theme plan for hired_instance_id=%s", hired_instance_id)
    campaign_id = await _persist_theme_plan_to_campaign(
        record=record,
        workspace=workspace,
        master_theme=master_theme,
        derived_themes=derived_themes,
        campaign_setup=campaign_setup,
        db=db,
    )
    persisted_campaign_setup = {
        **campaign_setup,
        "strategy_workshop": {
            **strategy_workshop,
        },
    }
    persisted_workspace = _build_theme_plan_workspace(
        workspace=workspace,
        campaign_setup=persisted_campaign_setup,
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

    # --- Intent detection: did the customer ask to generate content? ---
    auto_draft: dict[str, Any] | None = None
    should_generate, artifact_types = _detect_generation_intent(
        pending_input,
        workshop_status=strategy_workshop.get("status", "discovery"),
    )
    # Also allow generation when workshop is draft_ready (5+ core fields)
    if not should_generate and strategy_workshop.get("status") == "draft_ready":
        # Check if the pending input mentions a deliverable
        should_generate, artifact_types = _detect_generation_intent(
            pending_input,
            workshop_status="approval_ready",  # Treat draft_ready like approval_ready for intent
        )

    # If we should generate a TABLE but derived_themes are empty, generate them now
    if should_generate and ArtifactType.TABLE in artifact_types and not derived_themes:
        brief = strategy_workshop.get("brief_progress", {})
        core_filled = brief.get("core_filled_count", 0)
        if core_filled >= len(CORE_REQUIRED_FIELDS):
            # Second targeted LLM call: "generate themes from what we have"
            try:
                summary_snapshot = strategy_workshop.get("summary", {})
                theme_gen_prompt = (
                    f"Generate a content theme calendar for this business. Return ONLY JSON with "
                    f"master_theme (string) and derived_themes (array of 2-4 objects with title, description, frequency, pillar).\n\n"
                    f"Business: {summary_snapshot.get('profession_name', '')} in {summary_snapshot.get('location_focus', '')}\n"
                    f"Audience: {summary_snapshot.get('audience', '')}\n"
                    f"Goal: {summary_snapshot.get('business_goal', '')}\n"
                    f"Offer: {summary_snapshot.get('cta', '')}\n"
                    f"Tone: {summary_snapshot.get('tone', 'professional')}\n"
                    f"Channel: {summary_snapshot.get('youtube_angle', 'YouTube')}\n"
                    f"Brand: {workspace.get('brand_name', '')}"
                )
                theme_json_str = grok_complete(
                    client,
                    system="You are a content strategist. Return ONLY valid JSON with master_theme and derived_themes. No conversational text.",
                    user=theme_gen_prompt,
                    model="grok-3-latest",
                    temperature=0.5,
                )
                import json as _json
                theme_data = _json.loads(theme_json_str)
                derived_themes = _normalize_derived_themes(theme_data.get("derived_themes", []))
                if derived_themes:
                    master_theme = str(theme_data.get("master_theme") or master_theme)
                    # Persist the newly generated themes
                    campaign_id = await _persist_theme_plan_to_campaign(
                        record=record, workspace=workspace,
                        master_theme=master_theme, derived_themes=derived_themes,
                        campaign_setup=campaign_setup, db=db,
                    )
                    persisted_workspace = _build_theme_plan_workspace(
                        workspace=workspace,
                        campaign_setup={**campaign_setup, "strategy_workshop": strategy_workshop,
                                        "master_theme": master_theme, "derived_themes": derived_themes},
                        campaign_id=campaign_id,
                        master_theme=master_theme,
                        derived_themes=derived_themes,
                    )
                    if db is not None:
                        await db.commit()
                    logger.info("Generated themes via targeted LLM call for table intent, %d themes", len(derived_themes))
            except Exception as exc:
                logger.warning("Targeted theme generation for table intent failed: %s", exc)

    # Only auto-generate when the workshop has enough field coverage
    ws_status = strategy_workshop.get("status", "discovery")
    if should_generate and master_theme and ws_status in ("draft_ready", "approval_ready", "approved"):
        try:
            auto_draft = await _build_auto_draft(
                record=record,
                workspace=persisted_workspace,
                master_theme=master_theme,
                campaign_id=campaign_id,
                artifact_types=artifact_types,
                db=db,
            )
            if db is not None:
                await db.commit()
            # Mark workshop as approved since content was generated
            persisted_workspace = {
                **persisted_workspace,
                "campaign_setup": {
                    **persisted_workspace.get("campaign_setup", {}),
                    "strategy_workshop": {
                        **persisted_workspace.get("campaign_setup", {}).get("strategy_workshop", {}),
                        "status": "approved",
                    },
                },
            }
            logger.info(
                "Auto-generated draft from chat intent for hired_instance_id=%s artifact_types=%s",
                hired_instance_id,
                [a.value for a in artifact_types],
            )
        except Exception as exc:
            logger.warning("Auto-draft generation failed: %s", exc)

    # Surface posting-time suggestions when workshop is near scheduling
    posting_suggestions: list[dict[str, str]] = []
    workshop_status = strategy_workshop.get("status", "discovery")
    summary = strategy_workshop.get("summary") or {}
    filled_count = sum(1 for v in summary.values() if v)
    if workshop_status == "approval_ready" or filled_count >= 9:
        industry = str(summary.get("industry") or workspace.get("industry") or "marketing")
        posting_suggestions = await get_posting_time_suggestions(industry)

    return ThemePlanResponse(
        campaign_id=campaign_id,
        master_theme=master_theme,
        derived_themes=derived_themes,
        workspace=persisted_workspace,
        auto_generated_draft=auto_draft,
        posting_time_suggestions=posting_suggestions,
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
    existing_campaign_setup = dict(workspace.get("campaign_setup") or {})
    campaign_setup = {
        **existing_campaign_setup,
        **dict(body.campaign_setup or {}),
    }
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