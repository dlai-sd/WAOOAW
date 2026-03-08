"""LinkedInPublisher — posts to LinkedIn on behalf of the customer (EXEC-ENGINE-001 E7-S3).

Reads per_platform_variants["linkedin"] from previous_step_output (ContentProcessor output).
Decrypts the LinkedIn access token from skill_config.customer_fields.linkedin_access_token.
Posts via the LinkedIn UGC Posts API.

Uses @circuit_breaker(service="linkedin_api").
Access token MUST NOT appear in any log records.

Import and register:
    import linkedin_publisher  # noqa: F401  — triggers register_component()
"""
from __future__ import annotations

import httpx

from components import BaseComponent, ComponentInput, ComponentOutput, register_component
from core.encryption import decrypt_field
from core.logging import PiiMaskingFilter, get_logger
from core.security import circuit_breaker

logger = get_logger(__name__)
logger.addFilter(PiiMaskingFilter())


class LinkedInPublisher(BaseComponent):
    """Publishes a post to LinkedIn using the UGC Posts API."""

    @property
    def component_type(self) -> str:
        return "LinkedInPublisher"

    async def execute(self, input: ComponentInput) -> ComponentOutput:
        variants = (input.previous_step_output or {}).get("per_platform_variants", {})
        variant = variants.get("linkedin", {})
        if not variant:
            return ComponentOutput(
                success=False,
                error_message="No LinkedIn variant in previous output",
            )
        encrypted_key = input.skill_config.get("customer_fields", {}).get(
            "linkedin_access_token", ""
        )
        token = decrypt_field(encrypted_key)
        result = await self._post_to_linkedin(variant["post_text"], token)
        return ComponentOutput(success=True, data=result)

    @circuit_breaker(service="linkedin_api")
    async def _post_to_linkedin(self, text: str, token: str) -> dict:
        """Post to LinkedIn. Access token is never logged."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.linkedin.com/v2/ugcPosts",
                json={
                    "author": "urn:li:person:me",
                    "lifecycleState": "PUBLISHED",
                    "specificContent": {
                        "com.linkedin.ugc.ShareContent": {
                            "shareCommentary": {"text": text},
                            "shareMediaCategory": "NONE",
                        }
                    },
                },
                headers={"Authorization": f"Bearer {token}"},
                timeout=15.0,
            )
            resp.raise_for_status()
            return {
                "platform_post_id": resp.headers.get("x-linkedin-id", ""),
                "published_url": "",
                "platform": "linkedin",
            }


register_component(LinkedInPublisher())
