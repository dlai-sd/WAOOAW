"""AgentTypeDefinition DB model for persisting agent type schemas and goal templates.

Phase-1 approach: Store the entire JSON payload in a JSONB column to avoid
premature schema explosion. The structure follows the in-memory AgentTypeDefinition
schema from api.v1.agent_types_simple.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Column, DateTime, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base

from core.database import Base


class AgentTypeDefinitionModel(Base):
    """AgentTypeDefinition table for versioned agent type schemas + goal templates.
    
    Each row represents a specific version of an agent type definition.
    The payload column stores the full JSON structure including config_schema,
    goal_templates, and enforcement_defaults.
    
    Phase-1 constraints:
    - Unique (agent_type_id, version) to support versioning
    - JSONB payload for flexibility without premature normalization
    - Timestamps for audit trail
    """
    
    __tablename__ = "agent_type_definitions"
    
    # Primary key
    id = Column(String, primary_key=True, nullable=False)
    
    # Versioning columns
    agent_type_id = Column(String, nullable=False, index=True)
    version = Column(String, nullable=False)
    
    # Payload stored as JSONB (matches AgentTypeDefinition Pydantic model)
    payload = Column(JSONB, nullable=False)
    
    # Audit timestamps
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    
    # Constraints
    __table_args__ = (
        # Ensure each (agent_type_id, version) combo is unique
        UniqueConstraint("agent_type_id", "version", name="uq_agent_type_id_version"),
        # Index for faster lookups by agent_type_id
        Index("ix_agent_type_definitions_agent_type_id", "agent_type_id"),
    )
    
    def __init__(
        self,
        id: str,
        agent_type_id: str,
        version: str,
        payload: dict[str, Any],
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        """Initialize AgentTypeDefinitionModel.
        
        Args:
            id: Unique identifier (typically f"{agent_type_id}@{version}")
            agent_type_id: Agent type identifier (e.g., "marketing.digital_marketing.v1")
            version: Semantic version (e.g., "1.0.0")
            payload: Full JSON structure with config_schema, goal_templates, etc.
            created_at: Creation timestamp (defaults to now)
            updated_at: Last update timestamp (defaults to now)
        """
        self.id = id
        self.agent_type_id = agent_type_id
        self.version = version
        self.payload = payload
        now = datetime.now(timezone.utc)
        self.created_at = created_at or now
        self.updated_at = updated_at or now
    
    def __repr__(self) -> str:
        return (
            f"<AgentTypeDefinitionModel(id={self.id!r}, "
            f"agent_type_id={self.agent_type_id!r}, version={self.version!r})>"
        )
