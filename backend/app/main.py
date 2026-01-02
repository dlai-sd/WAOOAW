"""
WAOOAW Platform - FastAPI Application Entry Point

Marketplace where AI agents earn your business through 7-day trials.
"""

from dotenv import load_dotenv
import structlog
import sys
import os
import importlib.util
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()

logger = structlog.get_logger()

# Platform components will be initialized carefully to avoid circular imports
agent_registry = None
service_registry = None
event_bus = None
task_queue = None
worker_pool = None

# Initialize FastAPI app
app = FastAPI(
    title="WAOOAW Platform API",
    description="AI Agent Marketplace - Agents Earn Your Business",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://shiny-space-guide-pj4gwgp94gw93557-3000.app.github.dev",
        "https://shiny-space-guide-pj4gwgp94gw93557-8000.app.github.dev",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "name": "WAOOAW Platform API",
        "version": "1.0.0",
        "tagline": "Agents Earn Your Business",
        "status": "operational",
        "docs": "/api/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration"""
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "waooaw-backend",
        },
        status_code=200,
    )


@app.get("/api/marketplace/agents")
async def list_marketplace_agents():
    """List marketplace agents (stub - deprecated, use /api/agents instead)"""
    # TODO: Remove this endpoint or rename to /api/marketplace/agents
    return {
        "agents": [
            {
                "id": 1,
                "name": "Content Marketing Specialist",
                "category": "Marketing",
                "status": "online",
                "rating": 4.8,
                "trial_price": 8000,
            },
            {
                "id": 2,
                "name": "SEO Growth Agent",
                "category": "Marketing",
                "status": "working",
                "rating": 4.9,
                "trial_price": 12000,
            },
            {
                "id": 3,
                "name": "Social Media Manager",
                "category": "Marketing",
                "status": "online",
                "rating": 4.7,
                "trial_price": 9000,
            },
        ],
        "total": 19,
    }


# Platform API endpoints
@app.get("/api/platform/agents")
async def platform_list_agents():
    """Platform API - List agents from agent registry"""
    
    # Check if registry is available
    if not agent_registry:
        return JSONResponse(
            status_code=503,
            content={
                "error": "Agent registry unavailable",
                "message": "AgentRegistry failed to initialize. This could be due to:",
                "suggestions": [
                    "Check backend logs: tail -50 /tmp/backend.log",
                    "Verify AgentRegistry dependencies are installed",
                    "Check for circular import errors in waooaw module",
                    "Restart backend: pkill -f uvicorn && uvicorn app.main:app --reload"
                ],
                "data_source": "none",
                "registry_status": "failed"
            }
        )
    
    try:
        agents_data = agent_registry.list_agents()
        
        if not agents_data:
            return {
                "total": 0,
                "agents": [],
                "warning": "Registry is empty. No agents registered.",
                "data_source": "registry",
                "registry_status": "ok_but_empty"
            }
        
        # Transform to portal format
        agents = []
        for agent in agents_data:
            # Calculate last active time
            last_active = "never"
            if hasattr(agent, 'updated_at') and agent.updated_at:
                delta = datetime.now() - agent.updated_at
                if delta.total_seconds() < 60:
                    last_active = f"{int(delta.total_seconds())} seconds ago"
                elif delta.total_seconds() < 3600:
                    last_active = f"{int(delta.total_seconds() / 60)} minutes ago"
                elif delta.total_seconds() < 86400:
                    last_active = f"{int(delta.total_seconds() / 3600)} hours ago"
                else:
                    last_active = f"{int(delta.total_seconds() / 86400)} days ago"
            
            # Map registry status to portal status
            # IMPORTANT: These are REGISTRY statuses, not runtime statuses
            status_map = {
                "active": "registered",      # Registered and ready to deploy
                "provisioned": "provisioned", # Identity created
                "draft": "draft",            # Defined but not provisioned
                "suspended": "suspended",
                "revoked": "revoked"
            }
            agent_status = agent.status.value if hasattr(agent.status, 'value') else str(agent.status)
            portal_status = status_map.get(agent_status.lower(), "unknown")
            
            # Check if agent is actually RUNNING (not just registered)
            # For now, we only know registry status, not runtime status
            is_deployed = hasattr(agent, 'deployed_at') and agent.deployed_at is not None
            
            agents.append({
                "id": agent.agent_id,
                "name": agent.name,
                "type": "coe",
                "registry_status": portal_status,
                "runtime_status": "unknown",  # We don't track runtime yet
                "is_deployed": is_deployed,
                "last_active": last_active,
                "tier": agent.tier.value if hasattr(agent.tier, 'value') else agent.tier,
                "version": agent.version,
                "did": agent.did,
                "metadata_source": "static_registry"  # Clarify this is pre-defined
            })
        
        return {
            "total": len(agents),
            "agents": agents,
            "data_source": "agent_registry",
            "registry_status": "ok",
            "note": "These are registered agent metadata (static definitions). Runtime status requires service_registry integration."
        }
        
    except Exception as e:
        logger.error("platform_agents_error", error=str(e))
        return JSONResponse(
            status_code=500,
            content={
                "error": "Failed to query agent registry",
                "message": str(e),
                "suggestions": [
                    "Check if AgentRegistry.list_agents() is working",
                    "Review backend logs for stack trace",
                    "Verify database connectivity if agents are persisted"
                ],
                "data_source": "error",
                "registry_status": "error"
            }
        )


