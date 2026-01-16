# FastAPI Gateway Architecture Blueprint
**Version:** 1.0  
**Date:** 2026-01-16  
**Status:** Architectural Design  
**Purpose:** Define constitutional-aligned FastAPI gateway architecture for WAOOAW platform

---

## Executive Summary

**Problem:** Current gateways (CP/PP) are basic FastAPI apps with minimal middleware—no constitutional enforcement, RBAC, OPA integration, or audit logging.

**Solution:** Implement layered middleware architecture with:
- **7 constitutional middleware layers** (Auth → RBAC → Policy → Budget → Audit → Error → WebSocket)
- **OPA Policy Service integration** (trial mode, Governor role, agent budgets)
- **Audit enrichment** (causation_id, correlation_id, constitutional context)
- **PostgreSQL RLS session variables** (customer data isolation)
- **Rate limiting** (trial vs production tiers)

---

## 1. Layered Middleware Architecture

### 1.1 Middleware Stack (Execution Order)

```python
FastAPI Request Flow (7 Middleware Layers):

1. [Request Ingress]
   ↓
2. CORS Middleware (allow_origins, allow_credentials) ✅ CURRENT
   ↓
3. Constitutional Auth Middleware (JWT validation, Governor role extraction) ❌ MISSING
   ↓
4. RBAC Enforcement Middleware (check permissions via OPA) ❌ MISSING
   ↓
5. Policy Decision Point (PDP) Middleware (OPA query: trial mode, sandbox routing) ❌ MISSING
   ↓
6. Budget Guard Middleware (agent $1/day cap, platform $100/month cap) ❌ MISSING
   ↓
7. Audit Logging Middleware (correlation_id, causation_id, constitutional context) ❌ MISSING
   ↓
8. [Route Handler] (business logic)
   ↓
9. Error Handling Middleware (constitutional exceptions, WebSocket errors) ❌ MISSING
   ↓
10. [Response Egress]
```

### 1.2 File Structure (Ideal)

```
src/{CP,PP}/BackEnd/
├── main.py                     # FastAPI app with middleware registration
├── core/
│   ├── config.py              # Settings (current ✅)
│   ├── database.py            # PostgreSQL + RLS session setup ❌
│   ├── exceptions.py          # Constitutional exceptions ❌
│   └── security.py            # JWT utils (partial ✅)
│
├── middleware/
│   ├── __init__.py            # Middleware registry ❌
│   ├── auth.py                # Constitutional auth (Governor role) ❌
│   ├── rbac.py                # RBAC enforcement (OPA integration) ❌
│   ├── policy.py              # OPA PDP queries (trial mode, sandbox routing) ❌
│   ├── budget.py              # Budget guards (agent/platform caps) ❌
│   ├── audit.py               # Audit logging enrichment ❌
│   ├── error.py               # Error handling & enrichment ❌
│   └── websocket.py           # WebSocket middleware (PP only) ❌
│
├── services/
│   ├── opa_client.py          # OPA HTTP client ❌
│   ├── audit_service.py       # Audit log writer ❌
│   └── budget_tracker.py      # Budget tracking ❌
│
├── models/
│   ├── constitutional.py      # ConstitutionalContext, AuditLog models ❌
│   ├── policy.py              # OPA request/response models ❌
│   └── user.py                # User, Token models (partial ✅)
│
└── api/
    ├── __init__.py
    ├── auth/                  # Auth routes (current ✅)
    ├── agents/                # Agent routes ❌
    ├── marketplace/           # Marketplace routes (CP only) ❌
    └── admin/                 # Admin routes (PP only) ❌
```

---

## 2. CP Gateway (Customer Portal) - Port 8015

### 2.1 Constitutional Requirements

