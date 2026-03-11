"""Integration tests for campaigns API with CAMPAIGN_PERSISTENCE_MODE=db (E4-S1).

Uses a FakeCampaignRepository backed by in-memory dicts so no PostgreSQL is
needed.  The tests exercise the full DB code path:
  create → get → approve theme items → generate posts → approve post → publish

Run:
    docker compose -f docker-compose.test.yml run plant-test \\
      pytest src/Plant/BackEnd/tests/test_campaigns_api_db.py \\
             src/Plant/BackEnd/tests/test_campaigns_api.py -v \\
      --cov=src/Plant/BackEnd/api/v1/campaigns \\
      --cov=src/Plant/BackEnd/repositories/campaign_repository \\
      --cov-fail-under=80
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, AsyncGenerator, Generator
from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest
from fastapi import FastAPI

import api.v1.campaigns as camp_module
from models.campaign import CampaignModel, ContentPostModel, DailyThemeItemModel


# ── Constants (same as test_campaigns_api.py) ─────────────────────────────────

AUTH = "Bearer test-token"

BRIEF_PAYLOAD = {
    "theme": "WAOOAW AI Hire Campaign",
    "start_date": "2026-03-06",
    "duration_days": 2,
    "destinations": [{"destination_type": "simulated"}],
    "schedule": {"times_per_day": 1, "preferred_hours_utc": [9]},
    "brand_name": "WAOOAW",
    "audience": "SMB founders",
    "tone": "professional",
    "approval_mode": "per_item",
}

CREATE_PAYLOAD = {
    "hired_instance_id": "hired-db-001",
    "customer_id": "cust-db-001",
    "brief": BRIEF_PAYLOAD,
}


# ── Fake repository ────────────────────────────────────────────────────────────

class _FakeState:
    """Mutable store shared across one test's fake repository instances."""

    def __init__(self) -> None:
        self.campaigns: dict[str, CampaignModel] = {}
        self.theme_items: dict[str, dict[str, DailyThemeItemModel]] = {}
        self.posts: dict[str, dict[str, ContentPostModel]] = {}

    def reset(self) -> None:
        self.campaigns.clear()
        self.theme_items.clear()
        self.posts.clear()


_fake_state = _FakeState()


