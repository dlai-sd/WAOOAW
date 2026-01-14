"""
Team, Agent, Industry entities
Inherits from BaseEntity (7 sections)
"""

from sqlalchemy import Column, String, Text, Index, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PG_UUID
from pgvector.sqlalchemy import Vector

from models.base_entity import BaseEntity


class Team(BaseEntity):
    """Team entity - collection of agents with unified skill + job role."""
    __tablename__ = "team_entity"
    __mapper_args__ = {"polymorphic_identity": "Team"}

    id = Column(PG_UUID(as_uuid=True), ForeignKey("base_entity.id"), primary_key=True)
    
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=False)
    agents = Column(ARRAY(PG_UUID(as_uuid=True)), nullable=False, default=list)
    job_role_id = Column(PG_UUID(as_uuid=True), ForeignKey("job_role_entity.id"), nullable=False)
    industry_id = Column(PG_UUID(as_uuid=True), ForeignKey("industry_entity.id"), nullable=True)
    
    __table_args__ = (
        Index("ix_team_name", "name"),
        Index("ix_team_job_role_id", "job_role_id"),
    )


class Agent(BaseEntity):
    """Agent entity - individual AI workforce member with Skill + JobRole + Team."""
    __tablename__ = "agent_entity"
    __mapper_args__ = {"polymorphic_identity": "Agent"}
    
    id = Column(PG_UUID(as_uuid=True), ForeignKey("base_entity.id"), primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    skill_id = Column(PG_UUID(as_uuid=True), ForeignKey("skill_entity.id"), nullable=False)
    job_role_id = Column(PG_UUID(as_uuid=True), ForeignKey("job_role_entity.id"), nullable=False)
    team_id = Column(PG_UUID(as_uuid=True), ForeignKey("team_entity.id"), nullable=True)
    industry_id = Column(PG_UUID(as_uuid=True), ForeignKey("industry_entity.id"), nullable=False)
    
    __table_args__ = (
        Index("ix_agent_name", "name"),
        Index("ix_agent_industry_id", "industry_id"),
    )


class Industry(BaseEntity):
    """Industry entity - market segment with agents."""
    __tablename__ = "industry_entity"
    __mapper_args__ = {"polymorphic_identity": "Industry"}
    
    id = Column(PG_UUID(as_uuid=True), ForeignKey("base_entity.id"), primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=False)
    agents = Column(ARRAY(PG_UUID(as_uuid=True)), nullable=False, default=list)
    embedding_384 = Column(Vector(384), nullable=True)
    
    __table_args__ = (
        Index("ix_industry_name", "name"),
        Index("ix_industry_embedding", "embedding_384", postgresql_using="ivfflat", postgresql_ops={"embedding_384": "vector_cosine_ops"}),
    )
