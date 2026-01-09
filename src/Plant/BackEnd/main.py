"""
WAOOAW Plant Phase - Backend API
FastAPI application for agent manufacturing pipeline
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="WAOOAW Plant Phase API",
    description="API for agent creation, certification, and deployment",
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
        "service": "WAOOAW Plant Phase API",
        "status": "operational",
        "version": "0.1.0",
        "stages": [
            "Conceive",
            "Birth",
            "Assembly",
            "Wiring",
            "Power On",
            "Showroom",
            "Hired"
        ]
    }

@app.get("/health")
async def health_check():
    """Kubernetes health probe"""
    return {"status": "healthy"}

# TODO: Import and include routers
# from api import genesis, agents, simulation, audit
# app.include_router(genesis.router, prefix="/api/genesis", tags=["genesis"])
# app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
# app.include_router(simulation.router, prefix="/api/simulation", tags=["simulation"])
# app.include_router(audit.router, prefix="/api/audit", tags=["audit"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
