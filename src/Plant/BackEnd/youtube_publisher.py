"""YouTubePublisher — posts to YouTube on behalf of the customer (EXEC-ENGINE-001 E7-S3).

Reads per_platform_variants["youtube"] from previous_step_output (ContentProcessor output).
Decrypts the YouTube API key from skill_config.customer_fields.youtube_api_key.
Posts a community post (or creates a video description) via the YouTube Data API v3.

Uses @circuit_breaker(service="youtube_api").
API key MUST NOT appear in any log records.

Import and register:
    import youtube_publisher  # noqa: F401  — triggers register_component()
"""
from __future__ import annotations

import httpx

from components import BaseComponent, ComponentInput, ComponentOutput, register_component
from core.encryption import decrypt_field
from core.logging import PiiMaskingFilter, get_logger
from core.security import circuit_breaker

logger = get_logger(__name__)
logger.addFilter(PiiMaskingFilter())


class YouTubePublisher(BaseComponent):
    """Publishes a community post to YouTube using the YouTube Data API v3."""

    @property
    def component_type(self) -> str:
        return "YouTubePublisher"

    async def execute(self, input: ComponentInput) -> ComponentOutput:
        variants = (input.previous_step_output or {}).get("per_platform_variants", {})
        variant = variants.get("youtube", {})
        if not variant:
            return ComponentOutput(
                success=False,
                error_message="No YouTube variant in previous output",
            )
        encrypted_key = input.skill_config.get("customer_fields", {}).get(
            "youtube_api_key", ""
        )
        api_key = decrypt_field(encrypted_key)
        result = await self._post_to_youtube(variant["post_text"], api_key)
        return ComponentOutput(success=True, data=result)

    @circuit_breaker(service="youtube_api")
    async def _post_to_youtube(self, text: str, api_key: str) -> dict:
        """Post to YouTube community. API key is never logged."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://www.googleapis.com/youtube/v3/communityPosts",
                json={
                    "snippet": {
                        "text": text,
                    }
                },
                params={"part": "snippet", "key": api_key},
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "platform_post_id": data.get("id", ""),
                "published_url": "",
                "platform": "youtube",
            }


register_component(YouTubePublisher())
