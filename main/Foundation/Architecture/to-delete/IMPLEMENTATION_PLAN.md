# FastAPI Gateway Implementation Plan - Direct Integration

**Version:** 1.0  
**Last Updated:** 2026-01-16  
**Strategy:** Direct CP/PP → Plant integration (gateway layer added in Phase 4)  
**Story Size:** Medium (3-5 days per story)  
**Total Stories:** 11 stories across 3 phases  
**Total Timeline:** 8-10 weeks  

---

## Executive Summary

This implementation plan focuses on **getting CP, PP, and Plant working together NOW** using direct API integration, then adding the unified gateway layer later. This pragmatic approach delivers value incrementally:

**Phase 1 (Plant):** Make Plant APIs production-ready for CP/PP consumption (4 stories, 3 weeks)  
**Phase 2 (PP):** Wire PP admin portal to Plant backend (4 stories, 3 weeks)  
**Phase 3 (CP):** Wire CP marketplace to Plant backend (3 stories, 2-3 weeks)  
**Phase 4 (Future):** Add unified gateway layer with constitutional middleware (deferred)

**Key Principle:** Start simple (direct integration), evolve to sophisticated (gateway with OPA, audit, RBAC).

---

## Phase 1: Plant Backend - Production Readiness (3 weeks)

**Goal:** Make Plant APIs consumable by CP/PP with proper contracts, error handling, and documentation.

---

### PLANT-001: API Contract Publication & Type Safety

**Priority:** P0 (Blocker for all other stories)  
**Effort:** 3 days  
**Owner:** Plant Team  

**Problem:**
- CP/PP don't know what endpoints Plant offers
- No shared type definitions (TypeScript ↔ Python mismatch)
- Runtime type errors when frontends call Plant APIs

**User Story:**
```gherkin
As a CP/PP frontend developer
I want auto-generated TypeScript types from Plant's OpenAPI spec
So that I get compile-time type safety and IDE autocomplete
```

**Acceptance Criteria:**
- [ ] Plant backend exposes `/openapi.json` endpoint (FastAPI does this automatically)
- [ ] OpenAPI spec includes all Plant endpoints:
  - Genesis: `/api/v1/genesis/skills`, `/api/v1/genesis/job-roles`, `/api/v1/genesis/skills/{id}/certify`
  - Agents: `/api/v1/agents` (POST/GET), `/api/v1/agents/{id}`, `/api/v1/agents/{id}/assign-team`
  - Audit: `/api/v1/audit/run`, `/api/v1/audit/tampering/{id}`, `/api/v1/audit/export`
- [ ] TypeScript types generated using `openapi-typescript`:
  ```bash
  curl http://localhost:8000/openapi.json > openapi.json
  npx openapi-typescript openapi.json --output src/types/plant-api.generated.ts
  ```
- [ ] Types include Pydantic model mappings:
  - `AgentResponse`, `SkillResponse`, `JobRoleResponse`, `AuditReportResponse`
- [ ] CI/CD workflow added to regenerate types on Plant schema changes
- [ ] Documentation: `README_API_CONTRACT.md` explaining type generation process

**Technical Tasks:**
1. Verify Plant's FastAPI app serves `/openapi.json` (should work out-of-box)
2. Add `response_model` to all Plant route handlers (ensures OpenAPI accuracy)
3. Create npm script in CP/PP: `npm run generate-types` → runs `openapi-typescript`
4. Add GitHub Action: `.github/workflows/sync-api-types.yml` (runs on Plant changes)
5. Update CP/PP `tsconfig.json` to include generated types folder

**Dependencies:** None (can start immediately)

**Risks:**
- OpenAPI spec might be incomplete if Pydantic models missing fields
- UUID vs string type mismatch (Plant uses UUID, TypeScript expects string)

**Validation:**
```typescript
// CP/PP frontend code should compile with generated types
import { AgentResponse } from './types/plant-api.generated';

const agent: AgentResponse = await fetch('/api/v1/agents/123');
console.log(agent.id); // TypeScript knows this is a string (UUID)
console.log(agent.constitutional_alignment); // TypeScript knows this exists!
```

---

### PLANT-002: Error Handling Standardization

**Priority:** P0 (Blocker for CP/PP integration)  
**Effort:** 4 days  
**Owner:** Plant Team  

**Problem:**
- Plant has custom exceptions (ConstitutionalAlignmentError, HashChainBrokenError) but CP/PP don't understand them
- No standardized error response format
- Frontend can't distinguish between 400 Bad Request, 422 Validation Error, 500 Internal Error

**User Story:**
```gherkin
As a CP/PP frontend developer
I want standardized error responses from Plant APIs
So that I can show meaningful error messages to users
```

**Acceptance Criteria:**
- [ ] All Plant endpoints return errors in RFC 7807 format (Problem Details):
  ```json
  {
    "type": "https://waooaw.com/errors/constitutional-alignment",
    "title": "Constitutional Alignment Error",
    "status": 422,
    "detail": "Agent missing required governance_agent_id (L0-01 violation)",
    "instance": "/api/v1/agents",
    "correlation_id": "abc-123-def-456",
    "violations": ["L0-01: governance_agent_id missing"]
  }
  ```
