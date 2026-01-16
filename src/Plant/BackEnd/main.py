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
from core.database import Base, initialize_database
from core.exceptions import (
    PlantException,
    ConstitutionalAlignmentError,
    HashChainBrokenError,
    AmendmentSignatureError,
    EntityNotFoundError,
    DuplicateEntityError,
    ValidationError,
)

# Initialize FastAPI app with enhanced OpenAPI metadata
app = FastAPI(
    title=settings.app_name,
    description="""
# WAOOAW Plant Phase API

Backend API for agent manufacturing pipeline with constitutional alignment (L0/L1 principles).

## Key Features
- **Genesis Certification**: Skills and job roles certified via multi-gate approval
- **Agent Creation**: Constitutional validation with industry locking
- **Audit & Compliance**: L0/L1 constitutional alignment tracking
- **Type Safety**: Full OpenAPI 3.0 spec for TypeScript codegen

## Constitutional Principles (L0)
- **L0-01**: Single Governor - governance_agent_id required
- **L0-02**: Agent Specialization - skills + job roles certified before use
- **L0-03**: External Execution Approval - trial mode sandbox enforcement
- **L0-05**: Immutable Audit Trail - all entity changes logged
- **L0-06**: Version Control - hash-based version tracking
- **L0-07**: Amendment History - signature-verified evolution

## Authentication (Future)
- JWT tokens validated at gateway layer
- RBAC enforcement for Genesis/Governor operations
- Trial mode sandbox routing via OPA policy

## Rate Limits (Future)
- 100 req/min per customer (trial mode)
- 1000 req/min per customer (paid subscription)

## Support
- Documentation: https://docs.waooaw.com
- GitHub: https://github.com/dlai-sd/WAOOAW
""",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    debug=settings.debug,
    contact={
        "name": "WAOOAW Engineering Team",
        "url": "https://waooaw.com",
        "email": "engineering@waooaw.com"
    },
    license_info={
        "name": "Proprietary",
        "url": "https://waooaw.com/license"
    }
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== EXCEPTION HANDLERS (RFC 7807 Format) ==========

@app.exception_handler(PlantException)
async def plant_exception_handler(request: Request, exc: PlantException):
    """Handle custom Plant exceptions with RFC 7807 format."""
    correlation_id = request.headers.get("X-Correlation-ID", str(datetime.utcnow().timestamp()))
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "type": "https://waooaw.com/errors/plant-exception",
            "title": "Plant Exception",
            "status": 400,
            "detail": str(exc),
            "instance": str(request.url.path),
            "correlation_id": correlation_id,
        }
    )


@app.exception_handler(ConstitutionalAlignmentError)
async def constitutional_error_handler(request: Request, exc: ConstitutionalAlignmentError):
    """Handle L0/L1 constitutional alignment errors with RFC 7807 format."""
    correlation_id = request.headers.get("X-Correlation-ID", str(datetime.utcnow().timestamp()))
    
    # Extract violations from error message
    violations = []
    error_message = str(exc)
    if "L0-01" in error_message:
        violations.append("L0-01: Single Governor - governance_agent_id required")
    if "L0-02" in error_message:
        violations.append("L0-02: Agent Specialization - certified skills/roles required")
    if "L0-05" in error_message:
        violations.append("L0-05: Immutable Audit Trail - audit logging failed")
    if "L0-06" in error_message:
        violations.append("L0-06: Version Control - hash calculation failed")
    if "L0-07" in error_message:
        violations.append("L0-07: Amendment History - signature verification failed")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "type": "https://waooaw.com/errors/constitutional-alignment",
            "title": "Constitutional Alignment Error",
            "status": 422,
            "detail": error_message,
            "instance": str(request.url.path),
            "correlation_id": correlation_id,
            "violations": violations if violations else [error_message],
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with RFC 7807 format."""
    correlation_id = request.headers.get("X-Correlation-ID", str(datetime.utcnow().timestamp()))
    
    # Format Pydantic errors into human-readable violations
    violations = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        violations.append(f"{field}: {error['msg']}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "type": "https://waooaw.com/errors/validation-error",
            "title": "Request Validation Error",
            "status": 422,
            "detail": f"Request validation failed: {len(violations)} error(s)",
            "instance": str(request.url.path),
            "correlation_id": correlation_id,
            "violations": violations,
        }
    )


@app.exception_handler(EntityNotFoundError)
async def not_found_handler(request: Request, exc: EntityNotFoundError):
    """Handle entity not found errors with RFC 7807 format."""
    correlation_id = request.headers.get("X-Correlation-ID", str(datetime.utcnow().timestamp()))
    
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "type": "https://waooaw.com/errors/not-found",
            "title": "Entity Not Found",
            "status": 404,
            "detail": str(exc),
            "instance": str(request.url.path),
            "correlation_id": correlation_id,
        }
    )


@app.exception_handler(DuplicateEntityError)
async def duplicate_entity_handler(request: Request, exc: DuplicateEntityError):
    """Handle duplicate entity errors with RFC 7807 format."""
    correlation_id = request.headers.get("X-Correlation-ID", str(datetime.utcnow().timestamp()))
    
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "type": "https://waooaw.com/errors/duplicate-entity",
            "title": "Duplicate Entity Error",
            "status": 409,
            "detail": str(exc),
            "instance": str(request.url.path),
            "correlation_id": correlation_id,
        }
    )


@app.exception_handler(HashChainBrokenError)
async def hash_chain_error_handler(request: Request, exc: HashChainBrokenError):
    """Handle hash chain integrity errors with RFC 7807 format."""
    correlation_id = request.headers.get("X-Correlation-ID", str(datetime.utcnow().timestamp()))
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "type": "https://waooaw.com/errors/hash-chain-broken",
            "title": "Hash Chain Integrity Error",
            "status": 500,
            "detail": str(exc),
            "instance": str(request.url.path),
            "correlation_id": correlation_id,
            "violations": ["L0-06: Version Control - hash chain compromised"],
        }
    )


@app.exception_handler(AmendmentSignatureError)
async def amendment_signature_handler(request: Request, exc: AmendmentSignatureError):
    """Handle amendment signature errors with RFC 7807 format."""
    correlation_id = request.headers.get("X-Correlation-ID", str(datetime.utcnow().timestamp()))
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "type": "https://waooaw.com/errors/amendment-signature",
            "title": "Amendment Signature Error",
            "status": 422,
            "detail": str(exc),
            "instance": str(request.url.path),
            "correlation_id": correlation_id,
            "violations": ["L0-07: Amendment History - signature verification failed"],
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions with RFC 7807 format."""
    correlation_id = request.headers.get("X-Correlation-ID", str(datetime.utcnow().timestamp()))
    
    # Log the exception (add proper logging in production)
    logging.error(f"Unhandled exception: {type(exc).__name__}: {str(exc)}", exc_info=exc)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "type": "https://waooaw.com/errors/internal-server-error",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected error occurred. Please try again later.",
            "instance": str(request.url.path),
            "correlation_id": correlation_id,
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
    
    # Initialize database connection (async)
    await initialize_database()
    
    # NOTE: Use Alembic migrations for production, not create_all
    logging.info("   Database initialization complete")


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
from api.v1.router import api_v1_router
app.include_router(api_v1_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )

