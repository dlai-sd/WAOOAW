"""
WAOOAW Plant Backend - Phase 1 Minimal Application
Simple FastAPI app for testing Agent API

Run with:
    source venv/bin/activate
    python main_simple.py

Then test with:
    curl http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn

# Simple in-memory app
app = FastAPI(
    title="WAOOAW Plant Backend",
    description="AI Agent Marketplace Platform",
    version="1.0.0",
)


# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    print("✅ Plant Backend starting...")
    print("📍 API Docs: http://localhost:8000/docs")
    print("📍 ReDoc: http://localhost:8000/redoc")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("❌ Plant Backend shutting down...")


# ============================================================================
# Health Endpoints
# ============================================================================

@app.get("/", tags=["root"])
async def root():
    """Root endpoint"""
    return {
        "name": "WAOOAW Plant Backend",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["health"])
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "plant-backend",
        "version": "1.0.0",
    }


# ============================================================================
# Import and Include Routers
# ============================================================================

try:
    from api.v1.agents_simple import router as agents_router
    app.include_router(agents_router)
    print("✅ Agents router loaded")
except Exception as e:
    print(f"⚠️  Failed to load agents router: {e}")


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║   WAOOAW Plant Backend - Phase 1 Minimal Test Server        ║
    ║                                                              ║
    ║   Starting on http://localhost:8000                         ║
    ║   Docs: http://localhost:8000/docs                          ║
    ║   ReDoc: http://localhost:8000/redoc                        ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