```yaml
CP Gateway Responsibilities:
  Authentication:
    - Google OAuth (any email)
    - JWT token generation (HS256, 24hr expiry)
    - Refresh token support
    - Governor role detection (from JWT claims)
  
  Constitutional Enforcement:
    - Validate Governor role (from JWT)
    - Trial mode restrictions (10 tasks/day, 7-day limit)
    - Agent budget enforcement ($1/day per agent)
    - External execution approval gates
  
  Rate Limiting:
    - Trial users: 100 requests/hour
    - Production users: 1000 requests/hour
    - Governor role: 10000 requests/hour
  
  Audit Logging:
    - All requests logged to audit_logs table
    - correlation_id for request tracing
    - causation_id for constitutional decisions
    - Governor actions specially flagged
  
  Real-Time Features:
    - WebSocket for agent status updates
    - WebSocket for approval requests
    - Server-Sent Events (SSE) for trial progress
```

### 2.2 Middleware Implementation

#### 2.2.1 Constitutional Auth Middleware

```python
# src/CP/BackEnd/middleware/auth.py
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import jwt
from datetime import datetime

from core.config import settings
from models.constitutional import ConstitutionalContext

class ConstitutionalAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware for JWT validation + Governor role extraction
    Injects ConstitutionalContext into request.state
    """
    
    EXCLUDED_PATHS = ["/health", "/api/auth/google/login", "/api/auth/google/callback"]
    
    async def dispatch(self, request: Request, call_next):
        # Skip auth for public endpoints
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)
        
        # Extract JWT token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Missing or invalid Authorization header"}
            )
        
        token = auth_header.split(" ")[1]
        
        try:
            # Verify JWT
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
            
            # Extract constitutional context
            constitutional_context = ConstitutionalContext(
                user_id=payload.get("sub"),
                email=payload.get("email"),
                roles=payload.get("roles", []),
                is_governor=self._check_governor_role(payload),
                agent_id=payload.get("agent_id"),  # Which agent user is managing
                trial_mode=payload.get("trial_mode", True),
                trial_expires_at=payload.get("trial_expires_at"),
                issued_at=datetime.fromtimestamp(payload.get("iat")),
            )
            
            # Inject into request state
            request.state.constitutional_context = constitutional_context
            
            # Set PostgreSQL RLS session variable (customer data isolation)
            if hasattr(request.app.state, "db"):
                await self._set_rls_session_variable(
                    request.app.state.db,
                    customer_id=payload.get("customer_id")
                )
            
        except jwt.ExpiredSignatureError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Token expired", "action": "refresh_token"}
            )
        except jwt.InvalidTokenError as e:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": f"Invalid token: {str(e)}"}
            )
        
        # Continue to next middleware/route handler
        response = await call_next(request)
        return response
    
    def _check_governor_role(self, payload: dict) -> bool:
        """
        Determine if user is Platform Governor
        L0-01: Single Governor principle enforcement
        """
        roles = payload.get("roles", [])
        return "governor" in roles or payload.get("is_governor", False)
    
    async def _set_rls_session_variable(self, db, customer_id: str):
        """
        Set PostgreSQL RLS session variable for Row-Level Security
        Enforces customer data isolation (ADR-004)
        """
        await db.execute(f"SET app.current_customer_id = '{customer_id}';")
```

#### 2.2.2 OPA Policy Enforcement Middleware