- [ ] HTTP status code mapping:
  - `400` - Bad Request (client error, invalid input)
  - `401` - Unauthorized (missing/invalid JWT - future)
  - `403` - Forbidden (no permission - future)
  - `404` - Not Found (entity doesn't exist)
  - `422` - Unprocessable Entity (constitutional violation, validation error)
  - `500` - Internal Server Error (unexpected exceptions)
  - `503` - Service Unavailable (database down, OPA unavailable - future)
- [ ] Pydantic error response model:
  ```python
  class ErrorResponse(BaseModel):
      type: str
      title: str
      status: int
      detail: str
      instance: str
      correlation_id: Optional[str] = None
      violations: Optional[List[str]] = None
  ```
- [ ] Global exception handler added to Plant `main.py`:
  ```python
  @app.exception_handler(Exception)
  async def global_exception_handler(request: Request, exc: Exception):
      return JSONResponse(status_code=500, content=ErrorResponse(...).dict())
  ```
- [ ] Constitutional error handler returns 422 with L0 violation details
- [ ] Database error handler returns 503 with retry guidance
- [ ] TypeScript error types generated from OpenAPI spec

**Technical Tasks:**
1. Create `models/error_responses.py` with RFC 7807 Pydantic models
2. Update all exception handlers in `main.py` to use RFC 7807 format
3. Add correlation_id generation (UUID v4) to all error responses
4. Update OpenAPI schema to document error responses per endpoint
5. Write integration tests: call endpoint with bad input, assert 422 + RFC 7807 format
6. Update frontend to parse RFC 7807 errors and display `detail` field

**Dependencies:** 
- PLANT-001 (needs OpenAPI spec to document errors)

**Risks:**
- Breaking change for any existing Plant API consumers (none currently)
- Large refactor across all route handlers

**Validation:**
```bash
# Test constitutional error handling
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Agent", "skills": []}' # Missing governance_agent_id

# Expected response (422):
{
  "type": "https://waooaw.com/errors/constitutional-alignment",
  "title": "Constitutional Alignment Error",
  "status": 422,
  "detail": "governance_agent_id required (L0-01: Single Governor)",
  "violations": ["L0-01: governance_agent_id missing"]
}
```

---

### PLANT-003: CORS Configuration for CP/PP Origins

**Priority:** P1 (Required for browser-based API calls)  
**Effort:** 2 days  
**Owner:** Plant Team  

**Problem:**
- Plant's CORS allows `*` (wildcard) - security risk
- CP/PP frontends need to call Plant APIs directly (until gateway deployed)
- Browser blocks cross-origin requests without proper CORS headers

**User Story:**
```gherkin
As a CP/PP frontend
I want to call Plant APIs directly from the browser
So that I can display agent data without CORS errors
```

**Acceptance Criteria:**
- [ ] Plant CORS middleware allows specific origins:
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=[
          "http://localhost:3000",  # CP frontend (local dev)
          "http://localhost:5173",  # PP frontend (local dev)
          "https://cp.demo.waooaw.com",
          "https://pp.demo.waooaw.com",
          "https://cp.waooaw.com",  # Production
          "https://pp.waooaw.com",
      ],
      allow_credentials=True,
      allow_methods=["GET", "POST", "PUT", "DELETE"],
      allow_headers=["Authorization", "Content-Type", "X-Correlation-ID"],
      expose_headers=["X-Correlation-ID", "X-Request-ID"],
  )
  ```
- [ ] CORS origins configurable via environment variable:
  ```bash
  CORS_ORIGINS=http://localhost:3000,http://localhost:5173,https://cp.demo.waooaw.com
  ```
- [ ] Preflight OPTIONS requests return 200 OK with CORS headers
- [ ] `Access-Control-Allow-Credentials: true` header present (for future JWT cookies)
- [ ] CORS configuration documented in `README_CORS.md`

**Technical Tasks:**
1. Update `core/config.py` to load `CORS_ORIGINS` from environment
2. Update `main.py` CORS middleware to use environment-based origin list
3. Add `.env.example` with CORS_ORIGINS sample
4. Test CORS from CP/PP frontend (Chrome DevTools Network tab - check CORS headers)
5. Add CORS troubleshooting guide to documentation

**Dependencies:**
- None (can run in parallel with PLANT-001/002)

**Risks:**
- Too restrictive CORS breaks local development
- Missing CORS headers cause silent failures in browser

**Validation:**
```javascript
// CP frontend (React)
const response = await fetch('http://localhost:8000/api/v1/agents', {
  method: 'GET',
  credentials: 'include',  // Send cookies (future JWT)
  headers: {
    'Content-Type': 'application/json'
  }
});

// Should NOT see CORS error in Chrome DevTools console
// Response headers should include:
// Access-Control-Allow-Origin: http://localhost:3000
// Access-Control-Allow-Credentials: true
```

---

### PLANT-004: API Documentation & Postman Collection

**Priority:** P2 (Nice-to-have, not blocking)  
**Effort:** 3 days  
**Owner:** Plant Team  

**Problem:**
- CP/PP developers don't know how to call Plant APIs
- No examples of request/response payloads
- Trial-and-error API exploration wastes time

**User Story:**
```gherkin
As a CP/PP developer
I want comprehensive API documentation with examples
So that I can integrate with Plant APIs quickly
```

**Acceptance Criteria:**
- [ ] OpenAPI documentation enhanced with descriptions and examples:
  ```python
  @router.post(
      "/agents",
      response_model=AgentResponse,
      status_code=201,
      summary="Create new agent",
      description="""
      Creates a new agent with constitutional validation (L0/L1 compliance).
      
      **Required fields:**
      - name: Agent display name
      - industry_id: Must reference existing Industry entity
      - job_role_id: Must reference certified JobRole
      - skills: List of certified Skill UUIDs
      - governance_agent_id: Genesis or Governor UUID (L0-01 requirement)
      
      **Constitutional validation:**
      - L0-01: governance_agent_id must be present
      - L0-02: amendment_history initialized with creation event
      - L0-05: Audit trail entry created
      
      **Returns:**
      - 201 Created: Agent entity with UUID
      - 422 Unprocessable Entity: Constitutional alignment failure
      - 404 Not Found: Referenced industry/job_role/skills don't exist
      """,
      responses={
          201: {"description": "Agent created successfully"},
          422: {"description": "Constitutional alignment error"},
          404: {"description": "Referenced entity not found"},
      },
  )
  async def create_agent(...):
      ...
  ```
- [ ] FastAPI Swagger UI enhanced at `/docs` with:
  - All endpoints grouped by category (Genesis, Agents, Audit)
  - Request/response examples for each endpoint
  - Error response examples (400, 422, 500)
- [ ] ReDoc alternative documentation at `/redoc` (cleaner for reading)
- [ ] Postman collection exported:
  ```bash
  # Auto-generate from OpenAPI spec
  npx openapi-to-postmanv2 -s openapi.json -o postman_collection.json
  ```
- [ ] Postman collection includes:
  - Environment variables (base_url, auth_token placeholder)
  - Pre-request scripts for correlation_id generation
  - Test assertions for successful responses
- [ ] README_API_USAGE.md with quick start guide:
  - How to import Postman collection
  - How to run Plant locally
  - How to call APIs from frontend
  - Common error scenarios and solutions

**Technical Tasks:**
1. Add detailed docstrings to all Plant route handlers
2. Add Pydantic model `Config.schema_extra` with JSON examples
3. Export OpenAPI spec: `curl http://localhost:8000/openapi.json > openapi.json`
4. Generate Postman collection using `openapi-to-postmanv2`
5. Create environment variables in Postman (Local, Demo, Prod)
6. Write README_API_USAGE.md with screenshots

