"""seed demo DMA runtime records

Revision ID: 032_seed_demo_dma_runtime
Revises: 031_dma_iteration1_persistence
Create Date: 2026-03-12

Purpose:
    Seed visible Digital Marketing Agent runtime records for demo/uat so CP and
    PP show a truthful DMA journey instead of an empty runtime.
"""

from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta, timezone

from alembic import op
import sqlalchemy as sa


revision = "032_seed_demo_dma_runtime"
down_revision = "031_dma_iteration1_persistence"
branch_labels = None
depends_on = None


_NOW = datetime.now(timezone.utc)
_TODAY = _NOW.date()
_TRIAL_START = _NOW - timedelta(days=2)
_TRIAL_END = _NOW + timedelta(days=5)
_PLATFORM_SKILL_ID = "marketing.multichannel-post-v1"
_SKILL_DEFINITION_VERSION_ID = "v1"
_GOAL_TEMPLATE_ID = "marketing.weekly_multichannel_batch.v1"
_AGENT_DEFINITION_VERSION_ID = "1.0.0"

_USERS = [
    {
        "label": "yogesh",
        "customer_id": "1a9c1294-073e-4565-a359-27eae94a05b4",
        "subscription_id": "SUB-YOGESH-DMA-01",
        "hired_instance_id": "INST-YOGESH-DMA-01",
        "goal_instance_id": "GOAL-YOGESH-DMA-01",
        "campaign_id": "CMP-YOGESH-DMA-01",
        "theme_item_id": "THEME-YOGESH-DMA-01",
        "content_post_id": "POST-YOGESH-DMA-01",
        "draft_batch_id": "BATCH-YOGESH-DMA-01",
        "draft_post_id": "DRAFT-YOGESH-DMA-01",
        "deliverable_id": "DELIV-YOGESH-DMA-01",
        "approval_id": "APR-YOGESH-DMA-01",
        "skill_config_id": "SKCFG-YOGESH-DMA-01",
        "brand_name": "WAOOAW",
        "location": "Pune",
        "audience": "SMB founders exploring AI execution",
        "persona": "Growth-focused founder",
        "offer": "7-day free trial with keep-the-work guarantee",
        "objective": "Generate qualified discovery conversations from YouTube",
        "theme": "How founders can trial AI agents without procurement risk",
        "channel_status": "connected",
        "visibility": "public",
        "public_release_requested": True,
        "secret_ref": "projects/waooaw-oauth/secrets/demo-youtube-yogesh/versions/latest",
    },
    {
        "label": "rupali",
        "customer_id": "8a8e1d58-949f-41f3-81ff-7abf5d4a172e",
        "subscription_id": "SUB-RUPALI-DMA-01",
        "hired_instance_id": "INST-RUPALI-DMA-01",
        "goal_instance_id": "GOAL-RUPALI-DMA-01",
        "campaign_id": "CMP-RUPALI-DMA-01",
        "theme_item_id": "THEME-RUPALI-DMA-01",
        "content_post_id": "POST-RUPALI-DMA-01",
        "draft_batch_id": "BATCH-RUPALI-DMA-01",
        "draft_post_id": "DRAFT-RUPALI-DMA-01",
        "deliverable_id": "DELIV-RUPALI-DMA-01",
        "approval_id": "APR-RUPALI-DMA-01",
        "skill_config_id": "SKCFG-RUPALI-DMA-01",
        "brand_name": "WAOOAW",
        "location": "Mumbai",
        "audience": "Business owners evaluating AI teammates for growth",
        "persona": "Operator who needs publish-ready content with minimal follow-up",
        "offer": "Try talent, keep results",
        "objective": "Create a repeatable YouTube content lane for WAOOAW demos",
        "theme": "Weekly YouTube explainers that convert AI-curious operators",
        "channel_status": "pending",
        "visibility": "private",
        "public_release_requested": False,
        "secret_ref": "projects/waooaw-oauth/secrets/demo-youtube-rupali/versions/latest",
    },
]


def _json(value: object) -> str:
    return json.dumps(value)


