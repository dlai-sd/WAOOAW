from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from uuid import uuid4

from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.hired_agents_simple import (
    DEFAULT_TRIAL_DAYS,
    _HiredAgentRecord,
    _by_id,
    _assert_customer_owns_record,
    _assert_readable,
    _assert_refs_only_config,
    _assert_writable,
    _compute_agent_configured,
    _db_model_to_record,
    _fire_lifecycle_hire_hooks,
    _get_hired_agents_db_session,
    _get_record_by_id,
    _get_read_hired_agents_db_session,
    _is_marketing_agent,
    _is_trading_agent,
    _normalize_theme,
    _subscription_status_and_ended_at,
)
from core.routing import waooaw_router
from models.platform_connection import PlatformConnectionModel
from models.skill_config import SkillConfigModel
from repositories.hired_agent_repository import HiredAgentRepository

router = waooaw_router(prefix="/hired-agents", tags=["hired-agent-studio"])

StudioMode = Literal["activation", "edit"]
StudioStepKey = Literal["identity", "connection", "operating_plan", "review"]


class StudioStepResponse(BaseModel):
    key: StudioStepKey
    title: str
    complete: bool
    blocked: bool = False
    summary: str


class IdentityState(BaseModel):
    nickname: str | None = None
    theme: str | None = None
    complete: bool


class ConnectionState(BaseModel):
    platform_key: str | None = None
    skill_id: str | None = None
    connection_id: str | None = None
    customer_platform_credential_id: str | None = None
    status: str
    complete: bool
    summary: str


class OperatingPlanState(BaseModel):
    complete: bool
    goals_completed: bool
    goal_count: int
    skill_config_count: int
    summary: str


class ReviewState(BaseModel):
    complete: bool
    summary: str


class HiredAgentStudioResponse(BaseModel):
    hired_instance_id: str
    subscription_id: str
    agent_id: str
    agent_type_id: str
    customer_id: str | None = None
    mode: StudioMode
    selection_required: bool = False
    current_step: StudioStepKey
    steps: list[StudioStepResponse] = Field(default_factory=list)
    identity: IdentityState
    connection: ConnectionState
    operating_plan: OperatingPlanState
    review: ReviewState
    configured: bool
    goals_completed: bool
    trial_status: str
    subscription_status: str | None = None
    updated_at: datetime


class StudioIdentityUpdate(BaseModel):
    nickname: str | None = None
    theme: str | None = None


class StudioConnectionUpdate(BaseModel):
    platform_key: str = "youtube"
    skill_id: str = "default"
    customer_platform_credential_id: str | None = None
    secret_ref: str | None = None
    mark_connected: bool = False


class StudioOperatingPlanUpdate(BaseModel):
    config_patch: dict[str, Any] | None = None
    skill_id: str | None = None
    customer_fields: dict[str, Any] | None = None
    goals_completed: bool | None = None


class StudioReviewUpdate(BaseModel):
    goals_completed: bool | None = None
    finalize: bool = False


class StudioUpdateRequest(BaseModel):
    identity: StudioIdentityUpdate | None = None
    connection: StudioConnectionUpdate | None = None
    operating_plan: StudioOperatingPlanUpdate | None = None
    review: StudioReviewUpdate | None = None


