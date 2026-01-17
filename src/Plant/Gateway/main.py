"""
WAOOAW Plant Gateway - Main Application
Middleware stack + Proxy to Plant Backend
"""

import os
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import httpx

from middleware.error_handler import setup_error_handlers
from middleware.budget import BudgetGuardMiddleware
from middleware.policy import PolicyMiddleware
from middleware.rbac import RBACMiddleware
from middleware.auth import AuthMiddleware

# Configuration
PLANT_BACKEND_URL = os.getenv("PLANT_BACKEND_URL", "http://localhost:8001")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
OPA_URL = os.getenv("OPA_URL", "http://localhost:8181")
JWT_PUBLIC_KEY = os.getenv("JWT_PUBLIC_KEY", "")
APPROVAL_UI_URL = os.getenv("APPROVAL_UI_URL", "http://localhost:3000/approvals")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Create FastAPI app
app = FastAPI(
    title="WAOOAW Plant Gateway",
    description="API Gateway with middleware stack",
    version="1.0.0",
    docs_url="/docs" if ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if ENVIRONMENT == "development" else None
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup error handlers (must be first)
setup_error_handlers(app)

# Add middleware stack (order matters - last added = first executed)
# Execution order: Auth → RBAC → Policy → Budget → ErrorHandling → Backend

# 1. Budget Guard (cost tracking)
app.add_middleware(
    BudgetGuardMiddleware,
    redis_url=REDIS_URL,
    opa_url=OPA_URL
)

# 2. Policy Enforcement (trial limits, sandbox routing)
app.add_middleware(
    PolicyMiddleware,
    redis_url=REDIS_URL,
    opa_url=OPA_URL,
    approval_ui_url=APPROVAL_UI_URL
)

# 3. RBAC (role-based access control)
app.add_middleware(
    RBACMiddleware,
    opa_url=OPA_URL
)

# 4. Authentication (JWT validation)
app.add_middleware(
    AuthMiddleware,
    jwt_public_key=JWT_PUBLIC_KEY,
    redis_url=REDIS_URL
)

# HTTP client for proxying to backend
http_client = httpx.AsyncClient(timeout=30.0)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await http_client.aclose()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "plant-gateway",
        "backend": PLANT_BACKEND_URL
    }


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_to_backend(request: Request, path: str):
    """
    Proxy all requests to Plant Backend after middleware processing
    """
    # Skip health check
    if path == "health":
        return await health_check()
    
    # Build target URL
    target_url = f"{PLANT_BACKEND_URL}/{path}"
    
    # Forward query parameters
    if request.url.query:
        target_url = f"{target_url}?{request.url.query}"
    
    # Prepare headers
    headers = dict(request.headers)
    headers.pop("host", None)
    
    # Add gateway tracking headers
    headers["X-Gateway"] = "plant-gateway"
    if hasattr(request.state, "gateway_type"):
        headers["X-Gateway-Type"] = request.state.gateway_type
    
    # Get request body
    body = await request.body()
    
    try:
        # Proxy to backend
        response = await http_client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
            follow_redirects=False
        )
        
        # Return backend response
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.headers.get("content-type")
        )
        
    except httpx.RequestError as e:
        return Response(
            content=f"Backend unavailable: {str(e)}",
            status_code=503,
            media_type="text/plain"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
