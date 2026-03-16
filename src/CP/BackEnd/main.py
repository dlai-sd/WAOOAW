"""
WAOOAW Customer Portal - Thin Proxy to Plant Gateway
Simplified CP service that proxies all API calls to Plant Gateway
"""

from pathlib import Path
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, Response
import httpx
import os
import uuid

# Import auth router for local auth endpoints
from api.auth import router as auth_router
from api.platform_credentials import router as platform_credentials_router
from api.internal_plant_credential_resolver import router as internal_plant_credential_resolver_router
from api.marketing_review import router as marketing_review_router
from api.exchange_setup import router as exchange_setup_router
from api.trading import router as trading_router
from api.trading_strategy import router as trading_strategy_router
from api.payments_config import router as payments_config_router
from api.payments_coupon import router as payments_coupon_router
from api.payments_razorpay import router as payments_razorpay_router
from api.invoices import router as invoices_router
from api.receipts import router as receipts_router
from api.hire_wizard import router as hire_wizard_router
from api.subscriptions import router as subscriptions_router
from api.my_agents_summary import router as my_agents_summary_router
from api.hired_agents_proxy import router as hired_agents_proxy_router
from api.cp_registration import router as cp_registration_router
from api.cp_otp import router as cp_otp_router
from api.cp_registration_otp import router as cp_registration_otp_router
from api.feature_flags_proxy import router as feature_flags_proxy_router  # E2-S2 (It-7)
from api.cp_profile import router as cp_profile_router  # E4-S1 (CP-NAV-1 It-2)
from api.cp_catalog import router as cp_catalog_router
from api.cp_youtube_connections import router as cp_youtube_connections_router
from middleware.security import SecurityMiddleware
from core.config import Settings as _Settings
from core.dependencies import require_correlation_id  # P-2: global correlation ID
from core.observability import setup_observability, instrument_fastapi_app

_settings = _Settings()

# E1-S1: Configure OTel tracing BEFORE any other setup that uses logging
setup_observability(_settings)

# Configuration
APP_NAME = "WAOOAW Customer Portal"
APP_VERSION = "2.0.0"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
PLANT_GATEWAY_URL = os.getenv("PLANT_GATEWAY_URL", "http://localhost:8000")
DEBUG_VERBOSE = os.getenv("DEBUG_VERBOSE", "false").lower() in {"1", "true", "yes"}

# CORS origins — read from Settings (never wildcard; E3-S1 Iteration 3)
_CORS_ORIGINS = _settings.cors_origins_list

app = FastAPI(
    title=APP_NAME,
    description="Customer Portal - Thin proxy to Plant Gateway",
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    dependencies=[Depends(require_correlation_id)],  # P-2: runs on every request
)

# E1-S1: wire FastAPI auto-instrumentation
instrument_fastapi_app(app)

# CORS configuration (added last = outermost, handles preflight first)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security middleware: correlation ID + security headers (runs inside CORS layer)
app.add_middleware(SecurityMiddleware)

# Mount auth router for local authentication
app.include_router(auth_router, prefix="/api")

# Internal API for Plant Backend to resolve credentials (MUST be network-isolated in production)
app.include_router(internal_plant_credential_resolver_router, prefix="/api")

# CP-local onboarding endpoints must be registered before the /api/{path:path} proxy.
app.include_router(platform_credentials_router, prefix="/api")
app.include_router(exchange_setup_router, prefix="/api")
app.include_router(marketing_review_router, prefix="/api")
app.include_router(trading_router, prefix="/api")
app.include_router(trading_strategy_router, prefix="/api")
app.include_router(payments_config_router, prefix="/api")
app.include_router(payments_coupon_router, prefix="/api")
app.include_router(payments_razorpay_router, prefix="/api")
app.include_router(invoices_router, prefix="/api")
app.include_router(receipts_router, prefix="/api")
app.include_router(hire_wizard_router, prefix="/api")
app.include_router(subscriptions_router, prefix="/api")
app.include_router(my_agents_summary_router, prefix="/api")
app.include_router(hired_agents_proxy_router, prefix="/api")
app.include_router(cp_registration_router, prefix="/api")
app.include_router(cp_otp_router, prefix="/api")
app.include_router(cp_registration_otp_router, prefix="/api")
app.include_router(feature_flags_proxy_router, prefix="/api")  # E2-S2 (It-7)
app.include_router(cp_profile_router, prefix="/api")  # E4-S1 (CP-NAV-1 It-2)
app.include_router(cp_catalog_router, prefix="/api")
app.include_router(cp_youtube_connections_router, prefix="/api")

# CP-SKILLS-1: Skills, platform connections, performance proxy
from api.cp_skills import router as cp_skills_router
app.include_router(cp_skills_router, prefix="/api")

