"""
WAOOAW Plant Phase - Backend API
FastAPI application for agent manufacturing pipeline with constitutional alignment

Architecture: 7-section BaseEntity + L0/L1 constitutional validators + cryptographic signatures
Reference: /docs/plant/PLANT_BLUEPRINT.yaml Section 13
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime
import logging

from core.config import settings
from core.database import engine, Base
from core.exceptions import (
    PlantException,
    ConstitutionalAlignmentError,
    HashChainBrokenError,
    AmendmentSignatureError,
    EntityNotFoundError,
    DuplicateEntityError,
    ValidationError,
)

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="API for agent creation, certification, and constitutional compliance",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    debug=settings.debug,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== EXCEPTION HANDLERS ==========

@app.exception_handler(PlantException)
async def plant_exception_handler(request: Request, exc: PlantException):
    """Handle custom Plant exceptions with standardized response."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": str(exc),
            "error_code": exc.__class__.__name__,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


@app.exception_handler(ConstitutionalAlignmentError)
async def constitutional_error_handler(request: Request, exc: ConstitutionalAlignmentError):
    """Handle L0/L1 constitutional alignment errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": str(exc),
            "error_code": "CONSTITUTIONAL_ALIGNMENT_ERROR",
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "error_code": "VALIDATION_ERROR",
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


# ========== LIFESPAN EVENTS ==========

@app.on_event("startup")
async def startup_event():
    """
    Application startup - initialize database, register routes.
    """
    logging.info("🚀 Starting Plant Phase API")
    logging.info(f"   Environment: {settings.environment}")
    logging.info(f"   Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'unknown'}")
    logging.info(f"   ML Service: {settings.ml_service_url}")
    
    # Create tables (for development - use Alembic in production)
    if settings.debug:
        logging.info("   Creating database tables (development mode)")
        Base.metadata.create_all(bind=engine)


@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown - cleanup connections.
    """
    logging.info("🛑 Shutting down Plant Phase API")


# ========== ROOT ENDPOINTS ==========

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
        "environment": settings.environment,
        "constitutional_alignment": "L0/L1 enforced from first moment",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/health")
async def health_check():
    """Detailed health check with database status."""
    try:
        # Test database connection
        from core.database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected: {str(e)}"
    
    return {
        "status": "healthy",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ========== API ROUTE MOUNTING ==========
# Routes will be added here as they are implemented
# Example:
# from api.v1 import router as api_v1_router
# app.include_router(api_v1_router, prefix=settings.api_v1_prefix)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )

        "status": "operational",
        "version": "0.1.0",
        "stages": [
            "Conceive",
            "Birth",
            "Assembly",
            "Wiring",
            "Power On",
            "Showroom",
            "Hired"
        ]
    }

@app.get("/health")
async def health_check():
    """Kubernetes health probe"""
    return {"status": "healthy"}

# TODO: Import and include routers
# from api import genesis, agents, simulation, audit
# app.include_router(genesis.router, prefix="/api/genesis", tags=["genesis"])
# app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
# app.include_router(simulation.router, prefix="/api/simulation", tags=["simulation"])
# app.include_router(audit.router, prefix="/api/audit", tags=["audit"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