```python
# src/CP/BackEnd/middleware/policy.py
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from services.opa_client import OPAClient
from models.policy import PolicyDecision, PolicyRequest

class OPAPolicyMiddleware(BaseHTTPMiddleware):
    """
    Middleware for Open Policy Agent (OPA) policy enforcement
    Queries Policy Service (port 8013) for authorization decisions
    """
    
    def __init__(self, app, opa_client: OPAClient):
        super().__init__(app)
        self.opa = opa_client
    
    async def dispatch(self, request: Request, call_next):
        # Skip policy check for health/auth endpoints
        if request.url.path in ["/health", "/api/auth/google/login"]:
            return await call_next(request)
        
        # Get constitutional context from previous middleware
        ctx = getattr(request.state, "constitutional_context", None)
        if not ctx:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Constitutional context missing (auth middleware failed)"}
            )
        
        # Build OPA policy request
        policy_request = PolicyRequest(
            input={
                "user": {
                    "id": ctx.user_id,
                    "email": ctx.email,
                    "roles": ctx.roles,
                    "is_governor": ctx.is_governor,
                },
                "agent": {
                    "id": ctx.agent_id,
                    "trial_mode": ctx.trial_mode,
                    "trial_expires_at": str(ctx.trial_expires_at),
                },
                "request": {
                    "method": request.method,
                    "path": request.url.path,
                    "action": self._extract_action(request),
                },
            }
        )
        
        # Query OPA Policy Service
        try:
            decision = await self.opa.evaluate("trial_mode/allow", policy_request)
            
            if not decision.allow:
                # Policy denied request
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "error": "Policy denied",
                        "reason": decision.reason,
                        "policy": decision.policy_name,
                        "action_required": decision.obligations.get("action_required"),
                    }
                )
            
            # Policy approved - apply obligations (e.g., sandbox routing)
            request.state.policy_decision = decision
            request.state.sandbox_route = decision.obligations.get("sandbox_route", False)
            request.state.mask_fields = decision.obligations.get("mask_fields", [])
            
        except Exception as e:
            # OPA service unavailable - DENY BY DEFAULT (L0-04)
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "error": "Policy service unavailable",
                    "details": str(e),
                    "constitutional_principle": "L0-04: Deny-by-Default",
                }
            )
        
        # Continue to next middleware/route handler
        response = await call_next(request)
        return response
    
    def _extract_action(self, request: Request) -> str:
        """
        Determine action type from request (read, write, execute)
        Used for policy decision (external execution requires Governor approval)
        """
        if request.method in ["GET", "HEAD"]:
            return "read"
        elif request.method in ["POST", "PUT", "PATCH"]:
            if "execute" in request.url.path or "approve" in request.url.path:
                return "execute"  # Requires Governor approval (L0-03)
            return "write"
        elif request.method == "DELETE":
            return "delete"
        return "unknown"
```

#### 2.2.3 Budget Guard Middleware

```python
# src/CP/BackEnd/middleware/budget.py
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime

from services.budget_tracker import BudgetTracker

class BudgetGuardMiddleware(BaseHTTPMiddleware):
    """
    Middleware for budget enforcement
    - Agent budget: $1/day per agent
    - Platform budget: $100/month total
    """
    
    def __init__(self, app, budget_tracker: BudgetTracker):
        super().__init__(app)
        self.budget_tracker = budget_tracker
    
    async def dispatch(self, request: Request, call_next):
        # Skip budget check for health/auth endpoints
        if request.url.path in ["/health", "/api/auth/google/login"]:
            return await call_next(request)
        
        # Get constitutional context
        ctx = getattr(request.state, "constitutional_context", None)
        if not ctx or not ctx.agent_id:
            return await call_next(request)  # No agent context = no budget check
        
        # Check agent budget
        agent_budget = await self.budget_tracker.get_agent_budget(ctx.agent_id)
        
        if agent_budget.spent_today >= agent_budget.daily_cap:
            # Agent hit $1/day cap
            # Option 1: Reject request
            # Option 2: Escalate to Governor for emergency budget approval
            
            if ctx.is_governor:
                # Governor can override budget (emergency approval)
                request.state.budget_override = True
                request.state.budget_override_reason = "Governor emergency approval"
            else:
                # Non-Governor: reject request
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Agent budget exhausted",
                        "agent_id": ctx.agent_id,
                        "spent_today": f"${agent_budget.spent_today:.2f}",
                        "daily_cap": "$1.00",
                        "resets_at": agent_budget.resets_at.isoformat(),
                        "action_required": "Wait for budget reset or request emergency approval from Governor",
                    }
                )
        
        # Check platform budget
        platform_budget = await self.budget_tracker.get_platform_budget()
        
        if platform_budget.utilization >= 1.0:
            # Platform hit $100/month cap
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "error": "Platform budget exhausted",
                    "spent_month": f"${platform_budget.spent_month:.2f}",
                    "monthly_cap": "$100.00",
                    "utilization": f"{platform_budget.utilization * 100:.1f}%",
                    "action_required": "Systems Architect must approve budget increase",
                }
            )
        elif platform_budget.utilization >= 0.95:
            # Platform at 95% utilization - suspend non-critical agents
            if not ctx.is_governor and ctx.agent_id not in ["genesis", "architect", "vision_guardian"]:
                return JSONResponse(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    content={
                        "error": "Platform budget at 95% - non-critical agents suspended",
                        "utilization": f"{platform_budget.utilization * 100:.1f}%",
                        "action_required": "Governor escalation required",
                    }
                )
        
        # Budget OK - continue
        response = await call_next(request)
        return response
```

