"""ContentCreatorSkill — generates DailyThemeList + ContentPosts.

EXECUTOR_BACKEND env var controls the engine:
  "grok"          → Grok-3 API (requires XAI_API_KEY)
  "deterministic" → template-based, no API calls (default)
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta, timezone
from typing import List

from agent_mold.skills.adapters import (
    adapt_facebook,
    adapt_instagram,
    adapt_linkedin,
    adapt_whatsapp,
    adapt_youtube,
)
from agent_mold.skills.content_models import (
    Campaign,
    ChannelName,
    ContentCreatorOutput,
    ContentPost,
    DailyThemeItem,
    PostGeneratorInput,
    PostGeneratorOutput,
    estimate_cost,
)
from agent_mold.processor import BaseProcessor, ProcessorInput, ProcessorOutput
from agent_mold.skills.playbook import CanonicalMessage

# Channel → adapter map (add new channels here when adapters are created)
_CHANNEL_ADAPTER_MAP = {
    ChannelName.LINKEDIN: adapt_linkedin,
    ChannelName.INSTAGRAM: adapt_instagram,
    ChannelName.YOUTUBE: adapt_youtube,
    ChannelName.FACEBOOK: adapt_facebook,
    ChannelName.WHATSAPP: adapt_whatsapp,
}

_CONTENT_DIMENSIONS = [
    "social proof", "education", "inspiration", "product demo",
    "customer story", "behind the scenes", "FAQ", "trend commentary",
    "comparison", "how-to", "quick tip", "milestone celebration",
]


def _executor_backend() -> str:
    return os.getenv("EXECUTOR_BACKEND", "deterministic").lower()


class ContentCreatorSkill(BaseProcessor):
    """Plug-and-play skill. Register against any agent that needs content creation."""

    SKILL_ID = "content.creator.v1"

    async def process(self, input_data: ProcessorInput, hook_bus: "HookBus") -> ProcessorOutput:  # type: ignore[name-defined]
        """BaseProcessor ABC implementation — adapter shim for content creation.

        Unpacks ProcessorInput.goal_config and returns a ProcessorOutput.
        Full content creation (theme lists, posts) is driven by generate_theme_list()
        and generate_posts_for_theme(); this shim enables the typed
        GoalSchedulerService dispatch path when construct bindings are wired.
        """
        cfg = input_data.goal_config
        return ProcessorOutput(
            result={
                "status": "content_creation_dispatched",
                "processor": self.processor_type(),
                "goal_config_keys": sorted(cfg.keys()),
            },
            metadata={"processor_type": self.processor_type()},
            correlation_id=input_data.correlation_id,
        )

    def generate_theme_list(
        self,
        campaign: Campaign,
        analytics_context: str = "",
        brand_voice_context: str = "",
    ) -> ContentCreatorOutput:
        """Step 1: Generate DailyThemeItems for the full campaign duration."""
        brief = campaign.brief
        model_used = "grok-3-latest" if _executor_backend() == "grok" else "deterministic"
        cost = estimate_cost(brief, model_used=model_used)

        if _executor_backend() == "grok":
            theme_items = self._grok_theme_list(
                campaign,
                analytics_context=analytics_context,
                brand_voice_context=brand_voice_context,
            )
        else:
            theme_items = self._deterministic_theme_list(
                campaign,
                brand_voice_context=brand_voice_context,
            )

        return ContentCreatorOutput(
            campaign_id=campaign.campaign_id,
            theme_items=theme_items,
            cost_estimate=cost,
        )

    def generate_posts_for_theme(self, inp: PostGeneratorInput) -> PostGeneratorOutput:
        """Step 2: Generate ContentPosts for one approved DailyThemeItem."""
        if _executor_backend() == "grok":
            posts = self._grok_posts(inp)
        else:
            posts = self._deterministic_posts(inp)
        return PostGeneratorOutput(theme_item_id=inp.theme_item.theme_item_id, posts=posts)

    # ── Deterministic engine ──────────────────────────────────────────────────

    def _deterministic_theme_list(
        self,
        campaign: Campaign,
        brand_voice_context: str = "",
    ) -> List[DailyThemeItem]:
        brief = campaign.brief
        items: List[DailyThemeItem] = []
        for day in range(brief.duration_days):
            day_date = brief.start_date + timedelta(days=day)
            dim = _CONTENT_DIMENSIONS[day % len(_CONTENT_DIMENSIONS)]
            voice_note = f" Voice: {brand_voice_context}." if brand_voice_context else ""
            items.append(DailyThemeItem(
                campaign_id=campaign.campaign_id,
                day_number=day + 1,
                scheduled_date=day_date,
                theme_title=f"Day {day+1}: {brief.theme} — {dim.title()}",
                theme_description=(
                    f"Focus: {dim}. Brand: {brief.brand_name or 'WAOOAW'}. "
                    f"Audience: {brief.audience or 'general'}. Tone: {brief.tone}."
                    f"{voice_note}"
                ),
                dimensions=[dim],
            ))
        return items

    def _deterministic_posts(self, inp: PostGeneratorInput) -> List[ContentPost]:
        brief = inp.campaign.brief
        theme = inp.theme_item
        posts: List[ContentPost] = []

        canonical = CanonicalMessage(
            theme=theme.theme_title,
            core_message=f"{theme.theme_title}. {theme.theme_description}",
            call_to_action="Try WAOOAW — agents that earn your business.",
            key_points=theme.dimensions,
            hashtags=["WAOOAW", (brief.brand_name or "WAH").replace(" ", ""), "AIAgents"],
        )

        for dest in brief.destinations:
            channel_name = _destination_to_channel(dest.destination_type)
            adapter = _CHANNEL_ADAPTER_MAP.get(channel_name)
            if adapter is None:
                text = canonical.core_message
                hashtags = canonical.hashtags
            else:
                variant = adapter(canonical)
                text = variant.text
                hashtags = variant.hashtags

            scheduled = _compute_schedule(
                base_date=theme.scheduled_date,
                preferred_hours=brief.schedule.preferred_hours_utc,
                post_index=len(posts),
            )
            posts.append(ContentPost(
                campaign_id=inp.campaign.campaign_id,
                theme_item_id=theme.theme_item_id,
                destination=dest,
                content_text=text,
                hashtags=hashtags,
                scheduled_publish_at=scheduled,
            ))
        return posts

    # ── Grok engine ───────────────────────────────────────────────────────────

    def _grok_theme_list(
        self,
        campaign: Campaign,
        analytics_context: str = "",
        brand_voice_context: str = "",
    ) -> List[DailyThemeItem]:
        from agent_mold.skills.grok_client import get_grok_client, grok_complete
        client = get_grok_client()
        brief = campaign.brief

        system = (
            "You are an expert content strategist. "
            "Return ONLY a valid JSON array — no markdown, no explanation."
        )
        if brand_voice_context:
            system += (
                f"\n\nBrand voice guidelines (match this tone and style):\n"
                f"{brand_voice_context}"
            )
        user = (
            f"Create a {brief.duration_days}-day content calendar for the theme: "
            f"'{brief.theme}'. Brand: '{brief.brand_name}'. Audience: '{brief.audience}'. "
            f"Platforms: {[d.destination_type for d in brief.destinations]}. "
            f"Tone: {brief.tone}. Language: {brief.language}.\n"
            f"Return a JSON array of {brief.duration_days} objects, each with keys: "
            f"theme_title (string), theme_description (string), dimensions (list of strings). "
            f"Start date: {brief.start_date.isoformat()}."
        )
        if analytics_context:
            user += (
                "\n\nPast performance insights (use these to improve content):\n"
                f"{analytics_context}"
            )
        raw = grok_complete(client, system, user)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # Graceful fallback to deterministic if Grok returns non-JSON
            return self._deterministic_theme_list(
                campaign,
                brand_voice_context=brand_voice_context,
            )

        items: List[DailyThemeItem] = []
        for i, item in enumerate(data[: brief.duration_days]):
            items.append(DailyThemeItem(
                campaign_id=campaign.campaign_id,
                day_number=i + 1,
                scheduled_date=brief.start_date + timedelta(days=i),
                theme_title=item.get("theme_title", f"Day {i+1}"),
                theme_description=item.get("theme_description", ""),
                dimensions=item.get("dimensions", []),
            ))
        return items

    def _grok_posts(self, inp: PostGeneratorInput) -> List[ContentPost]:
        from agent_mold.skills.grok_client import get_grok_client, grok_complete
        client = get_grok_client()
        brief = inp.campaign.brief
        theme = inp.theme_item
        posts: List[ContentPost] = []

        for dest in brief.destinations:
            system = (
                "You are a professional social media copywriter. "
                "Write ready-to-publish content. Return ONLY the post text, no explanation."
            )
            user = (
                f"Platform: {dest.destination_type}. "
                f"Theme: {theme.theme_title}. Context: {theme.theme_description}. "
                f"Brand: {brief.brand_name}. Audience: {brief.audience}. Tone: {brief.tone}. "
                f"Language: {brief.language}. "
                f"Include 3-5 relevant hashtags at the end."
            )
            text = grok_complete(client, system, user, temperature=0.8)
            scheduled = _compute_schedule(
                base_date=theme.scheduled_date,
                preferred_hours=brief.schedule.preferred_hours_utc,
                post_index=len(posts),
            )
            posts.append(ContentPost(
                campaign_id=inp.campaign.campaign_id,
                theme_item_id=theme.theme_item_id,
                destination=dest,
                content_text=text,
                scheduled_publish_at=scheduled,
            ))
        return posts


# ── Helpers ───────────────────────────────────────────────────────────────────

def _destination_to_channel(destination_type: str) -> ChannelName:
    """Map destination_type string to ChannelName enum. Defaults to LINKEDIN."""
    mapping = {
        "linkedin": ChannelName.LINKEDIN,
        "instagram": ChannelName.INSTAGRAM,
        "youtube": ChannelName.YOUTUBE,
        "facebook": ChannelName.FACEBOOK,
        "whatsapp": ChannelName.WHATSAPP,
        "x": ChannelName.LINKEDIN,  # X uses LinkedIn-style text for now
        "twitter": ChannelName.LINKEDIN,
        "simulated": ChannelName.LINKEDIN,
    }
    return mapping.get(destination_type.lower(), ChannelName.LINKEDIN)


def _compute_schedule(
    *,
    base_date: date,
    preferred_hours: List[int],
    post_index: int,
) -> datetime:
    hour = preferred_hours[post_index % len(preferred_hours)] if preferred_hours else 9
    return datetime(base_date.year, base_date.month, base_date.day, hour, 0, 0, tzinfo=timezone.utc)
