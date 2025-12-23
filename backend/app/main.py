"""
WAOOAW Platform - FastAPI Application Entry Point

Marketplace where AI agents earn your business through 7-day trials.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.api.routes.domain_factory import router as domain_factory_router

logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="WAOOAW Platform API",
    description="AI Agent Marketplace - Agents Earn Your Business",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Include routers
app.include_router(domain_factory_router)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://*.github.dev",  # GitHub Codespaces
        "https://*.app.github.dev",  # GitHub Codespaces
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


@app.on_event("startup")
async def startup_event():
    """Startup tasks"""
    logger.info("waooaw_startup", message="WAOOAW Platform API starting...")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown tasks"""
    logger.info("waooaw_shutdown", message="WAOOAW Platform API shutting down...")
