"""Playbook executor.

Chunk C: deterministic executor that demonstrates the pipeline.
Later chunks will integrate AI Explorer for LLM-backed steps.
"""

from __future__ import annotations

from agent_mold.skills.adapters import (
    adapt_facebook,
    adapt_instagram,
    adapt_linkedin,
    adapt_whatsapp,
    adapt_youtube,
)
from agent_mold.skills.playbook import (
    CanonicalMessage,
    ChannelName,
    MarketingMultiChannelOutput,
    SkillExecutionInput,
    SkillExecutionResult,
    SkillPlaybook,
)


def _dedupe_preserve_order(channels: list[ChannelName]) -> list[ChannelName]:
    seen: set[ChannelName] = set()
    ordered: list[ChannelName] = []
    for channel in channels:
        if channel in seen:
            continue
        seen.add(channel)
        ordered.append(channel)
    return ordered


def execute_marketing_multichannel_v1(playbook: SkillPlaybook, inp: SkillExecutionInput) -> SkillExecutionResult:
    # Minimal deterministic canonical message (no LLM yet).
    theme = inp.theme.strip()
    brand = inp.brand_name.strip()

    offer = f" Offer: {inp.offer}." if inp.offer else ""
    location = f" Location: {inp.location}." if inp.location else ""

    canonical = CanonicalMessage(
        theme=theme,
        core_message=f"{brand}: {theme}.{offer}{location}".strip(),
        call_to_action="Tell us what you want next and we’ll tailor it.",
        key_points=[p for p in [inp.audience, inp.tone, inp.language] if p],
        hashtags=["WAOOAW", brand.replace(" ", ""), "SmallBusiness"],
    )

    adapter_map = {
        ChannelName.YOUTUBE: adapt_youtube,
        ChannelName.INSTAGRAM: adapt_instagram,
        ChannelName.FACEBOOK: adapt_facebook,
        ChannelName.LINKEDIN: adapt_linkedin,
        ChannelName.WHATSAPP: adapt_whatsapp,
    }

    default_channels = [
        ChannelName.YOUTUBE,
        ChannelName.INSTAGRAM,
        ChannelName.FACEBOOK,
        ChannelName.LINKEDIN,
        ChannelName.WHATSAPP,
    ]

    channels = default_channels if inp.channels is None else _dedupe_preserve_order(list(inp.channels))
    variants = [adapter_map[channel](canonical) for channel in channels]

    return SkillExecutionResult(
        playbook_id=playbook.metadata.playbook_id,
        output=MarketingMultiChannelOutput(canonical=canonical, variants=variants),
        debug={"executor": "deterministic_chunk_c"},
    )
