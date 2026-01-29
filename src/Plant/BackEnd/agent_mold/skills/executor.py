"""Playbook executor.

Chunk C: deterministic executor that demonstrates the pipeline.
Later chunks will integrate AI Explorer for LLM-backed steps.
"""

from __future__ import annotations

from agent_mold.skills.adapters import adapt_instagram, adapt_linkedin
from agent_mold.skills.playbook import (
    CanonicalMessage,
    MarketingMultiChannelOutput,
    SkillExecutionInput,
    SkillExecutionResult,
    SkillPlaybook,
)


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

    variants = [
        adapt_linkedin(canonical),
        adapt_instagram(canonical),
    ]

    return SkillExecutionResult(
        playbook_id=playbook.metadata.playbook_id,
        output=MarketingMultiChannelOutput(canonical=canonical, variants=variants),
        debug={"executor": "deterministic_chunk_c"},
    )
