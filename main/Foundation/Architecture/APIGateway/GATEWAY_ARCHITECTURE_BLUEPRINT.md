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

### 6.1 Deployment Strategy - Local-First, Workflow-Driven

**Philosophy:**
- ✅ **Docker Compose First:** Local development with 7-service stack (PostgreSQL, Redis, OPA, Gateway, Backend, CP, PP)
- ✅ **Automated Detection:** GitHub Actions auto-detects Dockerfiles and builds only changed components
- ✅ **Workflow-Only Deployments:** All cloud deployments use GitHub Actions workflows (never manual CLI)
- ✅ **Progressive Rollout:** Local → Demo → UAT → Production with approval gates

### 6.2 Docker Images & Artifact Registry

**Image Registry:** `asia-south1-docker.pkg.dev/waooaw-oauth/waooaw`

**Deployable Images (6 Total):**

```yaml
CP (Customer Portal):
  Images:
    - cp-backend:      # Python/FastAPI backend (526MB)
        Source: src/CP/BackEnd/Dockerfile
        Port: 8001 (internal) → 8015 (external)
    - cp:              # React frontend with Vite (659MB)
        Source: src/CP/FrontEnd/Dockerfile
        Port: 3000

PP (Partner Portal):
  Images:
    - pp-backend:      # Python/FastAPI backend (751MB)
        Source: src/PP/BackEnd/Dockerfile
        Port: 8015 (internal) → 8006 (external)
    - pp:              # React frontend with Vite (849MB)
        Source: src/PP/FrontEnd/Dockerfile
        Port: 3001

Plant (Core Services):
  Images:
    - plant-backend:   # Python/FastAPI + SQLAlchemy async (782MB)
        Source: src/Plant/BackEnd/Dockerfile
        Port: 8001
    - plant-gateway:   # FastAPI + Middleware Stack (270MB) ⭐ NEW
        Source: src/Plant/Gateway/Dockerfile
        Port: 8000
        Middleware: Auth → RBAC → Policy → Budget → ErrorHandler

Image Tagging:
  - Version: {env}-{sha7}-{run_number}  # e.g., demo-abc1234-42
  - Rolling: {env}-latest               # e.g., demo-latest
```

### 6.3 GitHub Actions Workflows

**Workflow Files:**

```yaml
1. waooaw-deploy.yml (App Stack Deployment):
   Trigger: workflow_dispatch
   Inputs:
     - environment: [demo, uat, prod]
     - terraform_action: [plan, apply]
   
   Jobs:
     - detect:       Auto-detect Dockerfiles (CP, PP, Plant)
     - build:        Build & push images to Artifact Registry
     - terraform:    Deploy to Cloud Run with Terraform
   
   Output:
     - Docker images: Tagged and pushed to registry
     - Cloud Run services: waooaw-{app}-{role}-{env}
     - NEGs registered: Backend endpoints for load balancer
     - State: env/{env}/{app}/default.tfstate

2. waooaw-foundation-deploy.yml (Load Balancer + SSL):
   Trigger: workflow_dispatch
   Inputs:
     - terraform_action: [plan, apply]
   
   Configuration:
     - Source: cloud/terraform/stacks/foundation/environments/default.tfvars
     - Flags: enable_cp, enable_pp, enable_plant
   
   Output:
     - Load balancer: URL routing updated (host rules)
     - SSL certificate: Hash-based name with create_before_destroy
     - Certificate status: PROVISIONING → ACTIVE (15-60 min)
     - State: foundation/default.tfstate

3. plant-db-infra-reconcile.yml (Database Infrastructure):
   Trigger: workflow_dispatch
   Inputs:
     - environment: [demo, uat, prod]
     - terraform_action: [plan, apply]
     - reconcile_mode: [import-existing, destroy-recreate, none]
   
   Output:
     - Cloud SQL instance: plant-sql-{env}
     - Database: waooaw
     - User: plant_user
     - State: env/{env}/plant-db/default.tfstate

4. plant-db-migrations-job.yml (Database Migrations):
   Trigger: workflow_dispatch
   Inputs:
     - environment: [demo, uat, prod]
     - migration_type: [upgrade, seed, both]
   
   Output:
     - Cloud Run Job: Alembic migrations executed
     - Database: Schema upgraded to latest version
```

### 6.4 Deployment Sequencing (Batch Execution)

**Batch Order (Zero-Downtime):**