def _brief(user: dict[str, object]) -> dict[str, object]:
    return {
        "theme": user["theme"],
        "start_date": (_TODAY + timedelta(days=1)).isoformat(),
        "duration_days": 7,
        "destinations": [
            {
                "destination_type": "youtube",
                "handle": "@waooaw",
                "metadata": {
                    "visibility": user["visibility"],
                    "public_release_requested": user["public_release_requested"],
                },
            }
        ],
        "schedule": {
            "times_per_day": 1,
            "preferred_hours_utc": [11],
        },
        "brand_name": user["brand_name"],
        "audience": user["audience"],
        "tone": "clear, credible, energetic",
        "language": "en",
        "approval_mode": "per_item",
        "theme_discovery": {
            "business_background": "WAOOAW is an AI agent marketplace where customers try agents before paying.",
            "objective": user["objective"],
            "industry": "AI services",
            "locality": user["location"],
            "target_audience": user["audience"],
            "persona": user["persona"],
            "tone": "clear, credible, energetic",
            "offer": user["offer"],
            "channel_intent": {
                "primary_destination": "youtube",
                "supported_live_destinations": ["youtube"],
                "content_formats": ["explainer video", "shorts teaser"],
                "call_to_action": "Book a demo and start a 7-day trial",
            },
            "posting_cadence": {
                "posts_per_week": 3,
                "preferred_days": ["tuesday", "thursday", "saturday"],
                "preferred_hours_utc": [11],
            },
            "success_metrics": [
                {"name": "qualified_leads", "target": "10 per month"},
                {"name": "youtube_watch_time", "target": "2000 minutes per month"},
            ],
        },
        "additional_context": "Demo runtime seeded by migration 032 so CP and PP can show a real DMA story.",
    }


def _brief_summary(user: dict[str, object]) -> dict[str, object]:
    return {
        "summary_text": f"{user['objective']} for {user['audience']} in {user['location']} using youtube.",
        "target_audience": user["audience"],
        "offer": user["offer"],
        "primary_destination": "youtube",
        "cadence_text": "3 posts/week",
        "success_metrics": [
            "qualified_leads: 10 per month",
            "youtube_watch_time: 2000 minutes per month",
        ],
    }


def _cost_estimate() -> dict[str, object]:
    return {
        "total_theme_items": 7,
        "total_posts": 7,
        "llm_calls": 8,
        "cost_per_call_usd": 0.0,
        "total_cost_usd": 0.0,
        "total_cost_inr": 0.0,
        "model_used": "deterministic",
        "note": "₹0 - demo runtime seed",
    }


def _destination(user: dict[str, object], approval_id: str | None) -> dict[str, object]:
    metadata: dict[str, object] = {
        "visibility": user["visibility"],
        "public_release_requested": user["public_release_requested"],
        "credential_ref": user["secret_ref"],
    }
    if approval_id:
        metadata["approval_id"] = approval_id

    return {
        "destination_type": "youtube",
        "handle": "@waooaw",
        "metadata": metadata,
    }


def _draft_deliverables(user: dict[str, object]) -> list[dict[str, object]]:
    return [
        {
            "deliverable_id": user["content_post_id"],
            "theme_item_id": user["theme_item_id"],
            "destination_type": "youtube",
            "review_status": "approved",
            "publish_status": "not_published",
        }
    ]


def _hired_agent_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for user in _USERS:
        rows.append(
            {
                "hired_instance_id": user["hired_instance_id"],
                "subscription_id": user["subscription_id"],
                "agent_id": "AGT-MKT-DMA-001",
                "agent_type_id": "marketing.digital_marketing.v1",
                "definition_version_id": _AGENT_DEFINITION_VERSION_ID,
                "customer_id": user["customer_id"],
                "nickname": "Digital Marketing Agent",
                "theme": "dark",
                "config": _json(
                    {
                        "primary_language": "en",
                        "timezone": "Asia/Kolkata",
                        "brand_name": user["brand_name"],
                        "offerings_services": ["AI agent marketplace"],
                        "location": user["location"],
                        "platforms_enabled": ["youtube"],
                        "posting_identity": user["brand_name"],
                    }
                ),
                "configured": True,
                "goals_completed": True,
                "active": True,
                "trial_status": "active",
                "trial_start_at": _TRIAL_START,
                "trial_end_at": _TRIAL_END,
                "created_at": _NOW,
                "updated_at": _NOW,
            }
        )
    return rows


def _goal_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for user in _USERS:
        rows.append(
            {
                "goal_instance_id": user["goal_instance_id"],
                "hired_instance_id": user["hired_instance_id"],
                "goal_template_id": _GOAL_TEMPLATE_ID,
                "frequency": "weekly",
                "settings": _json(
                    {
                        "topics": [
                            "AI agents for founders",
                            "YouTube growth for service businesses",
                        ],
                        "posts_per_platform": 3,
                    }
                ),
                "created_at": _NOW,
                "updated_at": _NOW,
            }
        )
    return rows


