"""
Team, Agent, Industry entities
Inherits from BaseEntity (7 sections)
"""

from sqlalchemy import Column, String, Text, Index
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PG_UUID, VECTOR
import uuid

from models.base_entity import BaseEntity


class Team(BaseEntity):
    """Team entity - collection of agents with unified skill + job role."""
    __tablename__ = "team_entity"
    entity_type = "Team"
    
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=False)
    agents = Column(ARRAY(PG_UUID(as_uuid=True)), nullable=False, default=list)
    job_role_id = Column(PG_UUID(as_uuid=True), nullable=False)
    industry_id = Column(PG_UUID(as_uuid=True), nullable=True)
    
    __table_args__ = (
        Index("ix_team_name", "name"),
        Index("ix_team_job_role_id", "job_role_id"),
    )


class Agent(BaseEntity):
    """Agent entity - individual AI workforce member with Skill + JobRole + Team."""
    __tablename__ = "agent_entity"
    entity_type = "Agent"
    
    name = Column(String(255), nullable=False, unique=True)
    skill_id = Column(PG_UUID(as_uuid=True), nullable=False)
    job_role_id = Column(PG_UUID(as_uuid=True), nullable=False)
    team_id = Column(PG_UUID(as_uuid=True), nullable=True)
    industry_id = Column(PG_UUID(as_uuid=True), nullable=False)
    
    __table_args__ = (
        Index("ix_agent_name", "name"),
        Index("ix_agent_industry_id", "industry_id"),
    )


class Industry(BaseEntity):
    """Industry entity - market segment with agents."""
    __tablename__ = "industry_entity"
    entity_type = "Industry"
    
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=False)
    agents = Column(ARRAY(PG_UUID(as_uuid=True)), nullable=False, default=list)
    embedding_384 = Column(VECTOR(384), nullable=True)
    
    __table_args__ = (
        Index("ix_industry_name", "name"),
        Index("ix_industry_embedding", "embedding_384", postgresql_using="ivfflat", postgresql_ops={"embedding_384": "vector_cosine_ops"}),
    )