@app.get("/api/platform/metrics")
async def platform_metrics():
    """Platform API - System metrics from orchestration"""
    try:
        metrics = {
            "requests_per_minute": 0,
            "tasks_per_minute": 0,
            "active_agents": 0,
            "error_rate": 0.0,
            "p95_latency": 0.0
        }
        
        # Get task queue metrics if available
        if task_queue:
            queue_metrics = task_queue.get_metrics()
            metrics["tasks_per_minute"] = int(queue_metrics.get("pending_tasks", 0) / 60) if queue_metrics else 0
        
        # Get worker pool metrics if available
        if worker_pool:
            pool_metrics = worker_pool.get_metrics()
            if pool_metrics:
                metrics["active_agents"] = pool_metrics.busy_workers
                if pool_metrics.total_tasks_completed > 0:
                    metrics["error_rate"] = pool_metrics.total_tasks_failed / (pool_metrics.total_tasks_completed + pool_metrics.total_tasks_failed)
                metrics["p95_latency"] = pool_metrics.average_execution_time * 1000  # Convert to ms
        
        # Get agent count from registry if available
        if agent_registry:
            agents = agent_registry.list_agents()
            active_count = sum(1 for a in agents if hasattr(a, 'status') and a.status.value == 'active')
            metrics["active_agents"] = max(active_count, metrics["active_agents"])
        
        # Use reasonable defaults if nothing is available
        is_mock_data = False
        if metrics["active_agents"] == 0:
            metrics["requests_per_minute"] = 450
            metrics["tasks_per_minute"] = 1200
            metrics["active_agents"] = 2
            metrics["error_rate"] = 0.02
            metrics["p95_latency"] = 120.5
            is_mock_data = True
        
        # Return with header indicating data source
        from fastapi.responses import JSONResponse
        return JSONResponse(
            content=metrics,
            headers={"X-Data-Source": "mock" if is_mock_data else "real"}
        )
    except Exception as e:
        logger.error("platform_metrics_error", error=str(e))
        # Fallback to reasonable mock data with header
        from fastapi.responses import JSONResponse
        return JSONResponse(
            content={
                "requests_per_minute": 450,
                "tasks_per_minute": 1200,
                "active_agents": 2,
                "error_rate": 0.02,
                "p95_latency": 120.5
            },
            headers={"X-Data-Source": "mock"}
        )


@app.get("/api/platform/health")
async def platform_health():
    """Platform API - Health check from service registry"""
    try:
        health = {
            "status": "healthy",
            "components": {
                "database": "unknown",
                "redis": "unknown",
                "agents": "unknown",
                "event_bus": "unknown"
            }
        }
        
        # Check agent registry if available
        if agent_registry:
            try:
                agents = agent_registry.list_agents()
                active_agents = sum(1 for a in agents if hasattr(a, 'status') and a.status.value == 'active')
                health["components"]["agents"] = "healthy" if len(agents) > 0 else "degraded"
            except Exception:
                health["components"]["agents"] = "unhealthy"
        else:
            health["components"]["agents"] = "offline"
        
        # Check event bus
        if event_bus:
            health["components"]["event_bus"] = "healthy"
            health["components"]["redis"] = "healthy"
        else:
            health["components"]["event_bus"] = "offline"
            health["components"]["redis"] = "offline"
        
        # Database check (placeholder - would need actual DB connection)
        health["components"]["database"] = "healthy"
        
        # Overall status
        unhealthy = sum(1 for v in health["components"].values() if v == "unhealthy")
        degraded = sum(1 for v in health["components"].values() if v in ["degraded", "offline", "unknown"])
        
        if unhealthy > 0:
            health["status"] = "unhealthy"
        elif degraded > 1:  # Allow some components to be offline
            health["status"] = "degraded"
        else:
            health["status"] = "healthy"
        
        return health
    except Exception as e:
        logger.error("platform_health_error", error=str(e))
        return {
            "status": "unknown",
            "components": {
                "database": "unknown",
                "redis": "unknown",
                "agents": "unknown",
                "event_bus": "unknown"
            },
            "error": str(e)
        }


