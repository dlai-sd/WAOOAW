"""Agent Type Definition DB-backed APIs (AGP1-DB-1.2).

Provides DB-persisted agent type definitions with feature flag support.
Falls back to in-memory implementation when USE_AGENT_TYPE_DB=false.
"""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.agent_types_simple import (
    AgentTypeDefinition,
    get_agent_type_definition as get_in_memory_definition,
    list_agent_types as list_in_memory_types,
)
from core.database import get_db_session
from services.agent_type_service import AgentTypeDefinitionService


router = APIRouter(prefix="/agent-types-db", tags=["agent-types-db"])

# Feature flag: USE_AGENT_TYPE_DB (default: false for Phase 1)
USE_AGENT_TYPE_DB = os.getenv("USE_AGENT_TYPE_DB", "false").lower() == "true"


def get_agent_type_service(
    db: AsyncSession = Depends(get_db_session),
) -> AgentTypeDefinitionService:
    """Dependency injection for AgentTypeDefinitionService.
    
    Args:
        db: Async database session
        
    Returns:
        AgentTypeDefinitionService instance
    """
    return AgentTypeDefinitionService(db)


@router.get("", response_model=list[AgentTypeDefinition])
@router.get("/", response_model=list[AgentTypeDefinition])
async def list_agent_types_db(
    service: AgentTypeDefinitionService = Depends(get_agent_type_service),
) -> list[AgentTypeDefinition]:
    """List all agent type definitions from DB.
    
    Returns latest version of each agent type.
    If USE_AGENT_TYPE_DB=false, falls back to in-memory store.
    
    Returns:
        List of AgentTypeDefinition objects
    """
    if not USE_AGENT_TYPE_DB:
        # Fallback to in-memory implementation
        return await list_in_memory_types()
    
    return await service.list_definitions()


@router.get("/{agent_type_id}", response_model=AgentTypeDefinition)
async def get_agent_type_db(
    agent_type_id: str,
    service: AgentTypeDefinitionService = Depends(get_agent_type_service),
) -> AgentTypeDefinition:
    """Get agent type definition by ID from DB.
    
    Returns latest version of the specified agent type.
    If USE_AGENT_TYPE_DB=false, falls back to in-memory store.
    
    Args:
        agent_type_id: Agent type identifier
        service: AgentTypeDefinitionService (injected)
        
    Returns:
        AgentTypeDefinition object
        
    Raises:
        HTTPException: 400 if agent_type_id empty, 404 if not found
    """
    key = (agent_type_id or "").strip()
    if not key:
        raise HTTPException(status_code=400, detail="agent_type_id is required")
    
    if not USE_AGENT_TYPE_DB:
        # Fallback to in-memory implementation
        definition = get_in_memory_definition(key)
        if not definition:
            raise HTTPException(status_code=404, detail="Agent type not found")
        return definition
    
    definition = await service.get_definition(key)
    if not definition:
        raise HTTPException(status_code=404, detail="Agent type not found")
    
    return definition


@router.post("/", response_model=AgentTypeDefinition, status_code=201)
async def create_agent_type_db(
    definition: AgentTypeDefinition,
    service: AgentTypeDefinitionService = Depends(get_agent_type_service),
) -> AgentTypeDefinition:
    """Create a new agent type definition in DB.
    
    Requires USE_AGENT_TYPE_DB=true.
    
    Args:
        definition: AgentTypeDefinition to create
        service: AgentTypeDefinitionService (injected)
        
    Returns:
        Created AgentTypeDefinition
        
    Raises:
        HTTPException: 400 if feature disabled or validation fails
    """
    if not USE_AGENT_TYPE_DB:
        raise HTTPException(
            status_code=400,
            detail="DB-backed agent types not enabled. Set USE_AGENT_TYPE_DB=true",
        )
    
    try:
        return await service.create_definition(definition)
    except Exception as e:
        # Handle unique constraint violations, etc.
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{agent_type_id}", response_model=AgentTypeDefinition)
async def update_agent_type_db(
    agent_type_id: str,
    definition: AgentTypeDefinition,
    service: AgentTypeDefinitionService = Depends(get_agent_type_service),
) -> AgentTypeDefinition:
    """Update an existing agent type definition in DB.
    
    Requires USE_AGENT_TYPE_DB=true.
    
    Args:
        agent_type_id: Agent type identifier (must match definition.agent_type_id)
        definition: Updated AgentTypeDefinition
        service: AgentTypeDefinitionService (injected)
        
    Returns:
        Updated AgentTypeDefinition
        
    Raises:
        HTTPException: 400 if validation fails, 404 if not found
    """
    if not USE_AGENT_TYPE_DB:
        raise HTTPException(
            status_code=400,
            detail="DB-backed agent types not enabled. Set USE_AGENT_TYPE_DB=true",
        )
    
    key = (agent_type_id or "").strip()
    if not key:
        raise HTTPException(status_code=400, detail="agent_type_id is required")
    
    if (definition.agent_type_id or "").strip() != key:
        raise HTTPException(status_code=400, detail="agent_type_id mismatch")
    
    updated = await service.update_definition(definition)
    if not updated:
        raise HTTPException(status_code=404, detail="Agent type not found")
    
    return updated
