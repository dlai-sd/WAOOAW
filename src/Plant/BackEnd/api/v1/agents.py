"""Agent endpoints - birth, industry locking, team assignment.

HIRE-1.3: Agent catalog responses must include pricing metadata:
- trial_days
- allowed_durations
- price (monthly INR)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from uuid import UUID
from sqlalchemy import select, func

from core.database import get_db
from models.schemas import AgentCreate, AgentResponse
from services.agent_service import AgentService
from core.exceptions import ConstitutionalAlignmentError, ValidationError
from models.agent import Agent
from models.team import Team
from models.industry import Industry


router = APIRouter(prefix="/agents", tags=["agents"])


DEFAULT_TRIAL_DAYS = 7
DEFAULT_ALLOWED_DURATIONS = ["monthly", "quarterly"]


def _compute_monthly_price_inr(industry_display_name: Optional[str]) -> int:
    industry_key = (industry_display_name or "").strip().lower()

    # Conservative, stable defaults until we have first-class pricing entities.
    if industry_key == "marketing":
        return 12000
    if industry_key == "education":
        return 8000
    if industry_key == "sales":
        return 15000
    return 12000


def _catalog_metadata(*, industry_display_name: Optional[str]) -> Dict[str, object]:
    return {
        "trial_days": DEFAULT_TRIAL_DAYS,
        "allowed_durations": DEFAULT_ALLOWED_DURATIONS,
        "price": _compute_monthly_price_inr(industry_display_name),
    }


@router.post("", response_model=AgentResponse, status_code=201,
    summary="Create new agent (birth)",
    description="""
    Create a new agent entity with industry locking and constitutional validation.
    
    **Constitutional Validation:**
    - L0-01: governance_agent_id must be present (genesis or governor UUID)
    - L0-02: skill_id + job_role_id must reference certified entities
    - L0-02: industry_id immutable after creation (birth industry lock)
    - L0-05: Agent creation logged to audit trail
    - L0-06: Version hash calculated and stored
    - L0-07: Amendment history initialized with birth signature
    
    **Required References:**
    - skill_id: Must be a certified Skill entity
    - job_role_id: Must be a certified JobRole entity
    - industry_id: Must be a valid Industry entity (locked after creation)
    - team_id: Optional Team UUID (can be assigned later)
    
    **Workflow:**
    1. Validate all referenced entities exist (skill, job role, industry)
    2. Check constitutional alignment (L0/L1 principles)
    3. Lock industry (immutable forever - agents cannot change industries)
    4. Calculate version hash from agent data
    5. Initialize amendment history with birth signature
    6. Store agent entity with status="active"
    7. Emit agent.created event to audit log
    
    **Returns:**
    - 201 Created: Agent entity with UUID
    - 404 Not Found: Referenced skill/job_role/industry doesn't exist
    - 422 Unprocessable Entity: Constitutional alignment failure or validation error
    - 500 Internal Server Error: Unexpected error
    
    **Example Request:**
    ```json
    {
      "name": "Email Marketing Agent",
      "skill_id": "550e8400-e29b-41d4-a716-446655440000",
      "job_role_id": "660e8400-e29b-41d4-a716-446655440001",
      "industry_id": "770e8400-e29b-41d4-a716-446655440002",
      "governance_agent_id": "genesis"
    }
    ```
    """,
    responses={
        201: {
            "description": "Agent created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "880e8400-e29b-41d4-a716-446655440003",
                        "name": "Email Marketing Agent",
                        "skill_id": "550e8400-e29b-41d4-a716-446655440000",
                        "job_role_id": "660e8400-e29b-41d4-a716-446655440001",
                        "industry_id": "770e8400-e29b-41d4-a716-446655440002",
                        "status": "active",
                        "created_at": "2026-01-16T10:30:00Z"
                    }
                }
            }
        },
        422: {
            "description": "Constitutional alignment failure",
            "content": {
                "application/json": {
                    "example": {
                        "type": "https://waooaw.com/errors/constitutional-alignment",
                        "title": "Constitutional Alignment Error",
                        "status": 422,
                        "detail": "skill_id must reference certified Skill (L0-02 violation)",
                        "violations": ["L0-02: Skill not certified", "L0-01: governance_agent_id missing"]
                    }
                }
            }
        }
    }
)
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


@router.get("", response_model=List[AgentResponse],
    summary="List all agents with optional filters",
    description="""
    Retrieve list of agents with optional filtering by industry or job role.
    
    **Query Parameters:**
    - industry_id: Filter by industry UUID (optional)
    - job_role_id: Filter by job role UUID (optional)
    - limit: Maximum results (default 100, max 1000)
    - offset: Pagination offset (default 0)
    
    **Returns:**
    - 200 OK: Array of agent entities (empty array if no matches)
    - 400 Bad Request: Invalid query parameters
    
    **Example Request:**
    ```
    GET /api/v1/agents?industry_id=770e8400-e29b-41d4-a716-446655440002&limit=50
    ```
    
    **Example Response:**
    ```json
    [
      {
        "id": "880e8400-e29b-41d4-a716-446655440003",
        "name": "Email Marketing Agent",
        "skill_id": "550e8400-e29b-41d4-a716-446655440000",
        "job_role_id": "660e8400-e29b-41d4-a716-446655440001",
        "industry_id": "770e8400-e29b-41d4-a716-446655440002",
        "status": "active"
      }
    ]
    ```
    """
)
async def list_agents(
    industry: Optional[str] = None,
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
    # Enrich response with display names so downstream UIs don't show raw UUIDs.
    stmt = (
        select(
            Agent.id,
            Agent.name,
            Agent.skill_id,
            Agent.job_role_id,
            Agent.team_id,
            Agent.industry_id,
            Agent.status,
            Agent.created_at,
            Industry.name.label("industry"),
            Team.name.label("team_name"),
        )
        .select_from(Agent)
        .join(Industry, Agent.industry_id == Industry.id)
        .outerjoin(Team, Agent.team_id == Team.id)
        .where(Agent.status == "active")
    )

    if industry is not None:
        # Match seeded industry names like "Marketing" against query "marketing".
        stmt = stmt.where(func.lower(Industry.name) == industry.lower())

    if industry_id is not None:
        stmt = stmt.where(Agent.industry_id == industry_id)

    if job_role_id is not None:
        stmt = stmt.where(Agent.job_role_id == job_role_id)

    stmt = stmt.limit(limit).offset(offset)
    result = await db.execute(stmt)
    rows = result.mappings().all()
    agents: List[Dict[str, object]] = []
    for r in rows:
        agent = dict(r)
        agent.update(_catalog_metadata(industry_display_name=agent.get("industry")))
        agents.append(agent)
    return agents


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Retrieve Agent by ID.
    """
    stmt = (
        select(
            Agent.id,
            Agent.name,
            Agent.skill_id,
            Agent.job_role_id,
            Agent.team_id,
            Agent.industry_id,
            Agent.status,
            Agent.created_at,
            Industry.name.label("industry"),
            Team.name.label("team_name"),
        )
        .select_from(Agent)
        .join(Industry, Agent.industry_id == Industry.id)
        .outerjoin(Team, Agent.team_id == Team.id)
        .where(Agent.id == agent_id)
    )

    result = await db.execute(stmt)
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    agent = dict(row)
    agent.update(_catalog_metadata(industry_display_name=agent.get("industry")))
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