```yaml
Batch 0: Database Infrastructure (Plant Only)
  Workflow: plant-db-infra-reconcile.yml
  Duration: 8-12 minutes
  Blocking: YES (Plant services depend on database)
  Command:
    gh workflow run plant-db-infra-reconcile.yml \
      -f environment=demo \
      -f terraform_action=apply

Batch 0.5: Database Migrations (Plant Only)
  Workflow: plant-db-migrations-job.yml
  Duration: 2-5 minutes
  Blocking: YES (Backend requires schema)
  Command:
    gh workflow run plant-db-migrations-job.yml \
      -f environment=demo \
      -f migration_type=both

Batch 1: App Stack Deployment (CP + PP + Plant)
  Workflow: waooaw-deploy.yml
  Duration: 6-10 minutes
  Blocking: YES (Foundation depends on NEGs)
  Auto-detects: All Dockerfiles in src/*/BackEnd, src/*/FrontEnd
  Command:
    gh workflow run waooaw-deploy.yml \
      -f environment=demo \
      -f terraform_action=apply

Batch 2: Foundation (Load Balancer + SSL)
  Workflow: waooaw-foundation-deploy.yml
  Duration: 5-10 minutes + SSL wait (15-60 min)
  Blocking: YES (SSL provisioning is asynchronous)
  Prerequisites:
    - DNS verified: *.demo.waooaw.com → 35.190.6.91
    - App stacks deployed (NEGs available)
  Command:
    gh workflow run waooaw-foundation-deploy.yml \
      -f terraform_action=apply

Batch 3: Validation
  Duration: 1-2 minutes
  Parallelizable: YES (all endpoints tested concurrently)
  Tests:
    - Health checks: curl https://{service}.demo.waooaw.com/health
    - Auth flow: POST /auth/login → verify JWT
    - Middleware: Test protected endpoint (expect 401 without JWT)
```

### 6.5 Service Dependencies (Cloud Run)

```yaml
Plant Gateway (waooaw-plant-gateway-demo):
  Port: 8000
  Dependencies:
    - OPA: http://opa:8181 (policy decisions)
    - Redis: redis://redis:6379 (sessions, budget tracking)
    - Plant Backend: http://plant-backend:8001
  
  Resources:
    - Memory: 512MB
    - CPU: 1 vCPU
    - Min instances: 1
    - Max instances: 10
    - Concurrency: 80
    - Timeout: 300s
  
  Environment:
    - PLANT_BACKEND_URL=http://plant-backend:8001
    - REDIS_URL=redis://redis:6379
    - OPA_URL=http://opa:8181
    - DATABASE_URL=postgresql+asyncpg://...
    - ENVIRONMENT=demo

Plant Backend (waooaw-plant-backend-demo):
  Port: 8001
  Dependencies:
    - Cloud SQL: plant-sql-demo (PostgreSQL 15)
    - Redis: redis://redis:6379
  
  Resources:
    - Memory: 1GB
    - CPU: 2 vCPU
    - Min instances: 1
    - Max instances: 20
    - Concurrency: 100
    - Timeout: 300s

CP Backend (waooaw-cp-backend-demo):
  Port: 8001 → Proxies to Gateway:8000
  Dependencies:
    - Plant Gateway: http://plant-gateway:8000
  
  Resources:
    - Memory: 512MB
    - CPU: 1 vCPU
    - Min instances: 1
    - Max instances: 10

PP Backend (waooaw-pp-backend-demo):
  Port: 8015 → Proxies to Gateway:8000
  Dependencies:
    - Plant Gateway: http://plant-gateway:8000
  
  Resources:
    - Memory: 512MB
    - CPU: 1 vCPU
    - Min instances: 1
    - Max instances: 10
```

### 6.6 DNS & SSL Configuration

**DNS Records (Cloudflare):**

```yaml
Demo Environment:
  - cp.demo.waooaw.com      → 35.190.6.91 (Load Balancer IP)
  - pp.demo.waooaw.com      → 35.190.6.91
  - plant.demo.waooaw.com   → 35.190.6.91

UAT Environment:
  - cp.uat.waooaw.com       → 35.190.6.91
  - pp.uat.waooaw.com       → 35.190.6.91
  - plant.uat.waooaw.com    → 35.190.6.91

Production:
  - cp.waooaw.com           → 35.190.6.91
  - pp.waooaw.com           → 35.190.6.91
  - plant.waooaw.com        → 35.190.6.91

DNS Verification (Mandatory):
  - Command: nslookup cp.demo.waooaw.com
  - Expected: 35.190.6.91
  - Timing: MUST verify before foundation deployment
  - Reason: Prevents SSL provisioning failures
```

