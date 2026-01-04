"""
WAOOAW Backend API - Version 2.0
FastAPI application with multi-domain OAuth support
"""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import structlog

from .config import settings
from .auth import oauth_v2
from .mock_data import get_agents, get_agent_by_id

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)

logger = structlog.get_logger()

# Create FastAPI application
app = FastAPI(
    title="WAOOAW API v2",
    description="Multi-domain backend with environment-aware OAuth",
    version="2.0.0",
    debug=settings.DEBUG,
)

# CORS middleware - environment-aware origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(oauth_v2.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "WAOOAW API",
        "version": "2.0.0",
        "environment": settings.ENV,
        "status": "operational",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run"""
    return {
        "status": "healthy",
        "environment": settings.ENV,
        "db_schema": settings.DB_SCHEMA,
    }


@app.get("/config")
async def config_info():
    """Configuration info (for debugging)"""
    return {
        "environment": settings.ENV,
        "db_schema": settings.DB_SCHEMA,
        "cors_origins": settings.CORS_ORIGINS,
        "domains": settings.DOMAIN_CONFIG[settings.ENV],
    }


@app.get("/agents")
async def list_agents(
    industry: Optional[str] = Query(
        None, description="Filter by industry: marketing, education, sales"
    ),
    min_rating: float = Query(
        0.0, description="Minimum rating (0.0 to 5.0)", ge=0.0, le=5.0
    ),
):
    """
    List all available agents with optional filters.

    Using mock data - no database required for demo.
    """
    agents = get_agents(industry=industry, min_rating=min_rating)
    logger.info(
        "agents_listed",
        count=len(agents),
        industry=industry,
        min_rating=min_rating,
    )
    return agents


@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """
    Get details for a specific agent by ID.

    Using mock data - no database required for demo.
    """
    agent = get_agent_by_id(agent_id)
    if not agent:
        logger.warning("agent_not_found", agent_id=agent_id)
        return JSONResponse(
            status_code=404,
            content={"detail": f"Agent {agent_id} not found"},
        )

    logger.info("agent_retrieved", agent_id=agent_id, agent_name=agent.get("name"))
    return agent


# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info(
        "application_startup",
        environment=settings.ENV,
        db_schema=settings.DB_SCHEMA,
        cors_origins=settings.CORS_ORIGINS,
    )


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("application_shutdown", environment=settings.ENV)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(
        "unhandled_exception",
        error=str(exc),
        path=request.url.path,
        method=request.method,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