#### 2.2.4 Audit Logging Middleware

```python
# src/CP/BackEnd/middleware/audit.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
from datetime import datetime

from services.audit_service import AuditService
from models.constitutional import AuditLog

class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for audit logging
    - Logs all requests to audit_logs table
    - Injects correlation_id, causation_id
    - Enriches with constitutional context
    """
    
    def __init__(self, app, audit_service: AuditService):
        super().__init__(app)
        self.audit = audit_service
    
    async def dispatch(self, request: Request, call_next):
        # Generate correlation_id (for request tracing)
        correlation_id = request.headers.get("X-Correlation-Id", str(uuid.uuid4()))
        request.state.correlation_id = correlation_id
        
        # Extract causation_id (for constitutional decision lineage)
        causation_id = request.headers.get("X-Causation-Id")
        request.state.causation_id = causation_id
        
        # Get constitutional context
        ctx = getattr(request.state, "constitutional_context", None)
        
        # Start timing
        start_time = datetime.utcnow()
        
        # Execute request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Create audit log entry
        audit_log = AuditLog(
            correlation_id=correlation_id,
            causation_id=causation_id,
            timestamp=start_time,
            user_id=ctx.user_id if ctx else None,
            email=ctx.email if ctx else None,
            is_governor=ctx.is_governor if ctx else False,
            agent_id=ctx.agent_id if ctx else None,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            policy_decision=getattr(request.state, "policy_decision", None),
            budget_override=getattr(request.state, "budget_override", False),
            constitutional_context={
                "trial_mode": ctx.trial_mode if ctx else None,
                "sandbox_route": getattr(request.state, "sandbox_route", None),
            },
        )
        
        # Write to audit log (async, non-blocking)
        await self.audit.log(audit_log)
        
        # Add correlation_id to response headers
        response.headers["X-Correlation-Id"] = correlation_id
        
        return response
```

### 2.3 Main Application Setup

```python
# src/CP/BackEnd/main.py (IMPROVED)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.database import database
from api import auth_router, marketplace_router

# Middleware
from middleware.auth import ConstitutionalAuthMiddleware
from middleware.policy import OPAPolicyMiddleware
from middleware.budget import BudgetGuardMiddleware
from middleware.audit import AuditLoggingMiddleware
from middleware.error import ErrorHandlingMiddleware

# Services
from services.opa_client import OPAClient
from services.audit_service import AuditService
from services.budget_tracker import BudgetTracker

app = FastAPI(
    title=settings.APP_NAME,
    description="Customer Portal API with Constitutional Governance",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize services
opa_client = OPAClient(base_url=settings.OPA_SERVICE_URL)
audit_service = AuditService(database=database)
budget_tracker = BudgetTracker(database=database)

# CORS (first middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constitutional middleware stack (order matters!)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(AuditLoggingMiddleware, audit_service=audit_service)
app.add_middleware(BudgetGuardMiddleware, budget_tracker=budget_tracker)
app.add_middleware(OPAPolicyMiddleware, opa_client=opa_client)
app.add_middleware(ConstitutionalAuthMiddleware)

# Health check (no auth required)
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "cp-gateway", "port": 8015}

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
app.include_router(marketplace_router, prefix="/api/marketplace", tags=["marketplace"])

# Startup event
@app.on_event("startup")
async def startup():
    await database.connect()
    app.state.db = database

# Shutdown event
@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
```

