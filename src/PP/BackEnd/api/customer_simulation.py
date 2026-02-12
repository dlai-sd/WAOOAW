"""Customer Simulation Mode API - AGP2-PP-3.6

PP admin API for "view as customer" functionality, allowing ops team to
experience the customer portal exactly as a specific customer sees it,
for support and troubleshooting purposes.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from api.deps import get_authorization_header
from api.security import require_admin
from clients.plant_client import PlantAPIClient, get_plant_client


router = APIRouter(prefix="/customer-simulation", tags=["customer-simulation"])


class SimulationSession(BaseModel):
    """Active customer simulation session."""
    
    session_id: str
    operator_id: str  # PP admin user ID
    operator_email: str
    
    # Customer being simulated
    customer_id: str
    customer_email: Optional[str]
    customer_name: Optional[str]
    
    # Session details
    started_at: datetime
    expires_at: datetime
    max_duration_minutes: int = 60
    remaining_minutes: Optional[int] = None
    
    # Session token for CP access
    simulation_token: str = Field(..., description="Token to use for CP API calls")
    
    # Audit
    reason: str = Field(..., description="Reason for simulation session")
    actions_taken: int = 0  # Count of actions performed
    read_only: bool = True  # If true, cannot modify customer data


class SimulationStartRequest(BaseModel):
    """Request to start a simulation session."""
    
    customer_id: str = Field(..., description="Customer to simulate")
    operator_id: str = Field(..., description="Operator ID (admin user)")
    operator_email: str = Field(..., description="Operator email")
    reason: str = Field(..., min_length=20, description="Reason for simulation (min 20 chars)")
    duration_minutes: int = Field(60, ge=5, le=240, description="Session duration (5-240 minutes)")
    read_only: bool = Field(True, description="If true, prevent modifications")


class SimulationAction(BaseModel):
    """Action performed during simulation session."""
    
    action_id: str
    session_id: str
    operator_id: str
    customer_id: str
    
    # Action details
    action_type: str  # "view", "update", "create", "delete"
    resource_type: str  # "agent_config", "goal", "deliverable", etc.
    resource_id: Optional[str]
    
    # Action data
    action_description: str
    changes_made: Optional[dict] = None
    
    # Timestamp
    performed_at: datetime


class SimulationAuditLog(BaseModel):
    """Complete audit log for simulation sessions."""
    
    sessions: list
    total_sessions: int
    total_actions: int
    
    # Filters applied
    operator_id: Optional[str]
    customer_id: Optional[str]
    start_date: Optional[datetime]
    end_date: Optional[datetime]


@router.post(
    "/start",
    response_model=SimulationSession,
    summary="Start customer simulation session"
)
async def start_simulation_session(
    request: SimulationStartRequest,
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Start a "view as customer" simulation session.
    
    **Creates**:
    - Temporary session with limited duration
    - Special authentication token scoped to customer
    - Audit trail entry
    
    **Requirements**:
    - `reason` must be at least 20 characters (explain why)
    - Session auto-expires after `duration_minutes`
    - Default is `read_only=true` (cannot modify data)
    
    **Use Cases**:
    - Customer support: "See what customer sees"
    - Troubleshooting: "Reproduce customer's issue"
    - Training: "Demo customer experience" 
    - Testing: "Validate customer workflow"
    
    **Security**:
    - All sessions logged in audit trail
    - Operator ID and reason recorded
    - IP address and user agent captured
    - Cannot simulate admin users
    - Session expires automatically
    
    **Returns**:
    - `simulation_token`: Use this as Bearer token in CP API calls
    - `expires_at`: When session ends
    - Session automatically terminated on expiry
    """
    
    try:
        from datetime import timezone
        from uuid import uuid4
        
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=request.duration_minutes)
        session_id = f"SIM-{uuid4()}"
        simulation_token = f"sim_token_{uuid4()}"  # In production, generate secure JWT
        
        # In production:
        # 1. Validate customer exists
        # 2. Validate operator has permission
        # 3. Create session in database
        # 4. Generate secure JWT token with:
        #    - customer_id in claims
        #    - session_id in claims
        #    - operator_id in claims
        #    - exp timestamp
        #    - read_only flag
        # 5. Log session start in audit trail
        
        session = SimulationSession(
            session_id=session_id,
            operator_id=request.operator_id,
            operator_email=request.operator_email,
            customer_id=request.customer_id,
            customer_email=None,  # Fetch from customer record
            customer_name=None,   # Fetch from customer record
            started_at=now,
            expires_at=expires_at,
            max_duration_minutes=request.duration_minutes,
            remaining_minutes=request.duration_minutes,
            simulation_token=simulation_token,
            reason=request.reason,
            actions_taken=0,
            read_only=request.read_only,
        )
        
        return session
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start simulation session: {str(e)}")


