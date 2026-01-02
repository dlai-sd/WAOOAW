"""
Agent Servicing API
Zero-downtime agent upgrades with automatic rollback
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

router = APIRouter(prefix="/api/servicing", tags=["servicing"])


# ==================== Models ====================

class AgentForServicing(BaseModel):
    """Agent available for servicing/upgrade"""
    agent_id: str
    name: str
    category: str
    current_version: str
    status: str  # running, stopped
    health: str  # healthy, degraded, unhealthy
    uptime_days: int
    last_upgraded: Optional[str] = None


class AgentVersion(BaseModel):
    """Available agent version"""
    version_id: str
    version: str
    release_date: str
    status: str  # current, available, deprecated
    changelog: str
    size_mb: float
    is_current: bool = False
    is_recommended: bool = False
    breaking_changes: bool = False


class DeploymentStrategy(BaseModel):
    """Deployment strategy configuration"""
    strategy_id: str
    name: str
    description: str
    icon: str
    estimated_time: str
    risk_level: str  # low, medium, high
    supports_rollback: bool
    config: Dict[str, Any] = {}


class HealthCheckResult(BaseModel):
    """Health check result"""
    check_id: str
    name: str
    status: str  # pass, fail, warning
    message: str
    timestamp: str
    response_time_ms: Optional[float] = None
    error_rate: Optional[float] = None
    latency_increase: Optional[float] = None


class UpgradeRequest(BaseModel):
    """Request to start an upgrade"""
    agent_ids: List[str]
    target_version: str
    strategy_id: str
    backup_enabled: bool = True
    backup_location: Optional[str] = None
    config_patches: Dict[str, Any] = {}
    auto_rollback: bool = True


class UpgradeResponse(BaseModel):
    """Response from upgrade operation"""
    upgrade_id: str
    status: str
    message: str
    agents_count: int
    estimated_completion: str


class UpgradeHistory(BaseModel):
    """Historical upgrade record"""
    upgrade_id: str
    agent_id: str
    agent_name: str
    from_version: str
    to_version: str
    strategy: str
    status: str  # completed, failed, rolled_back, in_progress
    start_time: str
    end_time: Optional[str]
    duration_min: Optional[float]
    performed_by: str


class RollbackRequest(BaseModel):
    """Request to rollback an upgrade"""
    upgrade_id: str
    reason: str


# ==================== Mock Data ====================

MOCK_AGENTS = [
    {
        "agent_id": "agent-001",
        "name": "Content Writer AI",
        "category": "marketing",
        "current_version": "v2.3.0",
        "status": "running",
        "health": "healthy",
        "uptime_days": 45,
        "last_upgraded": "2025-11-18",
    },
    {
        "agent_id": "agent-002",
        "name": "Math Tutor Pro",
        "category": "education",
        "current_version": "v1.8.2",
        "status": "running",
        "health": "healthy",
        "uptime_days": 120,
        "last_upgraded": "2025-09-03",
    },
    {
        "agent_id": "agent-003",
        "name": "SDR Agent Alpha",
        "category": "sales",
        "current_version": "v3.1.0",
        "status": "running",
        "health": "degraded",
        "uptime_days": 12,
        "last_upgraded": "2025-12-21",
    },
    {
        "agent_id": "agent-004",
        "name": "Social Media Manager",
        "category": "marketing",
        "current_version": "v2.0.1",
        "status": "running",
        "health": "healthy",
        "uptime_days": 89,
        "last_upgraded": "2025-10-05",
    },
    {
        "agent_id": "agent-005",
        "name": "Science Lab Assistant",
        "category": "education",
        "current_version": "v1.5.4",
        "status": "stopped",
        "health": "unknown",
        "uptime_days": 0,
        "last_upgraded": "2025-08-15",
    },
]

MOCK_VERSIONS = [
    {
        "version_id": "v3.2.0",
        "version": "v3.2.0",
        "release_date": "2026-01-10",
        "status": "available",
        "changelog": "Performance improvements, bug fixes, new ML model",
        "size_mb": 245.8,
        "is_recommended": True,
        "breaking_changes": False,
    },
    {
        "version_id": "v3.1.0",
        "version": "v3.1.0",
        "release_date": "2025-12-15",
        "status": "current",
        "changelog": "Feature enhancements, security updates",
        "size_mb": 238.2,
        "is_current": True,
        "breaking_changes": False,
    },
    {
        "version_id": "v3.0.5",
        "version": "v3.0.5",
        "release_date": "2025-11-20",
        "status": "available",
        "changelog": "Stability improvements, minor bug fixes",
        "size_mb": 235.1,
        "is_recommended": False,
        "breaking_changes": False,
    },
    {
        "version_id": "v2.9.2",
        "version": "v2.9.2",
        "release_date": "2025-10-01",
        "status": "deprecated",
        "changelog": "Legacy version, security patches only",
        "size_mb": 220.5,
        "is_recommended": False,
        "breaking_changes": True,
    },
]

MOCK_STRATEGIES = [
    {
        "strategy_id": "blue-green",
        "name": "Blue-Green Deployment",
        "description": "Deploy new version alongside old, switch traffic instantly",
        "icon": "🔵🟢",
        "estimated_time": "8-12 min",
        "risk_level": "low",
        "supports_rollback": True,
        "config": {
            "traffic_switch_mode": "instant",
            "keep_old_version": True,
            "validation_period_sec": 300,
        },
    },
    {
        "strategy_id": "canary",
        "name": "Canary Deployment",
        "description": "Gradual rollout: 10% → 50% → 100% with monitoring",
        "icon": "🐤",
        "estimated_time": "15-25 min",
        "risk_level": "low",
        "supports_rollback": True,
        "config": {
            "phase1_traffic": 10,
            "phase2_traffic": 50,
            "phase3_traffic": 100,
            "phase_duration_min": 5,
            "auto_promote": True,
        },
    },
    {
        "strategy_id": "rolling",
        "name": "Rolling Update",
        "description": "Update instances one-by-one, minimize resource usage",
        "icon": "🔄",
        "estimated_time": "10-15 min",
        "risk_level": "medium",
        "supports_rollback": True,
        "config": {
            "batch_size": 1,
            "wait_between_batches_sec": 60,
            "health_check_interval_sec": 30,
        },
    },
]

MOCK_HISTORY = [
    {
        "upgrade_id": "upg-001",
        "agent_id": "agent-001",
        "agent_name": "Content Writer AI",
        "from_version": "v2.2.0",
        "to_version": "v2.3.0",
        "strategy": "blue-green",
        "status": "completed",
        "start_time": "2026-01-10 08:15:00",
        "end_time": "2026-01-10 08:24:00",
        "duration_min": 9.0,
        "performed_by": "admin@waooaw.com",
    },
    {
        "upgrade_id": "upg-002",
        "agent_id": "agent-003",
        "agent_name": "SDR Agent Alpha",
        "from_version": "v3.0.5",
        "to_version": "v3.1.0",
        "strategy": "canary",
        "status": "completed",
        "start_time": "2026-01-12 14:30:00",
        "end_time": "2026-01-12 14:52:00",
        "duration_min": 22.0,
        "performed_by": "admin@waooaw.com",
    },
    {
        "upgrade_id": "upg-003",
        "agent_id": "agent-002",
        "agent_name": "Math Tutor Pro",
        "from_version": "v1.8.0",
        "to_version": "v1.8.2",
        "strategy": "rolling",
        "status": "rolled_back",
        "start_time": "2026-01-08 10:00:00",
        "end_time": "2026-01-08 10:28:00",
        "duration_min": 28.0,
        "performed_by": "admin@waooaw.com",
    },
]


# ==================== Endpoints ====================

@router.get("/agents", response_model=List[AgentForServicing])
async def list_agents_for_servicing(
    category: Optional[str] = Query(None, description="Filter by category"),
    health: Optional[str] = Query(None, description="Filter by health status"),
) -> List[AgentForServicing]:
    """
    List agents available for servicing/upgrade.
    
    Supports filtering by category and health status.
    """
    agents = MOCK_AGENTS.copy()
    
    if category:
        agents = [a for a in agents if a["category"] == category]
    
    if health:
        agents = [a for a in agents if a["health"] == health]
    
    return [AgentForServicing(**agent) for agent in agents]


@router.get("/versions", response_model=List[AgentVersion])
async def list_available_versions() -> List[AgentVersion]:
    """
    List all available agent versions.
    
    Returns versions sorted by release date (newest first).
    """
    return [AgentVersion(**version) for version in MOCK_VERSIONS]


@router.get("/strategies", response_model=List[DeploymentStrategy])
async def list_deployment_strategies() -> List[DeploymentStrategy]:
    """
    List available deployment strategies.
    
    Each strategy has different risk levels and estimated times.
    """
    return [DeploymentStrategy(**strategy) for strategy in MOCK_STRATEGIES]


@router.post("/upgrade/start", response_model=UpgradeResponse)
async def start_upgrade(request: UpgradeRequest) -> UpgradeResponse:
    """
    Start an agent upgrade with specified strategy.
    
    Supports multiple agents, backup, config patches, and auto-rollback.
    """
    if not request.agent_ids:
        raise HTTPException(status_code=400, detail="No agents specified")
    
    # Validate agents exist
    valid_ids = {a["agent_id"] for a in MOCK_AGENTS}
    invalid = [aid for aid in request.agent_ids if aid not in valid_ids]
    if invalid:
        raise HTTPException(
            status_code=404,
            detail=f"Agents not found: {', '.join(invalid)}"
        )
    
    # Validate version
    if request.target_version not in {v["version_id"] for v in MOCK_VERSIONS}:
        raise HTTPException(
            status_code=404,
            detail=f"Version not found: {request.target_version}"
        )
    
    # Validate strategy
    if request.strategy_id not in {s["strategy_id"] for s in MOCK_STRATEGIES}:
        raise HTTPException(
            status_code=404,
            detail=f"Strategy not found: {request.strategy_id}"
        )
    
    upgrade_id = f"upg-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    return UpgradeResponse(
        upgrade_id=upgrade_id,
        status="started",
        message=f"Upgrade initiated for {len(request.agent_ids)} agent(s)",
        agents_count=len(request.agent_ids),
        estimated_completion=datetime.now().isoformat(),
    )


@router.get("/upgrade/{upgrade_id}/status")
async def get_upgrade_status(upgrade_id: str) -> Dict[str, Any]:
    """
    Get real-time status of an ongoing upgrade.
    
    Returns upgrade progress, health checks, and current step.
    """
    return {
        "upgrade_id": upgrade_id,
        "status": "in_progress",
        "current_step": "deploying",
        "progress_percent": 45,
        "agents_completed": 2,
        "agents_total": 5,
        "health_status": "healthy",
        "can_rollback": True,
        "message": "Deploying new version with canary strategy",
    }


@router.post("/upgrade/{upgrade_id}/rollback")
async def rollback_upgrade(upgrade_id: str, request: RollbackRequest) -> Dict[str, Any]:
    """
    Rollback an upgrade to previous version.
    
    Instantly reverts to the backup created before upgrade.
    """
    return {
        "upgrade_id": upgrade_id,
        "status": "rolling_back",
        "message": f"Rollback initiated: {request.reason}",
        "estimated_completion": datetime.now().isoformat(),
    }


@router.get("/health/{agent_id}", response_model=List[HealthCheckResult])
async def get_health_checks(agent_id: str) -> List[HealthCheckResult]:
    """
    Get health check results for a specific agent.
    
    Returns latest health metrics and status.
    """
    if agent_id not in {a["agent_id"] for a in MOCK_AGENTS}:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return [
        HealthCheckResult(
            check_id="hc-001",
            name="API Endpoint Health",
            status="pass",
            message="All endpoints responding normally",
            timestamp=datetime.now().isoformat(),
            response_time_ms=45.2,
        ),
        HealthCheckResult(
            check_id="hc-002",
            name="Error Rate",
            status="pass",
            message="Error rate within acceptable range",
            timestamp=datetime.now().isoformat(),
            error_rate=0.02,
        ),
        HealthCheckResult(
            check_id="hc-003",
            name="Latency Check",
            status="warning",
            message="Slight latency increase detected",
            timestamp=datetime.now().isoformat(),
            latency_increase=15.5,
        ),
    ]


@router.get("/history", response_model=List[UpgradeHistory])
async def get_upgrade_history(
    limit: int = Query(10, description="Number of records to return"),
) -> List[UpgradeHistory]:
    """
    Get historical upgrade records.
    
    Returns past upgrades with status and performance data.
    """
    return [UpgradeHistory(**record) for record in MOCK_HISTORY[:limit]]


@router.post("/backup/{agent_id}")
async def create_backup(agent_id: str, location: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a backup of agent before upgrade.
    
    Enables safe rollback if upgrade fails.
    """
    if agent_id not in {a["agent_id"] for a in MOCK_AGENTS}:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    backup_id = f"backup-{agent_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    return {
        "backup_id": backup_id,
        "agent_id": agent_id,
        "status": "completed",
        "location": location or "s3://waooaw-backups/agents/",
        "size_mb": 125.4,
        "timestamp": datetime.now().isoformat(),
    }
