from __future__ import annotations

from datetime import datetime, timezone

import pytest

from api.v1 import agent_catalog
from models.agent_catalog import AgentCatalogReleaseModel


class _DummyDB:
    async def commit(self) -> None:
        return None


def _release(*, approved: bool, lifecycle_state: str) -> AgentCatalogReleaseModel:
    now = datetime.now(timezone.utc)
    return AgentCatalogReleaseModel(
        release_id="CAR-1",
        agent_id="AGT-MKT-DMA-001",
        agent_type_id="marketing.digital_marketing.v1",
        internal_definition_version_id="1.0.0",
        external_catalog_version="v1",
        public_name="Digital Marketing Agent",
        short_description="Hire-ready DMA release",
        industry_name="Marketing",
        job_role_label="Digital Marketing Strategist",
        monthly_price_inr=12000,
        trial_days=7,
        allowed_durations=["monthly", "quarterly"],
        supported_channels=["youtube"],
        approval_mode="manual_review",
        lifecycle_state=lifecycle_state,
        approved_for_new_hire=approved,
        retired_from_catalog_at=None,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_list_catalog_agents_returns_live_releases(monkeypatch):
    live_release = _release(approved=True, lifecycle_state="live_on_cp")

    class FakeRepo:
        def __init__(self, _db):
            pass

        async def list_live_releases(self):
            return [live_release]

    monkeypatch.setattr(agent_catalog, "AgentCatalogRepository", FakeRepo)

    results = await agent_catalog.list_catalog_agents(db=object())

    assert len(results) == 1
    assert results[0].id == "AGT-MKT-DMA-001"
    assert results[0].approved_for_new_hire is True
    assert results[0].lifecycle_state == "live_on_cp"


@pytest.mark.asyncio
async def test_approve_catalog_agent_bootstraps_release_when_missing(monkeypatch):
    draft_release = _release(approved=False, lifecycle_state="draft")
    live_release = _release(approved=True, lifecycle_state="live_on_cp")

    class FakeRepo:
        def __init__(self, _db):
            self.created = None

        async def get_latest_for_agent_id(self, _agent_id):
            return None

        async def upsert_release(self, **kwargs):
            self.created = kwargs
            return draft_release

        async def approve_release(self, _release_id):
            return live_release

    monkeypatch.setattr(agent_catalog, "AgentCatalogRepository", FakeRepo)
    async def _fake_resolve_agent_listing_row(*, agent_id, db):
        return {
            "agent_id": agent_id,
            "name": "Digital Marketing Agent",
            "industry_name": "Marketing",
            "job_role_label": "Digital Marketing Strategist",
        }

    async def _fake_resolve_definition_version(*, db, agent_type_id):
        return "1.0.0"

    monkeypatch.setattr(agent_catalog, "_resolve_agent_listing_row", _fake_resolve_agent_listing_row)
    monkeypatch.setattr(agent_catalog, "_resolve_definition_version", _fake_resolve_definition_version)

    result = await agent_catalog.approve_catalog_agent("AGT-MKT-DMA-001", db=_DummyDB())

    assert result.id == "AGT-MKT-DMA-001"
    assert result.agent_type_id == "marketing.digital_marketing.v1"
    assert result.lifecycle_state == "live_on_cp"
    assert result.approved_for_new_hire is True
