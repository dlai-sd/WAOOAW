"""
WAOOAW Platform - FastAPI Application Entry Point

Marketplace where AI agents earn your business through 7-day trials.
"""

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logger = structlog.get_logger()

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


@app.get("/api/agents")
async def list_agents():
    """List all available AI agents (stub)"""
    # TODO: Implement agent listing from database
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
    """Platform API - List agents"""
    return {
        "total": 2,
        "agents": [
            {
                "id": "wow-tester",
                "name": "WowTester",
                "type": "coe",
                "status": "online",
                "last_active": "2 minutes ago"
            },
            {
                "id": "wow-benchmark",
                "name": "WowBenchmark",
                "type": "coe",
                "status": "online",
                "last_active": "5 minutes ago"
            }
        ]
    }


@app.get("/api/platform/metrics")
async def platform_metrics():
    """Platform API - System metrics"""
    return {
        "requests_per_minute": 450,
        "tasks_per_minute": 1200,
        "active_agents": 16,
        "error_rate": 0.02,
        "p95_latency": 120.5
    }


@app.get("/api/platform/health")
async def platform_health():
    """Platform API - Health check"""
    return {
        "status": "healthy",
        "components": {
            "database": "healthy",
            "redis": "healthy",
            "agents": "healthy",
            "event_bus": "healthy"
        }
    }


# Register OAuth router
from app.auth import oauth_router
app.include_router(oauth_router)


@app.on_event("startup")
async def startup_event():
    """Startup tasks"""
    logger.info("waooaw_startup", message="WAOOAW Platform API starting...")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown tasks"""
    logger.info("waooaw_shutdown", message="WAOOAW Platform API shutting down...")