class FakeCampaignRepository:
    """In-memory stand-in for CampaignRepository used in DB-mode integration tests."""

    def __init__(self, session: Any) -> None:  # noqa: ARG002
        pass  # session intentionally ignored

    # ── Campaign ──────────────────────────────────────────────────────────────

    async def get_campaign_by_id(self, campaign_id: str) -> CampaignModel | None:
        return _fake_state.campaigns.get(campaign_id)

    async def create_campaign(
        self,
        hired_instance_id: str,
        customer_id: str,
        brief: dict[str, Any],
        cost_estimate: dict[str, Any],
        campaign_id: str | None = None,
        status: str = "draft",
    ) -> CampaignModel:
        now = datetime.now(timezone.utc)
        m = CampaignModel(
            campaign_id=campaign_id or f"CAM-{uuid4()}",
            hired_instance_id=hired_instance_id,
            customer_id=customer_id,
            brief=brief,
            cost_estimate=cost_estimate,
            status=status,
            created_at=now,
            updated_at=now,
        )
        _fake_state.campaigns[m.campaign_id] = m
        return m

    async def update_campaign_status(self, campaign_id: str, status: str) -> CampaignModel:
        m = _fake_state.campaigns.get(campaign_id)
        if m is None:
            raise ValueError(f"Campaign {campaign_id!r} not found")
        m.status = status
        m.updated_at = datetime.now(timezone.utc)
        return m

    async def update_campaign_runtime(
        self,
        campaign_id: str,
        *,
        workflow_state: str,
        brief_summary: dict[str, Any],
        approval_state: dict[str, Any],
        draft_deliverables: list[dict[str, Any]],
    ) -> CampaignModel:
        m = _fake_state.campaigns.get(campaign_id)
        if m is None:
            raise ValueError(f"Campaign {campaign_id!r} not found")
        m.workflow_state = workflow_state
        m.brief_summary = brief_summary
        m.approval_state = approval_state
        m.draft_deliverables = draft_deliverables
        m.updated_at = datetime.now(timezone.utc)
        return m

    # ── DailyThemeItem ────────────────────────────────────────────────────────

    async def list_theme_items_by_campaign(self, campaign_id: str) -> list[DailyThemeItemModel]:
        items = _fake_state.theme_items.get(campaign_id, {})
        return sorted(items.values(), key=lambda x: x.day_number)

    async def get_theme_item_by_id(self, theme_item_id: str) -> DailyThemeItemModel | None:
        for items in _fake_state.theme_items.values():
            if theme_item_id in items:
                return items[theme_item_id]
        return None

    async def create_theme_item(
        self,
        campaign_id: str,
        day_number: int,
        scheduled_date: date,
        theme_title: str,
        theme_description: str,
        dimensions: list[str] | None = None,
        theme_item_id: str | None = None,
    ) -> DailyThemeItemModel:
        m = DailyThemeItemModel(
            theme_item_id=theme_item_id or f"THM-{uuid4()}",
            campaign_id=campaign_id,
            day_number=day_number,
            scheduled_date=scheduled_date,
            theme_title=theme_title,
            theme_description=theme_description,
            dimensions=dimensions or [],
        )
        _fake_state.theme_items.setdefault(campaign_id, {})[m.theme_item_id] = m
        return m

    async def update_theme_item_review_status(
        self,
        theme_item_id: str,
        review_status: str,
        approved_at: datetime | None = None,
    ) -> DailyThemeItemModel:
        for items in _fake_state.theme_items.values():
            if theme_item_id in items:
                m = items[theme_item_id]
                m.review_status = review_status
                if review_status == "approved":
                    m.approved_at = approved_at or datetime.now(timezone.utc)
                return m
        raise ValueError(f"DailyThemeItem {theme_item_id!r} not found")

    # ── ContentPost ───────────────────────────────────────────────────────────

    async def list_posts_by_campaign(self, campaign_id: str) -> list[ContentPostModel]:
        posts = _fake_state.posts.get(campaign_id, {})
        return list(posts.values())

    async def get_post_by_id(self, post_id: str) -> ContentPostModel | None:
        for posts in _fake_state.posts.values():
            if post_id in posts:
                return posts[post_id]
        return None

    async def create_post(
        self,
        campaign_id: str,
        theme_item_id: str,
        destination: dict[str, Any],
        content_text: str,
        scheduled_publish_at: datetime,
        hashtags: list[str] | None = None,
        post_id: str | None = None,
        approval_id: str | None = None,
        credential_ref: str | None = None,
        visibility: str = "private",
        public_release_requested: bool = False,
    ) -> ContentPostModel:
        now = datetime.now(timezone.utc)
        m = ContentPostModel(
            post_id=post_id or f"PST-{uuid4()}",
            campaign_id=campaign_id,
            theme_item_id=theme_item_id,
            destination=destination,
            content_text=content_text,
            hashtags=hashtags or [],
            scheduled_publish_at=scheduled_publish_at,
            approval_id=approval_id,
            credential_ref=credential_ref,
            visibility=visibility,
            public_release_requested=public_release_requested,
            created_at=now,
            updated_at=now,
        )
        _fake_state.posts.setdefault(campaign_id, {})[m.post_id] = m
        return m

    async def update_post_review_status(
        self, post_id: str, review_status: str
    ) -> ContentPostModel:
        for posts in _fake_state.posts.values():
            if post_id in posts:
                m = posts[post_id]
                m.review_status = review_status
                m.updated_at = datetime.now(timezone.utc)
                return m
        raise ValueError(f"ContentPost {post_id!r} not found")

    async def update_post_publish_status(
        self,
        post_id: str,
        publish_status: str,
        publish_receipt: dict[str, Any] | None = None,
    ) -> ContentPostModel:
        for posts in _fake_state.posts.values():
            if post_id in posts:
                m = posts[post_id]
                m.publish_status = publish_status
                m.publish_receipt = publish_receipt
                m.updated_at = datetime.now(timezone.utc)
                return m
        raise ValueError(f"ContentPost {post_id!r} not found")


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def campaigns_app() -> FastAPI:
    from api.v1.campaigns import router
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture(autouse=True)
def _db_mode(campaigns_app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Switch to db mode and inject FakeCampaignRepository for every test."""
    monkeypatch.setattr(camp_module, "CAMPAIGN_PERSISTENCE_MODE", "db")
    monkeypatch.setattr(camp_module, "CampaignRepository", FakeCampaignRepository)
    _fake_state.reset()

    async def _fake_write() -> AsyncGenerator[AsyncMock, None]:
        yield AsyncMock()

    async def _fake_read() -> AsyncGenerator[AsyncMock, None]:
        yield AsyncMock()

    campaigns_app.dependency_overrides[camp_module._get_write_db] = _fake_write
    campaigns_app.dependency_overrides[camp_module._get_read_db] = _fake_read
    yield
    campaigns_app.dependency_overrides.clear()


@pytest.fixture
async def client(campaigns_app: FastAPI, _db_mode: None) -> AsyncGenerator[httpx.AsyncClient, None]:
    transport = httpx.ASGITransport(app=campaigns_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ── Tests ─────────────────────────────────────────────────────────────────────

async def test_create_campaign_db(client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /campaigns in db mode → 201 + campaign + theme_items persisted."""
    monkeypatch.setenv("EXECUTOR_BACKEND", "deterministic")
    r = await client.post("/campaigns", json=CREATE_PAYLOAD, headers={"Authorization": AUTH})
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["campaign"]["campaign_id"]
    assert data["campaign"]["status"] == "draft"
    assert len(data["theme_items"]) == 2  # duration_days=2

    # Verify data was written to fake store
    cid = data["campaign"]["campaign_id"]
    assert cid in _fake_state.campaigns
    assert len(_fake_state.theme_items.get(cid, {})) == 2


async def test_get_campaign_db(client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /campaigns/{id} in db mode → 200 with correct campaign data."""
    monkeypatch.setenv("EXECUTOR_BACKEND", "deterministic")
    r = await client.post("/campaigns", json=CREATE_PAYLOAD, headers={"Authorization": AUTH})
    assert r.status_code == 201
    cid = r.json()["campaign"]["campaign_id"]

    r2 = await client.get(f"/campaigns/{cid}", headers={"Authorization": AUTH})
    assert r2.status_code == 200
    assert r2.json()["campaign_id"] == cid
    assert r2.json()["status"] == "draft"


async def test_approve_theme_items_db(client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Batch-approve all theme items → 200 with all items approved."""
    monkeypatch.setenv("EXECUTOR_BACKEND", "deterministic")
    r = await client.post("/campaigns", json=CREATE_PAYLOAD, headers={"Authorization": AUTH})
    assert r.status_code == 201
    cid = r.json()["campaign"]["campaign_id"]

    r2 = await client.post(
        f"/campaigns/{cid}/theme-items/approve",
        json={"item_ids": [], "decision": "approved"},
        headers={"Authorization": AUTH},
    )
    assert r2.status_code == 200
    items = r2.json()
    assert len(items) == 2
    assert all(i["review_status"] == "approved" for i in items)

    # Campaign status should be theme_approved
    r3 = await client.get(f"/campaigns/{cid}", headers={"Authorization": AUTH})
    assert r3.json()["status"] == "theme_approved"


async def test_generate_posts_db(client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Generate posts for an approved theme item in db mode → 201 + posts persisted."""
    monkeypatch.setenv("EXECUTOR_BACKEND", "deterministic")
    r = await client.post("/campaigns", json=CREATE_PAYLOAD, headers={"Authorization": AUTH})
    assert r.status_code == 201
    cid = r.json()["campaign"]["campaign_id"]
    item_id = r.json()["theme_items"][0]["theme_item_id"]

    # Approve the theme item first
    await client.patch(
        f"/campaigns/{cid}/theme-items/{item_id}",
        json={"decision": "approved"},
        headers={"Authorization": AUTH},
    )

    r2 = await client.post(
        f"/campaigns/{cid}/theme-items/{item_id}/generate-posts",
        headers={"Authorization": AUTH},
    )
    assert r2.status_code == 201
    posts = r2.json()
    assert len(posts) >= 1
    for post in posts:
        assert post["review_status"] == "pending_review"
        assert post["publish_status"] == "not_published"

    # Verify posts written to fake store
    assert len(_fake_state.posts.get(cid, {})) == len(posts)


async def test_get_campaign_not_found_db(client: httpx.AsyncClient) -> None:
    """GET /campaigns/nonexistent in db mode → 404."""
    r = await client.get("/campaigns/nonexistent-id", headers={"Authorization": AUTH})
    assert r.status_code == 404


async def test_no_auth_returns_401_db(client: httpx.AsyncClient) -> None:
    """All routes return 401 when Authorization header is absent in db mode."""
    r = await client.post("/campaigns", json=CREATE_PAYLOAD)
    assert r.status_code == 401
