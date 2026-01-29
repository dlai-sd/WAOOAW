"""Agent Management API routes.

PP admin portal routes for agent CRUD operations via Plant API.

These handlers must forward the incoming Authorization header to the Plant
Gateway. Otherwise the Plant Gateway will treat calls as unauthenticated.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from uuid import UUID

from api.deps import get_authorization_header
from clients.plant_client import (
    PlantAPIClient,
    get_plant_client,
    AgentCreate,
    AgentResponse,
    PlantAPIError,
    ConstitutionalAlignmentError,
    EntityNotFoundError,
    DuplicateEntityError,
    ValidationError,
)


router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("", response_model=dict, status_code=201,
    summary="Create new agent entity",
    description="""
    Create a new AI agent in the Plant backend.
    
    **Workflow:**
    1. PP admin submits agent details (name, job role, industry)
    2. PP calls Plant API to create agent
    3. Agent created with initial "inactive" status
    4. Governor can activate agent after review
    
    **Constitutional Validation (Plant enforces):**
    - L0-01: governance_agent_id required
    - L0-02: Job role must be certified
    - L0-03: Agent name uniqueness within team
    - L0-05: Audit trail initialized
    
    **Returns:**
    - 201 Created: Agent entity with UUID
    - 404 Not Found: Referenced job role doesn't exist
    - 422 Unprocessable Entity: Validation error
    """)
async def create_agent(
    agent_data: dict,
    auth_header: Optional[str] = Depends(get_authorization_header),
    plant_client: PlantAPIClient = Depends(get_plant_client)
):
    """
    Create new agent via Plant API.
    
    Body:
    {
        "name": "Content Writer Agent #1",
        "description": "Creates marketing content",
        "job_role_id": "job-role-uuid",
        "industry": "marketing",
        "team_id": "team-uuid" (optional),
        "governance_agent_id": "genesis"
    }
    """
    try:
        # Convert dict to AgentCreate object
        agent_create = AgentCreate(
            name=agent_data["name"],
            description=agent_data["description"],
            job_role_id=agent_data["job_role_id"],
            industry=agent_data.get("industry", "general"),
            team_id=agent_data.get("team_id"),
            governance_agent_id=agent_data.get("governance_agent_id", "genesis")
        )
        
        # Call Plant API
        agent = await plant_client.create_agent(
            agent_create,
            auth_header=auth_header,
        )
        
        # TODO: Log to PP audit trail
        # await audit_service.log_action("agent.created", agent.id, current_user.id)
        
        return {
            "id": agent.id,
            "name": agent.name,
            "description": agent.description,
            "job_role_id": agent.job_role_id,
            "industry": agent.industry,
            "status": agent.status,
            "created_at": agent.created_at,
            "message": "Agent created successfully. Status: inactive. Governor review required for activation."
        }
    
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DuplicateEntityError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ConstitutionalAlignmentError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except PlantAPIError as e:
        raise HTTPException(status_code=500, detail=f"Plant API error: {str(e)}")


@router.get("", response_model=List[dict],
    summary="List all agents with filters",
    description="""
    Retrieve list of agents from Plant.
    
    **Query Parameters:**
    - industry: Filter by industry (marketing/education/sales/healthcare/finance/general)
    - job_role_id: Filter by job role
    - status: Filter by status (active/inactive/suspended)
    - limit: Maximum results (default 100)
    - offset: Pagination offset (default 0)
    
    **Returns:**
    - 200 OK: Array of agent entities
    """)
async def list_agents(
    industry: Optional[str] = Query(None, description="Filter by industry"),
    job_role_id: Optional[str] = Query(None, description="Filter by job role ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    auth_header: Optional[str] = Depends(get_authorization_header),
    plant_client: PlantAPIClient = Depends(get_plant_client)
):
    """List all agents with optional filtering."""
    try:
        agents = await plant_client.list_agents(
            industry=industry,
            job_role_id=job_role_id,
            status=status,
            limit=limit,
            offset=offset,
            auth_header=auth_header,
        )
        
        return [
            {
                "id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "job_role_id": agent.job_role_id,
                "industry": agent.industry,
                "status": agent.status,
                "team_id": agent.team_id,
                "created_at": agent.created_at
            }
            for agent in agents
        ]
    
    except PlantAPIError as e:
        raise HTTPException(status_code=500, detail=f"Plant API error: {str(e)}")


@router.get("/{agent_id}", response_model=dict,
    summary="Get agent details by ID",
    description="Retrieve detailed information about a specific agent.")
async def get_agent(
    agent_id: str,
    auth_header: Optional[str] = Depends(get_authorization_header),
    plant_client: PlantAPIClient = Depends(get_plant_client)
):
    """Get agent by ID."""
    try:
        agent = await plant_client.get_agent(agent_id, auth_header=auth_header)
        
        return {
            "id": agent.id,
            "name": agent.name,
            "description": agent.description,
            "job_role_id": agent.job_role_id,
            "industry": agent.industry,
            "entity_type": agent.entity_type,
            "status": agent.status,
            "team_id": agent.team_id,
            "created_at": agent.created_at,
            "updated_at": agent.updated_at,
            "l0_compliance_status": agent.l0_compliance_status
        }
    
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PlantAPIError as e:
        raise HTTPException(status_code=500, detail=f"Plant API error: {str(e)}")


@router.post("/{agent_id}/assign-team", response_model=dict,
    summary="Assign agent to team",
    description="""
    Assign an agent to a team.
    
    **Authorization (Future):**
    - Requires Governor or Team Lead role
    
    **Workflow:**
    1. PP admin selects agent and target team
    2. PP calls Plant API to update team assignment
    3. Plant validates team exists and capacity
    4. Agent team_id updated
    5. Assignment logged to audit trail
    
    **Returns:**
    - 200 OK: Agent assigned successfully
    - 404 Not Found: Agent or team doesn't exist
    - 422 Unprocessable Entity: Team capacity exceeded or other validation error
    """)
async def assign_agent_to_team(
    agent_id: str,
    assignment_data: dict,
    auth_header: Optional[str] = Depends(get_authorization_header),
    plant_client: PlantAPIClient = Depends(get_plant_client)
):
    """
    Assign agent to team.
    
    Body:
    {
        "team_id": "team-uuid"
    }
    """
    try:
        # TODO: Check current_user has Governor or Team Lead role (RBAC - future)
        # if not current_user.has_role(["governor", "team_lead"]):
        #     raise HTTPException(status_code=403, detail="Governor or Team Lead role required")
        
        team_id = assignment_data.get("team_id")
        if not team_id:
            raise HTTPException(status_code=400, detail="team_id is required")
        
        # Call Plant API
        agent = await plant_client.assign_agent_to_team(
            agent_id,
            team_id,
            auth_header=auth_header,
        )
        
        # TODO: Log assignment event
        # await audit_service.log_action("agent.assigned_to_team", agent.id, current_user.id, {"team_id": team_id})
        
        return {
            "id": agent.id,
            "name": agent.name,
            "team_id": agent.team_id,
            "message": f"Agent assigned to team {team_id} successfully"
        }
    
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConstitutionalAlignmentError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except PlantAPIError as e:
        raise HTTPException(status_code=500, detail=f"Plant API error: {str(e)}")


@router.patch("/{agent_id}/status", response_model=dict,
    summary="Update agent status",
    description="""
    Update agent status (activate/deactivate/suspend).
    
    **Authorization (Future):**
    - Requires Governor role
    
    **Status Transitions:**
    - inactive → active (activation by Governor)
    - active → inactive (deactivation)
    - active → suspended (suspension due to policy violation)
    - suspended → active (reinstatement by Governor)
    
    **Returns:**
    - 200 OK: Agent status updated
    - 404 Not Found: Agent doesn't exist
    - 422 Unprocessable Entity: Invalid status transition
    """)
async def update_agent_status(
    agent_id: str,
    status_data: dict,
    plant_client: PlantAPIClient = Depends(get_plant_client)
):
    """
    Update agent status.
    
    Body:
    {
        "status": "active",
        "reason": "Governor approval received" (optional)
    }
    """
    try:
        # TODO: Check current_user has Governor role (RBAC - future)
        # if not current_user.has_role("governor"):
        #     raise HTTPException(status_code=403, detail="Governor role required")
        
        new_status = status_data.get("status")
        if not new_status:
            raise HTTPException(status_code=400, detail="status is required")
        
        if new_status not in ["active", "inactive", "suspended"]:
            raise HTTPException(status_code=400, detail="Invalid status. Must be: active, inactive, or suspended")
        
        # NOTE: This endpoint doesn't exist in Plant yet - would need to add
        # For now, this is a placeholder for future implementation
        raise HTTPException(status_code=501, detail="Status update endpoint not yet implemented in Plant API")
        
        # Future implementation:
        # agent = await plant_client.update_agent_status(agent_id, new_status, status_data.get("reason"))
        # await audit_service.log_action("agent.status_updated", agent.id, current_user.id, {"new_status": new_status})
        # return {"id": agent.id, "name": agent.name, "status": agent.status, "message": "Agent status updated"}
    
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConstitutionalAlignmentError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except PlantAPIError as e:
        raise HTTPException(status_code=500, detail=f"Plant API error: {str(e)}")
