"""Hired agent instance APIs (Phase-1 simple implementation).

HIRE-3.3 + HIRE-3.4:
- Persist a customer-scoped hired agent instance tied to a subscription.
- Allow saving a draft configuration.
- Finalize config and start trial only when:
  1) subscription is active
  2) instance is configured
  3) goals step is completed

This is an in-memory implementation intended to unblock CP Hire wizard flows in lower envs.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, AsyncGenerator, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1 import payments_simple
from api.v1.agent_types_simple import SchemaFieldDefinition, get_agent_type_definition
from core.database import get_db_session
from models.hired_agent import HiredAgentModel
from models.agent import Agent
from models.job_role import JobRole
from models.skill import Skill
from repositories.hired_agent_repository import HiredAgentRepository
from repositories.hired_agent_repository import GoalInstanceRepository
from services.notification_events import NotificationEventRecord, get_notification_event_store


def _persistence_mode() -> str:
    # Feature flag: PERSISTENCE_MODE (default: "db"; memory is opt-in)
    # Options: "memory" (in-memory dicts), "db" (PostgreSQL via repositories)
    return os.getenv("PERSISTENCE_MODE", "db").strip().lower()


def _should_enforce_skill_chain() -> bool:
    """Return True only when SK-3.1 hire-time enforcement is explicitly enabled.

    Phase-1 product requirement: "no skills required" must be compatible with DB-backed
    persistence. Therefore, skill-chain enforcement is opt-in.
    """

    raw = (os.getenv("HIRE_ENFORCE_SKILL_CHAIN") or "").strip().lower()
    return raw in {"1", "true", "yes", "y", "on"}


async def _get_hired_agents_db_session() -> AsyncGenerator[AsyncSession | None, None]:
    """Return a DB session only when DB-backed mode is enabled.

    Important: Plant unit tests run without a Postgres service; keep Phase-1
    in-memory hired-agent flows DB-free unless PERSISTENCE_MODE=db.
    """

    if _persistence_mode() != "db":
        yield None
        return

    async for session in get_db_session():
        yield session


async def _validate_agent_job_role_skill_chain(*, agent_id: str, db: AsyncSession | None) -> None:
    """SK-3.1: Enforce Agent -> JobRole -> Skill chain is certified at hire time.

    DB-backed enforcement is enabled only when PERSISTENCE_MODE=db.
    """

    if not _should_enforce_skill_chain():
        return

    if db is None:
        return

    normalized_agent_id = (agent_id or "").strip()
    if not normalized_agent_id:
        raise HTTPException(status_code=422, detail="agent_id is required.")

    maybe_uuid: UUID | None = None
    try:
        maybe_uuid = UUID(normalized_agent_id)
    except Exception:
        maybe_uuid = None

    clauses = [Agent.external_id == normalized_agent_id]
    if maybe_uuid is not None:
        clauses.append(Agent.id == maybe_uuid)

    stmt_agent = select(Agent).where(or_(*clauses))
    agent_result = await db.execute(stmt_agent)
    agent = agent_result.scalars().first()
    if agent is None:
        raise HTTPException(status_code=422, detail="Agent is not eligible for hire (agent not found).")

    if getattr(agent, "status", None) in {"deleted", "archived"}:
        raise HTTPException(status_code=422, detail="Agent is not eligible for hire (inactive).")

    stmt_role = select(JobRole).where(JobRole.id == agent.job_role_id)
    role_result = await db.execute(stmt_role)
    role = role_result.scalars().first()
    if role is None:
        raise HTTPException(status_code=422, detail="Agent is not eligible for hire (job role not found).")

    if getattr(role, "status", None) in {"deleted", "archived"}:
        raise HTTPException(status_code=422, detail="Agent is not eligible for hire (job role inactive).")

    required_skill_ids = list(getattr(role, "required_skills", []) or [])
    if not required_skill_ids:
        raise HTTPException(status_code=422, detail="Agent is not eligible for hire (job role has no required skills).")

    stmt_skills = select(Skill).where(Skill.id.in_(required_skill_ids))
    skills_result = await db.execute(stmt_skills)
    skills = skills_result.scalars().all()

    by_id = {str(s.id): s for s in skills}
    missing = [str(skill_id) for skill_id in required_skill_ids if str(skill_id) not in by_id]
    uncertified = [
        str(s.id)
        for s in skills
        if getattr(s, "status", None) != "certified"
    ]

    if missing or uncertified:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Agent is not eligible for hire (required skills not certified).",
                "missing_skill_ids": missing,
                "uncertified_skill_ids": uncertified,
            },
        )


TrialStatus = Literal["not_started", "active", "ended_converted", "ended_not_converted"]


ALLOWED_THEMES: set[str] = {"default", "dark", "light"}
DEFAULT_TRIAL_DAYS = 7


SUPPORTED_TRADING_EXCHANGES: set[str] = {"delta_exchange_india"}


SUPPORTED_MARKETING_PLATFORMS: set[str] = {"youtube", "instagram", "facebook", "linkedin", "whatsapp", "x", "twitter"}


SUPPORTED_GOAL_FREQUENCIES: set[str] = {"daily", "weekly", "monthly", "on_demand"}


_SENSITIVE_KEY_EXACT: set[str] = {
    "api_key",
    "apikey",
    "api_secret",
    "client_secret",
    "access_token",
    "refresh_token",
    "password",
    "private_key",
    "secret_key",
}


def _find_raw_secret_path(value: Any, *, path: str = "config") -> str | None:
    """Return the first JSON path that appears to contain a raw secret.

    Phase-1 rule: Plant must never accept raw credentials. Only refs (e.g., credential_ref,
    exchange_credential_ref) may be stored.
    """

    if isinstance(value, dict):
        for k, v in value.items():
            key = str(k)
            key_lower = key.strip().lower()

            # Allowlist: refs/ids are allowed to be string-like.
            if key_lower.endswith("_ref") or key_lower.endswith("_id"):
                pass
            else:
                suspicious = (
                    key_lower in _SENSITIVE_KEY_EXACT
                    or key_lower.endswith("_token")
                    or key_lower.endswith("_secret")
                    or key_lower.endswith("_private_key")
                    or key_lower.endswith("_api_key")
                    or key_lower.endswith("_api_secret")
                )
                if suspicious and isinstance(v, str) and v.strip():
                    return f"{path}.{key}"

            nested = _find_raw_secret_path(v, path=f"{path}.{key}")
            if nested:
                return nested

    if isinstance(value, list):
        for i, item in enumerate(value):
            nested = _find_raw_secret_path(item, path=f"{path}[{i}]")
            if nested:
                return nested

    return None


def _assert_refs_only_config(config: dict[str, Any] | None) -> None:
    secret_path = _find_raw_secret_path(config or {})
    if secret_path:
        raise HTTPException(
            status_code=400,
            detail=f"Raw secrets are not allowed in Plant config (found at {secret_path}). Use credential refs only.",
        )


def _canonical_agent_type_id_or_400(agent_type_id: str | None) -> str:
    requested = str(agent_type_id or "").strip()
    if not requested:
        raise HTTPException(status_code=400, detail="agent_type_id is required.")

    definition = get_agent_type_definition(requested)
    if not definition:
        raise HTTPException(status_code=400, detail="Unknown agent_type_id.")

    canonical = str(definition.agent_type_id or "").strip()
    if not canonical:
        raise HTTPException(status_code=400, detail="Unknown agent_type_id.")

    return canonical


class HiredAgentDraftUpsertRequest(BaseModel):
    subscription_id: str = Field(..., min_length=1)
    agent_id: str = Field(..., min_length=1)
    agent_type_id: str = Field(..., min_length=1)
    customer_id: str = Field(..., min_length=1)

    nickname: str | None = None
    theme: str | None = None

    config: dict[str, Any] | None = None


class HiredAgentFinalizeRequest(BaseModel):
    customer_id: str = Field(..., min_length=1)
    agent_type_id: str = Field(..., min_length=1)
    goals_completed: bool = Field(False)


class GoalInstanceUpsertRequest(BaseModel):
    customer_id: str = Field(..., min_length=1)
    goal_instance_id: str | None = None
    goal_template_id: str = Field(..., min_length=1)
    frequency: str = Field(..., min_length=1)
    settings: dict[str, Any] = Field(default_factory=dict)


class GoalInstanceResponse(BaseModel):
    goal_instance_id: str
    hired_instance_id: str
    goal_template_id: str
    frequency: str
    settings: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class GoalsListResponse(BaseModel):
    hired_instance_id: str
    goals: list[GoalInstanceResponse] = Field(default_factory=list)


class HiredAgentInstanceResponse(BaseModel):
    hired_instance_id: str
    subscription_id: str
    agent_id: str
    agent_type_id: str
    customer_id: str | None = None

    nickname: str | None = None
    theme: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)

    configured: bool = False
    goals_completed: bool = False

    active: bool = True

    subscription_status: str | None = None
    subscription_ended_at: datetime | None = None
    retention_expires_at: datetime | None = None
    trial_status: TrialStatus = "not_started"
    trial_start_at: datetime | None = None
    trial_end_at: datetime | None = None

    created_at: datetime
    updated_at: datetime


class ProcessTrialEndRequest(BaseModel):
    now: datetime | None = None


class _HiredAgentRecord(BaseModel):
    hired_instance_id: str
    subscription_id: str
    agent_id: str
    agent_type_id: str
    customer_id: str | None
    nickname: str | None
    theme: str | None
    config: dict[str, Any]
    configured: bool
    goals_completed: bool
    active: bool
    trial_status: TrialStatus
    trial_start_at: datetime | None
    trial_end_at: datetime | None
    created_at: datetime
    updated_at: datetime


def _db_model_to_record(model: HiredAgentModel) -> _HiredAgentRecord:
    agent_type_id = (getattr(model, "agent_type_id", None) or "").strip()
    if not agent_type_id:
        # Rows created before agent_type_id existed cannot be served without inference.
        raise HTTPException(status_code=500, detail="hired agent record missing agent_type_id")

    return _HiredAgentRecord(
        hired_instance_id=model.hired_instance_id,
        subscription_id=model.subscription_id,
        agent_id=model.agent_id,
        agent_type_id=agent_type_id,
        customer_id=model.customer_id,
        nickname=model.nickname,
        theme=model.theme,
        config=dict(model.config or {}),
        configured=bool(model.configured),
        goals_completed=bool(model.goals_completed),
        active=bool(model.active),
        trial_status=model.trial_status,  # type: ignore[assignment]
        trial_start_at=model.trial_start_at,
        trial_end_at=model.trial_end_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


async def _get_record_by_id(*, hired_instance_id: str, db: AsyncSession | None) -> _HiredAgentRecord | None:
    if db is None:
        return _by_id.get(hired_instance_id)

    repo = HiredAgentRepository(db)
    model = await repo.get_by_id(hired_instance_id)
    if model is None:
        return None
    return _db_model_to_record(model)


_by_id: dict[str, _HiredAgentRecord] = {}
_by_subscription: dict[str, str] = {}


class _GoalRecord(BaseModel):
    goal_instance_id: str
    hired_instance_id: str
    goal_template_id: str
    frequency: str
    settings: dict[str, Any]
    created_at: datetime
    updated_at: datetime


_goals_by_hired_instance: dict[str, dict[str, _GoalRecord]] = {}


router = APIRouter(prefix="/hired-agents", tags=["hired-agents"])


def _normalize_theme(theme: str | None) -> str | None:
    if theme is None:
        return None
    normalized = (theme or "").strip().lower()
    if not normalized:
        return None
    if normalized not in ALLOWED_THEMES:
        raise HTTPException(status_code=400, detail="Unsupported theme.")
    return normalized


def _compute_configured(nickname: str | None, theme: str | None) -> bool:
    return bool((nickname or "").strip()) and bool((theme or "").strip())


def _is_trading_agent(agent_id: str | None) -> bool:
    return str(agent_id or "").strip().upper().startswith("AGT-TRD-")


def _is_marketing_agent(agent_id: str | None) -> bool:
    return str(agent_id or "").strip().upper().startswith("AGT-MKT-")


def _as_nonempty_str(value: Any) -> str | None:
    s = str(value or "").strip()
    return s or None


def _trading_config_complete(config: dict[str, Any] | None) -> bool:
    cfg = dict(config or {})

    timezone_val = _as_nonempty_str(cfg.get("timezone"))
    if not timezone_val:
        return False

    exchange_provider = _as_nonempty_str(cfg.get("exchange_provider"))
    if not exchange_provider or exchange_provider not in SUPPORTED_TRADING_EXCHANGES:
        return False

    credential_ref = _as_nonempty_str(cfg.get("exchange_credential_ref"))
    if not credential_ref:
        return False

    allowed_coins_raw = cfg.get("allowed_coins")
    allowed_coins: list[str] = []
    if isinstance(allowed_coins_raw, list):
        for c in allowed_coins_raw:
            coin = _as_nonempty_str(c)
            if coin:
                allowed_coins.append(coin.upper())
    if not allowed_coins:
        return False

    default_coin = _as_nonempty_str(cfg.get("default_coin"))
    if not default_coin:
        return False
    default_coin = default_coin.upper()
    if default_coin not in allowed_coins:
        return False

    interval_raw = cfg.get("interval_seconds")
    try:
        interval_seconds = int(interval_raw)
    except Exception:
        interval_seconds = 0
    if interval_seconds <= 0:
        return False

    risk_limits_raw = cfg.get("risk_limits")
    if not isinstance(risk_limits_raw, dict):
        return False
    max_units_raw = risk_limits_raw.get("max_units_per_order")
    try:
        max_units = int(max_units_raw)
    except Exception:
        max_units = 0
    if max_units <= 0:
        return False

    return True


def _marketing_config_complete(config: dict[str, Any] | None) -> bool:
    cfg = dict(config or {})

    primary_language = _as_nonempty_str(cfg.get("primary_language"))
    if not primary_language:
        return False

    timezone_val = _as_nonempty_str(cfg.get("timezone"))
    if not timezone_val:
        return False

    brand_name = _as_nonempty_str(cfg.get("brand_name"))
    if not brand_name:
        return False

    location = _as_nonempty_str(cfg.get("location"))
    if not location:
        return False

    offerings_raw = cfg.get("offerings_services")
    offerings: list[str] = []
    if isinstance(offerings_raw, list):
        for o in offerings_raw:
            v = _as_nonempty_str(o)
            if v:
                offerings.append(v)
    if not offerings:
        return False

    # Legacy shape (used by existing unit tests):
    # { platforms: [ { platform, credential_ref, posting_identity? }, ... ] }
    platforms_raw = cfg.get("platforms")
    if isinstance(platforms_raw, list) and platforms_raw:
        valid_count = 0
        for row in platforms_raw:
            if not isinstance(row, dict):
                continue
            platform = _as_nonempty_str(row.get("platform"))
            credential_ref = _as_nonempty_str(row.get("credential_ref"))
            if not platform or platform.lower() not in SUPPORTED_MARKETING_PLATFORMS:
                continue
            if not credential_ref:
                continue
            valid_count += 1
        return valid_count > 0

    # New schema-driven shape (AgentTypeDefinition):
    # { platforms_enabled: [...], platform_credentials: { instagram: "CRED-...", ... } }
    enabled_raw = cfg.get("platforms_enabled")
    enabled: list[str] = []
    if isinstance(enabled_raw, list):
        for p in enabled_raw:
            plat = _as_nonempty_str(p)
            if plat and plat.lower() in SUPPORTED_MARKETING_PLATFORMS:
                enabled.append(plat.lower())
    if not enabled:
        return False

    creds_raw = cfg.get("platform_credentials")
    if not isinstance(creds_raw, dict):
        return False

    for platform in enabled:
        val = creds_raw.get(platform) or creds_raw.get(platform.lower()) or creds_raw.get(platform.upper())
        if isinstance(val, str):
            if not _as_nonempty_str(val):
                return False
            continue
        if isinstance(val, dict):
            if not _as_nonempty_str(val.get("credential_ref")):
                return False
            continue
        return False

    return True


def _compute_agent_configured(
    nickname: str | None,
    theme: str | None,
    *,
    agent_id: str | None,
    config: dict[str, Any] | None,
) -> bool:
    base = bool((nickname or "").strip()) and bool((theme or "").strip())
    if not base:
        return False
    if _is_trading_agent(agent_id):
        return _trading_config_complete(config)
    if _is_marketing_agent(agent_id):
        return _marketing_config_complete(config)
    return True


def _retention_days_after_end() -> int:
    raw = (os.getenv("END_RETENTION_DAYS") or "30").strip()
    try:
        days = int(raw)
    except Exception:
        days = 30
    return max(days, 0)


def _assert_customer_owns_record(record: _HiredAgentRecord, customer_id: str) -> None:
    normalized_customer_id = (customer_id or "").strip()
    if not normalized_customer_id:
        raise HTTPException(status_code=400, detail="customer_id is required.")
    existing_customer_id = (record.customer_id or "").strip()
    if existing_customer_id and existing_customer_id != normalized_customer_id:
        # Use 404 to avoid leaking instance existence.
        raise HTTPException(status_code=404, detail="Hired agent instance not found.")


async def _subscription_status_and_ended_at(
    *,
    subscription_id: str,
    db: AsyncSession | None,
) -> tuple[str | None, datetime | None]:
    if db is not None and payments_simple._persistence_mode() == "db":
        return await payments_simple.get_subscription_status_and_ended_at_db(
            subscription_id=subscription_id,
            db=db,
        )

    return (
        payments_simple.get_subscription_status(subscription_id),
        payments_simple.get_subscription_ended_at(subscription_id),
    )


async def _assert_readable(
    record: _HiredAgentRecord,
    *,
    db: AsyncSession | None,
    as_of: datetime | None = None,
) -> None:
    subscription_status, ended_at = await _subscription_status_and_ended_at(
        subscription_id=record.subscription_id,
        db=db,
    )
    if subscription_status == "canceled":
        if ended_at is None:
            raise HTTPException(status_code=410, detail="Hired agent data is no longer available.")
        retention_days = _retention_days_after_end()
        if retention_days <= 0:
            raise HTTPException(status_code=410, detail="Hired agent data is no longer available.")
        effective_now = as_of or datetime.now(timezone.utc)
        if effective_now > ended_at + timedelta(days=retention_days):
            raise HTTPException(status_code=410, detail="Hired agent data is no longer available.")


async def _assert_writable(record: _HiredAgentRecord, *, db: AsyncSession | None) -> None:
    subscription_status, _ = await _subscription_status_and_ended_at(
        subscription_id=record.subscription_id,
        db=db,
    )
    if subscription_status is None:
        raise HTTPException(status_code=404, detail="Subscription not found.")
    if subscription_status != "active":
        raise HTTPException(status_code=409, detail="Subscription is not active; hired agent is read-only.")


def _goal_template_for_record(record: _HiredAgentRecord, goal_template_id: str) -> tuple[str, Any]:
    agent_type_id = _canonical_agent_type_id_or_400(record.agent_type_id)
    definition = get_agent_type_definition(agent_type_id)
    if not definition:
        raise HTTPException(status_code=400, detail="Agent type definition not found.")

    requested = str(goal_template_id or "").strip()
    for tmpl in definition.goal_templates:
        if tmpl.goal_template_id == requested:
            return agent_type_id, tmpl

    raise HTTPException(status_code=400, detail="Unknown goal_template_id for this agent type.")


def _missing_required_settings(fields: list[SchemaFieldDefinition], settings: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for field in fields:
        if not field.required:
            continue
        val = settings.get(field.key)
        if field.type in {"text", "enum"}:
            if not _as_nonempty_str(val):
                missing.append(field.key)
        elif field.type == "number":
            try:
                num = float(val)
            except Exception:
                num = float("nan")
            if not (num == num):
                missing.append(field.key)
        elif field.type == "boolean":
            if not isinstance(val, bool):
                missing.append(field.key)
        elif field.type == "list":
            if not isinstance(val, list) or len(val) == 0:
                missing.append(field.key)
        elif field.type == "object":
            if not isinstance(val, dict):
                missing.append(field.key)
        else:
            if val is None:
                missing.append(field.key)
    return missing


def _validate_goal_request(record: _HiredAgentRecord, body: GoalInstanceUpsertRequest) -> None:
    freq = str(body.frequency or "").strip().lower()
    if freq not in SUPPORTED_GOAL_FREQUENCIES:
        raise HTTPException(status_code=400, detail="Unsupported frequency.")

    if not isinstance(body.settings, dict):
        raise HTTPException(status_code=400, detail="settings must be an object.")

    _, tmpl = _goal_template_for_record(record, body.goal_template_id)
    missing = _missing_required_settings(list(tmpl.settings_schema.fields or []), body.settings)
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required settings: {', '.join(missing)}")


def _to_response(
    record: _HiredAgentRecord,
    *,
    subscription_status: str | None = None,
    ended_at: datetime | None = None,
) -> HiredAgentInstanceResponse:
    resolved_status = subscription_status
    resolved_ended_at = ended_at
    if resolved_status is None:
        resolved_status = payments_simple.get_subscription_status(record.subscription_id)
    if resolved_ended_at is None:
        resolved_ended_at = payments_simple.get_subscription_ended_at(record.subscription_id)

    retention_expires_at: datetime | None = None
    if resolved_status == "canceled" and resolved_ended_at is not None:
        retention_expires_at = resolved_ended_at + timedelta(days=_retention_days_after_end())

    return HiredAgentInstanceResponse(
        hired_instance_id=record.hired_instance_id,
        subscription_id=record.subscription_id,
        agent_id=record.agent_id,
        agent_type_id=_canonical_agent_type_id_or_400(record.agent_type_id),
        customer_id=record.customer_id,
        nickname=record.nickname,
        theme=record.theme,
        config=record.config,
        configured=record.configured,
        goals_completed=record.goals_completed,
        active=record.active,
        subscription_status=resolved_status,
        subscription_ended_at=resolved_ended_at,
        retention_expires_at=retention_expires_at,
        trial_status=record.trial_status,
        trial_start_at=record.trial_start_at,
        trial_end_at=record.trial_end_at,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.put("/draft", response_model=HiredAgentInstanceResponse)
async def upsert_draft(
    body: HiredAgentDraftUpsertRequest,
    db: AsyncSession | None = Depends(_get_hired_agents_db_session),
) -> HiredAgentInstanceResponse:
    now = datetime.now(timezone.utc)
    theme = _normalize_theme(body.theme)

    canonical_agent_type_id = _canonical_agent_type_id_or_400(body.agent_type_id)

    customer_id = (body.customer_id or "").strip()
    if not customer_id:
        raise HTTPException(status_code=400, detail="customer_id is required.")

    subscription_status, subscription_ended_at = await _subscription_status_and_ended_at(
        subscription_id=body.subscription_id,
        db=db,
    )
    if subscription_status is None:
        raise HTTPException(status_code=404, detail="Subscription not found.")
    if subscription_status != "active":
        raise HTTPException(status_code=409, detail="Subscription is not active; hired agent is read-only.")

    if db is not None:
        repo = HiredAgentRepository(db)
        existing = await repo.get_by_subscription_id(body.subscription_id)

        if existing is not None:
            if _canonical_agent_type_id_or_400(getattr(existing, "agent_type_id", None)) != canonical_agent_type_id:
                raise HTTPException(status_code=400, detail="agent_type_id mismatch for existing hired instance.")

            # SK-3.1: fail-closed only when explicitly enabled.
            await _validate_agent_job_role_skill_chain(agent_id=(body.agent_id or existing.agent_id), db=db)

            existing_customer_id = (getattr(existing, "customer_id", None) or "").strip()
            if existing_customer_id and existing_customer_id != customer_id:
                raise HTTPException(status_code=403, detail="Hired agent instance does not belong to customer.")

            updated_config = dict(getattr(existing, "config", {}) or {})
            if body.config is not None:
                updated_config = dict(body.config)
            _assert_refs_only_config(updated_config)

            nickname = body.nickname if body.nickname is not None else getattr(existing, "nickname", None)
            theme_value = theme if theme is not None else getattr(existing, "theme", None)
            configured = _compute_agent_configured(
                nickname,
                theme_value,
                agent_id=(body.agent_id or existing.agent_id),
                config=updated_config,
            )

            persisted = await repo.draft_upsert(
                subscription_id=body.subscription_id,
                agent_id=str(body.agent_id or existing.agent_id),
                agent_type_id=canonical_agent_type_id,
                customer_id=customer_id,
                nickname=nickname,
                theme=theme_value,
                config=updated_config,
                configured=configured,
            )
            await db.commit()
            record = _db_model_to_record(persisted)
            return _to_response(record, subscription_status=subscription_status, ended_at=subscription_ended_at)

        _assert_refs_only_config(body.config)
        await _validate_agent_job_role_skill_chain(agent_id=body.agent_id, db=db)

        configured = _compute_agent_configured(body.nickname, theme, agent_id=body.agent_id, config=(body.config or {}))
        persisted = await repo.draft_upsert(
            subscription_id=body.subscription_id,
            agent_id=str(body.agent_id),
            agent_type_id=canonical_agent_type_id,
            customer_id=customer_id,
            nickname=(body.nickname or None),
            theme=theme,
            config=dict(body.config or {}),
            configured=configured,
        )
        await db.commit()
        record = _db_model_to_record(persisted)
        return _to_response(record, subscription_status=subscription_status, ended_at=subscription_ended_at)

    existing_id = _by_subscription.get(body.subscription_id)
    if existing_id and existing_id in _by_id:
        record = _by_id[existing_id]

        if _canonical_agent_type_id_or_400(record.agent_type_id) != canonical_agent_type_id:
            raise HTTPException(status_code=400, detail="agent_type_id mismatch for existing hired instance.")

        # SK-3.1: fail-closed only when explicitly enabled.
        await _validate_agent_job_role_skill_chain(agent_id=(body.agent_id or record.agent_id), db=db)

        existing_customer_id = (record.customer_id or "").strip()
        if existing_customer_id and existing_customer_id != customer_id:
            raise HTTPException(status_code=403, detail="Hired agent instance does not belong to customer.")
        updated_config = dict(record.config)
        if body.config is not None:
            updated_config = dict(body.config)

        _assert_refs_only_config(updated_config)

        nickname = body.nickname if body.nickname is not None else record.nickname
        theme_value = theme if theme is not None else record.theme
        configured = _compute_agent_configured(
            nickname,
            theme_value,
            agent_id=(body.agent_id or record.agent_id),
            config=updated_config,
        )

        record = record.model_copy(
            update={
                "agent_id": body.agent_id or record.agent_id,
                "agent_type_id": canonical_agent_type_id,
                "customer_id": customer_id,
                "nickname": nickname,
                "theme": theme_value,
                "config": updated_config,
                "configured": configured,
                "active": True,
                "updated_at": now,
            }
        )
        _by_id[existing_id] = record
        return _to_response(record, subscription_status=subscription_status, ended_at=subscription_ended_at)

    hired_instance_id = f"HAI-{uuid4()}"
    _assert_refs_only_config(body.config)
    await _validate_agent_job_role_skill_chain(agent_id=body.agent_id, db=db)
    record = _HiredAgentRecord(
        hired_instance_id=hired_instance_id,
        subscription_id=body.subscription_id,
        agent_id=body.agent_id,
        agent_type_id=canonical_agent_type_id,
        customer_id=customer_id,
        nickname=(body.nickname or None),
        theme=theme,
        config=dict(body.config or {}),
        configured=_compute_agent_configured(body.nickname, theme, agent_id=body.agent_id, config=(body.config or {})),
        goals_completed=False,
        active=True,
        trial_status="not_started",
        trial_start_at=None,
        trial_end_at=None,
        created_at=now,
        updated_at=now,
    )

    _by_id[hired_instance_id] = record
    _by_subscription[body.subscription_id] = hired_instance_id
    return _to_response(record, subscription_status=subscription_status, ended_at=subscription_ended_at)


@router.get("/by-subscription/{subscription_id}", response_model=HiredAgentInstanceResponse)
async def get_by_subscription(
    subscription_id: str,
    as_of: datetime | None = None,
    customer_id: str | None = None,
    db: AsyncSession | None = Depends(_get_hired_agents_db_session),
) -> HiredAgentInstanceResponse:
    if db is not None:
        repo = HiredAgentRepository(db)
        model = await repo.get_by_subscription_id(subscription_id)
        if model is None:
            raise HTTPException(status_code=404, detail="Hired agent instance not found.")
        record = _db_model_to_record(model)
    else:
        hired_instance_id = _by_subscription.get(subscription_id)
        if not hired_instance_id:
            raise HTTPException(status_code=404, detail="Hired agent instance not found.")
        record = _by_id.get(hired_instance_id)
        if not record:
            raise HTTPException(status_code=404, detail="Hired agent instance not found.")

    normalized_customer_id = (customer_id or "").strip()
    if not normalized_customer_id:
        raise HTTPException(status_code=400, detail="customer_id is required.")
    existing_customer_id = (record.customer_id or "").strip()
    if existing_customer_id and existing_customer_id != normalized_customer_id:
        # Use 404 to avoid leaking subscription existence.
        raise HTTPException(status_code=404, detail="Hired agent instance not found.")

    subscription_status, ended_at = await _subscription_status_and_ended_at(
        subscription_id=record.subscription_id,
        db=db,
    )
    if subscription_status == "canceled":
        if ended_at is None:
            raise HTTPException(status_code=410, detail="Hired agent data is no longer available.")
        retention_days = _retention_days_after_end()
        if retention_days <= 0:
            raise HTTPException(status_code=410, detail="Hired agent data is no longer available.")
        effective_now = as_of or datetime.now(timezone.utc)
        if effective_now > ended_at + timedelta(days=retention_days):
            raise HTTPException(status_code=410, detail="Hired agent data is no longer available.")

    return _to_response(record, subscription_status=subscription_status, ended_at=ended_at)


@router.get("/{hired_instance_id}/goals", response_model=GoalsListResponse)
async def list_goals(
    hired_instance_id: str,
    customer_id: str | None = None,
    as_of: datetime | None = None,
    db: AsyncSession | None = Depends(_get_hired_agents_db_session),
) -> GoalsListResponse:
    record = await _get_record_by_id(hired_instance_id=hired_instance_id, db=db)
    if not record:
        raise HTTPException(status_code=404, detail="Hired agent instance not found.")

    _assert_customer_owns_record(record, str(customer_id or ""))
    await _assert_readable(record, db=db, as_of=as_of)

    if db is not None:
        repo = GoalInstanceRepository(db)
        models = await repo.list_by_hired_instance(hired_instance_id)
        goals = [
            GoalInstanceResponse(
                goal_instance_id=m.goal_instance_id,
                hired_instance_id=m.hired_instance_id,
                goal_template_id=m.goal_template_id,
                frequency=m.frequency,
                settings=dict(m.settings or {}),
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in models
        ]
    else:
        goals_map = _goals_by_hired_instance.get(hired_instance_id) or {}
        goals = [
            GoalInstanceResponse(
                goal_instance_id=g.goal_instance_id,
                hired_instance_id=g.hired_instance_id,
                goal_template_id=g.goal_template_id,
                frequency=g.frequency,
                settings=g.settings,
                created_at=g.created_at,
                updated_at=g.updated_at,
            )
            for g in goals_map.values()
        ]
    goals.sort(key=lambda g: (g.created_at, g.goal_instance_id))
    return GoalsListResponse(hired_instance_id=hired_instance_id, goals=goals)


@router.put("/{hired_instance_id}/goals", response_model=GoalInstanceResponse)
async def upsert_goal(
    hired_instance_id: str,
    body: GoalInstanceUpsertRequest,
    db: AsyncSession | None = Depends(_get_hired_agents_db_session),
) -> GoalInstanceResponse:
    record = await _get_record_by_id(hired_instance_id=hired_instance_id, db=db)
    if not record:
        raise HTTPException(status_code=404, detail="Hired agent instance not found.")
    _assert_customer_owns_record(record, body.customer_id)
    await _assert_writable(record, db=db)
    _validate_goal_request(record, body)

    if db is not None:
        repo = GoalInstanceRepository(db)
        model = await repo.upsert_goal(
            hired_instance_id=hired_instance_id,
            goal_template_id=str(body.goal_template_id).strip(),
            frequency=str(body.frequency).strip().lower(),
            settings=dict(body.settings or {}),
            goal_instance_id=_as_nonempty_str(body.goal_instance_id),
        )
        await db.commit()
        return GoalInstanceResponse(
            goal_instance_id=model.goal_instance_id,
            hired_instance_id=model.hired_instance_id,
            goal_template_id=model.goal_template_id,
            frequency=model.frequency,
            settings=dict(model.settings or {}),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    now = datetime.now(timezone.utc)
    goals_map = _goals_by_hired_instance.setdefault(hired_instance_id, {})
    goal_instance_id = _as_nonempty_str(body.goal_instance_id) or f"GOI-{uuid4()}"
    existing = goals_map.get(goal_instance_id)
    created_at = existing.created_at if existing else now
    goal_record = _GoalRecord(
        goal_instance_id=goal_instance_id,
        hired_instance_id=hired_instance_id,
        goal_template_id=str(body.goal_template_id).strip(),
        frequency=str(body.frequency).strip().lower(),
        settings=dict(body.settings or {}),
        created_at=created_at,
        updated_at=now,
    )
    goals_map[goal_instance_id] = goal_record
    return GoalInstanceResponse(
        goal_instance_id=goal_record.goal_instance_id,
        hired_instance_id=goal_record.hired_instance_id,
        goal_template_id=goal_record.goal_template_id,
        frequency=goal_record.frequency,
        settings=goal_record.settings,
        created_at=goal_record.created_at,
        updated_at=goal_record.updated_at,
    )


@router.delete("/{hired_instance_id}/goals")
async def delete_goal(
    hired_instance_id: str,
    goal_instance_id: str | None = None,
    customer_id: str | None = None,
    db: AsyncSession | None = Depends(_get_hired_agents_db_session),
) -> dict[str, Any]:
    record = await _get_record_by_id(hired_instance_id=hired_instance_id, db=db)
    if not record:
        raise HTTPException(status_code=404, detail="Hired agent instance not found.")
    normalized_customer_id = (customer_id or "").strip()
    if not normalized_customer_id:
        raise HTTPException(status_code=400, detail="customer_id is required.")
    _assert_customer_owns_record(record, normalized_customer_id)
    await _assert_writable(record, db=db)
    goal_id = (goal_instance_id or "").strip()
    if not goal_id:
        raise HTTPException(status_code=400, detail="goal_instance_id is required.")

    if db is not None:
        repo = GoalInstanceRepository(db)
        deleted = await repo.delete_goal(goal_id)
        await db.commit()
        return {"deleted": bool(deleted), "goal_instance_id": goal_id}

    goals_map = _goals_by_hired_instance.get(hired_instance_id) or {}
    if goal_id in goals_map:
        goals_map.pop(goal_id, None)
        _goals_by_hired_instance[hired_instance_id] = goals_map
        return {"deleted": True, "goal_instance_id": goal_id}
    return {"deleted": False, "goal_instance_id": goal_id}


@router.post("/{hired_instance_id}/finalize", response_model=HiredAgentInstanceResponse)
async def finalize(
    hired_instance_id: str,
    body: HiredAgentFinalizeRequest,
    db: AsyncSession | None = Depends(_get_hired_agents_db_session),
) -> HiredAgentInstanceResponse:
    record = await _get_record_by_id(hired_instance_id=hired_instance_id, db=db)
    if not record:
        raise HTTPException(status_code=404, detail="Hired agent instance not found.")

    customer_id = (body.customer_id or "").strip()
    if not customer_id:
        raise HTTPException(status_code=400, detail="customer_id is required.")
    existing_customer_id = (record.customer_id or "").strip()
    if existing_customer_id and existing_customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Hired agent instance not found.")

    now = datetime.now(timezone.utc)

    canonical_agent_type_id = _canonical_agent_type_id_or_400(body.agent_type_id)
    if _canonical_agent_type_id_or_400(record.agent_type_id) != canonical_agent_type_id:
        raise HTTPException(status_code=400, detail="agent_type_id mismatch for hired instance.")

    # SK-3.1: Enforce certified skill-chain at finalize time (opt-in).
    await _validate_agent_job_role_skill_chain(agent_id=record.agent_id, db=db)

    _assert_refs_only_config(record.config)
    configured = _compute_agent_configured(record.nickname, record.theme, agent_id=record.agent_id, config=record.config)

    trial_status: TrialStatus = record.trial_status
    trial_start_at = record.trial_start_at
    trial_end_at = record.trial_end_at

    subscription_status, subscription_ended_at = await _subscription_status_and_ended_at(
        subscription_id=record.subscription_id,
        db=db,
    )
    if subscription_status is None:
        raise HTTPException(status_code=404, detail="Subscription not found.")
    if subscription_status != "active":
        raise HTTPException(status_code=409, detail="Subscription is not active; hired agent is read-only.")
    should_start_trial = (
        subscription_status == "active" and configured and bool(body.goals_completed)
    )

    if should_start_trial and trial_status != "active":
        trial_status = "active"
        trial_start_at = now
        trial_end_at = now + timedelta(days=DEFAULT_TRIAL_DAYS)

        # NOTIF-1.1: emit trial activated (best-effort).
        try:
            get_notification_event_store().append(
                NotificationEventRecord(
                    event_type="trial_activated",
                    customer_id=(record.customer_id or None),
                    subscription_id=record.subscription_id,
                    hired_instance_id=record.hired_instance_id,
                    metadata={
                        "trial_start_at": trial_start_at.isoformat() if trial_start_at else None,
                        "trial_end_at": trial_end_at.isoformat() if trial_end_at else None,
                    },
                )
            )
        except Exception:
            pass

    updated = record.model_copy(
        update={
            "configured": configured,
            "goals_completed": bool(body.goals_completed),
            "active": record.active,
            "agent_type_id": canonical_agent_type_id,
            "trial_status": trial_status,
            "trial_start_at": trial_start_at,
            "trial_end_at": trial_end_at,
            "updated_at": now,
        }
    )
    if db is not None:
        repo = HiredAgentRepository(db)
        try:
            persisted = await repo.finalize(
                hired_instance_id=hired_instance_id,
                agent_type_id=canonical_agent_type_id,
                goals_completed=bool(body.goals_completed),
                configured=configured,
                trial_status=trial_status,
                trial_start=trial_start_at,
                trial_end=trial_end_at,
            )
        except ValueError:
            raise HTTPException(status_code=404, detail="Hired agent instance not found.")

        await db.commit()
        persisted_record = _db_model_to_record(persisted)
        return _to_response(
            persisted_record,
            subscription_status=subscription_status,
            ended_at=subscription_ended_at,
        )

    _by_id[hired_instance_id] = updated
    return _to_response(updated, subscription_status=subscription_status, ended_at=subscription_ended_at)


def _process_trial_end(now: datetime) -> int:
    processed = 0
    for hired_instance_id, record in list(_by_id.items()):
        if record.trial_status != "active":
            continue
        if record.trial_end_at is None:
            continue
        if record.trial_end_at > now:
            continue

        subscription_status = payments_simple.get_subscription_status(record.subscription_id)
        next_status: TrialStatus = "ended_not_converted"
        if subscription_status == "active":
            # Product decision: trial auto-converts to paid when it ends.
            next_status = "ended_converted"

        _by_id[hired_instance_id] = record.model_copy(
            update={
                "trial_status": next_status,
                "updated_at": now,
            }
        )

        # NOTIF-1.1: emit trial ended (best-effort).
        try:
            get_notification_event_store().append(
                NotificationEventRecord(
                    event_type="trial_ended",
                    customer_id=(record.customer_id or None),
                    subscription_id=record.subscription_id,
                    hired_instance_id=record.hired_instance_id,
                    metadata={
                        "next_status": next_status,
                        "processed_at": now.isoformat(),
                    },
                )
            )
        except Exception:
            pass
        processed += 1
    return processed


@router.post("/process-trial-end")
async def process_trial_end(body: ProcessTrialEndRequest) -> dict:
    now = body.now or datetime.now(timezone.utc)
    processed = _process_trial_end(now)
    return {"processed": processed, "now": now}


def deactivate_by_subscription(*, subscription_id: str, now: datetime | None = None) -> str | None:
    """Deactivate the hired agent instance tied to a subscription.

    Phase-1 helper called by payments period-end processing.
    """

    hired_instance_id = _by_subscription.get(subscription_id)
    if not hired_instance_id:
        return None
    record = _by_id.get(hired_instance_id)
    if not record:
        return None
    ts = now or datetime.now(timezone.utc)
    updated = record.model_copy(update={"active": False, "updated_at": ts})
    _by_id[hired_instance_id] = updated
    return hired_instance_id
