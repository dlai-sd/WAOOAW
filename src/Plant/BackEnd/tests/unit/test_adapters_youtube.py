from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from agent_mold.skills.adapters_youtube import YouTubeAdapter
from agent_mold.skills.content_models import ContentPost, DestinationRef, PublishInput
from integrations.social.base import SocialPlatformError, SocialPostResult


def _make_publish_input() -> PublishInput:
    return PublishInput(
        post=ContentPost(
            post_id="post-yt-001",
            campaign_id="camp-001",
            theme_item_id="theme-001",
            destination=DestinationRef(
                destination_type="youtube",
                metadata={"customer_id": "cust-001"},
            ),
            content_text="Launch update",
            hashtags=["#WAOOAW"],
            scheduled_publish_at=datetime.now(timezone.utc),
        ),
        credential_ref="cred-yt-001",
        approval_id="APR-001",
    )


@pytest.mark.asyncio
async def test_youtube_adapter_publish_success():
    now = datetime.now(timezone.utc)

    with patch(
        "agent_mold.skills.adapters_youtube.YouTubeClient.post_text",
        new=AsyncMock(
            return_value=SocialPostResult(
                success=True,
                platform="youtube",
                post_id="yt123",
                post_url="https://www.youtube.com/post/yt123",
                posted_at=now,
                raw_response={"id": "yt123"},
            )
        ),
    ):
        receipt = await YouTubeAdapter().publish(_make_publish_input())

    assert receipt.success is True
    assert receipt.platform_post_id == "yt123"
    assert receipt.published_at == now
    assert receipt.raw_response == {
        "id": "yt123",
        "post_url": "https://www.youtube.com/post/yt123",
    }


@pytest.mark.asyncio
async def test_youtube_adapter_publish_failure():
    with patch(
        "agent_mold.skills.adapters_youtube.YouTubeClient.post_text",
        new=AsyncMock(
            side_effect=SocialPlatformError(
                "boom",
                platform="youtube",
                error_code="POST_FAILED",
            )
        ),
    ):
        receipt = await YouTubeAdapter().publish(_make_publish_input())

    assert receipt.success is False
    assert "boom" in (receipt.error or "")
