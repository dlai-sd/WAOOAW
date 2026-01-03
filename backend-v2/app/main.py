"""
WAOOAW Backend API - Version 2.0
FastAPI application with multi-domain OAuth support
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from .config import settings
from .auth import oauth_v2

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
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