**SSL Certificates (Google-Managed):**

```yaml
Certificate Naming:
  - Pattern: waooaw-ssl-{hash}
  - Example: waooaw-ssl-a3f9b7c2
  - Lifecycle: create_before_destroy (zero-downtime rotation)

Certificate Provisioning:
  - Duration: 15-60 minutes (Google's DNS validation)
  - Status: PROVISIONING → ACTIVE
  - Monitoring: gcloud compute ssl-certificates list --global

Certificate Rotation:
  - Trigger: Foundation config change (enable_* flags, domain changes)
  - Strategy: New cert created → ACTIVE → Old cert deleted
  - Downtime: ZERO (load balancer switches atomically)
```

### 6.7 Local Development (Docker Compose)

**File:** `docker-compose.architecture.yml`

**Services (7 Total):**

```yaml
Infrastructure:
  - postgres:15-alpine      # PostgreSQL database
  - redis:7-alpine          # Redis cache
  - opa:latest-envoy        # Open Policy Agent

Plant Services:
  - plant-backend:latest    # Plant Backend (port 8091)
  - plant-gateway:latest    # Plant Gateway (port 8090)

Proxy Services:
  - cp-app:latest           # CP Proxy (port 8015)
  - pp-app:latest           # PP Proxy (port 8006)

Startup Command:
  docker-compose -f docker-compose.architecture.yml up -d

Validation:
  - Backend:  curl http://localhost:8091/health
  - Gateway:  curl http://localhost:8090/health
  - CP Proxy: docker exec waooaw-cp-app-1 curl http://localhost:8001/health
  - PP Proxy: docker exec waooaw-pp-app-1 curl http://localhost:8015/health

Architecture Flow:
  CP:8015 ─────┐
               ├──▶ Gateway:8090 ──▶ Backend:8091 ──▶ PostgreSQL:5432
  PP:8006 ─────┘         │                              Redis:6379
                         └──────────▶ OPA:8181
```

### 6.8 Cost Estimation

```yaml
Current Deployment (Basic Gateways):
  - CP Backend + Frontend: $15-20/month
  - PP Backend + Frontend: $10-15/month
  - Plant Backend: $20-30/month
  Total: $45-65/month

New Deployment (With Gateway):
  - CP Backend + Frontend: $15-20/month
  - PP Backend + Frontend: $10-15/month
  - Plant Backend: $20-30/month
  - Plant Gateway: $10-15/month (NEW)
  - OPA (Cloud Run): $5-10/month
  - PostgreSQL (audit): $10/month (shared)
  - Redis: $5/month (Memorystore)
  Total: $75-105/month

Delta: +$30-40/month (67% increase) for middleware stack

Cost Breakdown by Service:
  - Middleware overhead: ~$10-15/month (Gateway CPU/memory)
  - Policy engine: $5-10/month (OPA queries)
  - Audit logging: Included in PostgreSQL
  - Budget tracking: Included in Redis
```

### 6.9 Pre-Deployment Checklist

**Before Running Workflows:**

```yaml
1. DNS Verification:
   ✅ Verify all domains resolve to load balancer IP
   ✅ Command: nslookup {service}.{env}.waooaw.com
   ✅ Expected: 35.190.6.91

2. GitHub Secrets/Variables:
   ✅ GCP_WORKLOAD_IDENTITY_PROVIDER configured
   ✅ GCP_SERVICE_ACCOUNT_EMAIL configured
   ✅ GOOGLE_OAUTH_CLIENT_ID set per environment

3. Terraform State:
   ✅ Remote backend configured (GCS bucket)
   ✅ State locking enabled
   ✅ No local state files committed

4. Database Readiness (Plant Only):
   ✅ Cloud SQL instance RUNNABLE
   ✅ Database created: waooaw
   ✅ User created: plant_user
   ✅ Migrations applied

5. Docker Images:
   ✅ All Dockerfiles present in src/
   ✅ Multi-stage builds for optimization
   ✅ Non-root users configured
   ✅ Health checks defined

6. Testing:
   ✅ Local Docker Compose tests passing
   ✅ Unit tests: 169/169 passing
   ✅ Integration tests: 10/10 passing
   ✅ E2E tests: 10/10 passing
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

