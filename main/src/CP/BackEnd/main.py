"""
WAOOAW Customer Portal - Backend API
FastAPI application for customer-facing services
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="WAOOAW Customer Portal API",
    description="API for customer-facing agent marketplace",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration (adjust for production)
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
        "service": "WAOOAW Customer Portal API",
        "status": "operational",
        "version": "0.1.0"
    }

@app.get("/health")
async def health_check():
    """Kubernetes health probe"""
    return {"status": "healthy"}

# TODO: Import and include routers
# from api import agents, trials, subscriptions, customers
# app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
# app.include_router(trials.router, prefix="/api/trials", tags=["trials"])
# app.include_router(subscriptions.router, prefix="/api/subscriptions", tags=["subscriptions"])
# app.include_router(customers.router, prefix="/api/customers", tags=["customers"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