**Dependencies:**
- PLANT-001 (needs OpenAPI spec)
- PLANT-002 (needs error responses documented)

**Risks:**
- Documentation becomes stale if not updated with code changes
- Postman collection maintenance overhead

**Validation:**
- [ ] Developer can import Postman collection and successfully call all Plant endpoints
- [ ] FastAPI `/docs` page renders all 13 endpoints with descriptions
- [ ] ReDoc `/redoc` page shows detailed API reference

---

## Phase 2: PP Backend - Admin Integration (3 weeks)

**Goal:** Wire PP admin portal to Plant backend for Genesis workflow, agent management, and audit operations.

---

### PP-001: Plant API Client Library (Python)

**Priority:** P0 (Foundation for all PP → Plant calls)  
**Effort:** 4 days  
**Owner:** PP Team  

**Problem:**
- PP backend needs to call Plant APIs but no client library exists
- Manual HTTP requests are error-prone and lack type safety
- No retry logic or error handling for Plant API calls

**User Story:**
```gherkin
As a PP backend developer
I want a Python client library for Plant APIs
So that I can call Plant endpoints with type safety and error handling
```

**Acceptance Criteria:**
- [ ] Python client library created at `src/PP/BackEnd/clients/plant_client.py`:
  ```python
  class PlantAPIClient:
      def __init__(self, base_url: str, timeout: int = 30):
          self.base_url = base_url
          self.timeout = timeout
          self.session = httpx.AsyncClient(timeout=timeout)
      
      async def create_agent(self, agent_data: AgentCreate) -> AgentResponse:
          """POST /api/v1/agents"""
          response = await self.session.post(
              f"{self.base_url}/api/v1/agents",
              json=agent_data.dict(),
              headers={"Content-Type": "application/json"}
          )
          response.raise_for_status()
          return AgentResponse(**response.json())
      
      async def get_agent(self, agent_id: UUID) -> AgentResponse:
          """GET /api/v1/agents/{id}"""
          response = await self.session.get(
              f"{self.base_url}/api/v1/agents/{agent_id}"
          )
          response.raise_for_status()
          return AgentResponse(**response.json())
      
      async def certify_skill(self, skill_id: UUID) -> SkillResponse:
          """POST /api/v1/genesis/skills/{id}/certify"""
          response = await self.session.post(
              f"{self.base_url}/api/v1/genesis/skills/{skill_id}/certify"
          )
          response.raise_for_status()
          return SkillResponse(**response.json())
  ```
- [ ] Client uses `httpx` library (async HTTP client, same as requests but async)
- [ ] Pydantic models imported from Plant's OpenAPI spec:
  ```python
  # Copy from Plant or generate from OpenAPI
  from models.plant_schemas import AgentCreate, AgentResponse, SkillResponse
  ```
- [ ] Error handling for Plant API failures:
  ```python
  try:
      agent = await plant_client.create_agent(agent_data)
  except httpx.HTTPStatusError as e:
      if e.response.status_code == 422:
          # Parse RFC 7807 error response
          error = ErrorResponse(**e.response.json())
          raise ConstitutionalAlignmentError(error.detail)
      elif e.response.status_code == 404:
          raise EntityNotFoundError(f"Referenced entity not found: {e.response.json()}")
      else:
          raise PlantAPIError(f"Plant API error: {e.response.text}")
  ```
- [ ] Retry logic with exponential backoff (3 retries, max 10s delay):
  ```python
  @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
  async def create_agent(self, agent_data: AgentCreate) -> AgentResponse:
      ...
  ```
- [ ] Correlation ID propagation:
  ```python
  async def _request(self, method: str, path: str, **kwargs):
      headers = kwargs.get("headers", {})
      headers["X-Correlation-ID"] = str(uuid.uuid4())
      headers["X-Causation-ID"] = headers.get("X-Correlation-ID")
      response = await self.session.request(method, path, headers=headers, **kwargs)
      return response
  ```
- [ ] Client configured via environment variable:
  ```bash
  PLANT_API_URL=http://localhost:8000  # Local dev
  PLANT_API_URL=https://plant.demo.waooaw.com  # Demo environment
  ```
- [ ] Unit tests with mocked Plant responses (httpx-mock library)

**Technical Tasks:**
1. Add `httpx` and `tenacity` (retry library) to PP's `requirements.txt`
2. Copy Plant's Pydantic schemas to PP or generate from OpenAPI spec
3. Implement PlantAPIClient with all 13 Plant endpoints
4. Add error handling for RFC 7807 error responses
5. Write unit tests with httpx-mock: `test_plant_client.py`
6. Add integration test: call real Plant API in test environment

**Dependencies:**
- PLANT-001 (needs Plant OpenAPI spec for Pydantic models)
- PLANT-002 (needs RFC 7807 error format)

**Risks:**
- Pydantic model drift between PP and Plant (mitigate with OpenAPI codegen)
- Retry logic might amplify load during Plant outages

**Validation:**
```python
# PP backend code
plant_client = PlantAPIClient(base_url=settings.PLANT_API_URL)

# Create agent via Plant API
agent_data = AgentCreate(
    name="Finance Agent",
    industry_id=industry_id,
    job_role_id=job_role_id,
    skills=[skill1_id, skill2_id],
    governance_agent_id="genesis"
)

try:
    agent = await plant_client.create_agent(agent_data)
    print(f"Agent created: {agent.id}")
except ConstitutionalAlignmentError as e:
    print(f"Constitutional error: {e}")
```

---

### PP-002: Genesis Workflow Integration

**Priority:** P0 (Core PP feature)  
**Effort:** 5 days  
**Owner:** PP Team  

**Problem:**
- PP admin portal needs to certify skills/job roles via Genesis workflow
- Currently, PP has placeholder routes but no Plant integration
- No UI for Genesis certification (approval queue)

