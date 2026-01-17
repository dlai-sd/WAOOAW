"""
API Gateway Main Application for E2E Testing

Full gateway with all middleware configured for end-to-end testing.
"""

import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import httpx
from typing import Optional

# Import all middleware
from middleware.auth import AuthMiddleware
from middleware.rbac import RBACMiddleware
from middleware.policy import PolicyMiddleware
from middleware.budget import BudgetGuardMiddleware
from middleware.error_handler import ErrorHandlingMiddleware

# Configuration
PLANT_URL = os.getenv("PLANT_URL", "http://mock-plant:8001")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis-e2e:6379/0")
OPA_URL = os.getenv("OPA_URL", "http://opa-e2e:8181")
JWT_PUBLIC_KEY = os.getenv("JWT_PUBLIC_KEY", "")
APPROVAL_UI_URL = os.getenv("APPROVAL_UI_URL", "http://localhost:3000/approval")

# Create FastAPI app
app = FastAPI(
    title="WAOOAW API Gateway",
    description="Unified gateway with constitutional middleware",
    version="1.0.0"
)


# Health check (no auth)
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "api-gateway",
        "plant_url": PLANT_URL
    }


# Initialize services
class Services:
    """Shared services container"""
    def __init__(self):
        self.redis_url = REDIS_URL
        self.opa_url = OPA_URL
        self.jwt_public_key = JWT_PUBLIC_KEY
        self.approval_ui_url = APPROVAL_UI_URL


services = Services()


# Add middleware (in reverse order - last added runs first)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(BudgetGuardMiddleware, opa_service_url=services.opa_url, redis_url=services.redis_url)
app.add_middleware(PolicyMiddleware, opa_service_url=services.opa_url, redis_url=services.redis_url, approval_ui_url=services.approval_ui_url)
app.add_middleware(RBACMiddleware)
app.add_middleware(AuthMiddleware, jwt_public_key=services.jwt_public_key)


# Proxy all requests to Plant service
@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_to_plant(request: Request, full_path: str):
    """
    Proxy all API requests to Plant service after middleware processing
    """
    # Build target URL
    target_url = f"{PLANT_URL}/{full_path}"
    
    # Get query params
    query_params = dict(request.query_params)
    
    # Forward headers (add user_id from auth)
    headers = {}
    if hasattr(request.state, "user_id"):
        headers["X-User-Id"] = request.state.user_id
    if hasattr(request.state, "role"):
        headers["X-User-Role"] = request.state.role
    
    # Forward request to Plant
    async with httpx.AsyncClient() as client:
        try:
            # Get request body if present
            body = None
            if request.method in ["POST", "PUT", "PATCH"]:
                body = await request.body()
            
            response = await client.request(
                method=request.method,
                url=target_url,
                params=query_params,
                headers=headers,
                content=body,
                timeout=30.0
            )
            
            # Return Plant response
            return JSONResponse(
                status_code=response.status_code,
                content=response.json() if response.content else {},
                headers=dict(response.headers)
            )
        
        except httpx.TimeoutException:
            return JSONResponse(
                status_code=504,
                content={"error": "Plant service timeout"}
            )
        except httpx.ConnectError:
            return JSONResponse(
                status_code=503,
                content={"error": "Plant service unavailable"}
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"error": f"Gateway error: {str(e)}"}
            )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
