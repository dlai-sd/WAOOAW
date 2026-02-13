"""Service layer for AgentTypeDefinition operations.

Handles business logic and converts between DB models and Pydantic schemas.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from api.v1.agent_types_simple import AgentTypeDefinition
from repositories.agent_type_repository import AgentTypeDefinitionRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class AgentTypeDefinitionService:
    """Service for AgentTypeDefinition business logic."""
    
    def __init__(self, session: AsyncSession):
        """Initialize service with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self.repository = AgentTypeDefinitionRepository(session)
    
    async def get_definition(self, agent_type_id: str) -> AgentTypeDefinition | None:
        """Get agent type definition by ID (latest version).
        
        Args:
            agent_type_id: Agent type identifier
            
        Returns:
            AgentTypeDefinition Pydantic model or None
        """
        db_model = await self.repository.get_by_id(agent_type_id)
        if not db_model:
            return None
        return self._to_pydantic(db_model)
    
    async def list_definitions(self) -> list[AgentTypeDefinition]:
        """List all agent type definitions (latest versions).
        
        Returns:
            List of AgentTypeDefinition Pydantic models
        """
        db_models = await self.repository.list_all()
        return [self._to_pydantic(model) for model in db_models]
    
    async def create_definition(
        self, definition: AgentTypeDefinition
    ) -> AgentTypeDefinition:
        """Create a new agent type definition.
        
        Args:
            definition: AgentTypeDefinition Pydantic model
            
        Returns:
            Created AgentTypeDefinition
        """
        payload = definition.model_dump()
        db_model = await self.repository.create(
            agent_type_id=definition.agent_type_id,
            version=definition.version,
            payload=payload,
        )
        return self._to_pydantic(db_model)
    
    async def update_definition(
        self, definition: AgentTypeDefinition
    ) -> AgentTypeDefinition | None:
        """Update an existing agent type definition.
        
        Args:
            definition: AgentTypeDefinition Pydantic model with updates
            
        Returns:
            Updated AgentTypeDefinition or None if not found
        """
        payload = definition.model_dump()
        db_model = await self.repository.update(
            agent_type_id=definition.agent_type_id,
            version=definition.version,
            payload=payload,
        )
        if not db_model:
            return None
        return self._to_pydantic(db_model)
    
    @staticmethod
    def _to_pydantic(db_model) -> AgentTypeDefinition:
        """Convert DB model to Pydantic model.
        
        Args:
            db_model: AgentTypeDefinitionModel instance
            
        Returns:
            AgentTypeDefinition Pydantic model
        """
        # The payload already contains the full structure
        return AgentTypeDefinition(**db_model.payload)