# PLANT-CONTENT-1 It-4 E8: Campaign proxy routes
from api.campaigns import router as campaigns_router  # noqa: E402
app.include_router(campaigns_router, prefix="/api")

# CP-MOULD-1 It-1 E1: Scheduler summary, trial budget, pause/resume proxy routes
from api.cp_scheduler import router as cp_scheduler_router  # noqa: E402
app.include_router(cp_scheduler_router, prefix="/api")

# CP-MOULD-1 It-1 E2: Approval queue proxy routes
from api.cp_approvals_proxy import router as cp_approvals_proxy_router  # noqa: E402
app.include_router(cp_approvals_proxy_router, prefix="/api")

# EXEC-ENGINE-001 It-6 E14-S2: Flow-run + component-run proxy routes
from api.cp_flow_runs import router as cp_flow_runs_router  # noqa: E402
app.include_router(cp_flow_runs_router, prefix="/api")

# Frontend static files path
FRONTEND_DIST = Path("/app/frontend/dist")

# HTTP client for proxying requests
http_client = httpx.AsyncClient(timeout=30.0)


def _strip_untrusted_metering_headers(headers: dict) -> dict:
    # Browsers must never be able to spoof trusted metering envelope headers.
    return {k: v for k, v in headers.items() if not str(k).lower().startswith("x-metering-")}


def _ensure_correlation_id(headers: dict) -> dict:
    correlation_id = headers.get("X-Correlation-ID") or headers.get("x-correlation-id")
    if not correlation_id:
        correlation_id = str(uuid.uuid4())
    headers["X-Correlation-ID"] = str(correlation_id)
    return headers


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await http_client.aclose()


@app.get("/health")
async def health_check():
    """Kubernetes health probe"""
    return {
        "status": "healthy",
        "service": "cp-proxy",
        "version": APP_VERSION
    }


@app.get("/api")
async def api_root():
    """API info endpoint"""
    return {
        "service": APP_NAME,
        "status": "operational",
        "version": APP_VERSION,
        "environment": ENVIRONMENT,
        "gateway": PLANT_GATEWAY_URL,
        "mode": "proxy",
        "frontend_available": FRONTEND_DIST.exists()
    }


@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_to_gateway(request: Request, path: str):
    """
    Proxy all /api/* requests to Plant Gateway
    Preserves headers, method, body, and query parameters
    """
    # Build target URL
    target_url = f"{PLANT_GATEWAY_URL}/api/{path}"
    
    # Forward query parameters
    if request.url.query:
        target_url = f"{target_url}?{request.url.query}"
    
    # Prepare headers (exclude host-specific headers)
    headers = _ensure_correlation_id(_strip_untrusted_metering_headers(dict(request.headers)))
    headers.pop("host", None)
    headers["X-Forwarded-For"] = request.client.host if request.client else "unknown"
    headers["X-Gateway-Type"] = "CP"

    # Forward/enable debug tracing when explicitly requested.
    debug_trace = headers.get("X-Debug-Trace") or headers.get("x-debug-trace")
    if debug_trace:
        headers["X-Debug-Trace"] = str(debug_trace)
    elif DEBUG_VERBOSE:
        headers["X-Debug-Trace"] = "1"
    
    # Get request body
    body = await request.body()
    
    try:
        # Proxy request to Plant Gateway
        response = await http_client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
            follow_redirects=False
        )
        
        # Return response from gateway
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.headers.get("content-type")
        )
        
    except httpx.RequestError as e:
        return JSONResponse(
            status_code=503,
            content={
                "error": "Gateway Unavailable",
                "detail": f"Could not connect to Plant Gateway: {str(e)}",
                "gateway_url": PLANT_GATEWAY_URL
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Proxy Error",
                "detail": str(e)
            }
        )


# Mount static assets (only if frontend dist exists)
if FRONTEND_DIST.exists() and (FRONTEND_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")


@app.get("/")
async def serve_index():
    """Serve frontend index"""
    if FRONTEND_DIST.exists():
        return FileResponse(str(FRONTEND_DIST / "index.html"))
    return JSONResponse({"message": "Frontend not built. Run: cd FrontEnd && npm run build"})


@app.get("/auth/callback")
async def serve_auth_callback():
    """Serve frontend for auth callback route"""
    if FRONTEND_DIST.exists():
        return FileResponse(str(FRONTEND_DIST / "index.html"))
    return JSONResponse({"error": "Frontend not available"}, status_code=404)


# IMPORTANT: Catch-all route MUST be last
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve frontend SPA (catch-all route for client-side routing)"""
    if not FRONTEND_DIST.exists():
        return JSONResponse({"error": "Frontend not available"}, status_code=404)
    
    file_path = FRONTEND_DIST / full_path
    if file_path.is_file():
        return FileResponse(str(file_path))
    
    # SPA fallback - serve index.html for all non-file routes
    return FileResponse(str(FRONTEND_DIST / "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8015)

