"""YouTube publish adapter — wraps YouTubeClient for the unified PublisherEngine.

Converts PublishInput → YouTubeClient.post_text() → PublishReceipt.
All eligibility checks (approval_id, credential_ref, visibility) are handled
by PublisherEngine._check_publish_eligibility() — do NOT duplicate them here.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from agent_mold.skills.content_models import PublishInput, PublishReceipt
from agent_mold.skills.publisher_engine import DestinationAdapter
from integrations.social.youtube_client import YouTubeClient

logger = logging.getLogger(__name__)


class YouTubeAdapter(DestinationAdapter):
    """Publishes to YouTube via the real YouTubeClient.

    Delegates to YouTubeClient.post_text() for community posts.
    credential_ref and customer_id are extracted from PublishInput metadata.
    """

    DESTINATION_TYPE = "youtube"

    async def publish(self, inp: PublishInput) -> PublishReceipt:
        metadata = inp.post.destination.metadata or {}
        customer_id = metadata.get("customer_id", "")
        credential_ref = inp.credential_ref or metadata.get("credential_ref", "")

        client = YouTubeClient(customer_id=customer_id)
        try:
            result = await client.post_text(
                credential_ref=credential_ref,
                text=inp.post.content_text,
            )
            raw_response = dict(result.raw_response or {})
            if result.post_url:
                raw_response.setdefault("post_url", result.post_url)
            return PublishReceipt(
                post_id=inp.post.post_id,
                destination_type=self.DESTINATION_TYPE,
                success=result.success,
                platform_post_id=result.post_id,
                published_at=result.posted_at or datetime.now(timezone.utc),
                raw_response=raw_response or None,
            )
        except Exception as exc:
            logger.error("YouTubeAdapter.publish failed: %s", exc, exc_info=True)
            return PublishReceipt(
                post_id=inp.post.post_id,
                destination_type=self.DESTINATION_TYPE,
                success=False,
                error=str(exc),
            )
