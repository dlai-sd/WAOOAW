"""
WAOOAW Plant Phase - Backend API
FastAPI application for agent manufacturing pipeline with constitutional alignment

Architecture: 7-section BaseEntity + L0/L1 constitutional validators + cryptographic signatures
Reference: /docs/plant/PLANT_BLUEPRINT.yaml Section 13
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime
import logging

from core.config import settings
from core.database import Base, initialize_database
from core.exceptions import (
    PlantException,
    ConstitutionalAlignmentError,
    HashChainBrokenError,
    AmendmentSignatureError,
    EntityNotFoundError,
    DuplicateEntityError,
    ValidationError,
)

# Initialize FastAPI app with enhanced OpenAPI metadata
app = FastAPI(
    title=settings.app_name,
    description="""
# WAOOAW Plant Phase API

Backend API for agent manufacturing pipeline with constitutional alignment (L0/L1 principles).

## Key Features
- **Genesis Certification**: Skills and job roles certified via multi-gate approval
- **Agent Creation**: Constitutional validation with industry locking
- **Audit & Compliance**: L0/L1 constitutional alignment tracking
- **Type Safety**: Full OpenAPI 3.0 spec for TypeScript codegen

## Constitutional Principles (L0)
- **L0-01**: Single Governor - governance_agent_id required
- **L0-02**: Agent Specialization - skills + job roles certified before use
- **L0-03**: External Execution Approval - trial mode sandbox enforcement
- **L0-05**: Immutable Audit Trail - all entity changes logged
- **L0-06**: Version Control - hash-based version tracking
- **L0-07**: Amendment History - signature-verified evolution

## Authentication (Future)
- JWT tokens validated at gateway layer
- RBAC enforcement for Genesis/Governor operations
- Trial mode sandbox routing via OPA policy

## Rate Limits (Future)
- 100 req/min per customer (trial mode)
- 1000 req/min per customer (paid subscription)

## Support
- Documentation: https://docs.waooaw.com
- GitHub: https://github.com/dlai-sd/WAOOAW
""",
    version=settings.app_version,
    docs_url="/api/docs",  # Updated to include Swagger UI
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    debug=settings.debug,
    contact={
        "name": "WAOOAW Engineering Team",
        "url": "https://waooaw.com",
        "email": "engineering@waooaw.com"
    },
    license_info={
        "name": "Proprietary",
        "url": "https://waooaw.com/license"
    }
)

# CORS configuration - allow specific origins only
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,  # Allow cookies/JWT tokens (future)
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Correlation-ID",
        "X-Causation-ID",
        "X-Request-ID",
    ],
    expose_headers=[
        "X-Correlation-ID",
        "X-Causation-ID",
        "X-Request-ID",
    ],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# ... (rest of the code remains unchanged)

# ========== API ROUTE MOUNTING ==========
from api.v1.router import api_v1_router
app.include_router(api_v1_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,  # Plant Backend runs on 8001, Gateway on 8000
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
