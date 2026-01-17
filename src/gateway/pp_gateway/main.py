"""
Partner Platform (PP) Gateway - Main Application

Serves partner/developer requests, routes to Plant service.
Enforces RBAC (7 roles), trial mode, budget limits, audit logging.

Middleware Chain:
1. ErrorHandlingMiddleware: Catch all exceptions
2. AuditLoggingMiddleware: Log all requests
3. AuthMiddleware: JWT validation
4. RBACMiddleware: Role-based permissions (PP only)
5. PolicyMiddleware: Trial/Governor/Sandbox
6. BudgetGuardMiddleware: Budget enforcement
"""

import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx

from src.gateway.middleware import setup_middleware
from infrastructure.feature_flags.feature_flags import FeatureFlagService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
PORT = int(os.getenv("PORT", "8001"))  # Different port from CP Gateway

# Service URLs
PLANT_SERVICE_URL = os.getenv("PLANT_SERVICE_URL", "http://plant-service:8080")
OPA_SERVICE_URL = os.getenv("OPA_SERVICE_URL", "http://opa:8181")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@postgres:5432/waooaw")
APPROVAL_UI_URL = os.getenv("APPROVAL_UI_URL", "https://approval.waooaw.com")

# JWT Configuration
JWT_PUBLIC_KEY = os.getenv("JWT_PUBLIC_KEY", "")
JWT_ISSUER = os.getenv("JWT_ISSUER", "waooaw.com")

# LaunchDarkly
LAUNCHDARKLY_SDK_KEY = os.getenv("LAUNCHDARKLY_SDK_KEY", "")

# Create FastAPI app
app = FastAPI(
    title="WAOOAW Partner Platform Gateway",
    description="Constitutional enforcement gateway with RBAC for partners/developers",
    version="1.0.0",
    docs_url="/docs" if ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if ENVIRONMENT == "development" else None
)

# CORS (allow partner domains)
if ENVIRONMENT == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
else:
    # Production CORS (partner domains)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://partners.waooaw.com",
            "https://developers.waooaw.com",
            "https://pp.waooaw.com"
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"]
    )

# Initialize LaunchDarkly (optional)
feature_flag_service = None
if LAUNCHDARKLY_SDK_KEY:
    try:
        feature_flag_service = FeatureFlagService(LAUNCHDARKLY_SDK_KEY)
        logger.info("LaunchDarkly feature flags initialized")
    except Exception as e:
        logger.warning(f"LaunchDarkly initialization failed: {e}")

# Set up middleware chain (includes RBAC for PP Gateway)
setup_middleware(
    app,
    gateway_type="PP",  # Partner Platform
    opa_service_url=OPA_SERVICE_URL,
    redis_url=REDIS_URL,
    database_url=DATABASE_URL,
    approval_ui_url=APPROVAL_UI_URL,
    jwt_public_key=JWT_PUBLIC_KEY,
    jwt_issuer=JWT_ISSUER,
    feature_flag_service=feature_flag_service,
    environment=ENVIRONMENT
)

# HTTP client for Plant service
plant_client = httpx.AsyncClient(
    base_url=PLANT_SERVICE_URL,
    timeout=30.0,
    follow_redirects=True
)


# Health check endpoints
@app.get("/health", tags=["Health"])
async def health():
    """Health check endpoint (bypasses middleware)"""
    return {"status": "healthy", "gateway": "PP", "version": "1.0.0"}


@app.get("/healthz", tags=["Health"])
async def healthz():
    """Kubernetes health check"""
    return {"status": "ok"}


@app.get("/ready", tags=["Health"])
async def ready():
    """Readiness check (validates dependencies)"""
    checks = {
        "plant_service": False,
        "opa_service": False,
        "redis": False,
        "database": False
    }
    
    # Check Plant service
    try:
        response = await plant_client.get("/health", timeout=2.0)
        checks["plant_service"] = response.status_code == 200
    except Exception as e:
        logger.error(f"Plant service health check failed: {e}")
    
    # Check OPA service
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{OPA_SERVICE_URL}/health")
            checks["opa_service"] = response.status_code == 200
    except Exception as e:
        logger.error(f"OPA service health check failed: {e}")
    
    # Check Redis
    try:
        import redis.asyncio as redis
        r = redis.from_url(REDIS_URL, socket_connect_timeout=2)
        await r.ping()
        checks["redis"] = True
        await r.close()
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
    
    # Check PostgreSQL
    try:
        import asyncpg
        conn = await asyncpg.connect(DATABASE_URL, timeout=2)
        await conn.execute("SELECT 1")
        checks["database"] = True
        await conn.close()
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
    
    all_ready = all(checks.values())
    status_code = 200 if all_ready else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            "ready": all_ready,
            "checks": checks
        }
    )