**User Story:**
```gherkin
As a PP admin with Genesis role
I want to certify new skills and job roles
So that agents can be created with validated capabilities
```

**Acceptance Criteria:**
- [ ] PP backend routes call Plant Genesis API:
  ```python
  # src/PP/BackEnd/api/genesis.py
  
  @router.post("/genesis/skills", response_model=SkillResponse)
  async def create_skill(
      skill_data: SkillCreate,
      plant_client: PlantAPIClient = Depends(get_plant_client),
      current_user: User = Depends(get_current_user)  # Future: JWT auth
  ):
      """
      Create new skill (pending Genesis certification).
      Admin submits skill, Genesis agent certifies via Plant API.
      """
      # Call Plant API
      skill = await plant_client.create_skill(skill_data)
      
      # Log to PP audit trail (future)
      # await audit_service.log_action("skill.created", skill.id, current_user.id)
      
      return skill
  
  @router.post("/genesis/skills/{skill_id}/certify", response_model=SkillResponse)
  async def certify_skill(
      skill_id: UUID,
      plant_client: PlantAPIClient = Depends(get_plant_client),
      current_user: User = Depends(get_current_user)
  ):
      """
      Certify skill (Genesis role required).
      Calls Plant Genesis API to validate and certify skill.
      """
      # TODO: Check current_user has Genesis role (RBAC - future)
      
      # Call Plant API
      skill = await plant_client.certify_skill(skill_id)
      
      # Log certification event
      # await audit_service.log_action("skill.certified", skill.id, current_user.id)
      
      return skill
  ```
- [ ] PP routes mounted in `main.py`:
  ```python
  from api import genesis
  app.include_router(genesis.router, prefix="/api", tags=["genesis"])
  ```
- [ ] PP frontend pages for Genesis workflow:
  - `/admin/genesis/skills` - List pending skills
  - `/admin/genesis/skills/new` - Create new skill form
  - `/admin/genesis/skills/{id}` - Skill details + Certify button
  - `/admin/genesis/job-roles` - List pending job roles
  - `/admin/genesis/job-roles/new` - Create new job role form
- [ ] Frontend calls PP backend (which proxies to Plant):
  ```typescript
  // src/PP/FrontEnd/services/genesis.service.ts
  
  export async function createSkill(skillData: SkillCreate): Promise<SkillResponse> {
      const response = await fetch('/api/genesis/skills', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(skillData)
      });
      if (!response.ok) throw new Error('Failed to create skill');
      return response.json();
  }
  
  export async function certifySkill(skillId: string): Promise<SkillResponse> {
      const response = await fetch(`/api/genesis/skills/${skillId}/certify`, {
          method: 'POST'
      });
      if (!response.ok) throw new Error('Failed to certify skill');
      return response.json();
  }
  ```
- [ ] UI shows Genesis certification status:
  - Pending (yellow badge)
  - Certified (green checkmark)
  - Rejected (red X - future)

**Technical Tasks:**
1. Create `api/genesis.py` in PP backend with routes
2. Implement PlantAPIClient methods for Genesis endpoints
3. Create Genesis UI pages in PP frontend (React components)
4. Wire frontend forms to PP backend API
5. Add error handling UI for constitutional violations (422 errors)
6. Integration test: Create skill → Certify skill → Verify in Plant database

**Dependencies:**
- PP-001 (needs PlantAPIClient)
- PLANT-002 (needs error handling)

**Risks:**
- Genesis workflow is async (certification might take hours) - need polling or webhooks
- No rollback if Plant API fails after PP creates local record

**Validation:**
```bash
# PP Admin workflow
1. Login to PP admin portal (http://localhost:8006/admin/genesis/skills)
2. Click "Create Skill" button
3. Fill form: Name="Python 3.11", Category="technical", Description="..."
4. Submit form
5. PP calls Plant API → POST /api/v1/genesis/skills
6. Plant returns pending skill (status="pending_certification")
7. Admin sees skill in "Pending Certification" list
8. Admin clicks "Certify" button
9. PP calls Plant API → POST /api/v1/genesis/skills/{id}/certify
10. Plant validates L0/L1 compliance, updates status="certified"
11. Admin sees green checkmark, skill ready for agent creation
```

---

### PP-003: Agent Management Integration

**Priority:** P0 (Core PP feature)  
**Effort:** 4 days  
**Owner:** PP Team  

**Problem:**
- PP admin portal needs to create/list/view agents via Plant API
- Currently, PP has no agent management UI

**User Story:**
```gherkin
As a PP admin
I want to create and manage agents
So that customers can use them in the marketplace
```

**Acceptance Criteria:**
- [ ] PP backend routes for agent management:
  ```python
  # src/PP/BackEnd/api/agents.py
  
  @router.post("/agents", response_model=AgentResponse)
  async def create_agent(
      agent_data: AgentCreate,
      plant_client: PlantAPIClient = Depends(get_plant_client),
      current_user: User = Depends(get_current_user)
  ):
      """
      Create new agent (Governor role required in future).
      Calls Plant API to create agent with constitutional validation.
      """
      # TODO: Check current_user.is_governor (future)
      
      agent = await plant_client.create_agent(agent_data)
      
      # Log agent creation
      # await audit_service.log_action("agent.created", agent.id, current_user.id)
      
      return agent
  
  @router.get("/agents", response_model=List[AgentResponse])
  async def list_agents(
      industry_id: Optional[UUID] = None,
      job_role_id: Optional[UUID] = None,
      limit: int = 100,
      plant_client: PlantAPIClient = Depends(get_plant_client)
  ):
      """List all agents with optional filters."""
      agents = await plant_client.list_agents(
          industry_id=industry_id,
          job_role_id=job_role_id,
          limit=limit
      )
      return agents
  
  @router.get("/agents/{agent_id}", response_model=AgentResponse)
  async def get_agent(
      agent_id: UUID,
      plant_client: PlantAPIClient = Depends(get_plant_client)
  ):
      """Get agent details."""
      agent = await plant_client.get_agent(agent_id)
      return agent
  ```
- [ ] PP frontend pages:
  - `/admin/agents` - List all agents (table with filters)
  - `/admin/agents/new` - Create agent form
  - `/admin/agents/{id}` - Agent details page