---

## 3. PP Gateway (Platform Portal) - Port 8006

### 3.1 Constitutional Requirements

```yaml
PP Gateway Responsibilities:
  Authentication:
    - Google OAuth (@waooaw.com ONLY)
    - JWT token generation (HS256, 15-day expiry for internal users)
    - Domain restriction enforcement
  
  RBAC Enforcement:
    - 7 hierarchical roles (Admin, Subscription Manager, Agent Orchestrator, Infrastructure Engineer, Helpdesk Agent, Industry Manager, Viewer)
    - Permission checks via OPA
    - Role assignment validation
  
  Rate Limiting:
    - Unauthenticated: 100 requests/hour
    - Authenticated: 1000 requests/hour
    - Admin role: 10000 requests/hour
  
  Audit Logging:
    - All requests logged to pp_audit_logs (7-year retention)
    - Admin force actions require reason
    - Genesis validation status changes logged
    - Constitutional violation attempts logged
  
  Proxy Routing:
    - Route to 13 backend microservices
    - Service discovery via health checks
    - Circuit breaker for downstream failures
```

### 3.2 Additional PP-Specific Middleware

#### 3.2.1 RBAC Enforcement Middleware

```python
# src/PP/BackEnd/middleware/rbac.py
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from services.opa_client import OPAClient
from models.policy import RBACRequest

class RBACMiddleware(BaseHTTPMiddleware):
    """
    Middleware for Role-Based Access Control (RBAC)
    Enforces 7 hierarchical roles via OPA
    """
    
    # Route -> Required Permission mapping
    ROUTE_PERMISSIONS = {
        "/api/agents/create": "agent:create",
        "/api/agents/{id}/approve": "agent:approve",
        "/api/customers/{id}/force-cancel": "subscription:force_cancel",
        "/api/billing/credit-proposals/approve": "billing:approve_credit",
        "/api/users/assign-role": "user:assign_role",
        "/api/incidents/create": "incident:create",
        "/api/sla/breaches": "sla:view_breaches",
    }
    
    def __init__(self, app, opa_client: OPAClient):
        super().__init__(app)
        self.opa = opa_client
    
    async def dispatch(self, request: Request, call_next):
        # Skip RBAC for health/auth endpoints
        if request.url.path in ["/health", "/api/auth/google/login"]:
            return await call_next(request)
        
        # Get constitutional context
        ctx = getattr(request.state, "constitutional_context", None)
        if not ctx:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Authentication required"}
            )
        
        # Determine required permission
        required_permission = self._get_required_permission(request)
        
        if not required_permission:
            # Route has no permission requirement
            return await call_next(request)
        
        # Query OPA for RBAC decision
        rbac_request = RBACRequest(
            input={
                "user": {
                    "id": ctx.user_id,
                    "email": ctx.email,
                    "roles": ctx.roles,
                },
                "permission": required_permission,
            }
        )
        
        try:
            decision = await self.opa.evaluate("rbac/allow", rbac_request)
            
            if not decision.allow:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "error": "Permission denied",
                        "required_permission": required_permission,
                        "user_roles": ctx.roles,
                        "reason": decision.reason,
                    }
                )
        
        except Exception as e:
            # RBAC service unavailable - DENY BY DEFAULT
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "error": "RBAC service unavailable",
                    "details": str(e),
                    "constitutional_principle": "L0-04: Deny-by-Default",
                }
            )
        
        # RBAC check passed
        return await call_next(request)
    
    def _get_required_permission(self, request: Request) -> str:
        """
        Map route to required permission
        """
        path = request.url.path
        for route, permission in self.ROUTE_PERMISSIONS.items():
            if self._route_matches(path, route):
                return permission
        return None
    
    def _route_matches(self, path: str, route: str) -> bool:
        """
        Check if path matches route template (e.g., /api/agents/123 matches /api/agents/{id})
        """
        path_parts = path.split("/")
        route_parts = route.split("/")
        
        if len(path_parts) != len(route_parts):
            return False
        
        for p, r in zip(path_parts, route_parts):
            if r.startswith("{") and r.endswith("}"):
                continue  # Wildcard match
            if p != r:
                return False
        
        return True
```

