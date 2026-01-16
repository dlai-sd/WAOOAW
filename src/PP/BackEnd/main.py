"""
WAOOAW Platform Portal - Backend API
FastAPI application for platform admin services
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from api import auth, genesis
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


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": settings.APP_NAME,
        "status": "operational",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


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
    }


# Routers
app.include_router(auth.router, prefix="/api")
app.include_router(genesis.router, prefix="/api")
# from api import agents, customers, billing, governor
# app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
# app.include_router(customers.router, prefix="/api/customers", tags=["customers"])
# app.include_router(billing.router, prefix="/api/billing", tags=["billing"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.APP_PORT)
