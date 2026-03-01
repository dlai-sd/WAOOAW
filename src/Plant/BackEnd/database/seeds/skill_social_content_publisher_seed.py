"""Seed: social-content-publisher skill with goal_schema.

PLANT-SKILLS-1 E5-S1

Run: python -m database.seeds.skill_social_content_publisher_seed

Idempotent — upserts by external_id = "social-content-publisher".
"""
from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import select
from core.database import _connector

EXTERNAL_ID = "social-content-publisher"

SOCIAL_CONTENT_PUBLISHER_GOAL_SCHEMA = {
    "fields": [
        {
            "key": "target_audience",
            "type": "string",
            "required": True,
            "label": "Target Audience",
            "placeholder": "e.g. Indian SMB owners aged 30–50",
            "help": "Describe your ideal customer. The agent uses this to tailor every script.",
        },
        {
            "key": "platforms",
            "type": "multiselect",
            "required": True,
            "label": "Platforms to publish on",
            "options": ["facebook", "linkedin", "instagram", "x", "whatsapp"],
            "max_selections_plan_gate": "max_platforms",
            "help": "Select platforms. Maximum determined by your subscription plan.",
        },
        {
            "key": "posts_per_week",
            "type": "integer",
            "required": True,
            "label": "Posts per week",
            "min": 1,
            "max_plan_gate": "posts_per_week",
            "help": "How many posts per week. Maximum determined by your plan.",
        },
        {
            "key": "content_tone",
            "type": "select",
            "required": True,
            "label": "Content tone",
            "options": ["professional", "casual", "educational", "inspirational"],
            "default": "professional",
        },
        {
            "key": "brand_voice_notes",
            "type": "textarea",
            "required": False,
            "label": "Brand voice notes",
            "placeholder": "Any specific phrases, values, or topics to always/never include",
        },
    ],
    "platform_connections_required": True,
    "platform_connection_keys": ["facebook", "linkedin", "instagram", "x", "whatsapp"],
    "approval_workflow": "script_approval",
}


async def seed_social_content_publisher():
    """Upsert social-content-publisher skill with goal_schema."""
    from models.skill import Skill  # local import — avoids top-level SQLAlchemy init race

    print(f"Seeding skill: {EXTERNAL_ID} ...")
    session = await _connector.get_session()
    async with session:
        # Check if already exists by external_id
        result = await session.execute(
            select(Skill).where(Skill.external_id == EXTERNAL_ID)
        )
        existing = result.scalars().first()

        if existing:
            # Update goal_schema if it changed
            existing.goal_schema = SOCIAL_CONTENT_PUBLISHER_GOAL_SCHEMA
            await session.commit()
            print(f"  ↺  Updated goal_schema for existing skill: {EXTERNAL_ID} (id={existing.id})")
        else:
            skill = Skill(
                id=uuid.uuid4(),
                external_id=EXTERNAL_ID,
                entity_type="Skill",
                name="Social Content Publisher",
                description=(
                    "Generates scripts via Grok API, collects approval, produces "
                    "platform-specific content and publishes to Facebook/LinkedIn/"
                    "Instagram/X/WhatsApp on a configured schedule."
                ),
                category="domain_expertise",
                goal_schema=SOCIAL_CONTENT_PUBLISHER_GOAL_SCHEMA,
                governance_agent_id="genesis",
            )
            session.add(skill)
            await session.commit()
            print(f"  ✓  Created skill: {EXTERNAL_ID} (id={skill.id})")

    print("✓ social-content-publisher seed complete")


if __name__ == "__main__":
    asyncio.run(seed_social_content_publisher())