---

## 4. Shared Services

### 4.1 OPA Client Service

```python
# src/{CP,PP}/BackEnd/services/opa_client.py
import httpx
from typing import Optional

from models.policy import PolicyRequest, PolicyDecision

class OPAClient:
    """
    HTTP client for Open Policy Agent (OPA) service
    Port 8013: Policy Service
    """
    
    def __init__(self, base_url: str = "http://localhost:8013"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=5.0)
    
    async def evaluate(self, policy_path: str, request: PolicyRequest) -> PolicyDecision:
        """
        Query OPA for policy decision
        
        Args:
            policy_path: OPA policy path (e.g., "trial_mode/allow", "rbac/allow")
            request: PolicyRequest with input data
        
        Returns:
            PolicyDecision with allow/deny + reason + obligations
        
        Raises:
            httpx.HTTPError: If OPA service unavailable
        """
        url = f"{self.base_url}/v1/data/{policy_path}"
        
        response = await self.client.post(url, json=request.input)
        response.raise_for_status()
        
        result = response.json()
        
        return PolicyDecision(
            allow=result.get("result", {}).get("allow", False),
            reason=result.get("result", {}).get("reason", "Policy denied"),
            policy_name=policy_path,
            obligations=result.get("result", {}).get("obligations", {}),
        )
    
    async def close(self):
        await self.client.aclose()
```

### 4.2 Audit Service

```python
# src/{CP,PP}/BackEnd/services/audit_service.py
from databases import Database
from datetime import datetime

from models.constitutional import AuditLog

class AuditService:
    """
    Service for writing audit logs
    - CP: writes to audit_logs table
    - PP: writes to pp_audit_logs table (7-year retention)
    """
    
    def __init__(self, database: Database, table_name: str = "audit_logs"):
        self.db = database
        self.table_name = table_name
    
    async def log(self, audit_log: AuditLog):
        """
        Write audit log entry to database
        Non-blocking, fire-and-forget
        """
        query = f"""
            INSERT INTO {self.table_name} (
                correlation_id, causation_id, timestamp, user_id, email,
                is_governor, agent_id, method, path, status_code, duration_ms,
                policy_decision, budget_override, constitutional_context
            ) VALUES (
                :correlation_id, :causation_id, :timestamp, :user_id, :email,
                :is_governor, :agent_id, :method, :path, :status_code, :duration_ms,
                :policy_decision, :budget_override, :constitutional_context
            )
        """
        
        values = {
            "correlation_id": audit_log.correlation_id,
            "causation_id": audit_log.causation_id,
            "timestamp": audit_log.timestamp,
            "user_id": audit_log.user_id,
            "email": audit_log.email,
            "is_governor": audit_log.is_governor,
            "agent_id": audit_log.agent_id,
            "method": audit_log.method,
            "path": audit_log.path,
            "status_code": audit_log.status_code,
            "duration_ms": audit_log.duration_ms,
            "policy_decision": audit_log.policy_decision.dict() if audit_log.policy_decision else None,
            "budget_override": audit_log.budget_override,
            "constitutional_context": audit_log.constitutional_context,
        }
        
        try:
            await self.db.execute(query=query, values=values)
        except Exception as e:
            # Log error but don't fail request
            print(f"Audit log write failed: {e}")
```

---

## 5. Constitutional Models

