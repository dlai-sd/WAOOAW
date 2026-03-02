"""AgentSkill — join model for Agent ↔ Skill many-to-many relationship.

PLANT-SKILLS-1 E1-S1
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

from core.database import Base


class AgentSkillModel(Base):
    """Join table linking Agents to Skills.

    One Agent can carry N Skills. One Skill can be attached to M Agents.
    is_primary marks the canonical skill for display purposes.
    ordinal controls display order on the CP agent card.
    """

    __tablename__ = "agent_skills"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("agent_entity.id", ondelete="CASCADE"),
        nullable=False,
    )
    skill_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("skill_entity.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_primary = Column(Boolean, nullable=False, default=False)
    ordinal = Column(Integer, nullable=False, default=0)
    goal_config = Column(JSONB, nullable=True, default=None)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint("agent_id", "skill_id", name="uq_agent_skills_agent_skill"),
        Index("ix_agent_skills_agent_id", "agent_id"),
        Index("ix_agent_skills_skill_id", "skill_id"),
    )
