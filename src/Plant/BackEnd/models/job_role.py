"""
JobRole Entity - Collection of required Skills for a specific role
Inherits from BaseEntity (7 sections)
"""

from sqlalchemy import Column, String, Text, Index, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PG_UUID

from models.base_entity import BaseEntity


class JobRole(BaseEntity):
    """
    Represents a job role that requires a collection of skills.
    
    Inherits all 7 sections from BaseEntity.
    Adds role-specific attributes (name, required_skills, seniority_level).
    
    Example:
        >>> job_role = JobRole(
        ...     name="Senior Python Developer",
        ...     required_skills=[skill_1_id, skill_2_id],
        ...     seniority_level="senior",
        ...     governance_agent_id="genesis"
        ... )
        >>> job_role.validate_self()  # L0/L1 checks
    
    Constraints:
        - name must be unique
        - required_skills cannot be empty
        - seniority_level must be one of: [junior, mid, senior]
        - Genesis certification required for use
    """
    
    __tablename__ = "job_role_entity"
    __mapper_args__ = {"polymorphic_identity": "JobRole"}

    id = Column(PG_UUID(as_uuid=True), ForeignKey("base_entity.id"), primary_key=True)
    
    # JobRole-specific attributes
    name = Column(
        String(255),
        nullable=False,
        unique=True,
        doc="Job role name (e.g., 'Senior Python Developer')"
    )
    
    description = Column(
        Text,
        nullable=False,
        doc="Detailed description of the job role"
    )
    
    required_skills = Column(
        ARRAY(PG_UUID(as_uuid=True)),
        nullable=False,
        default=list,
        doc="Array of required Skill IDs"
    )
    
    seniority_level = Column(
        String(20),
        nullable=False,
        default="mid",
        doc="Seniority level (junior, mid, senior)"
    )
    
    industry_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("industry_entity.id"),
        nullable=True,
        doc="Associated Industry ID (FK)"
    )
    
    # Indexes for performance
    __table_args__ = (
        Index("ix_job_role_name", "name"),
        Index("ix_job_role_seniority_level", "seniority_level"),
        Index("ix_job_role_industry_id", "industry_id"),
    )
