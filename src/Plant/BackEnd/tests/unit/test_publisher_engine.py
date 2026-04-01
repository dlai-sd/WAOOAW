from __future__ import annotations

from datetime import datetime, timezone

import pytest

from agent_mold.skills.adapters_publish import SimulatedAdapter
from agent_mold.skills.content_models import ContentPost, DestinationRef, PublishInput
from agent_mold.skills.publisher_engine import DestinationRegistry, PublisherEngine


def _make_publish_input(destination_type: str = "simulated") -> PublishInput:
    return PublishInput(
        post=ContentPost(
            post_id="post-sim-001",
            campaign_id="camp-001",
            theme_item_id="theme-001",
            destination=DestinationRef(destination_type=destination_type),
            content_text="Hello WAOOAW",
            hashtags=[],
            scheduled_publish_at=datetime.now(timezone.utc),
        ),
    )


@pytest.mark.asyncio
async def test_publisher_engine_awaits_simulated_adapter():
    registry = DestinationRegistry()
    registry.register("simulated", SimulatedAdapter)

    receipt = await PublisherEngine(registry).publish(_make_publish_input())

    assert receipt.success is True
    assert receipt.destination_type == "simulated"
    assert receipt.platform_post_id.startswith("sim_")