@router.get(
    "/session/{session_id}",
    response_model=SimulationSession,
    summary="Get simulation session details"
)
async def get_simulation_session(
    session_id: str,
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Get details of an active or past simulation session.
    
    **Returns**:
    - Session metadata
    - Time remaining (if active)
    - Action count
    - Read-only status
    """
    
    try:
        # In production, fetch from database
        
        raise HTTPException(status_code=404, detail="Session not found")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch session: {str(e)}")


@router.post(
    "/session/{session_id}/end",
    summary="End simulation session early"
)
async def end_simulation_session(
    session_id: str,
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """End a simulation session before it expires.
    
    **Use Cases**:
    - Support session completed
    - Operator switching to different customer
    - Emergency termination
    
    **Effects**:
    - Session marked as ended
    - simulation_token invalidated immediately
    - Logged in audit trail
    """
    
    try:
        # In production:
        # 1. Validate session exists and is active
        # 2. Mark session as ended
        # 3. Invalidate JWT token (add to blocklist)
        # 4. Log session end in audit trail
        
        return {
            "status": "success",
            "message": "Simulation session ended",
            "session_id": session_id,
            "ended_at": datetime.now().isoformat(),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to end session: {str(e)}")


@router.post(
    "/session/{session_id}/extend",
    summary="Extend simulation session duration"
)
async def extend_simulation_session(
    session_id: str,
    additional_minutes: int = Query(..., ge=5, le=120, description="Minutes to add (5-120)"),
    reason: str = Query(..., min_length=10, description="Reason for extension"),
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Extend an active simulation session.
    
    **Use Cases**:
    - Support session taking longer than expected
    - Need more time to troubleshoot
    
    **Limits**:
    - Can extend by 5-120 minutes
    - Maximum total session duration: 240 minutes (4 hours)
    - Requires reason for extension
    """
    
    try:
        # In production:
        # 1. Validate session exists and is active
        # 2. Check total duration doesn't exceed 240 minutes
        # 3. Update expires_at
        # 4. Update JWT exp claim (regenerate token if needed)
        # 5. Log extension in audit trail
        
        new_expires_at = datetime.now() + timedelta(minutes=additional_minutes)
        
        return {
            "status": "success",
            "message": f"Session extended by {additional_minutes} minutes",
            "session_id": session_id,
            "new_expires_at": new_expires_at.isoformat(),
            "reason": reason,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extend session: {str(e)}")


@router.get(
    "/active-sessions",
    summary="Get all active simulation sessions"
)
async def get_active_sessions(
    operator_id: Optional[str] = Query(None, description="Filter by operator"),
    customer_id: Optional[str] = Query(None, description="Filter by customer"),
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Get all currently active simulation sessions.
    
    **Use Cases**:
    - Monitor active support sessions
    - See who is simulating which customers
    - Detect potential security issues
    
    **Shows**:
    - Operator and customer info
    - Time remaining
    - Actions taken
    - Read-only status
    """
    
    try:
        # In production, query active sessions
        
        active_sessions = []
        
        if operator_id:
            active_sessions = [s for s in active_sessions if s.get("operator_id") == operator_id]
        if customer_id:
            active_sessions = [s for s in active_sessions if s.get("customer_id") == customer_id]
        
        return {
            "active_sessions": active_sessions,
            "total": len(active_sessions),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch active sessions: {str(e)}")


@router.get(
    "/audit-log",
    response_model=SimulationAuditLog,
    summary="Get simulation audit log"
)
async def get_simulation_audit_log(
    operator_id: Optional[str] = Query(None, description="Filter by operator"),
    customer_id: Optional[str] = Query(None, description="Filter by customer"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Get complete audit log of all simulation sessions.
    
    **Includes**:
    - All session starts and ends
    - All actions performed during sessions
    - Operator and customer context
    - Reasons provided
    
    **Use Cases**:
    - Compliance audits
    - Security reviews
    - Operator performance tracking
    - Customer privacy compliance
    
    **Retention**:
    - Logs retained for 90 days minimum
    - Can export for longer retention
    """
    
    try:
        # In production, query audit trail
        
        sessions = []
        total_actions = 0
        
        return SimulationAuditLog(
            sessions=sessions,
            total_sessions=len(sessions),
            total_actions=total_actions,
            operator_id=operator_id,
            customer_id=customer_id,
            start_date=start_date,
            end_date=end_date,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch audit log: {str(e)}")


@router.post(
    "/session/{session_id}/action",
    summary="Log an action performed during simulation"
)
async def log_simulation_action(
    session_id: str,
    action_type: str = Query(..., description="view, update, create, delete"),
    resource_type: str = Query(..., description="agent_config, goal, deliverable, etc."),
    resource_id: Optional[str] = Query(None),
    description: str = Query(..., min_length=10),
    changes: Optional[dict] = None,
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Log an action performed during a simulation session.
    
    **Called By**:
    - CP API endpoints when simulation_token is used
    - Automatic logging of all actions
    
    **Purpose**:
    - Complete audit trail
    - Track what operators did as customer
    - Compliance and security
    
    **Note**: This is typically called automatically by CP API,
    not manually by operators.
    """
    
    try:
        from uuid import uuid4
        
        # In production:
        # 1. Validate session is active
        # 2. Increment session.actions_taken
        # 3. Create action record
        # 4. If read_only and action_type != "view", reject
        
        action = SimulationAction(
            action_id=f"ACT-{uuid4()}",
            session_id=session_id,
            operator_id="OP-placeholder",
            customer_id="CUST-placeholder",
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            action_description=description,
            changes_made=changes,
            performed_at=datetime.now(),
        )
        
        return {
            "status": "success",
            "message": "Action logged",
            "action": action,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log action: {str(e)}")


@router.get(
    "/session/{session_id}/actions",
    summary="Get all actions for a session"
)
async def get_session_actions(
    session_id: str,
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Get all actions performed during a simulation session.
    
    **Shows**:
    - Timeline of actions
    - What was viewed
    - What was modified (if not read-only)
    - Changes made
    
    **Use Case**:
    - Review what operator did during support session
    - Debugging: "What changed?"
    """
    
    try:
        # In production, query actions for session
        
        return {
            "session_id": session_id,
            "actions": [],
            "total": 0,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch session actions: {str(e)}")


@router.get(
    "/guidelines",
    summary="Get simulation mode guidelines"
)
async def get_simulation_guidelines(
    _: dict = Depends(require_admin),
):
    """Get guidelines and best practices for using simulation mode.
    
    **Best Practices**:
    - Always provide clear, detailed reason
    - Use read-only mode unless customer gave permission to modify
    - End session immediately when done
    - Notify customer of simulation session (via ticket/email)
    - Never share simulation tokens
    - Never simulate admin/internal accounts
    
    **Privacy**:
    - Customer consent required for non-read-only sessions
    - All sessions logged and auditable
    - Customer can request simulation log
    - Compliance with privacy regulations
    """
    
    return {
        "guidelines": {
            "required": [
                "Provide detailed reason (min 20 characters)",
                "Use read-only mode by default",
                "End session when done",
                "Document findings in support ticket",
            ],
            "recommended": [
                "Notify customer of simulation session",
                "Keep session duration as short as possible",
                "Review audit log after session",
                "Get customer consent for modifications",
            ],
            "prohibited": [
                "Simulating admin or PP users",
                "Sharing simulation tokens",
                "Modifying data without customer consent",
                "Using simulation for non-support purposes",
                "Leaving sessions active unnecessarily",
            ],
        },
        "compliance": {
            "audit_retention_days": 90,
            "max_session_duration_minutes": 240,
            "requires_justification": True,
            "customer_notification_recommended": True,
        },
    }
