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
from datetime import datetime, timezone
import os
import logging

from core.config import settings
from core.database import Base, initialize_database
from core.observability import (
    setup_observability,
    get_logger,
    log_route_registration,
    RequestLoggingMiddleware,
)
from core.metrics import setup_metrics, MetricsMiddleware

# Configure observability BEFORE any other imports that use logging
setup_observability(settings)
logger = get_logger(__name__)
from core.exceptions import (
    PlantException,
    ConstitutionalAlignmentError,
    HashChainBrokenError,
    AmendmentSignatureError,
    EntityNotFoundError,
    DuplicateEntityError,
    ValidationError,
    PolicyEnforcementError,
    UsageLimitError,
    JWTTokenExpiredError,
    JWTInvalidSignatureError,
    JWTInvalidTokenError,
    BearerTokenMissingError,
    JWTMissingClaimError,
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

# CORS configuration - allow specific origins only
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,  # Allow cookies/JWT tokens (future)
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Correlation-ID",
        "X-Causation-ID",
        "X-Request-ID",
    ],
    expose_headers=[
        "X-Correlation-ID",
        "X-Causation-ID",
        "X-Request-ID",
    ],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Prometheus metrics middleware (always enabled for /metrics endpoint)
app.add_middleware(MetricsMiddleware)
logger.info("✅ Prometheus metrics middleware ENABLED")

# Request logging middleware (controlled by ENABLE_REQUEST_LOGGING)
if settings.enable_request_logging:
    app.add_middleware(RequestLoggingMiddleware, enable_logging=True)
    logger.info("✅ Request logging middleware ENABLED")


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


# ========== AUTHENTICATION ERROR HANDLERS ==========

@app.exception_handler(JWTTokenExpiredError)
async def jwt_expired_handler(request: Request, exc: JWTTokenExpiredError):
    """Handle expired JWT tokens with detailed guidance."""
    correlation_id = request.headers.get("X-Correlation-ID", str(datetime.utcnow().timestamp()))
    
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "type": "https://waooaw.com/errors/jwt-expired",
            "title": "JWT Token Expired",
            "status": 401,
            "detail": str(exc),
            "instance": str(request.url.path),
            "correlation_id": correlation_id,
            "expired_at": exc.expired_at,
        },
        headers={"WWW-Authenticate": "Bearer"}
    )


@app.exception_handler(JWTInvalidSignatureError)
async def jwt_invalid_signature_handler(request: Request, exc: JWTInvalidSignatureError):
    """Handle JWT signature verification failures."""
    correlation_id = request.headers.get("X-Correlation-ID", str(datetime.utcnow().timestamp()))
    
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "type": "https://waooaw.com/errors/jwt-invalid-signature",
            "title": "JWT Invalid Signature",
            "status": 401,
            "detail": str(exc),
            "instance": str(request.url.path),
            "correlation_id": correlation_id,
        },
        headers={"WWW-Authenticate": "Bearer"}
    )


@app.exception_handler(JWTInvalidTokenError)
async def jwt_invalid_token_handler(request: Request, exc: JWTInvalidTokenError):
    """Handle malformed JWT tokens."""
    correlation_id = request.headers.get("X-Correlation-ID", str(datetime.utcnow().timestamp()))
    
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "type": "https://waooaw.com/errors/jwt-invalid-token",
            "title": "JWT Invalid Token",
            "status": 401,
            "detail": str(exc),
            "instance": str(request.url.path),
            "correlation_id": correlation_id,
            "reason": exc.reason,
        },
        headers={"WWW-Authenticate": "Bearer"}
    )


@app.exception_handler(BearerTokenMissingError)
async def bearer_token_missing_handler(request: Request, exc: BearerTokenMissingError):
    """Handle missing or malformed Authorization headers."""
    correlation_id = request.headers.get("X-Correlation-ID", str(datetime.utcnow().timestamp()))
    
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "type": "https://waooaw.com/errors/bearer-token-missing",
            "title": "Bearer Token Missing",
            "status": 401,
            "detail": str(exc),
            "instance": str(request.url.path),
            "correlation_id": correlation_id,
        },
        headers={"WWW-Authenticate": "Bearer"}
    )


@app.exception_handler(JWTMissingClaimError)
async def jwt_missing_claim_handler(request: Request, exc: JWTMissingClaimError):
    """Handle JWT tokens missing required claims."""
    correlation_id = request.headers.get("X-Correlation-ID", str(datetime.utcnow().timestamp()))
    
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "type": "https://waooaw.com/errors/jwt-missing-claim",
            "title": "JWT Missing Required Claim",
            "status": 401,
            "detail": str(exc),
            "instance": str(request.url.path),
            "correlation_id": correlation_id,
            "missing_claim": exc.claim,
        },
        headers={"WWW-Authenticate": "Bearer"}
    )


