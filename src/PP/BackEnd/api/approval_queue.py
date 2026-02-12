"""Deliverable Approval Queue API - AGP2-PP-3.4

PP admin API for managing deliverable approvals, including ops-assisted approvals
when customers need help or for emergency situations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field

from api.deps import get_authorization_header
from api.security import require_admin
from clients.plant_client import PlantAPIClient, get_plant_client


router = APIRouter(prefix="/approval-queue", tags=["approval-queue"])


class DeliverableApprovalSummary(BaseModel):
    """Summary of a deliverable pending approval."""
    
    deliverable_id: str
    hired_instance_id: str
    customer_id: str
    agent_id: str
    
    # Goal context
    goal_instance_id: str
    goal_template_id: str
    goal_name: Optional[str] = None
    
    # Deliverable info
    deliverable_type: str  # "marketing_post", "trade_intent", etc.
    status: Literal["draft", "pending_review", "approved", "rejected", "executed"]
    
    # Content preview
    title: Optional[str] = None
    description: Optional[str] = None
    content_preview: Optional[str] = Field(None, description="First 200 chars of content")
    platforms: List[str] = Field(default_factory=list, description="Target platforms")
    
    # Risk assessment
    estimated_cost_usd: Optional[float] = None
    requires_approval: bool = True
    approval_reason: Optional[str] = Field(None, description="Why approval is required")
    
    # Timing
    created_at: datetime
    waiting_since: datetime
    waiting_hours: Optional[float] = None
    urgency: Literal["low", "medium", "high"] = "medium"
    
    # Customer context
    customer_name: Optional[str] = None
    trial_mode: bool = False


class DeliverableApprovalDetail(BaseModel):
    """Detailed view of a deliverable for approval decision."""
    
    deliverable_id: str
    hired_instance_id: str
    customer_id: str
    agent_id: str
    
    goal_instance_id: str
    goal_template_id: str
    goal_name: Optional[str]
    goal_settings: dict = Field(default_factory=dict)
    
    # Full deliverable content
    deliverable_type: str
    status: str
    title: Optional[str]
    description: Optional[str]
    full_content: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)
    
    # Risk details
    estimated_cost_usd: Optional[float]
    estimated_tokens: Optional[int]
    requires_approval: bool
    approval_reason: Optional[str]
    risk_flags: List[str] = Field(default_factory=list)
    
    # Agent config snapshot
    agent_config: dict = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    waiting_since: datetime
    

class ApprovalQueueFilters(BaseModel):
    """Filters for approval queue."""
    
    customer_id: Optional[str]
    agent_id: Optional[str]
    deliverable_type: Optional[str]
    urgency: Optional[Literal["low", "medium", "high"]]
    trial_mode: Optional[bool]
    min_waiting_hours: Optional[float]


class ApprovalQueueStats(BaseModel):
    """Statistics for approval queue."""
    
    total_pending: int = 0
    high_urgency: int = 0
    medium_urgency: int = 0
    low_urgency: int = 0
    
    trial_mode_count: int = 0
    paid_count: int = 0
    
    avg_waiting_hours: Optional[float] = None
    oldest_waiting_hours: Optional[float] = None


class ApprovalQueueResponse(BaseModel):
    """Approval queue with stats and items."""
    
    stats: ApprovalQueueStats
    pending_approvals: List[DeliverableApprovalSummary]
    total: int
    page: int
    page_size: int


class OpsApprovalRequest(BaseModel):
    """Request for ops-assisted approval."""
    
    deliverable_id: str
    approve: bool = Field(..., description="True to approve, False to reject")
    operator_id: str = Field(..., description="ID/email of operator approving")
    justification: str = Field(..., min_length=10, description="Reason for ops approval (required, min 10 chars)")
    notify_customer: bool = Field(True, description="Send notification to customer about ops approval")


class BulkApprovalRequest(BaseModel):
    """Bulk approval/rejection request."""
    
    deliverable_ids: List[str] = Field(..., min_items=1, max_items=50)
    approve: bool
    operator_id: str
    justification: str = Field(..., min_length=10)
    notify_customers: bool = True


@router.get(
    "/queue",
    response_model=ApprovalQueueResponse,
    summary="Get deliverable approval queue"
)
async def get_approval_queue(
    # Filters
    customer_id: Optional[str] = Query(None),
    agent_id: Optional[str] = Query(None),
    deliverable_type: Optional[str] = Query(None),
    urgency: Optional[str] = Query(None),
    trial_mode: Optional[bool] = Query(None),
    min_waiting_hours: Optional[float] = Query(None, ge=0),
    
    # Sorting
    sort_by: str = Query("waiting_since", description="Sort by: waiting_since, urgency, estimated_cost_usd"),
    sort_order: str = Query("asc", description="asc (oldest first) or desc"),
    
    # Pagination
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    
    # Auth
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Get deliverables pending customer approval.
    
    Shows all deliverables in `pending_review` status across all customers.
    Used by PP ops team to:
    - Monitor approval queue health
    - Identify stuck approvals
    - Assist customers with approval decisions
    
    **Urgency Calculation**:
    - `high`: Waiting > 24 hours, or high estimated cost
    - `medium`: Waiting 4-24 hours
    - `low`: Waiting < 4 hours
    
    **Filters**:
    - `customer_id`: Specific customer
    - `agent_id`: Specific agent type
    - `deliverable_type`: marketing_post, trade_intent, etc.
    - `urgency`: low, medium, high
    - `trial_mode`: true (trial users only), false (paid users only)
    - `min_waiting_hours`: Only show items waiting ≥ X hours
    """
    
    try:
        # In production, query deliverables table with status=pending_review
        pending_approvals: List[DeliverableApprovalSummary] = []
        
        # Calculate stats
        stats = ApprovalQueueStats(
            total_pending=len(pending_approvals),
            high_urgency=sum(1 for d in pending_approvals if d.urgency == "high"),
            medium_urgency=sum(1 for d in pending_approvals if d.urgency == "medium"),
            low_urgency=sum(1 for d in pending_approvals if d.urgency == "low"),
            trial_mode_count=sum(1 for d in pending_approvals if d.trial_mode),
            paid_count=sum(1 for d in pending_approvals if not d.trial_mode),
        )
        
        # Calculate average and oldest waiting times
        if pending_approvals:
            waiting_times = [d.waiting_hours for d in pending_approvals if d.waiting_hours]
            if waiting_times:
                stats.avg_waiting_hours = sum(waiting_times) / len(waiting_times)
                stats.oldest_waiting_hours = max(waiting_times)
        
        # Apply filters
        filtered = pending_approvals
        if customer_id:
            filtered = [d for d in filtered if d.customer_id == customer_id]
        if agent_id:
            filtered = [d for d in filtered if d.agent_id == agent_id]
        if deliverable_type:
            filtered = [d for d in filtered if d.deliverable_type == deliverable_type]
        if urgency:
            filtered = [d for d in filtered if d.urgency == urgency]
        if trial_mode is not None:
            filtered = [d for d in filtered if d.trial_mode == trial_mode]
        if min_waiting_hours is not None:
            filtered = [d for d in filtered if d.waiting_hours and d.waiting_hours >= min_waiting_hours]
        
        # Sorting
        reverse = sort_order.lower() == "desc"
        if sort_by == "waiting_since":
            filtered.sort(key=lambda x: x.waiting_since, reverse=reverse)
        elif sort_by == "urgency":
            urgency_order = {"high": 3, "medium": 2, "low": 1}
            filtered.sort(key=lambda x: urgency_order.get(x.urgency, 0), reverse=reverse)
        elif sort_by == "estimated_cost_usd":
            filtered.sort(key=lambda x: x.estimated_cost_usd or 0, reverse=reverse)
        
        # Pagination
        total = len(filtered)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated = filtered[start_idx:end_idx]
        
        return ApprovalQueueResponse(
            stats=stats,
            pending_approvals=paginated,
            total=total,
            page=page,
            page_size=page_size,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch approval queue: {str(e)}")


@router.get(
    "/{deliverable_id}/detail",
    response_model=DeliverableApprovalDetail,
    summary="Get deliverable approval details"
)
async def get_approval_detail(
    deliverable_id: str,
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Get full details of a deliverable for approval review.
    
    Includes:
    - Complete deliverable content
    - Agent configuration snapshot
    - Risk assessment details
    - Goal context
    """
    
    try:
        # In production, fetch from database
        raise HTTPException(status_code=404, detail="Deliverable not found")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch deliverable detail: {str(e)}")


@router.post(
    "/ops-approve",
    summary="Ops-assisted approval of deliverable"
)
async def ops_approve_deliverable(
    request: OpsApprovalRequest,
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Approve or reject a deliverable on behalf of customer (ops-assisted).
    
    **Use Cases**:
    - Customer requested help via support
    - Emergency approval needed
    - Customer unable to access portal
    
    **Audit Trail**:
    - All ops approvals logged with operator_id and justification
    - Customer notified (unless notify_customer=false)
    - Approval marked as `ops_assisted=true`
    
    **Requirements**:
    - `justification` must be at least 10 characters
    - Operator ID recorded for accountability
    - Cannot approve already executed deliverables
    """
    
    try:
        # In production, this would:
        # 1. Validate deliverable exists and is pending_review
        # 2. Create approval record with ops_assisted=true
        # 3. Log in audit trail with operator_id and justification
        # 4. Update deliverable status to approved/rejected
        # 5. Send notification to customer if requested
        # 6. If approved and auto-execute, trigger execution
        
        action = "approved" if request.approve else "rejected"
        
        return {
            "status": "success",
            "message": f"Deliverable {action} by ops",
            "deliverable_id": request.deliverable_id,
            "action": action,
            "operator_id": request.operator_id,
            "ops_assisted": True,
            "justification": request.justification,
            "notification_sent": request.notify_customer,
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve deliverable: {str(e)}")


@router.post(
    "/ops-bulk-approve",
    summary="Bulk ops-assisted approval"
)
async def ops_bulk_approve(
    request: BulkApprovalRequest,
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Approve or reject multiple deliverables at once (ops-assisted).
    
    **Use Cases**:
    - Batch approval for trusted customer
    - Emergency approvals during incident
    - Clearing backlog after system issue
    
    **Limits**:
    - Max 50 deliverables per request
    - All deliverables must be pending_review
    - Same justification applies to all
    
    **Returns**:
    - Success count
    - Failed count with error details
    """
    
    try:
        action = "approved" if request.approve else "rejected"
        
        # In production, process each deliverable
        # Track successes and failures
        
        return {
            "status": "success",
            "message": f"Bulk {action} completed",
            "total_requested": len(request.deliverable_ids),
            "successful": 0,
            "failed": 0,
            "operator_id": request.operator_id,
            "justification": request.justification,
            "errors": [],
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to bulk approve: {str(e)}")


@router.get(
    "/ops-approval-history",
    summary="Get history of ops-assisted approvals"
)
async def get_ops_approval_history(
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
    """Get history of all ops-assisted approvals for audit purposes.
    
    Shows:
    - Who approved what
    - Justifications provided
    - Customers affected
    - Timestamps
    
    **Compliance**:
    - Complete audit trail of all ops interventions
    - Filterable by operator, customer, time period
    - Exportable for reporting
    """
    
    try:
        # In production, query approval audit trail
        
        return {
            "ops_approvals": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "filters": {
                "operator_id": operator_id,
                "customer_id": customer_id,
                "start_date": start_date,
                "end_date": end_date,
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch ops approval history: {str(e)}")


@router.get(
    "/health",
    summary="Get approval queue health metrics"
)
async def get_queue_health(
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
):
    """Get health metrics for the approval queue.
    
    **Metrics**:
    - Queue depth (total pending)
    - Average wait time
    - SLA breaches (>24 hours pending)
    - Approval rate trends
    
    **Use Case**:
    - Monitor queue health on dashboard
    - Alert on SLA breaches
    - Capacity planning
    """
    
    try:
        return {
            "status": "healthy",
            "queue_depth": 0,
            "avg_wait_hours": 0.0,
            "sla_breaches": 0,
            "approval_rate_24h": 0.0,
            "rejection_rate_24h": 0.0,
            "ops_approval_rate": 0.0,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch queue health: {str(e)}")