def _merge_dict(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_dict(dict(merged[key]), value)
        else:
            merged[key] = value
    return merged


def _first_nonempty_platform(config: dict[str, Any]) -> str | None:
    enabled = config.get("platforms_enabled")
    if isinstance(enabled, list):
        for item in enabled:
            candidate = str(item or "").strip().lower()
            if candidate:
                return candidate

    legacy_rows = config.get("platforms")
    if isinstance(legacy_rows, list):
        for row in legacy_rows:
            if not isinstance(row, dict):
                continue
            candidate = str(row.get("platform") or "").strip().lower()
            if candidate:
                return candidate

    return None


def _apply_connection_config(record: _HiredAgentRecord, config: dict[str, Any], update: StudioConnectionUpdate) -> dict[str, Any]:
    platform_key = str(update.platform_key or "youtube").strip().lower() or "youtube"
    skill_id = str(update.skill_id or "default").strip() or "default"
    credential_ref = update.customer_platform_credential_id or update.secret_ref

    next_config = dict(config)
    if _is_marketing_agent(record.agent_id):
        enabled = [str(item).strip().lower() for item in list(next_config.get("platforms_enabled") or []) if str(item).strip()]
        if platform_key not in enabled:
            enabled.append(platform_key)
        next_config["platforms_enabled"] = enabled

        platform_credentials = dict(next_config.get("platform_credentials") or {})
        if credential_ref:
            platform_credentials[platform_key] = credential_ref
        next_config["platform_credentials"] = platform_credentials

        legacy_platforms: list[dict[str, Any]] = []
        for row in list(next_config.get("platforms") or []):
            if isinstance(row, dict):
                legacy_platforms.append(dict(row))

        updated = False
        for row in legacy_platforms:
            if str(row.get("platform") or "").strip().lower() == platform_key:
                row["platform"] = platform_key
                row["posting_identity"] = row.get("posting_identity") or "default"
                if credential_ref:
                    row["credential_ref"] = credential_ref
                updated = True
                break
        if not updated:
            legacy_platforms.append(
                {
                    "platform": platform_key,
                    "credential_ref": credential_ref,
                    "posting_identity": "default",
                    "skill_id": skill_id,
                }
            )
        next_config["platforms"] = legacy_platforms
    elif _is_trading_agent(record.agent_id):
        if credential_ref:
            next_config["exchange_credential_ref"] = credential_ref

    return next_config


async def _connection_state(record: _HiredAgentRecord, db: AsyncSession | None) -> ConnectionState:
    config = dict(record.config or {})
    platform_key = _first_nonempty_platform(config)
    connection: PlatformConnectionModel | None = None
    if db is not None:
        result = await db.execute(
            select(PlatformConnectionModel)
            .where(PlatformConnectionModel.hired_instance_id == record.hired_instance_id)
            .order_by(PlatformConnectionModel.updated_at.desc())
        )
        connection = result.scalars().first()

    if connection is not None:
        is_complete = str(connection.status or "").strip().lower() == "connected"
        status = str(connection.status or "pending").strip().lower() or "pending"
        label = "Connection verified and ready." if is_complete else "Connection exists but still needs verification."
        return ConnectionState(
            platform_key=str(connection.platform_key or platform_key or "").strip() or None,
            skill_id=str(connection.skill_id or "").strip() or None,
            connection_id=connection.id,
            customer_platform_credential_id=str(connection.customer_platform_credential_id or "").strip() or None,
            status=status,
            complete=is_complete,
            summary=label,
        )

    if _is_marketing_agent(record.agent_id):
        credentials = dict(config.get("platform_credentials") or {})
        if platform_key and credentials.get(platform_key):
            is_active = record.trial_status == "active"
            return ConnectionState(
                platform_key=platform_key,
                skill_id="default",
                connection_id=None,
                customer_platform_credential_id=str(credentials.get(platform_key) or "").strip() or None,
                status="connected" if is_active else "reference_saved",
                complete=is_active,
                summary=(
                    "A platform credential is already linked for this active hire."
                    if is_active
                    else "A platform reference is saved, but the connection is not verified yet."
                ),
            )
        return ConnectionState(
            platform_key=platform_key or "youtube",
            skill_id="default",
            connection_id=None,
            customer_platform_credential_id=None,
            status="missing",
            complete=False,
            summary="No verified publishing connection is attached yet.",
        )

    if _is_trading_agent(record.agent_id):
        credential_ref = str(config.get("exchange_credential_ref") or "").strip()
        return ConnectionState(
            platform_key="delta_exchange_india",
            skill_id="default",
            connection_id=None,
            customer_platform_credential_id=credential_ref or None,
            status="connected" if credential_ref else "missing",
            complete=bool(credential_ref),
            summary=(
                "Exchange credential reference is configured."
                if credential_ref
                else "Exchange credential reference is still missing."
            ),
        )

    return ConnectionState(
        platform_key=None,
        skill_id=None,
        connection_id=None,
        customer_platform_credential_id=None,
        status="connected" if record.configured else "missing",
        complete=bool(record.configured),
        summary="This agent type does not require an external connection." if record.configured else "Connection setup is still incomplete.",
    )


async def _operating_plan_state(record: _HiredAgentRecord, db: AsyncSession | None) -> OperatingPlanState:
    if db is None:
        goal_count = 0
        skill_config_count = 0
    else:
        goals_result = await db.execute(
            select(SkillConfigModel.hired_instance_id).where(SkillConfigModel.hired_instance_id == record.hired_instance_id)
        )
        skill_config_count = len(goals_result.all())

        goals_table_result = await db.execute(
            select(PlatformConnectionModel.hired_instance_id).where(PlatformConnectionModel.hired_instance_id == record.hired_instance_id)
        )
        goal_count = 0 if goals_table_result is None else 0
        # Goal count is intentionally derived from the durable hired-agent flag first.

    complete = bool(record.goals_completed) or skill_config_count > 0
    summary = (
        "Operating plan is in place."
        if complete
        else "Operating plan still needs customer input before review."
    )
    return OperatingPlanState(
        complete=complete,
        goals_completed=bool(record.goals_completed),
        goal_count=goal_count,
        skill_config_count=skill_config_count,
        summary=summary,
    )


def _build_steps(
    *,
    identity_complete: bool,
    connection_state: ConnectionState,
    operating_plan: OperatingPlanState,
    review_complete: bool,
    mode: StudioMode,
) -> list[StudioStepResponse]:
    return [
        StudioStepResponse(
            key="identity",
            title="Identity and voice",
            complete=identity_complete,
            summary=(
                "Business-facing name and theme are ready."
                if identity_complete
                else "Choose a name and theme before continuing."
            ),
        ),
        StudioStepResponse(
            key="connection",
            title="Connection",
            complete=connection_state.complete,
            blocked=not identity_complete,
            summary=connection_state.summary,
        ),
        StudioStepResponse(
            key="operating_plan",
            title="Operating plan",
            complete=operating_plan.complete,
            blocked=not identity_complete,
            summary=operating_plan.summary,
        ),
        StudioStepResponse(
            key="review",
            title="Review and activate" if mode == "activation" else "Review edits",
            complete=review_complete,
            blocked=not (identity_complete and connection_state.complete and operating_plan.complete),
            summary=(
                "Everything required for activation is complete."
                if review_complete and mode == "activation"
                else "Use review to confirm the updated operating setup."
                if review_complete
                else "Finish the earlier steps before final review."
            ),
        ),
    ]


def _current_step(steps: list[StudioStepResponse]) -> StudioStepKey:
    for step in steps:
        if not step.complete and not step.blocked:
            return step.key
    return "review"


async def _build_studio_response(record: _HiredAgentRecord, db: AsyncSession | None) -> HiredAgentStudioResponse:
    subscription_status, _ = await _subscription_status_and_ended_at(
        subscription_id=record.subscription_id,
        db=db,
    )
    identity_complete = bool(str(record.nickname or "").strip()) and bool(str(record.theme or "").strip())
    connection_state = await _connection_state(record, db)
    operating_plan = await _operating_plan_state(record, db)
    mode: StudioMode = "edit" if record.trial_status != "not_started" else "activation"
    review_complete = identity_complete and connection_state.complete and operating_plan.complete
    review = ReviewState(
        complete=review_complete,
        summary=(
            "Ready to start the trial."
            if mode == "activation" and review_complete
            else "Ready to save the updated configuration."
            if review_complete
            else "This agent still has incomplete steps before review."
        ),
    )
    steps = _build_steps(
        identity_complete=identity_complete,
        connection_state=connection_state,
        operating_plan=operating_plan,
        review_complete=review_complete,
        mode=mode,
    )
    return HiredAgentStudioResponse(
        hired_instance_id=record.hired_instance_id,
        subscription_id=record.subscription_id,
        agent_id=record.agent_id,
        agent_type_id=record.agent_type_id,
        customer_id=record.customer_id,
        mode=mode,
        selection_required=False,
        current_step=_current_step(steps),
        steps=steps,
        identity=IdentityState(
            nickname=record.nickname,
            theme=record.theme,
            complete=identity_complete,
        ),
        connection=connection_state,
        operating_plan=operating_plan,
        review=review,
        configured=bool(record.configured),
        goals_completed=bool(record.goals_completed),
        trial_status=record.trial_status,
        subscription_status=subscription_status,
        updated_at=record.updated_at,
    )


async def _load_owned_record(
    *,
    hired_instance_id: str,
    customer_id: str,
    db: AsyncSession | None,
) -> _HiredAgentRecord:
    record = await _get_record_by_id(hired_instance_id=hired_instance_id, db=db)
    if not record:
        raise HTTPException(status_code=404, detail="Hired agent instance not found.")
    _assert_customer_owns_record(record, customer_id)
    await _assert_readable(record, db=db)
    return record


async def _upsert_platform_connection(
    *,
    db: AsyncSession,
    hired_instance_id: str,
    body: StudioConnectionUpdate,
) -> None:
    result = await db.execute(
        select(PlatformConnectionModel)
        .where(PlatformConnectionModel.hired_instance_id == hired_instance_id)
        .where(PlatformConnectionModel.skill_id == body.skill_id)
        .where(PlatformConnectionModel.platform_key == body.platform_key)
    )
    existing = result.scalars().first()
    now = datetime.now(timezone.utc)
    if existing is None:
        existing = PlatformConnectionModel(
            id=str(uuid4()),
            hired_instance_id=hired_instance_id,
            skill_id=body.skill_id,
            customer_platform_credential_id=body.customer_platform_credential_id,
            platform_key=body.platform_key,
            secret_ref=body.secret_ref,
            status="connected" if body.mark_connected else "pending",
            connected_at=now if body.mark_connected else None,
            last_verified_at=now if body.mark_connected else None,
            created_at=now,
            updated_at=now,
        )
        db.add(existing)
        await db.flush()
        return

    existing.customer_platform_credential_id = body.customer_platform_credential_id
    if body.secret_ref is not None:
        existing.secret_ref = body.secret_ref
    existing.updated_at = now
    if body.mark_connected:
        existing.status = "connected"
        existing.connected_at = existing.connected_at or now
        existing.last_verified_at = now
    await db.flush()


async def _upsert_skill_config(
    *,
    db: AsyncSession,
    record: _HiredAgentRecord,
    skill_id: str,
    customer_fields: dict[str, Any],
) -> None:
    result = await db.execute(
        select(SkillConfigModel)
        .where(SkillConfigModel.hired_instance_id == record.hired_instance_id)
        .where(SkillConfigModel.skill_id == skill_id)
    )
    existing = result.scalars().first()
    now = datetime.now(timezone.utc)
    if existing is None:
        db.add(
            SkillConfigModel(
                id=str(uuid4()),
                hired_instance_id=record.hired_instance_id,
                skill_id=skill_id,
                definition_version_id=record.internal_definition_version_id or "studio",
                pp_locked_fields={},
                customer_fields=customer_fields,
                created_at=now,
                updated_at=now,
            )
        )
        await db.flush()
        return

    existing.customer_fields = customer_fields
    existing.updated_at = now
    await db.flush()


async def _persist_record_update(
    *,
    db: AsyncSession,
    record: _HiredAgentRecord,
    nickname: str | None,
    theme: str | None,
    config: dict[str, Any],
) -> _HiredAgentRecord:
    configured = _compute_agent_configured(nickname, theme, agent_id=record.agent_id, config=config)
    _assert_refs_only_config(config)
    repo = HiredAgentRepository(db)
    persisted = await repo.draft_upsert(
        subscription_id=record.subscription_id,
        agent_id=record.agent_id,
        agent_type_id=record.agent_type_id,
        customer_id=record.customer_id or "",
        nickname=nickname,
        theme=theme,
        config=config,
        configured=configured,
        internal_definition_version_id=record.internal_definition_version_id,
        external_catalog_version=record.external_catalog_version,
        catalog_release_id=record.catalog_release_id,
        catalog_status_at_hire=record.catalog_status_at_hire,
    )
    return _db_model_to_record(persisted)


async def _apply_goals_and_trial_state(
    *,
    db: AsyncSession,
    record: _HiredAgentRecord,
    goals_completed: bool,
) -> _HiredAgentRecord:
    subscription_status, _ = await _subscription_status_and_ended_at(
        subscription_id=record.subscription_id,
        db=db,
    )
    if subscription_status is None:
        raise HTTPException(status_code=404, detail="Subscription not found.")
    if subscription_status != "active":
        raise HTTPException(status_code=409, detail="Subscription is not active; hired agent is read-only.")

    now = datetime.now(timezone.utc)
    configured = _compute_agent_configured(record.nickname, record.theme, agent_id=record.agent_id, config=record.config)
    trial_status = record.trial_status
    trial_start_at = record.trial_start_at
    trial_end_at = record.trial_end_at
    if configured and goals_completed and trial_status != "active":
        trial_status = "active"
        trial_start_at = now
        trial_end_at = now + timedelta(days=DEFAULT_TRIAL_DAYS)

    repo = HiredAgentRepository(db)
    persisted = await repo.finalize(
        hired_instance_id=record.hired_instance_id,
        agent_type_id=record.agent_type_id,
        goals_completed=goals_completed,
        configured=configured,
        trial_status=trial_status,
        trial_start=trial_start_at,
        trial_end=trial_end_at,
        catalog_release_id=record.catalog_release_id,
        internal_definition_version_id=record.internal_definition_version_id,
        external_catalog_version=record.external_catalog_version,
        catalog_status_at_hire=record.catalog_status_at_hire,
    )
    next_record = _db_model_to_record(persisted)
    if record.trial_status != "active" and next_record.trial_status == "active":
        await _fire_lifecycle_hire_hooks(record, trial_start_at=next_record.trial_start_at)
    return next_record


@router.get("/{hired_instance_id}/studio", response_model=HiredAgentStudioResponse)
async def get_hired_agent_studio(
    hired_instance_id: str,
    customer_id: str,
    db: AsyncSession | None = Depends(_get_read_hired_agents_db_session),
) -> HiredAgentStudioResponse:
    if not customer_id.strip():
        raise HTTPException(status_code=400, detail="customer_id is required.")
    record = await _load_owned_record(
        hired_instance_id=hired_instance_id,
        customer_id=customer_id,
        db=db,
    )
    return await _build_studio_response(record, db)


@router.patch("/{hired_instance_id}/studio", response_model=HiredAgentStudioResponse)
async def update_hired_agent_studio(
    hired_instance_id: str,
    body: StudioUpdateRequest,
    customer_id: str,
    db: AsyncSession | None = Depends(_get_hired_agents_db_session),
) -> HiredAgentStudioResponse:
    record = await _load_owned_record(
        hired_instance_id=hired_instance_id,
        customer_id=customer_id,
        db=db,
    )
    await _assert_writable(record, db=db)

    next_nickname = record.nickname
    next_theme = record.theme
    next_config = dict(record.config or {})

    if body.identity is not None:
        if body.identity.nickname is not None:
            next_nickname = body.identity.nickname
        if body.identity.theme is not None:
            next_theme = _normalize_theme(body.identity.theme)

    if body.connection is not None:
        next_config = _apply_connection_config(record, next_config, body.connection)
        if db is not None:
            await _upsert_platform_connection(
                db=db,
                hired_instance_id=hired_instance_id,
                body=body.connection,
            )

    if body.operating_plan is not None:
        if body.operating_plan.config_patch:
            next_config = _merge_dict(next_config, body.operating_plan.config_patch)
        if body.operating_plan.customer_fields is not None and db is not None:
            await _upsert_skill_config(
                db=db,
                record=record,
                skill_id=body.operating_plan.skill_id or "default",
                customer_fields=body.operating_plan.customer_fields,
            )

    if db is not None:
        next_record = await _persist_record_update(
            db=db,
            record=record,
            nickname=next_nickname,
            theme=next_theme,
            config=next_config,
        )
    else:
        next_record = record.model_copy(
            update={
                "nickname": next_nickname,
                "theme": next_theme,
                "config": next_config,
                "configured": _compute_agent_configured(next_nickname, next_theme, agent_id=record.agent_id, config=next_config),
                "updated_at": datetime.now(timezone.utc),
            }
        )
        _by_id[next_record.hired_instance_id] = next_record

    next_goals_completed = next_record.goals_completed
    if body.operating_plan is not None and body.operating_plan.goals_completed is not None:
        next_goals_completed = body.operating_plan.goals_completed
    if body.review is not None and body.review.goals_completed is not None:
        next_goals_completed = body.review.goals_completed

    if next_goals_completed != next_record.goals_completed or (body.review is not None and body.review.finalize):
        if db is not None:
            next_record = await _apply_goals_and_trial_state(
                db=db,
                record=next_record,
                goals_completed=bool(next_goals_completed),
            )
        else:
            now = datetime.now(timezone.utc)
            configured = _compute_agent_configured(next_record.nickname, next_record.theme, agent_id=next_record.agent_id, config=next_record.config)
            trial_status = next_record.trial_status
            trial_start_at = next_record.trial_start_at
            trial_end_at = next_record.trial_end_at
            if configured and bool(next_goals_completed) and trial_status != "active":
                trial_status = "active"
                trial_start_at = now
                trial_end_at = now + timedelta(days=DEFAULT_TRIAL_DAYS)
            next_record = next_record.model_copy(
                update={
                    "configured": configured,
                    "goals_completed": bool(next_goals_completed),
                    "trial_status": trial_status,
                    "trial_start_at": trial_start_at,
                    "trial_end_at": trial_end_at,
                    "updated_at": now,
                }
            )
            _by_id[next_record.hired_instance_id] = next_record

    if db is not None:
        await db.commit()
    return await _build_studio_response(next_record, db)