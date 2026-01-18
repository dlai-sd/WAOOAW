"""
WAOOAW Platform Portal - Thin Proxy to Plant Gateway
Simplified PP service that proxies all API calls to Plant Gateway
"""

from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, Response
import httpx
import os

# Configuration
APP_NAME = "WAOOAW Platform Portal"
APP_VERSION = "2.0.0"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
PLANT_GATEWAY_URL = os.getenv("PLANT_GATEWAY_URL", "http://localhost:8000")

# CORS origins
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:8006,http://localhost:5173"
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


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await http_client.aclose()


@app.get("/health")
async def health_check():
    """Kubernetes health probe"""
    return {
        "status": "healthy",
        "service": "pp-proxy",
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
    headers = dict(request.headers)
    headers.pop("host", None)
    headers["X-Forwarded-For"] = request.client.host if request.client else "unknown"
    headers["X-Gateway-Type"] = "PP"
    
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
