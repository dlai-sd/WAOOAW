"""GoalConfigPump — extracts campaign brief from run_context (EXEC-ENGINE-001 E7-S1).

First step of the Marketing Agent flow. Reads the customer's campaign brief and
platform targets from flow_run.run_context.goal_context, normalises them, and
returns a structured brief_payload for ContentProcessor.

No external HTTP calls — pure context extraction.
Missing campaign_brief → ComponentOutput(success=False).

Import and register:
    import goal_config_pump  # noqa: F401  — triggers register_component()
"""
from __future__ import annotations

from components import BaseComponent, ComponentInput, ComponentOutput, register_component
from core.logging import PiiMaskingFilter, get_logger

logger = get_logger(__name__)
logger.addFilter(PiiMaskingFilter())


class GoalConfigPump(BaseComponent):
    """Normalises the customer campaign brief into a structured brief_payload."""

    @property
    def component_type(self) -> str:
        return "GoalConfigPump"

    async def execute(self, input: ComponentInput) -> ComponentOutput:
        goal_context = input.run_context.get("goal_context", {})
        campaign_brief = goal_context.get("campaign_brief")
        if not campaign_brief:
            return ComponentOutput(success=False, error_message="campaign_brief required")
        content_type = goal_context.get("content_type", "post")
        target_platforms = input.skill_config.get("customer_fields", {}).get(
            "target_platforms", ["linkedin"]
        )
        platform_specs = [{"platform": p, "format": content_type} for p in target_platforms]
        return ComponentOutput(
            success=True,
            data={
                "brief_payload": {
                    "campaign_brief": campaign_brief,
                    "content_type": content_type,
                    "brand_name": input.skill_config.get("customer_fields", {}).get(
                        "brand_name", ""
                    ),
                    "tone": input.skill_config.get("customer_fields", {}).get(
                        "tone", "professional"
                    ),
                    "audience": input.skill_config.get("customer_fields", {}).get(
                        "audience", ""
                    ),
                },
                "platform_specs": platform_specs,
            },
        )


register_component(GoalConfigPump())