def _skill_config_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for user in _USERS:
        rows.append(
            {
                "id": user["skill_config_id"],
                "hired_instance_id": user["hired_instance_id"],
                "skill_id": _PLATFORM_SKILL_ID,
                "definition_version_id": _SKILL_DEFINITION_VERSION_ID,
                "pp_locked_fields": _json(
                    {
                        "supported_live_destinations": ["youtube"],
                        "visible_skills": [
                            "Theme Discovery",
                            "Content Creation",
                            "Content Publishing",
                        ],
                    }
                ),
                "customer_fields": _json(
                    {
                        "business_background": "WAOOAW is an AI agent marketplace where customers keep the work from the free trial.",
                        "objective": user["objective"],
                        "industry": "AI services",
                        "locality": user["location"],
                        "target_audience": user["audience"],
                        "persona": user["persona"],
                        "tone": "clear, credible, energetic",
                        "offer": user["offer"],
                        "channel_intent": {
                            "primary_destination": "youtube",
                            "supported_live_destinations": ["youtube"],
                            "content_formats": ["explainer video", "shorts teaser"],
                            "call_to_action": "Start a 7-day trial",
                        },
                        "posting_cadence": {
                            "posts_per_week": 3,
                            "preferred_days": ["tuesday", "thursday", "saturday"],
                            "preferred_hours_utc": [11],
                        },
                        "success_metrics": [
                            {"name": "qualified_leads", "target": "10 per month"},
                            {"name": "youtube_watch_time", "target": "2000 minutes per month"},
                        ],
                    }
                ),
                "created_at": _NOW,
                "updated_at": _NOW,
            }
        )
    return rows


def _campaign_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for user in _USERS:
        rows.append(
            {
                "campaign_id": user["campaign_id"],
                "hired_instance_id": user["hired_instance_id"],
                "customer_id": user["customer_id"],
                "brief": _json(_brief(user)),
                "cost_estimate": _json(_cost_estimate()),
                "status": "draft",
                "workflow_state": "approved_for_upload",
                "brief_summary": _json(_brief_summary(user)),
                "approval_state": _json(
                    {
                        "pending_review_count": 0,
                        "approved_count": 1,
                        "rejected_count": 0,
                    }
                ),
                "draft_deliverables": _json(_draft_deliverables(user)),
                "created_at": _NOW,
                "updated_at": _NOW,
            }
        )
    return rows


def _theme_item_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for user in _USERS:
        rows.append(
            {
                "theme_item_id": user["theme_item_id"],
                "campaign_id": user["campaign_id"],
                "day_number": 1,
                "scheduled_date": _TODAY + timedelta(days=1),
                "theme_title": user["theme"],
                "theme_description": "A customer-facing explainer showing how WAOOAW reduces procurement risk with try-before-hire AI agents.",
                "dimensions": _json(["education", "trust", "conversion"]),
                "review_status": "approved",
                "approved_at": _NOW,
            }
        )
    return rows


def _content_post_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for user in _USERS:
        rows.append(
            {
                "post_id": user["content_post_id"],
                "campaign_id": user["campaign_id"],
                "theme_item_id": user["theme_item_id"],
                "destination": _json(_destination(user, str(user["approval_id"]))),
                "content_text": f"{user['brand_name']} explainer: why {user['audience']} can start with a zero-risk AI agent trial and keep the deliverables.",
                "hashtags": _json(["WAOOAW", "AIAgents", "YouTubeMarketing"]),
                "scheduled_publish_at": _NOW + timedelta(days=1),
                "review_status": "approved",
                "publish_status": "not_published",
                "approval_id": user["approval_id"],
                "credential_ref": user["secret_ref"],
                "visibility": user["visibility"],
                "public_release_requested": user["public_release_requested"],
                "publish_receipt": _json(None),
                "created_at": _NOW,
                "updated_at": _NOW,
            }
        )
    return rows


def _draft_batch_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for user in _USERS:
        rows.append(
            {
                "batch_id": user["draft_batch_id"],
                "agent_id": "AGT-MKT-DMA-001",
                "hired_instance_id": user["hired_instance_id"],
                "campaign_id": user["campaign_id"],
                "customer_id": user["customer_id"],
                "theme": user["theme"],
                "brand_name": user["brand_name"],
                "brief_summary": _brief_summary(user)["summary_text"],
                "created_at": _NOW,
                "status": "approved",
                "workflow_state": "draft_ready_for_review",
            }
        )
    return rows


