"""Unit tests for CampaignRepository (E2-S1).

Uses AsyncMock to simulate the SQLAlchemy async session so no live
database connection is required.

Run:
    docker compose -f docker-compose.test.yml run plant-test \\
      pytest src/Plant/BackEnd/tests/unit/test_campaign_repository.py -v \\
      --cov=repositories/campaign_repository --cov-fail-under=80
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.campaign import CampaignModel, ContentPostModel, DailyThemeItemModel
from repositories.campaign_repository import CampaignRepository


# ── Fixtures ──────────────────────────────────────────────────────────────────

BRIEF = {
    "theme": "Hire AI Agents — WAOOAW",
    "start_date": "2026-03-06",
    "duration_days": 7,
    "destinations": [{"destination_type": "simulated"}],
    "schedule": {"times_per_day": 1, "preferred_hours_utc": [9]},
    "approval_mode": "per_item",
}

COST_ESTIMATE = {
    "total_theme_items": 7,
    "total_posts": 7,
    "llm_calls": 8,
    "cost_per_call_usd": 0.0,
    "total_cost_usd": 0.0,
    "total_cost_inr": 0.0,
    "model_used": "deterministic",
}

DESTINATION = {"destination_type": "simulated"}


def _make_mock_session() -> AsyncMock:
    """Return a minimal async session mock with add / flush / refresh."""
    session = AsyncMock()
    session.add = MagicMock()  # synchronous
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    return session


def _make_campaign(campaign_id: str = "CAM-001") -> CampaignModel:
    now = datetime.now(timezone.utc)
    return CampaignModel(
        campaign_id=campaign_id,
        hired_instance_id="hired-001",
        customer_id="cust-001",
        brief=BRIEF,
        cost_estimate=COST_ESTIMATE,
        created_at=now,
        updated_at=now,
    )


def _make_theme_item(theme_item_id: str = "THM-001") -> DailyThemeItemModel:
    return DailyThemeItemModel(
        theme_item_id=theme_item_id,
        campaign_id="CAM-001",
        day_number=1,
        scheduled_date=date(2026, 3, 6),
        theme_title="Day 1: AI Agents",
        theme_description="Social proof angle",
    )


def _make_post(post_id: str = "PST-001") -> ContentPostModel:
    now = datetime.now(timezone.utc)
    return ContentPostModel(
        post_id=post_id,
        campaign_id="CAM-001",
        theme_item_id="THM-001",
        destination=DESTINATION,
        content_text="Hello WAOOAW!",
        scheduled_publish_at=now,
    )


# ── CampaignRepository — Campaign ─────────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_campaign_by_id_found():
    """E2-S1: get_campaign_by_id returns CampaignModel when row exists."""
    session = _make_mock_session()
    campaign = _make_campaign()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = campaign
    session.execute = AsyncMock(return_value=mock_result)

    repo = CampaignRepository(session)
    result = await repo.get_campaign_by_id("CAM-001")

    assert result is campaign


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_campaign_by_id_not_found():
    """E2-S1: get_campaign_by_id returns None when row is missing."""
    session = _make_mock_session()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=mock_result)

    repo = CampaignRepository(session)
    result = await repo.get_campaign_by_id("NONEXISTENT")

    assert result is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_campaign_adds_and_flushes():
    """E2-S1: create_campaign calls session.add + flush + refresh."""
    session = _make_mock_session()
    repo = CampaignRepository(session)

    result = await repo.create_campaign(
        hired_instance_id="hired-001",
        customer_id="cust-001",
        brief=BRIEF,
        cost_estimate=COST_ESTIMATE,
        campaign_id="CAM-EXPLICIT",
    )

    session.add.assert_called_once()
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once()
    assert result.campaign_id == "CAM-EXPLICIT"
    assert result.status == "draft"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_campaign_auto_generates_id():
    """E2-S1: create_campaign auto-generates CAM-<uuid> when no id supplied."""
    session = _make_mock_session()
    repo = CampaignRepository(session)

    result = await repo.create_campaign(
        hired_instance_id="hired-001",
        customer_id="cust-001",
        brief=BRIEF,
        cost_estimate=COST_ESTIMATE,
    )

    assert result.campaign_id.startswith("CAM-")


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_campaign_status_success():
    """E2-S1: update_campaign_status mutates status and flushes."""
    session = _make_mock_session()
    campaign = _make_campaign()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = campaign
    session.execute = AsyncMock(return_value=mock_result)

    repo = CampaignRepository(session)
    result = await repo.update_campaign_status("CAM-001", "running")

    assert result.status == "running"
    session.flush.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_campaign_status_not_found_raises():
    """E2-S1: update_campaign_status raises ValueError for unknown id."""
    session = _make_mock_session()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=mock_result)

    repo = CampaignRepository(session)

    with pytest.raises(ValueError, match="CAM-MISSING"):
        await repo.update_campaign_status("CAM-MISSING", "running")


@pytest.mark.asyncio
@pytest.mark.unit
async def test_delete_campaign_returns_true():
    """E2-S1: delete_campaign returns True when row found."""
    session = _make_mock_session()
    campaign = _make_campaign()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = campaign
    session.execute = AsyncMock(return_value=mock_result)

    repo = CampaignRepository(session)
    deleted = await repo.delete_campaign("CAM-001")

    assert deleted is True
    session.delete.assert_awaited_once_with(campaign)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_delete_campaign_returns_false():
    """E2-S1: delete_campaign returns False when row not found."""
    session = _make_mock_session()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=mock_result)

    repo = CampaignRepository(session)
    deleted = await repo.delete_campaign("CAM-MISSING")

    assert deleted is False
    session.delete.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_active_draft_campaign_by_hired_instance_returns_single_latest_draft():
    """E2-S1-T1: same hired instance reuses one active draft campaign."""
    session = _make_mock_session()
    latest_campaign = _make_campaign("CAM-LATEST")
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = latest_campaign
    session.execute = AsyncMock(return_value=mock_result)

    repo = CampaignRepository(session)
    result = await repo.get_active_draft_campaign_by_hired_instance("hired-001")

    assert result is latest_campaign


@pytest.mark.asyncio
@pytest.mark.unit
async def test_replace_theme_items_removes_old_and_persists_new():
    """E2-S1-T2: replacing theme items deletes old rows before inserting new ones."""
    session = _make_mock_session()
    repo = CampaignRepository(session)

    existing_item = _make_theme_item("THM-OLD")
    repo.create_theme_item = AsyncMock(
        side_effect=[
            _make_theme_item("THM-NEW-1"),
            _make_theme_item("THM-NEW-2"),
        ]
    )

    with patch.object(repo, "list_theme_items_by_campaign", AsyncMock(return_value=[existing_item])):
        items = await repo.replace_theme_items(
            "CAM-001",
            [
                {
                    "day_number": 1,
                    "scheduled_date": date(2026, 3, 7),
                    "theme_title": "New 1",
                    "theme_description": "New theme 1",
                    "dimensions": ["weekly"],
                },
                {
                    "day_number": 2,
                    "scheduled_date": date(2026, 3, 8),
                    "theme_title": "New 2",
                    "theme_description": "New theme 2",
                    "dimensions": ["weekly"],
                },
            ],
        )

    session.execute.assert_awaited()
    assert [item.theme_item_id for item in items] == ["THM-NEW-1", "THM-NEW-2"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_upsert_draft_campaign_with_theme_items_reuses_existing_campaign_id():
    """E2-S1-T1: repeated DMA setup saves reuse the same active draft campaign."""
    session = _make_mock_session()
    repo = CampaignRepository(session)
    existing_campaign = _make_campaign("CAM-REUSED")

    with patch.object(
        repo,
        "get_active_draft_campaign_by_hired_instance",
        AsyncMock(side_effect=[None, existing_campaign]),
    ), patch.object(
        repo,
        "create_campaign",
        AsyncMock(return_value=existing_campaign),
    ) as create_campaign, patch.object(
        repo,
        "update_campaign_brief",
        AsyncMock(return_value=existing_campaign),
    ) as update_campaign_brief, patch.object(
        repo,
        "replace_theme_items",
        AsyncMock(return_value=[]),
    ) as replace_theme_items:
        first = await repo.upsert_draft_campaign_with_theme_items(
            hired_instance_id="hired-001",
            customer_id="cust-001",
            brief=BRIEF,
            cost_estimate=COST_ESTIMATE,
            theme_items=[],
        )
        second = await repo.upsert_draft_campaign_with_theme_items(
            hired_instance_id="hired-001",
            customer_id="cust-001",
            brief={**BRIEF, "theme": "Updated theme"},
            cost_estimate=COST_ESTIMATE,
            theme_items=[],
        )

    assert first.campaign_id == "CAM-REUSED"
    assert second.campaign_id == "CAM-REUSED"
    create_campaign.assert_awaited_once()
    update_campaign_brief.assert_awaited_once()
    assert replace_theme_items.await_count == 2


@pytest.mark.asyncio
@pytest.mark.unit
async def test_upsert_draft_campaign_with_theme_items_replaces_theme_rows():
    """E2-S1-T2: the upsert helper replaces theme items on the reused draft."""
    session = _make_mock_session()
    repo = CampaignRepository(session)
    existing_campaign = _make_campaign("CAM-REUSED")
    replacement_items = [
        {
            "day_number": 1,
            "scheduled_date": date(2026, 3, 7),
            "theme_title": "New 1",
            "theme_description": "Replacement theme",
            "dimensions": ["weekly"],
        }
    ]

    with patch.object(
        repo,
        "get_active_draft_campaign_by_hired_instance",
        AsyncMock(return_value=existing_campaign),
    ), patch.object(
        repo,
        "update_campaign_brief",
        AsyncMock(return_value=existing_campaign),
    ), patch.object(
        repo,
        "replace_theme_items",
        AsyncMock(return_value=[_make_theme_item("THM-NEW")]),
    ) as replace_theme_items:
        result = await repo.upsert_draft_campaign_with_theme_items(
            hired_instance_id="hired-001",
            customer_id="cust-001",
            brief=BRIEF,
            cost_estimate=COST_ESTIMATE,
            theme_items=replacement_items,
        )

    assert result.campaign_id == "CAM-REUSED"
    replace_theme_items.assert_awaited_once_with("CAM-REUSED", replacement_items)


# ── CampaignRepository — DailyThemeItem ───────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_theme_item_adds_and_flushes():
    """E2-S1: create_theme_item calls session.add + flush + refresh."""
    session = _make_mock_session()
    repo = CampaignRepository(session)

    result = await repo.create_theme_item(
        campaign_id="CAM-001",
        day_number=1,
        scheduled_date=date(2026, 3, 6),
        theme_title="Day 1: AI Agents",
        theme_description="Social proof",
        theme_item_id="THM-EXPLICIT",
    )

    session.add.assert_called_once()
    session.flush.assert_awaited_once()
    assert result.theme_item_id == "THM-EXPLICIT"
    assert result.review_status == "pending_review"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_theme_item_auto_id():
    """E2-S1: create_theme_item auto-generates THM-<uuid> when no id supplied."""
    session = _make_mock_session()
    repo = CampaignRepository(session)

    result = await repo.create_theme_item(
        campaign_id="CAM-001",
        day_number=2,
        scheduled_date=date(2026, 3, 7),
        theme_title="Day 2",
        theme_description="Description",
    )

    assert result.theme_item_id.startswith("THM-")


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_theme_item_review_status_approved():
    """E2-S1: update_theme_item_review_status sets approved_at when approved."""
    session = _make_mock_session()
    item = _make_theme_item()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = item
    session.execute = AsyncMock(return_value=mock_result)

    repo = CampaignRepository(session)
    result = await repo.update_theme_item_review_status("THM-001", "approved")

    assert result.review_status == "approved"
    assert result.approved_at is not None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_theme_item_review_status_not_found_raises():
    """E2-S1: update_theme_item_review_status raises ValueError for unknown id."""
    session = _make_mock_session()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=mock_result)

    repo = CampaignRepository(session)

    with pytest.raises(ValueError, match="THM-MISSING"):
        await repo.update_theme_item_review_status("THM-MISSING", "approved")


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_campaign_runtime_counters_rolls_up_post_review_counts():
    session = _make_mock_session()
    repo = CampaignRepository(session)

    with patch.object(repo, "list_theme_items_by_campaign", AsyncMock(return_value=[_make_theme_item()])):
        approved = _make_post("PST-APPROVED")
        approved.review_status = "approved"
        pending = _make_post("PST-PENDING")
        pending.review_status = "pending_review"
        rejected = _make_post("PST-REJECTED")
        rejected.review_status = "rejected"

        with patch.object(repo, "list_posts_by_campaign", AsyncMock(return_value=[approved, pending, rejected])):
            counters = await repo.get_campaign_runtime_counters("CAM-001")

    assert counters == {
        "theme_items": 1,
        "posts": 3,
        "pending_review_posts": 1,
        "approved_posts": 1,
        "rejected_posts": 1,
    }


# ── CampaignRepository — ContentPost ─────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_post_adds_and_flushes():
    """E2-S1: create_post calls session.add + flush + refresh."""
    session = _make_mock_session()
    repo = CampaignRepository(session)

    now = datetime.now(timezone.utc)
    result = await repo.create_post(
        campaign_id="CAM-001",
        theme_item_id="THM-001",
        destination=DESTINATION,
        content_text="Hello WAOOAW!",
        scheduled_publish_at=now,
        post_id="PST-EXPLICIT",
    )

    session.add.assert_called_once()
    session.flush.assert_awaited_once()
    assert result.post_id == "PST-EXPLICIT"
    assert result.review_status == "pending_review"
    assert result.publish_status == "not_published"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_post_auto_id():
    """E2-S1: create_post auto-generates PST-<uuid> when no id supplied."""
    session = _make_mock_session()
    repo = CampaignRepository(session)

    now = datetime.now(timezone.utc)
    result = await repo.create_post(
        campaign_id="CAM-001",
        theme_item_id="THM-001",
        destination=DESTINATION,
        content_text="Hello!",
        scheduled_publish_at=now,
    )

    assert result.post_id.startswith("PST-")


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_post_review_status_success():
    """E2-S1: update_post_review_status mutates status and flushes."""
    session = _make_mock_session()
    post = _make_post()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = post
    session.execute = AsyncMock(return_value=mock_result)

    repo = CampaignRepository(session)
    result = await repo.update_post_review_status("PST-001", "approved")

    assert result.review_status == "approved"
    session.flush.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_post_review_status_not_found_raises():
    """E2-S1: update_post_review_status raises ValueError for unknown id."""
    session = _make_mock_session()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=mock_result)

    repo = CampaignRepository(session)

    with pytest.raises(ValueError, match="PST-MISSING"):
        await repo.update_post_review_status("PST-MISSING", "approved")


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_post_publish_status_with_receipt():
    """E2-S1: update_post_publish_status stores receipt and publish_status."""
    session = _make_mock_session()
    post = _make_post()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = post
    session.execute = AsyncMock(return_value=mock_result)

    receipt = {"platform_post_id": "SIM-999", "success": True}
    repo = CampaignRepository(session)
    result = await repo.update_post_publish_status(
        "PST-001", "published", publish_receipt=receipt
    )

    assert result.publish_status == "published"
    assert result.publish_receipt == receipt


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_post_publish_status_not_found_raises():
    """E2-S1: update_post_publish_status raises ValueError for unknown id."""
    session = _make_mock_session()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=mock_result)

    repo = CampaignRepository(session)

    with pytest.raises(ValueError, match="PST-MISSING"):
        await repo.update_post_publish_status("PST-MISSING", "published")


@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_posts_due_for_publish():
    """E2-S1: list_posts_due_for_publish returns approved not_published posts."""
    session = _make_mock_session()
    post = _make_post()
    post.review_status = "approved"

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [post]
    session.execute = AsyncMock(return_value=mock_result)

    repo = CampaignRepository(session)
    results = await repo.list_posts_due_for_publish()

    assert len(results) == 1
    assert results[0] is post