# ========== CONSTITUTIONAL ERROR HANDLERS ==========

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


@app.exception_handler(PolicyEnforcementError)
async def policy_enforcement_error_handler(request: Request, exc: PolicyEnforcementError):
    """Return policy denials as explicit 403s (RFC 7807)."""

    correlation_id = request.headers.get("X-Correlation-ID", str(datetime.utcnow().timestamp()))

    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "type": "https://waooaw.com/errors/policy-enforcement-denied",
            "title": "Policy Enforcement Denied",
            "status": 403,
            "detail": str(exc),
            "instance": str(request.url.path),
            "correlation_id": correlation_id,
            "reason": getattr(exc, "reason", None),
            "details": getattr(exc, "details", None),
        },
    )


@app.exception_handler(UsageLimitError)
async def usage_limit_error_handler(request: Request, exc: UsageLimitError):
    """Return metering denials as explicit 429s (RFC 7807)."""

    correlation_id = request.headers.get("X-Correlation-ID", str(datetime.utcnow().timestamp()))

    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "type": "https://waooaw.com/errors/usage-limit-denied",
            "title": "Usage Limit Denied",
            "status": 429,
            "detail": str(exc),
            "instance": str(request.url.path),
            "correlation_id": correlation_id,
            "reason": getattr(exc, "reason", None),
            "details": getattr(exc, "details", None),
        },
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


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception):
    """
    Handle 404 Not Found errors with helpful guidance.
    
    Provides available routes and documentation links.
    """
    correlation_id = request.headers.get("X-Correlation-ID", str(datetime.utcnow().timestamp()))
    
    # Build list of available routes
    available_routes = []
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            methods = ", ".join(sorted(route.methods - {"HEAD", "OPTIONS"}))
            if methods:  # Skip routes with no user-facing methods
                available_routes.append(f"{methods:8} {route.path}")
    
    available_routes_str = "\n".join(sorted(available_routes)[:20])  # Show first 20 routes
    
    detail_msg = (
        f"❌ Route Not Found\n\n"
        f"PROBLEM:\n"
        f"The requested path does not exist: {request.url.path}\n\n"
        f"AVAILABLE ROUTES (first 20):\n"
        f"{available_routes_str}\n"
        f"... and more (see API documentation)\n\n"
        f"COMMON MISTAKES:\n"
        f"- Typos in URL path\n"
        f"- Missing /api/v1 prefix\n"
        f"- Wrong HTTP method (e.g., POST instead of GET)\n"
        f"- Route exists but requires different version\n\n"
        f"DOCUMENTATION:\n"
        f"- API Reference: {request.url.scheme}://{request.url.netloc}/docs\n"
        f"- OpenAPI Spec: {request.url.scheme}://{request.url.netloc}/openapi.json\n"
        f"- Full docs: https://docs.waooaw.com/api\n\n"
        f"SUPPORT:\n"
        f"If you believe this route should exist, please contact:\n"
        f"- Email: engineering@waooaw.com\n"
        f"- Include correlation ID: {correlation_id}"
    )
    
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "type": "https://waooaw.com/errors/not-found",
            "title": "Route Not Found",
            "status": 404,
            "detail": detail_msg,
            "instance": str(request.url.path),
            "correlation_id": correlation_id,
            "available_routes": available_routes[:20],
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
    if settings.enable_startup_diagnostics:
        logger.info("=" * 80)
        logger.info("🚀 PLANT BACKEND STARTING")
        logger.info("=" * 80)
        logger.info(f"   Environment: {settings.environment}")
        logger.info(f"   App Version: {settings.app_version}")
        logger.info(f"   Debug Mode: {settings.debug}")
        logger.info(f"   Workers: {os.getenv('WORKERS', 'N/A')}")
        logger.info(f"   Process ID: {os.getpid()}")
        logger.info(f"   Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'unknown'}")
        logger.info(f"   ML Service: {settings.ml_service_url}")
        logger.info("=" * 80)
    else:
        logger.info("🚀 Starting Plant Phase API")
        logger.info(f"   Environment: {settings.environment}")
        logger.info(f"   Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'unknown'}")
        logger.info(f"   ML Service: {settings.ml_service_url}")
    
    # Initialize database connection (async).
    # CI unit tests run without a Postgres service; those tests should be able
    # to use TestClient without requiring DB connectivity.
    running_under_pytest = os.getenv("PYTEST_CURRENT_TEST") is not None
    force_db_init = os.getenv("PLANT_FORCE_DB_INIT", "false").lower() in {"1", "true", "yes"}

    if running_under_pytest and not force_db_init:
        logger.info("   Skipping database initialization (pytest context)")
    else:
        await initialize_database()
    
    # Setup Prometheus metrics
    setup_metrics(app, version=settings.app_version)
    logger.info("   ✅ Prometheus metrics initialized (/metrics endpoint)")

    # Optional marketing scheduler (off by default to keep tests deterministic).
    if os.getenv("ENABLE_MARKETING_SCHEDULER", "false").lower() in {"1", "true", "yes"}:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        from api.v1.agent_mold import get_usage_event_store
        from services.draft_batches import FileDraftBatchStore
        from services.marketing_scheduler import run_due_posts_once

        store_path = os.getenv("DRAFT_BATCH_STORE_PATH", "/app/data/draft_batches.jsonl")
        store = FileDraftBatchStore(store_path)
        usage_events = get_usage_event_store()

        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            run_due_posts_once,
            trigger="interval",
            seconds=int(os.getenv("MARKETING_SCHEDULER_INTERVAL_SECONDS", "30")),
            args=[store, None, usage_events],
            id="marketing_due_posts",
            replace_existing=True,
        )
        scheduler.start()
        app.state.marketing_scheduler = scheduler
        logger.info("   Marketing scheduler enabled")

    # Optional goal draft scheduler (off by default to keep tests deterministic).
    if os.getenv("ENABLE_GOAL_SCHEDULER", "false").lower() in {"1", "true", "yes"}:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        from api.v1.deliverables_simple import _ensure_drafts_generated  # type: ignore
        from api.v1.hired_agents_simple import _by_id as hired_by_id

        async def run_due_goal_drafts_once() -> None:
            now = datetime.now(timezone.utc)
            for record in list(hired_by_id.values()):
                if not record.active:
                    continue
                if not record.configured or not record.goals_completed:
                    continue
                _ensure_drafts_generated(record, now=now)

        goal_scheduler = AsyncIOScheduler()
        goal_scheduler.add_job(
            run_due_goal_drafts_once,
            trigger="interval",
            seconds=int(os.getenv("GOAL_SCHEDULER_INTERVAL_SECONDS", "60")),
            id="goal_due_drafts",
            replace_existing=True,
        )
        goal_scheduler.start()
        app.state.goal_scheduler = goal_scheduler
        logger.info("   Goal scheduler enabled")
    
    # NOTE: Use Alembic migrations for production, not create_all
    logger.info("   Database initialization complete")
    
    # Log route registration if enabled
    if settings.enable_route_registration_logging:
        log_route_registration(app)


