"""
WAOOAW Platform Portal - Backend API
FastAPI application for platform admin services
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="WAOOAW Platform Portal API",
    description="API for platform administration and operations",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "WAOOAW Platform Portal API",
        "status": "operational",
        "version": "0.1.0"
    }

@app.get("/health")
async def health_check():
    """Kubernetes health probe"""
    return {"status": "healthy"}

# TODO: Import and include routers
# from api import agents, customers, billing, governor, genesis
# app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
# app.include_router(customers.router, prefix="/api/customers", tags=["customers"])
# app.include_router(billing.router, prefix="/api/billing", tags=["billing"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