def _draft_post_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for user in _USERS:
        rows.append(
            {
                "post_id": user["draft_post_id"],
                "batch_id": user["draft_batch_id"],
                "campaign_id": user["campaign_id"],
                "channel": "youtube",
                "text": f"Storyboard draft for {user['brand_name']}: show why {user['audience']} can trial AI agents without procurement drag.",
                "hashtags": _json(["WAOOAW", "DigitalMarketing", "YouTube"]),
                "review_status": "approved",
                "approval_id": user["approval_id"],
                "credential_ref": user["secret_ref"],
                "execution_status": "not_scheduled",
                "visibility": user["visibility"],
                "public_release_requested": user["public_release_requested"],
                "scheduled_at": None,
                "attempts": 0,
                "last_error": None,
                "provider_post_id": None,
                "provider_post_url": None,
                "created_at": _NOW,
                "updated_at": _NOW,
            }
        )
    return rows


def _platform_connection_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for user in _USERS:
        rows.append(
            {
                "id": f"PC-{user['label'].upper()}-DMA-YT-01",
                "hired_instance_id": user["hired_instance_id"],
                "skill_id": _PLATFORM_SKILL_ID,
                "platform_key": "youtube",
                "secret_ref": user["secret_ref"],
                "status": user["channel_status"],
                "connected_at": _NOW,
                "last_verified_at": _NOW if user["channel_status"] == "connected" else None,
                "created_at": _NOW,
                "updated_at": _NOW,
            }
        )
    return rows


def _deliverable_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for user in _USERS:
        rows.append(
            {
                "deliverable_id": user["deliverable_id"],
                "hired_instance_id": user["hired_instance_id"],
                "goal_instance_id": user["goal_instance_id"],
                "goal_template_id": _GOAL_TEMPLATE_ID,
                "title": f"YouTube publish-ready draft for {user['brand_name']}",
                "payload": _json(
                    {
                        "destination": _destination(user, str(user["approval_id"])),
                        "destination_type": "youtube",
                        "channel": "youtube",
                        "publish_status": "not_published",
                        "content_text": f"Final YouTube draft for {user['brand_name']} focused on {user['objective']}.",
                    }
                ),
                "review_status": "approved",
                "review_notes": "Demo migration seeded approved DMA deliverable.",
                "execution_status": "not_executed",
                "executed_at": None,
                "created_at": _NOW,
                "updated_at": _NOW,
            }
        )
    return rows


def _approval_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for user in _USERS:
        rows.append(
            {
                "approval_id": user["approval_id"],
                "deliverable_id": user["deliverable_id"],
                "customer_id": user["customer_id"],
                "decision": "approved",
                "notes": "Demo DMA approval seeded for deployed CP/PP walkthrough.",
                "created_at": _NOW,
            }
        )
    return rows


def upgrade() -> None:
    environment = os.getenv("ENVIRONMENT", "").lower()
    if environment not in ("demo", "uat"):
        print(f"⏭️  Skipping demo DMA runtime seed (environment: {environment or 'not set'})")
        return

    connection = op.get_bind()

    for row in _hired_agent_rows():
        connection.execute(
            sa.text(
                """
                INSERT INTO hired_agents (
                    hired_instance_id, subscription_id, agent_id, agent_type_id,
                    definition_version_id, customer_id, nickname, theme, config,
                    configured, goals_completed, active,
                    trial_status, trial_start_at, trial_end_at,
                    created_at, updated_at
                )
                VALUES (
                    :hired_instance_id, :subscription_id, :agent_id, :agent_type_id,
                    :definition_version_id, :customer_id, :nickname, :theme, CAST(:config AS jsonb),
                    :configured, :goals_completed, :active,
                    :trial_status, :trial_start_at, :trial_end_at,
                    :created_at, :updated_at
                )
                ON CONFLICT (subscription_id) DO NOTHING
                """
            ),
            row,
        )

    for row in _goal_rows():
        connection.execute(
            sa.text(
                """
                INSERT INTO goal_instances (
                    goal_instance_id, hired_instance_id, goal_template_id, frequency,
                    settings, created_at, updated_at
                )
                VALUES (
                    :goal_instance_id, :hired_instance_id, :goal_template_id, :frequency,
                    CAST(:settings AS jsonb), :created_at, :updated_at
                )
                ON CONFLICT (goal_instance_id) DO NOTHING
                """
            ),
            row,
        )

    for row in _skill_config_rows():
        connection.execute(
            sa.text(
                """
                INSERT INTO skill_configs (
                    id, hired_instance_id, skill_id, definition_version_id,
                    pp_locked_fields, customer_fields, created_at, updated_at
                )
                VALUES (
                    :id, :hired_instance_id, :skill_id, :definition_version_id,
                    CAST(:pp_locked_fields AS jsonb), CAST(:customer_fields AS jsonb), :created_at, :updated_at
                )
                ON CONFLICT ON CONSTRAINT uq_skill_config_per_hire DO NOTHING
                """
            ),
            row,
        )

    for row in _campaign_rows():
        connection.execute(
            sa.text(
                """
                INSERT INTO campaigns (
                    campaign_id, hired_instance_id, customer_id, brief, cost_estimate,
                    status, workflow_state, brief_summary, approval_state, draft_deliverables,
                    created_at, updated_at
                )
                VALUES (
                    :campaign_id, :hired_instance_id, :customer_id, CAST(:brief AS jsonb), CAST(:cost_estimate AS jsonb),
                    :status, :workflow_state, CAST(:brief_summary AS jsonb), CAST(:approval_state AS jsonb), CAST(:draft_deliverables AS jsonb),
                    :created_at, :updated_at
                )
                ON CONFLICT (campaign_id) DO NOTHING
                """
            ),
            row,
        )

    for row in _theme_item_rows():
        connection.execute(
            sa.text(
                """
                INSERT INTO daily_theme_items (
                    theme_item_id, campaign_id, day_number, scheduled_date,
                    theme_title, theme_description, dimensions, review_status, approved_at
                )
                VALUES (
                    :theme_item_id, :campaign_id, :day_number, :scheduled_date,
                    :theme_title, :theme_description, CAST(:dimensions AS jsonb), :review_status, :approved_at
                )
                ON CONFLICT (theme_item_id) DO NOTHING
                """
            ),
            row,
        )

    for row in _content_post_rows():
        connection.execute(
            sa.text(
                """
                INSERT INTO content_posts (
                    post_id, campaign_id, theme_item_id, destination, content_text,
                    hashtags, scheduled_publish_at, review_status, publish_status,
                    approval_id, credential_ref, visibility, public_release_requested,
                    publish_receipt, created_at, updated_at
                )
                VALUES (
                    :post_id, :campaign_id, :theme_item_id, CAST(:destination AS jsonb), :content_text,
                    CAST(:hashtags AS jsonb), :scheduled_publish_at, :review_status, :publish_status,
                    :approval_id, :credential_ref, :visibility, :public_release_requested,
                    CAST(:publish_receipt AS jsonb), :created_at, :updated_at
                )
                ON CONFLICT (post_id) DO NOTHING
                """
            ),
            row,
        )

    for row in _draft_batch_rows():
        connection.execute(
            sa.text(
                """
                INSERT INTO marketing_draft_batches (
                    batch_id, agent_id, hired_instance_id, campaign_id, customer_id,
                    theme, brand_name, brief_summary, created_at, status, workflow_state
                )
                VALUES (
                    :batch_id, :agent_id, :hired_instance_id, :campaign_id, :customer_id,
                    :theme, :brand_name, :brief_summary, :created_at, :status, :workflow_state
                )
                ON CONFLICT (batch_id) DO NOTHING
                """
            ),
            row,
        )

    for row in _draft_post_rows():
        connection.execute(
            sa.text(
                """
                INSERT INTO marketing_draft_posts (
                    post_id, batch_id, campaign_id, channel, text, hashtags,
                    review_status, approval_id, credential_ref, execution_status,
                    visibility, public_release_requested, scheduled_at, attempts,
                    last_error, provider_post_id, provider_post_url, created_at, updated_at
                )
                VALUES (
                    :post_id, :batch_id, :campaign_id, :channel, :text, CAST(:hashtags AS jsonb),
                    :review_status, :approval_id, :credential_ref, :execution_status,
                    :visibility, :public_release_requested, :scheduled_at, :attempts,
                    :last_error, :provider_post_id, :provider_post_url, :created_at, :updated_at
                )
                ON CONFLICT (post_id) DO NOTHING
                """
            ),
            row,
        )

    for row in _platform_connection_rows():
        connection.execute(
            sa.text(
                """
                INSERT INTO platform_connections (
                    id, hired_instance_id, skill_id, platform_key, secret_ref,
                    status, connected_at, last_verified_at, created_at, updated_at
                )
                VALUES (
                    :id, :hired_instance_id, :skill_id, :platform_key, :secret_ref,
                    :status, :connected_at, :last_verified_at, :created_at, :updated_at
                )
                ON CONFLICT ON CONSTRAINT uq_platform_conn_hired_skill_platform DO NOTHING
                """
            ),
            row,
        )

    for row in _deliverable_rows():
        connection.execute(
            sa.text(
                """
                INSERT INTO deliverables (
                    deliverable_id, hired_instance_id, goal_instance_id, goal_template_id,
                    title, payload, review_status, review_notes, approval_id,
                    execution_status, executed_at, created_at, updated_at
                )
                VALUES (
                    :deliverable_id, :hired_instance_id, :goal_instance_id, :goal_template_id,
                    :title, CAST(:payload AS jsonb), :review_status, :review_notes, NULL,
                    :execution_status, :executed_at, :created_at, :updated_at
                )
                ON CONFLICT (deliverable_id) DO NOTHING
                """
            ),
            row,
        )

    for row in _approval_rows():
        connection.execute(
            sa.text(
                """
                INSERT INTO approvals (
                    approval_id, deliverable_id, customer_id, decision, notes, created_at
                )
                VALUES (
                    :approval_id, :deliverable_id, :customer_id, :decision, :notes, :created_at
                )
                ON CONFLICT (approval_id) DO NOTHING
                """
            ),
            row,
        )

    for user in _USERS:
        connection.execute(
            sa.text(
                """
                UPDATE deliverables
                SET approval_id = :approval_id, updated_at = :updated_at
                WHERE deliverable_id = :deliverable_id
                """
            ),
            {
                "approval_id": user["approval_id"],
                "deliverable_id": user["deliverable_id"],
                "updated_at": _NOW,
            },
        )


def downgrade() -> None:
    environment = os.getenv("ENVIRONMENT", "").lower()
    if environment not in ("demo", "uat"):
        return

    connection = op.get_bind()
    hired_instance_ids = [str(user["hired_instance_id"]) for user in _USERS]
    goal_instance_ids = [str(user["goal_instance_id"]) for user in _USERS]
    subscription_ids = [str(user["subscription_id"]) for user in _USERS]
    campaign_ids = [str(user["campaign_id"]) for user in _USERS]
    batch_ids = [str(user["draft_batch_id"]) for user in _USERS]
    deliverable_ids = [str(user["deliverable_id"]) for user in _USERS]
    approval_ids = [str(user["approval_id"]) for user in _USERS]
    skill_config_ids = [str(user["skill_config_id"]) for user in _USERS]

    connection.execute(
        sa.text("DELETE FROM approvals WHERE approval_id = ANY(:ids)"),
        {"ids": approval_ids},
    )
    connection.execute(
        sa.text("DELETE FROM deliverables WHERE deliverable_id = ANY(:ids)"),
        {"ids": deliverable_ids},
    )
    connection.execute(
        sa.text("DELETE FROM platform_connections WHERE hired_instance_id = ANY(:ids)"),
        {"ids": hired_instance_ids},
    )
    connection.execute(
        sa.text("DELETE FROM marketing_draft_batches WHERE batch_id = ANY(:ids)"),
        {"ids": batch_ids},
    )
    connection.execute(
        sa.text("DELETE FROM content_posts WHERE campaign_id = ANY(:ids)"),
        {"ids": campaign_ids},
    )
    connection.execute(
        sa.text("DELETE FROM daily_theme_items WHERE campaign_id = ANY(:ids)"),
        {"ids": campaign_ids},
    )
    connection.execute(
        sa.text("DELETE FROM campaigns WHERE campaign_id = ANY(:ids)"),
        {"ids": campaign_ids},
    )
    connection.execute(
        sa.text("DELETE FROM skill_configs WHERE id = ANY(:ids)"),
        {"ids": skill_config_ids},
    )
    connection.execute(
        sa.text("DELETE FROM goal_instances WHERE goal_instance_id = ANY(:ids)"),
        {"ids": goal_instance_ids},
    )
    connection.execute(
        sa.text("DELETE FROM hired_agents WHERE subscription_id = ANY(:ids)"),
        {"ids": subscription_ids},
    )