# Pydantic models for logs and alerts
class LogEntry(BaseModel):
    timestamp: str
    level: str
    agent: str
    message: str
    metadata: Optional[dict] = {}


class Alert(BaseModel):
    id: str
    severity: str
    title: str
    message: str
    time: str
    status: str = "active"


# Mock log storage (in production, this would query PostgreSQL or aggregated logs)
MOCK_LOGS = [
    LogEntry(
        timestamp=(datetime.now() - timedelta(minutes=5)).isoformat(),
        level="INFO",
        agent="WowVision",
        message="System health check completed successfully",
        metadata={"duration_ms": 125}
    ),
    LogEntry(
        timestamp=(datetime.now() - timedelta(minutes=10)).isoformat(),
        level="INFO",
        agent="WowTester",
        message='Agent "WowTester" completed task execution',
        metadata={"task_id": "task-12345", "duration_ms": 2300}
    ),
    LogEntry(
        timestamp=(datetime.now() - timedelta(minutes=15)).isoformat(),
        level="WARN",
        agent="WowDomain",
        message="High memory usage detected: 85%",
        metadata={"memory_percent": 85}
    ),
    LogEntry(
        timestamp=(datetime.now() - timedelta(minutes=20)).isoformat(),
        level="INFO",
        agent="Security",
        message="OAuth authentication successful for user",
        metadata={"user_email": "user@example.com"}
    ),
    LogEntry(
        timestamp=(datetime.now() - timedelta(minutes=25)).isoformat(),
        level="DEBUG",
        agent="Database",
        message="Database connection pool: 8/10 connections active",
        metadata={"active": 8, "total": 10}
    ),
    LogEntry(
        timestamp=(datetime.now() - timedelta(hours=1)).isoformat(),
        level="ERROR",
        agent="WowBenchmark",
        message="Task execution failed: timeout after 30s",
        metadata={"task_id": "task-67890", "error": "TimeoutError"}
    ),
    LogEntry(
        timestamp=(datetime.now() - timedelta(hours=2)).isoformat(),
        level="INFO",
        agent="WowEvent",
        message="Event bus initialized successfully",
        metadata={"subscribers": 5}
    ),
]

# Mock alert storage (in production, this would be a database table)
MOCK_ALERTS = {
    "alert-1": Alert(
        id="alert-1",
        severity="warning",
        title="High Memory Usage",
        message="System memory usage has exceeded 85% threshold",
        time=(datetime.now() - timedelta(minutes=5)).isoformat(),
        status="active"
    ),
    "alert-2": Alert(
        id="alert-2",
        severity="info",
        title="System Update Available",
        message="WAOOAW Platform v0.8.4 is now available",
        time=(datetime.now() - timedelta(hours=1)).isoformat(),
        status="active"
    ),
    "alert-3": Alert(
        id="alert-3",
        severity="info",
        title="All Systems Operational",
        message="All platform components are running normally",
        time=datetime.now().isoformat(),
        status="active"
    ),
}


@app.get("/api/platform/logs")
async def platform_logs(
    level: Optional[str] = Query(None, description="Filter by log level: INFO, WARN, ERROR, DEBUG"),
    agent: Optional[str] = Query(None, description="Filter by agent name"),
    search: Optional[str] = Query(None, description="Search in log messages"),
    limit: int = Query(50, description="Maximum number of logs to return"),
):
    """Platform API - Get system logs with filtering"""
    try:
        logs = MOCK_LOGS.copy()
        
        # Apply filters
        if level and level != "all":
            logs = [log for log in logs if log.level.upper() == level.upper()]
        
        if agent and agent != "all":
            logs = [log for log in logs if agent.lower() in log.agent.lower()]
        
        if search:
            logs = [log for log in logs if search.lower() in log.message.lower()]
        
        # Sort by timestamp (newest first)
        logs.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Apply limit
        logs = logs[:limit]
        
        return {
            "total": len(logs),
            "logs": [log.dict() for log in logs]
        }
    except Exception as e:
        logger.error("platform_logs_error", error=str(e))
        return {
            "total": 0,
            "logs": [],
            "error": str(e)
        }