@app.get("/metrics", tags=["Observability"])
async def metrics():
    """Prometheus metrics endpoint"""
    # TODO: Implement Prometheus metrics
    return {"message": "Metrics endpoint (TODO: implement Prometheus)"}


# Plant API Proxy
@app.api_route(
    "/api/v1/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    tags=["Plant Proxy"]
)
async def proxy_to_plant(path: str, request: Request):
    """
    Proxy requests to Plant service.
    
    All middleware has already run:
    - Auth: JWT validated
    - RBAC: Role-based permissions enforced (PP only)
    - Policy: Trial mode, Governor approval, sandbox routing checked
    - Budget: Budget enforcement applied
    - Audit: Request logged
    
    This endpoint forwards to Plant, tracks latency, and returns response.
    """
    # Determine target backend (sandbox vs production)
    target_backend = getattr(request.state, "target_backend", "production")
    plant_url = PLANT_SERVICE_URL
    
    if target_backend == "sandbox":
        sandbox_url = os.getenv("PLANT_SANDBOX_URL", PLANT_SERVICE_URL)
        plant_url = sandbox_url
        logger.info(f"Routing trial user to sandbox: {sandbox_url}")
    
    # Build Plant request
    url = f"{plant_url}/api/v1/{path}"
    
    # Forward headers (add correlation_id)
    headers = dict(request.headers)
    correlation_id = getattr(request.state, "correlation_id", None)
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id
    
    # Add user context headers for Plant
    jwt_claims = getattr(request.state, "jwt", {})
    user_info = getattr(request.state, "user_info", None)
    
    headers["X-User-ID"] = jwt_claims.get("user_id", "")
    headers["X-Customer-ID"] = jwt_claims.get("customer_id", "")
    headers["X-Trial-Mode"] = str(jwt_claims.get("trial_mode", False))
    
    # Add RBAC context (PP Gateway only)
    if user_info:
        headers["X-User-Roles"] = ",".join(user_info.roles)
        headers["X-User-Role-Level"] = str(user_info.role_level)
        headers["X-User-Is-Admin"] = str(user_info.is_admin)
    
    # Forward request body
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        body = await request.body()
    
    # Track Plant latency
    import time
    start_time = time.time()
    
    try:
        # Make request to Plant
        plant_response = await plant_client.request(
            method=request.method,
            url=url,
            params=dict(request.query_params),
            headers=headers,
            content=body
        )
        
        # Calculate Plant latency
        plant_latency_ms = (time.time() - start_time) * 1000
        request.state.plant_latency_ms = plant_latency_ms
        
        logger.info(
            f"Plant request: {request.method} {path} -> {plant_response.status_code} "
            f"({plant_latency_ms:.2f}ms)"
        )
        
        # Return Plant response
        return JSONResponse(
            status_code=plant_response.status_code,
            content=plant_response.json() if plant_response.text else None,
            headers=dict(plant_response.headers)
        )
    
    except httpx.TimeoutException:
        logger.error(f"Plant request timeout: {request.method} {path}")
        return JSONResponse(
            status_code=504,
            content={
                "type": "https://waooaw.com/errors/gateway-timeout",
                "title": "Gateway Timeout",
                "status": 504,
                "detail": "Plant service timeout",
                "instance": str(request.url.path)
            }
        )
    
    except httpx.HTTPStatusError as e:
        logger.error(f"Plant HTTP error: {e}")
        return JSONResponse(
            status_code=e.response.status_code,
            content=e.response.json() if e.response.text else None
        )
    
    except Exception as e:
        logger.error(f"Plant request error: {e}", exc_info=True)
        return JSONResponse(
            status_code=502,
            content={
                "type": "https://waooaw.com/errors/service-unavailable",
                "title": "Bad Gateway",
                "status": 502,
                "detail": "Plant service error",
                "instance": str(request.url.path)
            }
        )


# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("=" * 80)
    logger.info("🚀 PP Gateway Starting")
    logger.info("=" * 80)
    logger.info(f"Environment: {ENVIRONMENT}")
    logger.info(f"Port: {PORT}")
    logger.info(f"Plant Service: {PLANT_SERVICE_URL}")
    logger.info(f"OPA Service: {OPA_SERVICE_URL}")
    logger.info(f"Redis: {REDIS_URL}")
    logger.info(f"Database: {DATABASE_URL}")
    logger.info(f"Feature Flags: {'Enabled' if feature_flag_service else 'Disabled'}")
    logger.info(f"RBAC: Enabled (PP Gateway)")
    logger.info("=" * 80)


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("PP Gateway shutting down...")
    await plant_client.aclose()
    if feature_flag_service:
        feature_flag_service.close()
    logger.info("PP Gateway shutdown complete")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        log_level="info",
        access_log=True,
        reload=(ENVIRONMENT == "development")
    )