- [ ] Agent creation form includes:
  - Name (text input)
  - Industry (dropdown, fetched from Plant)
  - Job Role (dropdown, fetched from Plant)
  - Skills (multi-select, fetched from Plant)
  - Governance Agent ID (dropdown: Genesis or Governor)
- [ ] Agent list table shows:
  - Agent name, industry, job role, status, created date
  - Filters: Industry, Job Role, Status
  - Pagination (if >100 agents)
- [ ] Error handling for constitutional violations:
  ```typescript
  try {
      const agent = await createAgent(agentData);
      toast.success('Agent created successfully');
      navigate(`/admin/agents/${agent.id}`);
  } catch (error) {
      if (error.status === 422) {
          const errorData = await error.json();
          toast.error(`Constitutional error: ${errorData.detail}`);
          setErrors(errorData.violations);  // Show L0 violations in form
      } else {
          toast.error('Failed to create agent');
      }
  }
  ```

**Technical Tasks:**
1. Create `api/agents.py` in PP backend
2. Implement agent CRUD operations in PlantAPIClient
3. Create agent management UI pages (React components)
4. Add form validation (Formik + Yup)
5. Add error display for constitutional violations (red alert boxes)
6. Integration test: Create agent → List agents → View agent details

**Dependencies:**
- PP-001 (needs PlantAPIClient)
- PP-002 (needs Genesis workflow to create skills/job roles first)

**Risks:**
- Agent creation form is complex (3 dropdowns with dependencies)
- Skills multi-select needs typeahead/autocomplete for UX

**Validation:**
```bash
# PP Admin workflow
1. Login to PP admin portal
2. Navigate to /admin/agents
3. Click "Create Agent" button
4. Fill form:
   - Name: "Email Marketing Agent"
   - Industry: "Marketing"
   - Job Role: "Content Writer"
   - Skills: Select "Email Copywriting", "A/B Testing", "Analytics"
   - Governance Agent: "Genesis"
5. Submit form
6. PP calls Plant API → POST /api/v1/agents
7. Plant validates constitutional compliance (L0-01: governance_agent_id present)
8. Agent created, redirected to /admin/agents/{id}
9. Agent details page shows:
   - Name, industry, job role, skills
   - Constitutional alignment status: "✅ L0/L1 Compliant"
   - Created timestamp, version hash, amendment history
```

---

### PP-004: Audit Dashboard Integration

**Priority:** P2 (Nice-to-have, not blocking)  
**Effort:** 3 days  
**Owner:** PP Team  

**Problem:**
- PP admin portal needs to show constitutional compliance audit reports
- Plant has audit API but no UI to visualize results

**User Story:**
```gherkin
As a PP admin
I want to view constitutional compliance audit reports
So that I can verify platform integrity
```

**Acceptance Criteria:**
- [ ] PP backend route for audit operations:
  ```python
  @router.post("/audit/run", response_model=AuditReportResponse)
  async def run_audit(
      entity_type: Optional[str] = None,
      entity_id: Optional[UUID] = None,
      plant_client: PlantAPIClient = Depends(get_plant_client),
      current_user: User = Depends(get_current_user)
  ):
      """Run constitutional compliance audit."""
      # TODO: Check current_user has Viewer role or higher (RBAC - future)
      
      report = await plant_client.run_compliance_audit(
          entity_type=entity_type,
          entity_id=entity_id
      )
      return report
  ```
- [ ] PP frontend audit dashboard page: `/admin/audit`
- [ ] Audit dashboard shows:
  - Overall compliance score (percentage)
  - Breakdown by entity type (Agents: 95%, Skills: 100%, JobRoles: 98%)
  - L0 principle compliance (7 checkboxes with pass/fail)
  - Recent violations (table with entity ID, violation type, timestamp)
- [ ] "Run Audit" button triggers Plant audit API
- [ ] Audit results displayed in cards/charts:
  - Donut chart: Compliant vs Non-Compliant entities
  - Bar chart: Violations by L0 principle
  - Table: Non-compliant entities with details
- [ ] Export audit report as CSV (future: PDF)

**Technical Tasks:**
1. Create `api/audit.py` in PP backend
2. Implement audit methods in PlantAPIClient
3. Create audit dashboard UI (React components with Chart.js)
4. Add CSV export functionality
5. Style audit report (green/red indicators, warning icons)

**Dependencies:**
- PP-001 (needs PlantAPIClient)

**Risks:**
- Audit operation is expensive (scans all entities) - need loading spinner
- Large audit reports might timeout HTTP request

**Validation:**
```bash
# PP Admin workflow
1. Navigate to /admin/audit
2. Click "Run Constitutional Audit" button
3. PP calls Plant API → POST /api/v1/audit/run
4. Plant scans all entities, validates L0/L1 compliance
5. Audit report returned (10 seconds later)
6. Dashboard shows:
   - Compliance Score: 97%
   - L0-01 (Single Governor): ✅ Pass (100%)
   - L0-02 (Agent Specialization): ✅ Pass (100%)
   - L0-03 (External Execution Approval): ⚠️ Partial (95%)
   - Violations: 3 agents missing trial_mode_sandbox_url
7. Admin clicks "Export CSV" → downloads audit_report_2026-01-16.csv
```

---

## Phase 3: CP Backend - Customer Integration (2-3 weeks)

**Goal:** Wire CP marketplace to Plant backend for agent discovery, trial signup, and agent execution.

---

### CP-001: Agent Marketplace API Integration

**Priority:** P0 (Core CP feature)  
**Effort:** 4 days  
**Owner:** CP Team  

**Problem:**
- CP marketplace shows hardcoded agent list (no Plant integration)
- Customers can't see real agents from Plant backend
- Agent details (rating, specialty, activity) not synced

**User Story:**
```gherkin
As a CP customer
I want to browse real agents from the platform
So that I can discover agents for my business needs
```

**Acceptance Criteria:**
- [ ] CP backend has Plant API client (same as PP-001):
  ```python
  # src/CP/BackEnd/clients/plant_client.py
  # (Copy from PP or extract to shared library)
  
  class PlantAPIClient:
      async def list_agents(self, industry_id: Optional[UUID] = None, limit: int = 100):
          """GET /api/v1/agents"""
          ...
      
      async def get_agent(self, agent_id: UUID):
          """GET /api/v1/agents/{id}"""
          ...
  ```