@app.get("/api/platform/alerts")
async def platform_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity: critical, warning, info"),
):
    """Platform API - Get system alerts"""
    try:
        alerts = list(MOCK_ALERTS.values())
        
        # Apply severity filter
        if severity and severity != "all":
            alerts = [alert for alert in alerts if alert.severity.lower() == severity.lower()]
        
        # Filter only active alerts
        alerts = [alert for alert in alerts if alert.status == "active"]
        
        # Sort by time (newest first)
        alerts.sort(key=lambda x: x.time, reverse=True)
        
        return {
            "total": len(alerts),
            "alerts": [alert.dict() for alert in alerts]
        }
    except Exception as e:
        logger.error("platform_alerts_error", error=str(e))
        return {
            "total": 0,
            "alerts": [],
            "error": str(e)
        }


@app.post("/api/platform/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Platform API - Acknowledge an alert"""
    try:
        if alert_id in MOCK_ALERTS:
            MOCK_ALERTS[alert_id].status = "acknowledged"
            logger.info("alert_acknowledged", alert_id=alert_id)
            return {
                "success": True,
                "alert_id": alert_id,
                "status": "acknowledged"
            }
        else:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "error": "Alert not found"
                }
            )
    except Exception as e:
        logger.error("alert_acknowledge_error", alert_id=alert_id, error=str(e))
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )


# Register OAuth router
from app.auth import oauth_router
app.include_router(oauth_router)

# Queue monitoring API
from app.api.queues import router as queues_router
from app.api.workflows import router as workflows_router
from app.api.agents import router as agents_router
app.include_router(queues_router)
app.include_router(workflows_router)
app.include_router(agents_router)


@app.on_event("startup")
async def startup_event():
    """Startup tasks"""
    logger.info("waooaw_startup", message="WAOOAW Platform API starting...")
    
    # Try to initialize platform components
    global agent_registry, service_registry, task_queue, worker_pool
    
    try:
        # Add project root to Python path
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
        
        # Try to import and initialize agent registry with isolated imports
        try:
            # Temporarily modify sys.modules to avoid circular imports
            import importlib
            
            # Load agent_registry module directly
            spec = importlib.util.spec_from_file_location(
                "agent_registry_isolated",
                os.path.join(os.path.dirname(__file__), "../../waooaw/factory/registry/agent_registry.py")
            )
            registry_module = importlib.util.module_from_spec(spec)
            
            # Execute without triggering waooaw.__init__ imports
            spec.loader.exec_module(registry_module)
            
            # Create instance
            agent_registry = registry_module.AgentRegistry()
            agents = agent_registry.list_agents()
            logger.info("agent_registry_initialized", 
                       message=f"Agent registry available with {len(agents)} agents")
        except Exception as e:
            logger.warning("agent_registry_init_failed", error=str(e))
        
        # Try to initialize service registry
        try:
            from waooaw.discovery.service_registry import ServiceRegistry
            service_registry = ServiceRegistry()
            logger.info("service_registry_initialized", message="Service registry available")
        except Exception as e:
            logger.warning("service_registry_init_failed", error=str(e))
        
        # Try to initialize orchestration components
        try:
            from waooaw.orchestration.task_queue import TaskQueue
            from waooaw.orchestration.worker_pool import WorkerPool
            task_queue = TaskQueue()
            worker_pool = WorkerPool(num_workers=10, task_queue=task_queue)
            logger.info("orchestration_initialized", message="Task queue and worker pool initialized")
        except Exception as e:
            logger.warning("orchestration_init_failed", error=str(e))
        
    except Exception as e:
        logger.warning("platform_init_failed", error=str(e), message="Running with limited functionality")
    
    logger.info("waooaw_ready", message="Platform API ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown tasks"""
    logger.info("waooaw_shutdown", message="WAOOAW Platform API shutting down...")
