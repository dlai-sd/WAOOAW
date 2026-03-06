"""Phase 1 publish adapters.

SimulatedAdapter: always succeeds, returns a fake receipt.
Used for all destinations until real OAuth adapters are built.

To add a real adapter:
1. Create adapters_<platform>.py
2. class <Platform>Adapter(DestinationAdapter): DESTINATION_TYPE = "<platform>"
3. Register in publisher_engine.py build_default_registry()
"""
from __future__ import annotations

from datetime import datetime, timezone

from agent_mold.skills.content_models import PublishInput, PublishReceipt
from agent_mold.skills.publisher_engine import DestinationAdapter


class SimulatedAdapter(DestinationAdapter):
    """Simulates a successful publish. Phase 1 stand-in for all real platforms.

    Returns a deterministic fake platform_post_id so tests are reproducible.
    Does NOT make any external HTTP calls.
    """
    DESTINATION_TYPE = "simulated"

    def publish(self, inp: PublishInput) -> PublishReceipt:
        fake_id = f"sim_{inp.post.post_id[:8]}"
        return PublishReceipt(
            post_id=inp.post.post_id,
            destination_type=inp.post.destination.destination_type,
            success=True,
            platform_post_id=fake_id,
            published_at=datetime.now(timezone.utc),
            raw_response={"simulated": True, "post_id": fake_id},
        )