```python
# src/{CP,PP}/BackEnd/models/constitutional.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict

class ConstitutionalContext(BaseModel):
    """
    Constitutional context extracted from JWT
    Injected into request.state by ConstitutionalAuthMiddleware
    """
    user_id: str
    email: str
    roles: List[str]
    is_governor: bool
    agent_id: Optional[str] = None
    trial_mode: bool = True
    trial_expires_at: Optional[datetime] = None
    issued_at: datetime

class AuditLog(BaseModel):
    """
    Audit log entry for constitutional compliance
    """
    correlation_id: str  # Request tracing
    causation_id: Optional[str] = None  # Constitutional decision lineage
    timestamp: datetime
    user_id: Optional[str] = None
    email: Optional[str] = None
    is_governor: bool = False
    agent_id: Optional[str] = None
    method: str
    path: str
    status_code: int
    duration_ms: float
    policy_decision: Optional[Dict] = None
    budget_override: bool = False
    constitutional_context: Dict

class PolicyDecision(BaseModel):
    """
    OPA policy decision response
    """
    allow: bool
    reason: str
    policy_name: str
    obligations: Dict  # e.g., {"sandbox_route": true, "mask_fields": ["pii"]}
```

---

## 6. Deployment Architecture

### 6.1 Service Dependencies

```yaml
CP Gateway (Port 8015):
  Dependencies:
    - OPA Policy Service (Port 8013) - CRITICAL
    - Audit Writer (Port 8010) - CRITICAL
    - PostgreSQL (audit_logs table)
    - Redis (rate limiting, JWT sessions)
    - Plant API (Port 8000+) - Backend services
  
  Deployment:
    - Cloud Run (min_instances=1, max_instances=20)
    - Memory: 512MB
    - CPU: 1 vCPU
    - Timeout: 300s
    - Concurrency: 80

PP Gateway (Port 8006):
  Dependencies:
    - OPA Policy Service (Port 8013) - CRITICAL
    - Audit Writer (Port 8010) - CRITICAL
    - PostgreSQL (pp_audit_logs table, pp_users, pp_roles)
    - Redis (rate limiting, JWT sessions, RBAC cache)
    - 13 Backend Microservices
  
  Deployment:
    - Cloud Run (min_instances=1, max_instances=10)
    - Memory: 512MB
    - CPU: 1 vCPU
    - Timeout: 300s
    - Concurrency: 80
```

### 6.2 Cost Impact

```yaml
Current Cost (Basic Gateways):
  - CP Gateway: $10-15/month
  - PP Gateway: $5-10/month
  Total: $15-25/month

Improved Cost (Constitutional Gateways):
  - CP Gateway: $15-20/month (higher traffic, middleware overhead)
  - PP Gateway: $10-15/month (higher traffic, RBAC queries)
  - OPA Policy Service: $5-10/month (new service)
  - Audit Writer: $5/month (always-on)
  Total: $35-50/month

Delta: +$20-25/month (67% increase) for full constitutional compliance
```

---

## 7. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)

```yaml
Sprint 1: Middleware Infrastructure
  Tasks:
    - Create middleware/ directory structure
    - Implement ConstitutionalAuthMiddleware
    - Implement AuditLoggingMiddleware
    - Create OPAClient service
    - Create AuditService
  
  Testing:
    - Unit tests for each middleware
    - Integration test: Auth → Audit flow
    - Verify correlation_id propagation

Sprint 2: OPA Integration
  Tasks:
    - Deploy OPA Policy Service (Port 8013)
    - Write trial_mode_sandbox_routing.rego policy
    - Write rbac_policy.rego (7 roles)
    - Implement OPAPolicyMiddleware
    - Implement RBACMiddleware (PP only)
  
  Testing:
    - OPA policy unit tests (pytest)
    - Integration test: Policy denial → 403 response
    - Verify deny-by-default behavior
```

### Phase 2: Advanced Features (Week 3-4)

```yaml
Sprint 3: Budget Guards & WebSocket
  Tasks:
    - Implement BudgetGuardMiddleware
    - Create BudgetTracker service
    - Add WebSocket support (CP Gateway)
    - Implement ErrorHandlingMiddleware
  
  Testing:
    - Budget cap enforcement tests
    - WebSocket connection tests
    - Error handling tests

Sprint 4: PostgreSQL RLS & Proxy Routing
  Tasks:
    - Implement RLS session variable setting
    - Add proxy routing for PP Gateway
    - Add circuit breaker for backend services
    - Performance optimization
  
  Testing:
    - RLS isolation tests
    - Proxy routing tests
    - Load testing (1000 req/s)
```

