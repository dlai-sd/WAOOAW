"""Repository for AgentTypeDefinition database operations.

Provides async CRUD operations for agent_type_definitions table.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.agent_type import AgentTypeDefinitionModel


class AgentTypeDefinitionRepository:
    """Repository for AgentTypeDefinition persistence operations."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with async database session.
        
        Args:
            session: SQLAlchemy async session for database operations
        """
        self.session = session
    
    async def get_by_id(self, agent_type_id: str) -> AgentTypeDefinitionModel | None:
        """Get the latest version of an agent type definition by agent_type_id.
        
        Args:
            agent_type_id: Agent type identifier (e.g., "marketing.healthcare.v1")
            
        Returns:
            AgentTypeDefinitionModel instance or None if not found
        """
        stmt = (
            select(AgentTypeDefinitionModel)
            .where(AgentTypeDefinitionModel.agent_type_id == agent_type_id)
            .order_by(AgentTypeDefinitionModel.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_id_and_version(
        self, agent_type_id: str, version: str
    ) -> AgentTypeDefinitionModel | None:
        """Get a specific version of an agent type definition.
        
        Args:
            agent_type_id: Agent type identifier
            version: Semantic version (e.g., "1.0.0")
            
        Returns:
            AgentTypeDefinitionModel instance or None if not found
        """
        stmt = select(AgentTypeDefinitionModel).where(
            AgentTypeDefinitionModel.agent_type_id == agent_type_id,
            AgentTypeDefinitionModel.version == version,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list_all(self) -> list[AgentTypeDefinitionModel]:
        """List all agent type definitions (latest version of each).
        
        Returns:
            List of AgentTypeDefinitionModel instances
        """
        # Get latest version for each agent_type_id
        # Using a subquery to get max created_at per agent_type_id
        subquery = (
            select(
                AgentTypeDefinitionModel.agent_type_id,
                select(AgentTypeDefinitionModel.id)
                .where(
                    AgentTypeDefinitionModel.agent_type_id
                    == AgentTypeDefinitionModel.agent_type_id
                )
                .order_by(AgentTypeDefinitionModel.created_at.desc())
                .limit(1)
                .correlate(AgentTypeDefinitionModel)
                .scalar_subquery()
                .label("latest_id"),
            )
            .distinct()
            .subquery()
        )
        
        # Simpler approach: just get all and deduplicate in Python
        # (more efficient for small datasets)
        stmt = select(AgentTypeDefinitionModel).order_by(
            AgentTypeDefinitionModel.agent_type_id,
            AgentTypeDefinitionModel.created_at.desc(),
        )
        result = await self.session.execute(stmt)
        all_defs = result.scalars().all()
        
        # Deduplicate: keep only latest version per agent_type_id
        seen_ids = set()
        latest_defs = []
        for definition in all_defs:
            if definition.agent_type_id not in seen_ids:
                seen_ids.add(definition.agent_type_id)
                latest_defs.append(definition)
        
        return latest_defs
    
    async def create(
        self,
        agent_type_id: str,
        version: str,
        payload: dict[str, Any],
    ) -> AgentTypeDefinitionModel:
        """Create a new agent type definition.
        
        Args:
            agent_type_id: Agent type identifier
            version: Semantic version
            payload: Full JSON structure with config_schema, goal_templates, etc.
            
        Returns:
            Created AgentTypeDefinitionModel instance
            
        Raises:
            IntegrityError: If (agent_type_id, version) already exists
        """
        definition = AgentTypeDefinitionModel(
            id=f"{agent_type_id}@{version}",
            agent_type_id=agent_type_id,
            version=version,
            payload=payload,
        )
        self.session.add(definition)
        await self.session.flush()
        return definition
    
    async def update(
        self,
        agent_type_id: str,
        version: str,
        payload: dict[str, Any],
    ) -> AgentTypeDefinitionModel | None:
        """Update an existing agent type definition's payload.
        
        Args:
            agent_type_id: Agent type identifier
            version: Semantic version
            payload: Updated JSON structure
            
        Returns:
            Updated AgentTypeDefinitionModel instance or None if not found
        """
        definition = await self.get_by_id_and_version(agent_type_id, version)
        if definition:
            definition.payload = payload
            definition.updated_at = datetime.now(timezone.utc)
            await self.session.flush()
        return definition
