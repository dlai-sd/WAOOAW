"""
Agent endpoints - birth, industry locking, team assignment
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from core.database import get_db
from models.schemas import AgentCreate, AgentResponse
from services.agent_service import AgentService
from core.exceptions import ConstitutionalAlignmentError, ValidationError


router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("", response_model=AgentResponse, status_code=201)
async def create_agent(
    agent_data: AgentCreate,
    db: Session = Depends(get_db)
):
    """
    Create new Agent (birth) with skill + job role + industry locking.
    
    - Validates skill/role/industry exist
    - Locks industry (immutable after birth)
    - Validates constitutional alignment
    - Returns Agent entity
    """
    try:
        service = AgentService(db)
        agent = await service.create_agent(agent_data)
        return agent
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ConstitutionalAlignmentError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("", response_model=List[AgentResponse])
async def list_agents(
    industry_id: Optional[UUID] = None,
    job_role_id: Optional[UUID] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List all agents with optional filtering.
    
    - Filter by industry
    - Filter by job role
    - Pagination support
    """
    service = AgentService(db)
    agents = await service.list_agents(
        industry_id=industry_id,
        job_role_id=job_role_id,
        limit=limit,
        offset=offset
    )
    return agents


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Retrieve Agent by ID.
    """
    service = AgentService(db)
    agent = await service.get_agent_by_id(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    return agent


@router.post("/{agent_id}/assign-team", response_model=AgentResponse)
async def assign_agent_to_team(
    agent_id: UUID,
    team_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Assign Agent to Team.
    
    - Validates agent and team exist
    - Updates agent's team_id
    - Updates team's agents array
    """
    try:
        service = AgentService(db)
        agent = await service.assign_agent_to_team(agent_id, team_id)
        return agent
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