### Phase 3: Production Hardening (Week 5-6)

```yaml
Sprint 5: Observability & Monitoring
  Tasks:
    - Add Prometheus metrics (request rate, latency, error rate)
    - Create Cloud Monitoring dashboards
    - Set up alerting (OPA down, audit write failures)
    - Add distributed tracing (Cloud Trace)
  
  Testing:
    - Chaos engineering (kill OPA, verify deny-by-default)
    - Latency benchmarking (target <50ms middleware overhead)

Sprint 6: Security & Compliance
  Tasks:
    - Security audit (OWASP Top 10)
    - Penetration testing
    - Compliance verification (constitutional principles)
    - Documentation updates
  
  Testing:
    - Security scan (Bandit, Safety)
    - Compliance audit script
```

---

## 8. Success Metrics

```yaml
Performance:
  - Middleware overhead: <50ms (p95)
  - OPA query latency: <10ms (p95)
  - Audit write latency: <5ms (async, non-blocking)
  - Gateway throughput: >1000 req/s (load test)

Constitutional Compliance:
  - 100% requests have correlation_id
  - 100% Governor actions logged
  - 100% policy decisions attested
  - 0 RLS policy violations (cross-customer data leaks)

Reliability:
  - Gateway uptime: 99.9% (SLA)
  - OPA uptime: 99.9% (critical dependency)
  - Deny-by-default coverage: 100% (if OPA down, all requests denied)
  - Zero audit log data loss
```

---

## 9. Migration Strategy (Current → Ideal)

```yaml
Step 1: Add Middleware Skeleton (No Breaking Changes)
  - Create middleware/ directory
  - Add ConstitutionalAuthMiddleware (no-op if JWT missing)
  - Add AuditLoggingMiddleware (log to stdout initially)
  - Deploy to demo environment

Step 2: Deploy OPA Policy Service
  - Create Policy Service (Port 8013)
  - Deploy basic policies (allow all)
  - Test OPA integration

Step 3: Enable Constitutional Middleware (Feature Flag)
  - Add feature flag: ENABLE_CONSTITUTIONAL_MIDDLEWARE=true
  - Test with 10% traffic (canary deployment)
  - Monitor latency, error rates

Step 4: Full Rollout
  - Enable for 100% traffic
  - Monitor for 7 days
  - Fix issues, optimize performance

Step 5: Remove Legacy Code
  - Remove basic auth (replace with ConstitutionalAuthMiddleware)
  - Remove manual audit logging (use middleware)
  - Clean up deprecated endpoints
```

---

## 10. Conclusion

**Current State:** Basic FastAPI gateways with minimal features (auth, CORS, health checks)

**Ideal State:** Constitutional-aligned gateways with 7 middleware layers enforcing L0 principles

**Key Benefits:**
1. ✅ **Constitutional Compliance:** L0 principles enforced at gateway layer
2. ✅ **Unified Policy:** OPA centralizes trial mode, RBAC, sandbox routing
3. ✅ **Audit Trail:** 100% request coverage with correlation_id tracing
4. ✅ **Budget Safety:** Platform/agent budget caps prevent cost overruns
5. ✅ **Security:** Deny-by-default, RLS isolation, JWT validation

**Cost:** +$20-25/month (67% increase) for full constitutional governance

**Timeline:** 6 weeks (foundation → advanced features → production hardening)

**Next Steps:**
1. Review blueprint with Systems Architect Agent
2. Create Epic in GitHub Projects (6 sprints)
3. Implement Phase 1 (middleware infrastructure)
4. Deploy OPA Policy Service
5. Test with 10% traffic (canary)

---

**Document Status:** Ready for Implementation  
**Approval Required:** Systems Architect Agent  
**Implementation Owner:** Platform Engineering Team  
**Go-Live Target:** End of Week 6