- [ ] CP backend routes for marketplace:
  ```python
  # src/CP/BackEnd/api/marketplace.py
  
  @router.get("/marketplace/agents", response_model=List[AgentMarketplaceCard])
  async def list_marketplace_agents(
      industry: Optional[str] = None,
      min_rating: float = 0.0,
      plant_client: PlantAPIClient = Depends(get_plant_client)
  ):
      """
      List agents for marketplace browsing.
      Enriches Plant agent data with CP-specific fields (rating, status, activity).
      """
      # Get agents from Plant
      agents = await plant_client.list_agents(industry_id=industry)
      
      # Enrich with CP data (future: join with cp_agent_stats table)
      marketplace_agents = []
      for agent in agents:
          marketplace_agents.append(AgentMarketplaceCard(
              id=agent.id,
              name=agent.name,
              industry=agent.entity_type,  # Map from Plant schema
              specialty="Placeholder",  # TODO: Get from CP database
              rating=4.5,  # TODO: Calculate from CP reviews
              status="available",  # TODO: Get from CP agent_status table
              activity="Posted 23 times today"  # TODO: Get from CP analytics
          ))
      
      return marketplace_agents
  
  @router.get("/marketplace/agents/{agent_id}", response_model=AgentDetailPage)
  async def get_agent_details(
      agent_id: UUID,
      plant_client: PlantAPIClient = Depends(get_plant_client)
  ):
      """Get detailed agent info for marketplace profile page."""
      # Get base agent from Plant
      agent = await plant_client.get_agent(agent_id)
      
      # Enrich with CP data
      # TODO: Fetch rating, reviews, trial stats from CP database
      
      return AgentDetailPage(
          id=agent.id,
          name=agent.name,
          description="...",
          rating=4.5,
          reviews_count=127,
          trial_signups=45,
          retention_rate=0.98
      )
  ```
- [ ] CP frontend marketplace pages:
  - `/marketplace` - Agent card grid (browse all agents)
  - `/marketplace/agents/{id}` - Agent profile page
- [ ] Agent card shows:
  - Agent avatar (gradient with initials)
  - Name, industry, specialty
  - Rating (stars)
  - Status badge (🟢 Available, 🟡 Working, 🔴 Offline)
  - Activity ("Posted 23 times today")
  - "Try for Free" button
- [ ] Marketplace filters:
  - Industry (Marketing, Education, Sales)
  - Rating (1-5 stars)
  - Price range (₹8,000 - ₹20,000/month)
  - Specialty tags (B2B SaaS, Healthcare, etc.)
- [ ] Search functionality (by agent name, specialty)

**Technical Tasks:**
1. Create PlantAPIClient in CP backend (or extract to shared library)
2. Create `api/marketplace.py` with agent listing routes
3. Create marketplace UI pages (React components)
4. Add agent card component with styling
5. Add search + filter UI (Algolia or client-side filtering)
6. Integration test: List agents → Filter by industry → View agent details

**Dependencies:**
- PLANT-001 (needs Plant API)
- PLANT-003 (needs CORS for browser calls - if frontend calls Plant directly)

**Risks:**
- Agent data enrichment (rating, status) requires CP database tables (not yet built)
- Marketplace performance if 100+ agents (need pagination)

**Validation:**
```bash
# CP Customer workflow
1. Visit CP marketplace: http://localhost:3000/marketplace
2. See agent card grid (loaded from Plant API via CP backend)
3. Agent cards show:
   - Name: "Email Marketing Agent"
   - Industry: "Marketing"
   - Specialty: "B2B SaaS"
   - Rating: ⭐⭐⭐⭐⭐ (4.8)
   - Status: 🟢 Available
   - Activity: "Posted 23 times today"
4. Click agent card → Navigate to /marketplace/agents/{id}
5. Agent profile page shows:
   - Full description
   - Skills list (from Plant)
   - Reviews (future: from CP database)
   - "Start 7-Day Trial" button
```

---

### CP-002: Trial Signup Integration

**Priority:** P0 (Core CP feature - revenue driver)  
**Effort:** 5 days  
**Owner:** CP Team  

**Problem:**
- CP trial signup flow doesn't create agent instances in Plant
- No link between CP trial record and Plant agent
- Trial mode routing not implemented (agent executes in production instead of sandbox)

**User Story:**
```gherkin
As a CP customer
I want to start a 7-day trial of an agent
So that I can test the agent before subscribing
```

**Acceptance Criteria:**
- [ ] CP backend trial signup route:
  ```python
  # src/CP/BackEnd/api/trials.py
  
  @router.post("/trials", response_model=TrialResponse)
  async def create_trial(
      trial_data: TrialCreate,
      plant_client: PlantAPIClient = Depends(get_plant_client),
      current_user: User = Depends(get_current_user)  # Future: JWT auth
  ):
      """
      Start 7-day trial for an agent.
      
      Steps:
      1. Create trial record in CP database (customer_id, agent_id, expires_at)
      2. Link trial to Plant agent (store trial_mode=true in agent metadata)
      3. Create sandbox environment for trial agent (future: Kubernetes namespace)
      4. Return trial credentials + sandbox URL
      """
      # TODO: Check customer doesn't have active trial for this agent
      
      # Create trial record in CP database
      trial = Trial(
          customer_id=current_user.id,
          agent_id=trial_data.agent_id,
          status="active",
          expires_at=datetime.utcnow() + timedelta(days=7),
          trial_mode=True
      )
      db.add(trial)
      db.commit()
      
      # TODO: Update Plant agent metadata (trial_mode=true)
      # TODO: Provision sandbox environment
      
      return TrialResponse(
          trial_id=trial.id,
          agent_id=trial.agent_id,
          expires_at=trial.expires_at,
          sandbox_url=f"https://sandbox.demo.waooaw.com/agents/{trial.agent_id}",
          deliverables_url=f"https://cp.demo.waooaw.com/trials/{trial.id}/deliverables"
      )
  ```
