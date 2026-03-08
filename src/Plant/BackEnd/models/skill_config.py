"""SkillConfigModel — separates PP-locked fields from customer-editable fields.

Replaces the single `config` JSONB blob on HiredAgentModel with per-skill
configuration records that carry clear ownership boundaries.

Unique constraint: (hired_instance_id, skill_id)
"""

from sqlalchemy import Column, String, DateTime, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from core.database import Base


class SkillConfigModel(Base):
    """Skill configuration record for a hired agent instance."""

    __tablename__ = "skill_configs"

    id = Column(String, primary_key=True, nullable=False)
    hired_instance_id = Column(String, nullable=False, index=True)
    skill_id = Column(String, nullable=False)
    definition_version_id = Column(String, nullable=False)
    pp_locked_fields = Column(JSONB, nullable=False, default=dict)
    customer_fields = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("hired_instance_id", "skill_id", name="uq_skill_config_per_hire"),
        Index("ix_skill_configs_hired_instance_id", "hired_instance_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<SkillConfigModel(id={self.id!r}, hired_instance_id={self.hired_instance_id!r}, "
            f"skill_id={self.skill_id!r})>"
        )
