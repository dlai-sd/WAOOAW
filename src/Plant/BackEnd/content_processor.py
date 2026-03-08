"""ContentProcessor — calls LLM to generate platform-specific content (EXEC-ENGINE-001 E7-S2).

Takes GoalConfigPump output from previous_step_output, reads
skill_config.pp_locked_fields.brand_voice_model (e.g. gpt-4o), decrypts the
OpenAI API key from skill_config.customer_fields, and calls the LLM to generate
platform-specific post variants.

Uses @circuit_breaker(service="openai_api") on the LLM call.
API key MUST NOT appear in any log records.

Import and register:
    import content_processor  # noqa: F401  — triggers register_component()
"""
from __future__ import annotations

import httpx

from components import BaseComponent, ComponentInput, ComponentOutput, register_component
from core.encryption import decrypt_field
from core.logging import PiiMaskingFilter, get_logger
from core.security import circuit_breaker

logger = get_logger(__name__)
logger.addFilter(PiiMaskingFilter())


class ContentProcessor(BaseComponent):
    """Calls an LLM to generate platform-specific post variants."""

    @property
    def component_type(self) -> str:
        return "ContentProcessor"

    async def execute(self, input: ComponentInput) -> ComponentOutput:
        brief_payload = (input.previous_step_output or {}).get("brief_payload", {})
        platform_specs = (input.previous_step_output or {}).get("platform_specs", [])
        model = input.skill_config.get("pp_locked_fields", {}).get(
            "brand_voice_model", "gpt-4o-mini"
        )
        encrypted_key = input.skill_config.get("customer_fields", {}).get("openai_api_key", "")
        api_key = decrypt_field(encrypted_key)
        variants: dict = {}
        for spec in platform_specs:
            platform = spec["platform"]
            prompt = self._build_prompt(brief_payload, spec)
            text = await self._call_llm(prompt, model, api_key)
            variants[platform] = {
                "post_text": text,
                "hashtags": [],
                "format": spec["format"],
            }
        return ComponentOutput(
            success=True,
            data={
                "post_text": list(variants.values())[0]["post_text"] if variants else "",
                "hashtags": [],
                "per_platform_variants": variants,
            },
        )

    def _build_prompt(self, brief: dict, spec: dict) -> str:
        return (
            f"Write a {spec['format']} for {spec['platform']} about: "
            f"{brief.get('campaign_brief', '')}. "
            f"Brand: {brief.get('brand_name', '')}. "
            f"Tone: {brief.get('tone', 'professional')}. "
            f"Audience: {brief.get('audience', 'general')}."
        )

    @circuit_breaker(service="openai_api")
    async def _call_llm(self, prompt: str, model: str, api_key: str) -> str:
        """Call OpenAI chat completions. API key is never logged."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500,
                },
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=30.0,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]


register_component(ContentProcessor())