- [ ] CP database table for trials:
  ```sql
  CREATE TABLE cp_trials (
      id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
      customer_id UUID NOT NULL REFERENCES cp_customers(id),
      agent_id UUID NOT NULL,  -- References Plant agent
      status VARCHAR(20) NOT NULL DEFAULT 'active',  -- active, completed, converted, cancelled
      trial_mode BOOLEAN DEFAULT true,
      expires_at TIMESTAMP NOT NULL,
      deliverables_count INTEGER DEFAULT 0,
      created_at TIMESTAMP DEFAULT NOW(),
      UNIQUE(customer_id, agent_id)  -- One trial per agent per customer
  );
  ```
- [ ] CP frontend trial signup flow:
  1. Customer clicks "Start 7-Day Trial" on agent profile page
  2. Modal shows trial terms: "Keep deliverables even if you cancel"
  3. Customer confirms → CP calls POST /api/trials
  4. Trial created → Redirect to /trials/{id}/dashboard
- [ ] Trial dashboard shows:
  - Days remaining (countdown)
  - Deliverables (list of completed tasks, kept even if trial cancelled)
  - Agent activity feed
  - "Convert to Subscription" button (future)
  - "Cancel Trial" button (future)

**Technical Tasks:**
1. Create `cp_trials` table in CP database
2. Create `api/trials.py` with trial CRUD routes
3. Implement trial creation logic (record creation, sandbox provisioning placeholder)
4. Create trial signup modal component (React)
5. Create trial dashboard page
6. Integration test: Sign up for trial → View trial dashboard → Verify trial record in database

**Dependencies:**
- CP-001 (needs marketplace to browse agents)
- PLANT-001 (needs Plant agent data)

**Risks:**
- Sandbox provisioning is complex (deferred to gateway implementation)
- Trial mode routing not enforced (agents execute in production until OPA deployed)

**Validation:**
```bash
# CP Customer workflow
1. Browse marketplace, click "Email Marketing Agent"
2. Click "Start 7-Day Trial" button
3. Modal shows:
   - "Try for 7 days free"
   - "Keep all deliverables even if you cancel"
   - "No credit card required"
4. Customer clicks "Start Trial"
5. CP creates trial record:
   - customer_id: abc-123
   - agent_id: xyz-789
   - expires_at: 2026-01-23 (7 days from now)
   - trial_mode: true
6. Redirect to /trials/{trial_id}/dashboard
7. Dashboard shows:
   - "6 days 23 hours remaining"
   - Deliverables: 0 (no tasks executed yet)
   - "Execute First Task" button
```

---

### CP-003: Agent Execution Integration (Placeholder)

**Priority:** P1 (Required for functional trial, but execution logic complex)  
**Effort:** 4 days  
**Owner:** CP Team  

**Problem:**
- CP needs to execute agent tasks during trial
- No integration with Plant agent execution logic (Plant is data layer, not execution engine)
- Agent execution requires:
  - Task queue (Pub/Sub)
  - Execution service (port 8002 - Agent Execution Service)
  - Sandbox environment for trial mode
  - Budget tracking (spend accumulation)

**User Story:**
```gherkin
As a CP trial customer
I want to execute agent tasks during my trial
So that I can evaluate agent performance
```

**Acceptance Criteria:**
- [ ] CP backend execution route (placeholder for now):
  ```python
  @router.post("/agents/{agent_id}/execute", response_model=TaskExecutionResponse)
  async def execute_agent_task(
      agent_id: UUID,
      task_data: TaskExecutionRequest,
      current_user: User = Depends(get_current_user)
  ):
      """
      Execute agent task (trial mode routed to sandbox).
      
      NOTE: This is a placeholder until Agent Execution Service (port 8002) is deployed.
      For now, returns mock response.
      """
      # TODO: Check trial status (active, not expired)
      trial = await get_active_trial(current_user.id, agent_id)
      if not trial:
          raise HTTPException(400, "No active trial for this agent")
      
      # TODO: Publish task to Pub/Sub queue
      # task_id = await publish_agent_task(agent_id, task_data, trial_mode=True)
      
      # Mock response for now
      return TaskExecutionResponse(
          task_id=str(uuid.uuid4()),
          agent_id=agent_id,
          status="pending",
          estimated_completion="2 minutes",
          sandbox_mode=True,  # Trial mode = sandbox
          cost_estimate_usd=0.50
      )
  ```
- [ ] CP frontend execution UI:
  - "Execute Task" button on trial dashboard
  - Task input form (textarea for task description + context JSON)
  - Task status page (pending → running → completed)
  - Task results display (output JSON + cost breakdown)
- [ ] Task execution flow (future - requires Agent Execution Service):
  1. Customer submits task
  2. CP publishes to Pub/Sub topic: `agent.task.requested`
  3. Agent Execution Service (port 8002) consumes message
  4. Execution service routes to sandbox if trial_mode=true
  5. Agent executes task in isolated sandbox (no external API access)
  6. Execution service publishes result to Pub/Sub: `agent.task.completed`
  7. CP consumes result, updates trial deliverables
  8. Customer sees result in trial dashboard

**Technical Tasks:**
1. Create `api/execution.py` with placeholder execution route
2. Create execution UI components (task form, status page, results display)
3. Add mock task execution flow (returns hardcoded result after 5 seconds)
4. Document Agent Execution Service requirements for future implementation

**Dependencies:**
- CP-002 (needs trial signup)
- (Future) Agent Execution Service deployment (port 8002)
- (Future) OPA Policy Service for sandbox routing

**Risks:**
- ⚠️ **This is a placeholder** - real agent execution requires multiple services not yet deployed
- Execution service architecture is complex (queue, workers, sandbox isolation)

**Validation (Placeholder):**
```bash
# CP Customer workflow (mock execution)
1. Navigate to /trials/{trial_id}/dashboard
2. Click "Execute Task" button
3. Fill task form:
   - Task: "Analyze competitor pricing for SaaS products"
   - Context: {"industry": "B2B SaaS", "region": "North America"}
4. Submit task
5. CP returns mock response:
   - Task ID: abc-123
   - Status: "pending"
   - Estimated completion: "2 minutes"
   - Sandbox mode: true (trial mode)
6. Mock status updates after 5 seconds:
   - Status: "running"
7. Mock completion after 2 minutes:
   - Status: "completed"
   - Result: "Competitor pricing ranges from $50-$200/user/month..."
   - Cost: $0.50
   - Sandbox mode: true
8. Result added to trial deliverables (kept even if trial cancelled)
```

---

## Phase 4: Future - Unified Gateway Layer (Deferred)

