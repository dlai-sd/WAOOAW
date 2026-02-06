# This file is created to handle the proxy functionality for the Platform Portal.

from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, Response
import httpx
import os

from api import agents, audit, auth, genesis, db_updates, metering_debug, agent_setups
from clients import close_plant_client

# Configuration
APP_NAME = "WAOOAW Platform Portal"
APP_VERSION = "2.0.0"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
PLANT_GATEWAY_URL = os.getenv("PLANT_GATEWAY_URL", "http://localhost:8000")
DEBUG_VERBOSE = os.getenv("DEBUG_VERBOSE", "false").lower() in {"1", "true", "yes"}

# CORS origins
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:8080,http://localhost:8006,http://localhost:5173"
).split(",")

app = FastAPI(
    title=APP_NAME,
    description="Platform Portal - Thin proxy to Plant Gateway",
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

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
async def health_check():
    """Kubernetes health probe"""
    return {
        "status": "healthy",
        "service": "pp-proxy",
        "version": APP_VERSION
    }


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
app.include_router(agent_setups.router, prefix="/api/pp")
app.include_router(metering_debug.router, prefix="/api/pp")
app.include_router(db_updates.router, prefix="/api/pp")


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
