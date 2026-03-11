"""Tests for Publisher Engine — PLANT-CONTENT-1 Iteration 3, Epic E5.

E5-S1-T1: SimulatedAdapter publish → success=True, platform_post_id set
E5-S1-T2: Unregistered destination type → success=False, no exception raised
E5-S1-T3: registry.list_registered() includes "simulated"
E5-S1-T4: SimulatedAdapter().estimate_cost(inp) == 0.0

Run:
    docker compose -f docker-compose.test.yml run plant-test \\
      pytest src/Plant/BackEnd/tests/test_publisher_engine.py -v \\
      --cov=src/Plant/BackEnd/agent_mold/skills/publisher_engine \\
      --cov=src/Plant/BackEnd/agent_mold/skills/adapters_publish \\
      --cov-fail-under=85
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from agent_mold.skills.adapters_publish import SimulatedAdapter
from agent_mold.skills.content_models import (
    CampaignBrief,
    ContentPost,
    DestinationRef,
    PublishInput,
    PublishStatus,
    ReviewStatus,
)
from agent_mold.skills.publisher_engine import (
    DestinationRegistry,
    PublisherEngine,
    build_default_registry,
    default_engine,
    default_registry,
)


# ─── Fixtures ─────────────────────────────────────────────────────────────────

def _make_post(destination_type: str = "simulated") -> ContentPost:
    return ContentPost(
        campaign_id="campaign-001",
        theme_item_id="theme-item-001",
        destination=DestinationRef(destination_type=destination_type),
        content_text="Test post content for WAOOAW.",
        scheduled_publish_at=datetime(2026, 3, 6, 9, 0, 0, tzinfo=timezone.utc),
    )


def _make_publish_input(destination_type: str = "simulated") -> PublishInput:
    return PublishInput(post=_make_post(destination_type))


# ─── E5-S1-T1: SimulatedAdapter publish → success=True, platform_post_id set ──

@pytest.mark.unit
def test_simulated_adapter_publish_returns_success():
    """E5-S1-T1: SimulatedAdapter.publish returns PublishReceipt with success=True and platform_post_id set."""
    adapter = SimulatedAdapter()
    inp = _make_publish_input("simulated")

    receipt = adapter.publish(inp)

    assert receipt.success is True
    assert receipt.platform_post_id is not None
    assert receipt.platform_post_id.startswith("sim_")
    assert receipt.post_id == inp.post.post_id
    assert receipt.destination_type == "simulated"
    assert receipt.published_at is not None
    assert receipt.error is None


# ─── E5-S1-T2: Unregistered destination → success=False, no exception ─────────

@pytest.mark.unit
def test_publish_engine_unregistered_destination_returns_failure_without_exception():
    """E5-S1-T2: PublisherEngine.publish with unknown destination_type returns success=False, no exception."""
    registry = DestinationRegistry()
    engine = PublisherEngine(registry)

    inp = _make_publish_input("unknown_platform")
    receipt = engine.publish(inp)

    assert receipt.success is False
    assert receipt.error is not None
    assert "unknown_platform" in receipt.error
    assert receipt.post_id == inp.post.post_id


# ─── E5-S1-T3: registry.list_registered() includes "simulated" ────────────────

@pytest.mark.unit
def test_default_registry_includes_simulated():
    """E5-S1-T3: default_registry.list_registered() includes 'simulated'."""
    registered = default_registry.list_registered()
    assert "simulated" in registered


@pytest.mark.unit
def test_default_registry_is_registered_simulated():
    """E5-S1-T3 (extended): default_registry.is_registered('simulated') returns True."""
    assert default_registry.is_registered("simulated") is True


# ─── E5-S1-T4: SimulatedAdapter.estimate_cost == 0.0 ─────────────────────────

@pytest.mark.unit
def test_simulated_adapter_estimate_cost_is_zero():
    """E5-S1-T4: SimulatedAdapter().estimate_cost(inp) == 0.0"""
    adapter = SimulatedAdapter()
    inp = _make_publish_input("simulated")

    cost = adapter.estimate_cost(inp)

    assert cost == 0.0


# ─── Additional coverage ──────────────────────────────────────────────────────

@pytest.mark.unit
def test_default_engine_publishes_simulated_post():
    """default_engine.publish with simulated destination returns success=True."""
    inp = _make_publish_input("simulated")
    receipt = default_engine.publish(inp)

    assert receipt.success is True
    assert receipt.platform_post_id is not None


@pytest.mark.unit
def test_default_registry_includes_x_and_twitter_aliases():
    """default_registry registers 'x' and 'twitter' as aliases for SimulatedAdapter."""
    assert default_registry.is_registered("x") is True
    assert default_registry.is_registered("twitter") is True


@pytest.mark.unit
def test_default_registry_includes_youtube():
    assert default_registry.is_registered("youtube") is True


@pytest.mark.unit
def test_youtube_publish_requires_approval_and_credential_ref():
    post = _make_post("youtube")
    engine = PublisherEngine(build_default_registry())

    missing_approval = engine.publish(PublishInput(post=post, credential_ref="secret-ref"))
    assert missing_approval.success is False
    assert missing_approval.error == "approval_required_for_youtube_publish"

    missing_credential = engine.publish(PublishInput(post=post, approval_id="APR-1"))
    assert missing_credential.success is False
    assert missing_credential.error == "credential_ref_required_for_youtube_publish"


@pytest.mark.unit
def test_youtube_public_release_requires_explicit_customer_action():
    post = _make_post("youtube")
    engine = PublisherEngine(build_default_registry())

    denied = engine.publish(
        PublishInput(
            post=post,
            approval_id="APR-1",
            credential_ref="secret-ref",
            visibility="public",
            public_release_requested=False,
        )
    )
    assert denied.success is False
    assert denied.error == "public_release_requires_explicit_customer_action"

    allowed = engine.publish(
        PublishInput(
            post=post,
            approval_id="APR-1",
            credential_ref="secret-ref",
            visibility="public",
            public_release_requested=True,
        )
    )
    assert allowed.success is True


@pytest.mark.unit
def test_build_default_registry_returns_fresh_registry():
    """build_default_registry() returns a new independent DestinationRegistry."""
    r1 = build_default_registry()
    r2 = build_default_registry()
    assert r1 is not r2
    assert r1.is_registered("simulated")
    assert r2.is_registered("simulated")


@pytest.mark.unit
def test_publisher_engine_catches_adapter_exception():
    """PublisherEngine catches exceptions raised inside adapters and returns failure receipt."""
    class BrokenAdapter(SimulatedAdapter):
        DESTINATION_TYPE = "broken"

        def publish(self, inp: PublishInput):
            raise RuntimeError("Simulated publish failure")

    registry = DestinationRegistry()
    registry.register("broken", BrokenAdapter)
    engine = PublisherEngine(registry)

    inp = _make_publish_input("broken")
    receipt = engine.publish(inp)

    assert receipt.success is False
    assert "Simulated publish failure" in (receipt.error or "")


@pytest.mark.unit
def test_registry_register_is_case_insensitive():
    """DestinationRegistry matches destination_type case-insensitively."""
    registry = DestinationRegistry()
    registry.register("LinkedIn", SimulatedAdapter)

    assert registry.is_registered("linkedin") is True
    assert registry.is_registered("LINKEDIN") is True
    assert registry.get("LinkedIn") is SimulatedAdapter
