"""
Agent API Routes - V1 Endpoints for Agent Management
Simple in-memory implementation for Phase 1 testing
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum

# ============================================================================
# Data Models (Pydantic Schemas)
# ============================================================================

class AgentStatus(str, Enum):
    AVAILABLE = "available"
    WORKING = "working"
    OFFLINE = "offline"


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    specialization: str = Field(..., min_length=1, max_length=100)
    industry: str = Field(..., min_length=1, max_length=50)
    hourly_rate: float = Field(..., gt=0)


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    specialization: Optional[str] = None
    hourly_rate: Optional[float] = None


class AgentStatusUpdate(BaseModel):
    status: AgentStatus


class AgentMetrics(BaseModel):
    total_jobs: int = 0
    completed_jobs: int = 0
    avg_rating: float = 0.0
    response_time_seconds: float = 0.0
    retention_rate: float = 0.0


class AgentResponse(BaseModel):
    id: UUID
    name: str
    specialization: str
    industry: str
    status: AgentStatus
    hourly_rate: float
    metrics: AgentMetrics
    created_at: datetime
    last_active_at: datetime
    
    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


# ============================================================================
# In-Memory Storage (for Phase 1 testing)
# ============================================================================

class Agent:
    """Agent entity"""
    def __init__(
        self,
        id: UUID,
        name: str,
        specialization: str,
        industry: str,
        hourly_rate: float,
    ):
        self.id = id
        self.name = name
        self.specialization = specialization
        self.industry = industry
        self.hourly_rate = hourly_rate
        self.status = AgentStatus.AVAILABLE
        self.metrics = AgentMetrics()
        self.created_at = datetime.utcnow()
        self.last_active_at = datetime.utcnow()
    
    def to_response(self) -> AgentResponse:
        return AgentResponse(
            id=self.id,
            name=self.name,
            specialization=self.specialization,
            industry=self.industry,
            status=self.status,
            hourly_rate=self.hourly_rate,
            metrics=self.metrics,
            created_at=self.created_at,
            last_active_at=self.last_active_at,
        )


# Global in-memory storage
_agents_db: dict[UUID, Agent] = {}


def get_agents_db() -> dict[UUID, Agent]:
    """Get agents database"""
    return _agents_db


# ============================================================================
# FastAPI Router
# ============================================================================

router = APIRouter(
    prefix="/api/v1/agents",
    tags=["agents"],
    responses={
        404: {"description": "Agent not found"},
        400: {"description": "Invalid request"},
    }
)


@router.post("/", response_model=AgentResponse, status_code=201)
async def create_agent(
    agent_data: AgentCreate,
    db: dict = Depends(get_agents_db),
) -> AgentResponse:
    """
    Create a new AI agent
    
    Args:
        agent_data: Agent creation data
        
    Returns:
        Created agent with UUID
        
    Example:
        POST /api/v1/agents/
        {
            "name": "Sarah Marketing Expert",
            "specialization": "healthcare",
            "industry": "marketing",
            "hourly_rate": 85.0
        }
    """
    agent_id = uuid4()
    agent = Agent(
        id=agent_id,
        name=agent_data.name,
        specialization=agent_data.specialization,
        industry=agent_data.industry,
        hourly_rate=agent_data.hourly_rate,
    )
    
    db[agent_id] = agent
    return agent.to_response()


@router.get("/", response_model=List[AgentResponse])
async def list_agents(
    industry: Optional[str] = Query(None),
    specialization: Optional[str] = Query(None),
    status: Optional[AgentStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: dict = Depends(get_agents_db),
) -> List[AgentResponse]:
    """
    List all agents with optional filtering
    
    Args:
        industry: Filter by industry (e.g., "marketing")
        specialization: Filter by specialization (e.g., "healthcare")
        status: Filter by status
        skip: Pagination offset
        limit: Pagination limit (max 100)
        
    Returns:
        List of agents matching filters
        
    Example:
        GET /api/v1/agents/?industry=marketing&limit=10
    """
    agents = list(db.values())
    
    # Apply filters
    if industry:
        agents = [a for a in agents if a.industry.lower() == industry.lower()]
    if specialization:
        agents = [a for a in agents if a.specialization.lower() == specialization.lower()]
    if status:
        agents = [a for a in agents if a.status == status]
    
    # Apply pagination
    agents = agents[skip : skip + limit]
    
    return [a.to_response() for a in agents]


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: UUID,
    db: dict = Depends(get_agents_db),
) -> AgentResponse:
    """
    Get a specific agent by ID
    
    Args:
        agent_id: Agent UUID
        
    Returns:
        Agent details
        
    Raises:
        HTTPException: 404 if agent not found
    """
    agent = db.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    return agent.to_response()


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: UUID,
    update_data: AgentUpdate,
    db: dict = Depends(get_agents_db),
) -> AgentResponse:
    """
    Update agent details
    
    Args:
        agent_id: Agent UUID
        update_data: Fields to update
        
    Returns:
        Updated agent
        
    Raises:
        HTTPException: 404 if agent not found
    """
    agent = db.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    if update_data.name:
        agent.name = update_data.name
    if update_data.specialization:
        agent.specialization = update_data.specialization
    if update_data.hourly_rate:
        agent.hourly_rate = update_data.hourly_rate
    
    agent.last_active_at = datetime.utcnow()
    
    return agent.to_response()


@router.put("/{agent_id}/status", response_model=AgentResponse)
async def update_agent_status(
    agent_id: UUID,
    status_update: AgentStatusUpdate,
    db: dict = Depends(get_agents_db),
) -> AgentResponse:
    """
    Update agent status
    
    Args:
        agent_id: Agent UUID
        status_update: New status
        
    Returns:
        Updated agent
    """
    agent = db.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    agent.status = status_update.status
    agent.last_active_at = datetime.utcnow()
    
    return agent.to_response()


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: UUID,
    db: dict = Depends(get_agents_db),
) -> None:
    """
    Delete an agent
    
    Args:
        agent_id: Agent UUID
        
    Raises:
        HTTPException: 404 if agent not found
    """
    if agent_id not in db:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    del db[agent_id]


@router.get("/available/search", response_model=List[AgentResponse])
async def search_available_agents(
    query: str = Query(..., min_length=1),
    industry: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50),
    db: dict = Depends(get_agents_db),
) -> List[AgentResponse]:
    """
    Search for available agents
    
    Args:
        query: Search query (name or specialization)
        industry: Optional industry filter
        limit: Max results
        
    Returns:
        Available agents matching query
    """
    agents = [
        a for a in db.values()
        if a.status == AgentStatus.AVAILABLE
    ]
    
    if industry:
        agents = [a for a in agents if a.industry.lower() == industry.lower()]
    
    query_lower = query.lower()
    agents = [
        a for a in agents
        if query_lower in a.name.lower() or query_lower in a.specialization.lower()
    ]
    
    # Sort by rating
    agents.sort(key=lambda a: a.metrics.avg_rating, reverse=True)
    
    return [a.to_response() for a in agents[:limit]]


@router.get("/{agent_id}/metrics", response_model=AgentMetrics)
async def get_agent_metrics(
    agent_id: UUID,
    db: dict = Depends(get_agents_db),
) -> AgentMetrics:
    """
    Get agent performance metrics
    
    Args:
        agent_id: Agent UUID
        
    Returns:
        Agent metrics (jobs, rating, response time, etc.)
    """
    agent = db.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    return agent.metrics


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health", tags=["health"])
async def health_check() -> dict:
    """Health check for agents endpoint"""
    return {
        "status": "healthy",
        "service": "agents-api",
        "agents_count": len(_agents_db),
    }
