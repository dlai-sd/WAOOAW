"""
Mock Plant Service for E2E Testing

Simulates the backend CP/PP service with realistic responses.
Used for end-to-end gateway testing without requiring actual Plant deployment.
"""

from fastapi import FastAPI, Header, HTTPException, Query
from typing import Optional
import uvicorn

app = FastAPI(title="Mock Plant Service", version="1.0.0")


# Mock data
MOCK_AGENTS = [
    {
        "id": "agent-001",
        "name": "Content Marketing Agent",
        "industry": "marketing",
        "specialty": "Healthcare Content",
        "rating": 4.8,
        "price": 12000,
        "status": "available"
    },
    {
        "id": "agent-002",
        "name": "Math Tutor Agent",
        "industry": "education",
        "specialty": "JEE/NEET Prep",
        "rating": 4.9,
        "price": 15000,
        "status": "working"
    },
    {
        "id": "agent-003",
        "name": "SDR Agent",
        "industry": "sales",
        "specialty": "B2B SaaS",
        "rating": 4.7,
        "price": 18000,
        "status": "available"
    }
]

MOCK_USERS = {
    "user-001": {
        "id": "user-001",
        "email": "test@waooaw.com",
        "role": "customer",
        "trial_expires": "2026-01-24T00:00:00Z"
    },
    "user-admin": {
        "id": "user-admin",
        "email": "admin@waooaw.com",
        "role": "admin",
        "permissions": ["read_agents", "update_agents", "delete_agents"]
    }
}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "mock-plant"}


@app.get("/api/v1/agents")
async def list_agents(
    industry: Optional[str] = None,
    x_user_id: Optional[str] = Header(None)
):
    """List all agents with optional filtering"""
    agents = MOCK_AGENTS
    
    if industry:
        agents = [a for a in agents if a["industry"] == industry]
    
    return {
        "agents": agents,
        "total": len(agents),
        "user_id": x_user_id
    }


@app.get("/api/v1/agents/{agent_id}")
async def get_agent(
    agent_id: str,
    x_user_id: Optional[str] = Header(None)
):
    """Get specific agent details"""
    agent = next((a for a in MOCK_AGENTS if a["id"] == agent_id), None)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {
        "agent": agent,
        "user_id": x_user_id
    }


@app.post("/api/v1/agents/{agent_id}/hire")
async def hire_agent(
    agent_id: str,
    x_user_id: Optional[str] = Header(None)
):
    """Hire an agent (creates trial)"""
    agent = next((a for a in MOCK_AGENTS if a["id"] == agent_id), None)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {
        "trial_id": f"trial-{agent_id}-{x_user_id}",
        "agent_id": agent_id,
        "user_id": x_user_id,
        "status": "active",
        "expires": "2026-01-24T00:00:00Z"
    }


@app.delete("/api/v1/agents/{agent_id}")
async def delete_agent(
    agent_id: str,
    x_user_id: Optional[str] = Header(None)
):
    """Delete an agent (requires governor approval)"""
    agent = next((a for a in MOCK_AGENTS if a["id"] == agent_id), None)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # This endpoint should trigger governor approval in gateway
    return {
        "message": "Agent deleted",
        "agent_id": agent_id,
        "deleted_by": x_user_id
    }


@app.get("/api/v1/users/{user_id}")
async def get_user(user_id: str):
    """Get user details"""
    user = MOCK_USERS.get(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@app.post("/api/v1/analytics/track")
async def track_event(
    x_user_id: Optional[str] = Header(None)
):
    """Track analytics event"""
    return {
        "tracked": True,
        "user_id": x_user_id,
        "timestamp": "2026-01-17T00:00:00Z"
    }


# Endpoints that trigger specific gateway behaviors

@app.get("/api/v1/expensive")
async def expensive_endpoint(
    x_user_id: Optional[str] = Header(None)
):
    """High-cost endpoint for budget testing (100 credits)"""
    return {
        "data": "expensive_data",
        "cost": 100,
        "user_id": x_user_id
    }


@app.get("/api/v1/sandbox")
async def sandbox_endpoint(
    x_user_id: Optional[str] = Header(None)
):
    """Endpoint that should be routed to sandbox"""
    return {
        "environment": "sandbox",
        "user_id": x_user_id
    }


@app.post("/api/v1/admin/settings")
async def update_settings(
    x_user_id: Optional[str] = Header(None)
):
    """Admin-only endpoint for RBAC testing"""
    return {
        "updated": True,
        "updated_by": x_user_id
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
