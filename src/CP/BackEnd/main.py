"""
WAOOAW Customer Portal - Backend API
FastAPI application for customer-facing services
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from core.config import settings
from api import auth_router

app = FastAPI(
    title=settings.APP_NAME,
    description="API for customer-facing agent marketplace",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth_router, prefix="/api")

# Frontend static files path
FRONTEND_DIST = Path(__file__).parent.parent / "FrontEnd" / "dist"

@app.get("/health")
async def health_check():
    """Kubernetes health probe"""
    return {"status": "healthy"}

@app.get("/api")
async def api_root():
    """API info endpoint"""
    return {
        "service": settings.APP_NAME,
        "status": "operational",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "frontend_available": FRONTEND_DIST.exists()
    }

# Mount static assets
if FRONTEND_DIST.exists():
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

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve frontend SPA (catch-all route)"""
    if not FRONTEND_DIST.exists():
        return JSONResponse({"error": "Frontend not available"}, status_code=404)
    
    file_path = FRONTEND_DIST / full_path
    if file_path.is_file():
        return FileResponse(str(file_path))
    
    # SPA fallback - serve index.html for all non-file routes
    return FileResponse(str(FRONTEND_DIST / "index.html"))
frontend_dist = Path(__file__).parent.parent.parent / "FrontEnd" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")
    
    @app.get("/")
    async def serve_index():
        """Serve frontend index"""
        return FileResponse(str(frontend_dist / "index.html"))
    
    @app.get("/auth/callback")
    async def serve_auth_callback():
        """Serve frontend for auth callback route"""
        return FileResponse(str(frontend_dist / "index.html"))
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve frontend for all other routes (SPA routing)"""
        file_path = frontend_dist / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        # SPA fallback - serve index.html for all non-file routes
        return FileResponse(str(frontend_dist / "index.html"))

# TODO: Import and include additional routers
# from api import agents, trials, subscriptions, customers
# app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
# app.include_router(trials.router, prefix="/api/trials", tags=["trials"])
# app.include_router(subscriptions.router, prefix="/api/subscriptions", tags=["subscriptions"])
# app.include_router(customers.router, prefix="/api/customers", tags=["customers"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