**Goal:** Add unified FastAPI Gateway with constitutional middleware (OPA, RBAC, audit, budget tracking). This phase is **deferred** until CP/PP/Plant direct integration is stable and delivering value.

**Stories (Placeholder for future sprint):**
- GATEWAY-001: Deploy OPA Policy Service + Rego policies
- GATEWAY-002: Deploy Audit Writer Service
- GATEWAY-003: Create database-driven routing table
- GATEWAY-004: Implement 7-layer middleware stack
- GATEWAY-005: Migrate CP/PP to route via gateway instead of direct Plant calls
- GATEWAY-006: Implement trial mode sandbox routing via OPA
- GATEWAY-007: Implement per-agent budget tracking
- GATEWAY-008: Blue/green deployment with route versioning

**Timeline:** 6 weeks (as outlined in API_GATEWAY_ARCHITECTURE.md)

**Why defer:** Focus on delivering value (CP/PP/Plant integration) before adding architectural complexity (gateway layer). Gateway adds:
- 40% latency overhead
- $180/month infrastructure cost
- 6 weeks implementation time
- Operational complexity (OPA, audit, routing table)

**When to start Phase 4:**
- CP marketplace is live with 10+ customers using trials
- PP admin portal is stable with Genesis workflow
- Plant APIs are battle-tested (no critical bugs)
- Business case for constitutional governance is validated (L0 principle violations detected in production)

---

## Implementation Schedule

### Sprint 1 (Week 1-2): Plant Production Readiness
- PLANT-001: API Contract + Type Safety (3 days)
- PLANT-002: Error Handling (4 days)
- PLANT-003: CORS Configuration (2 days)

**Deliverable:** Plant APIs production-ready, OpenAPI spec published, TypeScript types generated

---

### Sprint 2 (Week 3-4): Plant Documentation + PP Client
- PLANT-004: API Documentation (3 days)
- PP-001: Plant API Client Library (4 days)

**Deliverable:** Plant API documented, PP can call Plant endpoints

---

### Sprint 3 (Week 5-6): PP Genesis + Agent Management
- PP-002: Genesis Workflow (5 days)
- PP-003: Agent Management (4 days)

**Deliverable:** PP admin portal can certify skills, create agents

---

### Sprint 4 (Week 7-8): PP Audit + CP Marketplace
- PP-004: Audit Dashboard (3 days)
- CP-001: Marketplace Integration (4 days)

**Deliverable:** PP has audit dashboard, CP marketplace shows real agents

---

### Sprint 5 (Week 9-10): CP Trial Signup + Execution Placeholder
- CP-002: Trial Signup (5 days)
- CP-003: Execution Placeholder (4 days)

**Deliverable:** CP customers can sign up for trials, execute mock tasks

---

## Success Metrics

### Sprint 1 Metrics (Plant)
- [ ] Plant `/openapi.json` endpoint returns valid OpenAPI 3.0 spec
- [ ] TypeScript types generated successfully for CP/PP frontends
- [ ] All Plant endpoints return RFC 7807 error format
- [ ] CORS allows CP/PP origins, blocks other origins

### Sprint 2 Metrics (Plant + PP Client)
- [ ] FastAPI Swagger UI shows all 13 Plant endpoints with descriptions
- [ ] Postman collection includes all Plant endpoints with examples
- [ ] PP backend can call Plant APIs (3 retries, error handling)

### Sprint 3 Metrics (PP Genesis + Agents)
- [ ] PP admin can create skill, certify skill via Genesis workflow
- [ ] PP admin can create agent with L0/L1 validation
- [ ] Genesis workflow UI shows pending/certified status

### Sprint 4 Metrics (PP Audit + CP Marketplace)
- [ ] PP admin can run constitutional audit, view compliance score
- [ ] CP marketplace displays agent cards loaded from Plant API
- [ ] CP marketplace filters work (industry, rating)

### Sprint 5 Metrics (CP Trial)
- [ ] CP customer can sign up for 7-day trial
- [ ] Trial dashboard shows days remaining, deliverables
- [ ] Mock task execution returns result after 2 minutes

---

## Risk Mitigation

### Risk 1: API Contract Drift (TypeScript ↔ Python)
**Mitigation:**
- Add CI/CD workflow: regenerate TypeScript types on Plant schema changes
- Fail build if frontend uses outdated types
- Weekly review: compare Plant OpenAPI spec with CP/PP API calls

### Risk 2: Plant API Breaking Changes
**Mitigation:**
- Semantic versioning for Plant API (v1, v2, etc.)
- Deprecation notices in OpenAPI spec (6 months before removal)
- Backward compatibility layer if breaking changes required

### Risk 3: Trial Mode Execution Without Sandbox
**Mitigation:**
- ⚠️ **Acknowledge limitation:** Trial agents execute in production until OPA deployed
- Add warning in CP trial dashboard: "Trial mode - limited functionality"
- Budget caps enforced in CP backend (not Plant) as temporary safeguard

### Risk 4: Constitutional Violations Undetected
**Mitigation:**
- Plant validates L0/L1 compliance on entity creation (already implemented)
- PP audit dashboard shows compliance score (Sprint 4)
- Weekly manual audit until gateway + OPA deployed

---

## Document Control

**Version:** 1.0  
**Last Updated:** 2026-01-16  
**Next Review:** Sprint 1 completion (Week 2)  

**Change Log:**
- 2026-01-16: Initial implementation plan created (11 stories, 3 phases)
- Pending: Update after Sprint 1 (Plant production readiness)

**References:**
- [API_GATEWAY_ARCHITECTURE.md](./API_GATEWAY_ARCHITECTURE.md) - Source of truth for future gateway layer
- [GATEWAY_INTEGRATION_GAP_ANALYSIS.md](./GATEWAY_INTEGRATION_GAP_ANALYSIS.md) - 26 blockers identified
- [GATEWAY_ARCHITECTURE_BLUEPRINT.md](./GATEWAY_ARCHITECTURE_BLUEPRINT.md) - 7-layer middleware design (Phase 4)

---

**Status:** ✅ Implementation plan complete. Ready for Sprint 1 kickoff (Plant production readiness).  
**Next Action:** Begin PLANT-001 (API Contract + Type Safety) - 3-day story.
