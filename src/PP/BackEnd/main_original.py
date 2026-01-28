# This file is created to handle the main FastAPI application for the Platform Portal.

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from core.config import settings
from api import auth, genesis, agents, audit
from clients import close_plant_client

app = FastAPI(
    title=settings.APP_NAME,
    description="API for platform administration and operations",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Frontend static files path - Docker container path
FRONTEND_DIST = Path("/app/frontend/dist")


@app.get("/health")
async def health_check():
    """Kubernetes health probe"""
    return {"status": "healthy"}


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await close_plant_client()


@app.get("/api")
async def api_info():
    """API info endpoint"""
    return {
        "service": settings.APP_NAME,
        "status": "operational",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "frontend_available": FRONTEND_DIST.exists()
    }


# Routers
app.include_router(auth.router, prefix="/api")
app.include_router(genesis.router, prefix="/api")
app.include_router(agents.router, prefix="/api")
app.include_router(audit.router, prefix="/api")

# Mount static assets (only if frontend dist exists)
if FRONTEND_DIST.exists() and (FRONTEND_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

# Frontend routes (catch-all must be LAST)
@app.get("/")
async def serve_index():
    """Serve frontend index"""
    if FRONTEND_DIST.exists():
        return FileResponse(str(FRONTEND_DIST / "index.html"))
    return JSONResponse({"message": "Frontend not built"})

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

    uvicorn.run(app, host="0.0.0.0", port=settings.APP_PORT)

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from core.config import settings
from api import auth, genesis, agents, audit
from clients import close_plant_client

app = FastAPI(
    title=settings.APP_NAME,
    description="API for platform administration and operations",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Frontend static files path - Docker container path
FRONTEND_DIST = Path("/app/frontend/dist")


@app.get("/health")
async def health_check():
    """Kubernetes health probe"""
    return {"status": "healthy"}


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await close_plant_client()


@app.get("/api")
async def api_info():
    """API info endpoint"""
    return {
        "service": settings.APP_NAME,
        "status": "operational",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "frontend_available": FRONTEND_DIST.exists()
    }


# Routers
app.include_router(auth.router, prefix="/api")
app.include_router(genesis.router, prefix="/api")
app.include_router(agents.router, prefix="/api")
app.include_router(audit.router, prefix="/api")

# Mount static assets (only if frontend dist exists)
if FRONTEND_DIST.exists() and (FRONTEND_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

# Frontend routes (catch-all must be LAST)
@app.get("/")
async def serve_index():
    """Serve frontend index"""
    if FRONTEND_DIST.exists():
        return FileResponse(str(FRONTEND_DIST / "index.html"))
    return JSONResponse({"message": "Frontend not built"})

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
# from api import customers, billing, governor
# app.include_router(customers.router, prefix="/api/customers", tags=["customers"])
# app.include_router(customers.router, prefix="/api/customers", tags=["customers"])
# app.include_router(billing.router, prefix="/api/billing", tags=["billing"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.APP_PORT)