@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown - cleanup connections.
    """
    logging.info("🛑 Shutting down Plant Phase API")

    scheduler = getattr(app.state, "marketing_scheduler", None)
    if scheduler is not None:
        try:
            scheduler.shutdown(wait=False)
        except Exception:
            pass

    scheduler = getattr(app.state, "goal_scheduler", None)
    if scheduler is not None:
        try:
            scheduler.shutdown(wait=False)
        except Exception:
            pass


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
        # Test database connection using async connector
        from core.database import _connector
        session = await _connector.get_session()
        try:
            from sqlalchemy import text
            result = await session.execute(text("SELECT 1"))
            result.scalar()
            db_status = "connected"
        finally:
            await session.close()
    except Exception as e:
        db_status = f"disconnected: {str(e)}"
    
    return {
        "status": "healthy",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ========== API ROUTE MOUNTING ==========
if settings.enable_route_registration_logging:
    logger.info("=" * 80)
    logger.info("MOUNTING API V1 ROUTER")
    logger.info("=" * 80)

from api.v1.router import api_v1_router

if settings.enable_route_registration_logging:
    logger.info(f"api_v1_router prefix: {api_v1_router.prefix}")
    logger.info(f"api_v1_router loaded with {len(api_v1_router.routes)} routes")
    
    # Log auth routes specifically
    auth_routes = [r.path for r in api_v1_router.routes if 'auth' in r.path]
    logger.info(f"Auth routes found: {auth_routes}")

app.include_router(api_v1_router)

if settings.enable_route_registration_logging:
    logger.info("api_v1_router mounted to app")
    
    # Verify routes in final app
    all_app_routes = [r.path for r in app.routes if hasattr(r, 'path')]
    auth_in_app = [r for r in all_app_routes if 'auth' in r]
    logger.info(f"Total app routes after mounting: {len(all_app_routes)}")
    logger.info(f"Auth routes in final app: {auth_in_app}")

# Add a simple test endpoint to verify base routing works
@app.get("/debug/test")
async def debug_test():
    return {"status": "ok", "message": "Direct app route works"}

if settings.enable_route_registration_logging:
    logger.info(f"Added debug test endpoint")
    logger.info(f"Final route count: {len([r for r in app.routes if hasattr(r, 'path')])}")
    logger.info("=" * 80)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,  # Plant Backend runs on 8001, Gateway on 8000
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )

