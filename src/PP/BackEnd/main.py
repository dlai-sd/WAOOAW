"""
WAOOAW Platform Portal - Backend API
FastAPI application for platform admin services
"""

from pathlib import Path
from fastapi import FastAPI
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from core.config import settings
from api import auth, genesis, agents, audit
from clients import close_plant_client

# Frontend static files path
FRONTEND_DIST = Path("/app/frontend/dist")

from core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description="Platform Portal - Thin proxy to Plant Gateway",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Mount static assets (only if frontend dist exists)
if FRONTEND_DIST.exists() and (FRONTEND_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

@app.get("/")
async def serve_index():
    """Serve frontend index"""
    if FRONTEND_DIST.exists():
        return FileResponse(str(FRONTEND_DIST / "index.html"))
    return JSONResponse({"message": "Frontend not built"})

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
