# This file is created to handle the proxy functionality for the Platform Portal.

from pathlib import Path
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, Response
import httpx

from api import agents, audit, auth, genesis, db_updates, metering_debug, exchange_credentials, approvals, agent_types, agent_catalog, ops_subscriptions, ops_hired_agents
from api.ops_dlq import router as ops_dlq_router
from clients import close_plant_client
from core.config import get_settings as _get_settings, get_settings, Settings  # E6: single config source
from core.dependencies import require_correlation_id  # P-2: global correlation ID
from core.logging import PIIMaskingFilter as _PIIMaskingFilter  # PP-N5: PII masking
from core.metrics import get_metrics_response  # E8: Prometheus metrics
from core.observability import instrument_fastapi_app, instrument_httpx, setup_pp_observability  # PP-N2
from services.audit_dependency import get_audit_logger  # PP-N4: audit trail

# ── PP-N2: initialise OTel tracing (no-op if packages not installed) ──────────
setup_pp_observability()
instrument_httpx()

# ── PP-N5: wire PII masking filter at root logger ─────────────────────────────
import logging as _logging
_logging.getLogger().addFilter(_PIIMaskingFilter())

# ── E6: single config source — no duplicate os.getenv() ───────────────────────
_startup_settings = _get_settings()

# Configuration (derived from Settings — not os.getenv)
APP_NAME = "WAOOAW Platform Portal"
APP_VERSION = "2.0.0"
ENVIRONMENT = _startup_settings.ENVIRONMENT
PLANT_GATEWAY_URL = _startup_settings.plant_base_url
DEBUG_VERBOSE = _startup_settings.DEBUG_VERBOSE

# CORS origins
CORS_ORIGINS = _startup_settings.cors_origins_list

app = FastAPI(
    title=APP_NAME,
    description="Platform Portal - Thin proxy to Plant Gateway",
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    dependencies=[
        Depends(require_correlation_id),  # P-2: runs on every request
        Depends(get_audit_logger),         # PP-N4: audit trail on every request
    ],
)

# PP-N2: instrument FastAPI app with OTel request spans
instrument_fastapi_app(app)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Frontend static files path
FRONTEND_DIST = Path("/app/frontend/dist")

# HTTP client for proxying requests
http_client = httpx.AsyncClient(timeout=30.0)


def _strip_untrusted_metering_headers(headers: dict) -> dict:
    # Browsers must never be able to spoof trusted metering envelope headers.
    return {k: v for k, v in headers.items() if not str(k).lower().startswith("x-metering-")}


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await http_client.aclose()
    await close_plant_client()


@app.get("/health")
async def health_check(app_settings: Settings = Depends(get_settings)) -> dict:
    """Deep health probe — checks PP and downstream Plant Gateway."""
    components: dict[str, str] = {}

    # Probe Plant Gateway
    plant_url = (app_settings.plant_base_url or "").rstrip("/")
    if plant_url:
        try:
            async with httpx.AsyncClient(timeout=3.0) as hc:
                resp = await hc.get(f"{plant_url}/health")
            components["plant_gateway"] = "healthy" if resp.status_code < 400 else "degraded"
        except Exception:
            components["plant_gateway"] = "degraded"
    else:
        components["plant_gateway"] = "unconfigured"

    overall = "degraded" if "degraded" in components.values() else "healthy"
    return {
        "status": overall,
        "service": "pp-backend",
        "version": APP_VERSION,
        "components": components,
    }


@app.get("/metrics", include_in_schema=False)
async def metrics_endpoint() -> Response:
    """Prometheus metrics endpoint. Returns 501 when prometheus-client is not installed."""
    body, content_type = get_metrics_response()
    if body is None:
        return JSONResponse(status_code=501, content={"detail": "prometheus-client not installed"})
    return Response(content=body, media_type=content_type)


@app.get("/api/health", include_in_schema=False)
async def api_health_check():
    """Compatibility endpoint used by the PP frontend."""
    return {
        "status": "healthy",
        "service": "pp-proxy",
        "version": APP_VERSION,
        "gateway": PLANT_GATEWAY_URL,
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


# PP Admin API (non-conflicting prefix)
# These routes are PP's "full" API surface. The proxy route below continues
# to forward generic /api/* calls to the Plant Gateway.
# Auth endpoints used by the PP frontend
app.include_router(auth.router, prefix="/api")
app.include_router(genesis.router, prefix="/api/pp")
app.include_router(agents.router, prefix="/api/pp")
app.include_router(audit.router, prefix="/api/pp")
app.include_router(exchange_credentials.router, prefix="/api/pp")
app.include_router(approvals.router, prefix="/api/pp")
app.include_router(agent_types.router, prefix="/api/pp")
app.include_router(agent_catalog.router, prefix="/api/pp")
app.include_router(metering_debug.router, prefix="/api/pp")
app.include_router(db_updates.router, prefix="/api/pp")
app.include_router(ops_subscriptions.router, prefix="/api/pp")
app.include_router(ops_hired_agents.router, prefix="/api/pp")
app.include_router(ops_dlq_router, prefix="/api/pp")


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
    headers = _strip_untrusted_metering_headers(dict(request.headers))
    headers.pop("host", None)
    headers["X-Forwarded-For"] = request.client.host if request.client else "unknown"
    headers["X-Gateway-Type"] = "PP"

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
    uvicorn.run(app, host="0.0.0.0", port=8006)
