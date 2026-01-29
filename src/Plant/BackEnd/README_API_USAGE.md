# Plant API Usage Guide

## Quick Start

### 1. Start Plant Backend

```bash
# Docker-first: start Plant backend via compose (no local virtualenv)
cd /workspaces/WAOOAW
docker compose up -d
```

### 2. Access API Documentation

- **Swagger UI**: http://localhost:8000/docs (interactive API documentation)
- **ReDoc**: http://localhost:8000/redoc (clean, readable documentation)
- **OpenAPI Spec**: http://localhost:8000/openapi.json (JSON schema)

### 3. Import Postman Collection

Download and import the Postman collection from this directory:
- `Plant_API.postman_collection.json`
- `Plant_Environments.postman_environment.json`

## API Endpoints Overview

### Genesis Certification (Skill & Job Role Creation)

| Method | Endpoint | Description | Status Code |
|--------|----------|-------------|-------------|
| POST | `/api/v1/genesis/skills` | Create new skill | 201 Created |
| GET | `/api/v1/genesis/skills` | List all skills | 200 OK |
| GET | `/api/v1/genesis/skills/{id}` | Get skill details | 200 OK |
| POST | `/api/v1/genesis/skills/{id}/certify` | Certify skill via Genesis | 200 OK |
| POST | `/api/v1/genesis/job-roles` | Create new job role | 201 Created |
| GET | `/api/v1/genesis/job-roles` | List all job roles | 200 OK |
| GET | `/api/v1/genesis/job-roles/{id}` | Get job role details | 200 OK |
| POST | `/api/v1/genesis/job-roles/{id}/certify` | Certify job role via Genesis | 200 OK |

### Agent Management

| Method | Endpoint | Description | Status Code |
|--------|----------|-------------|-------------|
| POST | `/api/v1/agents` | Create new agent (birth) | 201 Created |
| GET | `/api/v1/agents` | List all agents (with filters) | 200 OK |
| GET | `/api/v1/agents/{id}` | Get agent details | 200 OK |
| POST | `/api/v1/agents/{id}/assign-team` | Assign agent to team | 200 OK |

### Audit & Compliance

| Method | Endpoint | Description | Status Code |
|--------|----------|-------------|-------------|
| POST | `/api/v1/audit/run` | Run constitutional compliance audit | 200 OK |
| GET | `/api/v1/audit/tampering/{id}` | Check entity for tampering | 200 OK |
| GET | `/api/v1/audit/export` | Export audit report | 200 OK |

## Common Workflows

### Workflow 1: Create Certified Skill

```bash
# Step 1: Create skill (pending certification)
curl -X POST http://localhost:8000/api/v1/genesis/skills \
  -H "Content-Type: application/json" \
  -H "X-Correlation-ID: $(uuidgen)" \
  -d '{
    "name": "Python 3.11",
    "description": "Modern Python programming with async/await, type hints, and FastAPI framework",
    "category": "technical",
    "governance_agent_id": "genesis"
  }'

# Response (201 Created):
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Python 3.11",
  "description": "Modern Python programming...",
  "category": "technical",
  "entity_type": "skill",
  "status": "pending_certification",
  "created_at": "2026-01-16T10:30:00Z",
  "l0_compliance_status": {
    "L0-01": true,
    "L0-02": true,
    "L0-05": true
  }
}

# Step 2: Certify skill (Genesis role required in future)
curl -X POST http://localhost:8000/api/v1/genesis/skills/550e8400-e29b-41d4-a716-446655440000/certify \
  -H "Content-Type: application/json" \
  -H "X-Correlation-ID: $(uuidgen)" \
  -d '{
    "certification_notes": "Skill validated by Genesis Agent",
    "approval_gate": "technical_review"
  }'

# Response (200 OK):
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Python 3.11",
  "status": "certified",
  "certification_date": "2026-01-16T10:35:00Z"
}
```

---

### Workflow 2: Create Agent with Industry Lock

```bash
# Prerequisites: Create certified skill, job role, industry first

# Step 1: Create skill (see Workflow 1)
# Step 2: Create job role
curl -X POST http://localhost:8000/api/v1/genesis/job-roles \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Content Writer",
    "description": "Creates engaging content",
    "required_skills": ["550e8400-e29b-41d4-a716-446655440000"],
    "seniority_level": "mid",
    "governance_agent_id": "genesis"
  }'

# Response: job_role_id = 660e8400-e29b-41d4-a716-446655440001

# Step 3: Create industry (assume industry_id exists)
# industry_id = 770e8400-e29b-41d4-a716-446655440002 (Marketing)

# Step 4: Create agent
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -H "X-Correlation-ID: $(uuidgen)" \
  -d '{
    "name": "Email Marketing Agent",
    "skill_id": "550e8400-e29b-41d4-a716-446655440000",
    "job_role_id": "660e8400-e29b-41d4-a716-446655440001",
    "industry_id": "770e8400-e29b-41d4-a716-446655440002",
    "governance_agent_id": "genesis"
  }'

# Response (201 Created):
{
  "id": "880e8400-e29b-41d4-a716-446655440003",
  "name": "Email Marketing Agent",
  "skill_id": "550e8400-e29b-41d4-a716-446655440000",
  "job_role_id": "660e8400-e29b-41d4-a716-446655440001",
  "industry_id": "770e8400-e29b-41d4-a716-446655440002",
  "status": "active",
  "created_at": "2026-01-16T10:30:00Z"
}

# Industry is now LOCKED - agent cannot change industries!
```

---

### Workflow 3: List Agents with Filters

```bash
# List all agents
curl http://localhost:8000/api/v1/agents

# Filter by industry
curl "http://localhost:8000/api/v1/agents?industry_id=770e8400-e29b-41d4-a716-446655440002"

# Filter by job role
curl "http://localhost:8000/api/v1/agents?job_role_id=660e8400-e29b-41d4-a716-446655440001"

# Pagination
curl "http://localhost:8000/api/v1/agents?limit=50&offset=0"

# Combine filters
curl "http://localhost:8000/api/v1/agents?industry_id=770e8400-e29b-41d4-a716-446655440002&limit=20"
```

---

### Workflow 4: Run Constitutional Compliance Audit

```bash
# Run audit on all entities
curl -X POST http://localhost:8000/api/v1/audit/run \
  -H "Content-Type: application/json" \
  -H "X-Correlation-ID: $(uuidgen)"

# Response (200 OK):
{
  "audit_id": "abc-123-def-456",
  "compliance_score": 0.97,
  "entities_audited": 156,
  "violations": [
    {
      "entity_id": "xyz-789",
      "entity_type": "agent",
      "violation": "L0-03: Missing trial_mode_sandbox_url"
    }
  ],
  "l0_compliance": {
    "L0-01": {"pass": 156, "fail": 0},
    "L0-02": {"pass": 156, "fail": 0},
    "L0-03": {"pass": 153, "fail": 3}
  }
}

# Check specific entity for tampering
curl http://localhost:8000/api/v1/audit/tampering/880e8400-e29b-41d4-a716-446655440003 \
  -H "X-Correlation-ID: $(uuidgen)"

# Response:
{
  "entity_id": "880e8400-e29b-41d4-a716-446655440003",
  "tampered": false,
  "hash_chain_valid": true,
  "amendment_signatures_valid": true
}
```

## Error Handling Examples

### Constitutional Alignment Error (422)

```bash
# Missing governance_agent_id (L0-01 violation)
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Agent",
    "skill_id": "550e8400-e29b-41d4-a716-446655440000",
    "job_role_id": "660e8400-e29b-41d4-a716-446655440001",
    "industry_id": "770e8400-e29b-41d4-a716-446655440002"
  }'

# Response (422 Unprocessable Entity):
{
  "type": "https://waooaw.com/errors/constitutional-alignment",
  "title": "Constitutional Alignment Error",
  "status": 422,
  "detail": "governance_agent_id required (L0-01: Single Governor)",
  "instance": "/api/v1/agents",
  "correlation_id": "abc-123",
  "violations": ["L0-01: Single Governor - governance_agent_id required"]
}
```

### Validation Error (422)

```bash
# Invalid category value
curl -X POST http://localhost:8000/api/v1/genesis/skills \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Python",
    "description": "Programming",
    "category": "invalid_category"
  }'

# Response (422 Unprocessable Entity):
{
  "type": "https://waooaw.com/errors/validation-error",
  "title": "Request Validation Error",
  "status": 422,
  "detail": "Request validation failed: 1 error(s)",
  "instance": "/api/v1/genesis/skills",
  "violations": [
    "category: value is not a valid enumeration member"
  ]
}
```

### Entity Not Found (404)

```bash
# Request non-existent agent
curl http://localhost:8000/api/v1/agents/999e8400-e29b-41d4-a716-446655440000

# Response (404 Not Found):
{
  "type": "https://waooaw.com/errors/not-found",
  "title": "Entity Not Found",
  "status": 404,
  "detail": "Agent with ID 999e8400-e29b-41d4-a716-446655440000 not found",
  "instance": "/api/v1/agents/999e8400-e29b-41d4-a716-446655440000"
}
```

### Duplicate Entity (409)

```bash
# Create duplicate skill
curl -X POST http://localhost:8000/api/v1/genesis/skills \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Python 3.11",
    "description": "Python programming",
    "category": "technical"
  }'

# Response (409 Conflict):
{
  "type": "https://waooaw.com/errors/duplicate-entity",
  "title": "Duplicate Entity Error",
  "status": 409,
  "detail": "Skill 'Python 3.11' already exists in category 'technical'",
  "instance": "/api/v1/genesis/skills"
}
```

## Advanced Features

### Correlation ID Tracking

Add `X-Correlation-ID` header to all requests for distributed tracing:

```bash
# Generate correlation ID
CORRELATION_ID=$(uuidgen)

# Use in request
curl -X POST http://localhost:8000/api/v1/agents \
  -H "X-Correlation-ID: $CORRELATION_ID" \
  -H "Content-Type: application/json" \
  -d '{...}'

# Server echoes correlation ID in response
# Also included in error responses for debugging
```

### Pagination

Use `limit` and `offset` for large result sets:

```bash
# Page 1 (first 50 agents)
curl "http://localhost:8000/api/v1/agents?limit=50&offset=0"

# Page 2 (next 50 agents)
curl "http://localhost:8000/api/v1/agents?limit=50&offset=50"

# Page 3 (next 50 agents)
curl "http://localhost:8000/api/v1/agents?limit=50&offset=100"
```

### Filtering

Combine multiple filters:

```bash
# Marketing agents with Content Writer role
curl "http://localhost:8000/api/v1/agents?industry_id=770e8400-e29b-41d4-a716-446655440002&job_role_id=660e8400-e29b-41d4-a716-446655440001&limit=20"
```

## Postman Collection

### Import Collection

1. Open Postman
2. Click "Import" button
3. Select `Plant_API.postman_collection.json`
4. Select `Plant_Environments.postman_environment.json`
5. Select "Local" environment from dropdown

### Collection Structure

```
Plant API/
├── Genesis/
│   ├── Create Skill
│   ├── List Skills
│   ├── Get Skill
│   ├── Certify Skill
│   ├── Create Job Role
│   ├── List Job Roles
│   ├── Get Job Role
│   └── Certify Job Role
├── Agents/
│   ├── Create Agent
│   ├── List Agents
│   ├── Get Agent
│   └── Assign Agent to Team
└── Audit/
    ├── Run Compliance Audit
    ├── Check Tampering
    └── Export Audit Report
```

### Environments

**Local Environment:**
```json
{
  "base_url": "http://localhost:8000",
  "correlation_id": "{{$randomUUID}}"
}
```

**Demo Environment:**
```json
{
  "base_url": "https://plant.demo.waooaw.com",
  "correlation_id": "{{$randomUUID}}"
}
```

**Production Environment:**
```json
{
  "base_url": "https://plant.waooaw.com",
  "correlation_id": "{{$randomUUID}}",
  "jwt_token": "<INSERT_TOKEN_HERE>"
}
```

### Pre-Request Scripts

All requests include automatic correlation ID generation:

```javascript
// Pre-request script (applied to all requests)
pm.environment.set("correlation_id", pm.variables.replaceIn("{{$randomUUID}}"));
```

### Test Assertions

All requests include response validation:

```javascript
// Test script (example for Create Agent)
pm.test("Status code is 201 Created", function() {
    pm.response.to.have.status(201);
});

pm.test("Response has agent ID", function() {
    const jsonData = pm.response.json();
    pm.expect(jsonData.id).to.exist;
    pm.expect(jsonData.id).to.match(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/);
});

pm.test("Response has required fields", function() {
    const jsonData = pm.response.json();
    pm.expect(jsonData.name).to.exist;
    pm.expect(jsonData.status).to.equal("active");
    pm.expect(jsonData.created_at).to.exist;
});
```

## Troubleshooting

### Connection Refused

**Symptom:** `curl: (7) Failed to connect to localhost port 8000: Connection refused`

**Solution:** Start Plant backend first:
```bash
cd src/Plant/BackEnd
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

### CORS Error (Browser)

**Symptom:** `Access to fetch at 'http://localhost:8000/api/v1/agents' has been blocked by CORS`

**Solution:** Check CP/PP frontend origin is in Plant's CORS allowed list (see README_CORS.md)

---

### 422 Validation Error

**Symptom:** Unexpected validation error

**Solution:** Check request payload matches Pydantic schema. View OpenAPI spec at `/docs` for required fields.

---

### 404 Not Found

**Symptom:** `Agent with ID xxx not found`

**Solution:** Verify entity exists using List endpoint before trying to Get by ID.

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Postman Documentation](https://learning.postman.com/docs/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [README_API_CONTRACT.md](./README_API_CONTRACT.md) - TypeScript type generation
- [README_ERROR_HANDLING.md](./README_ERROR_HANDLING.md) - Error response formats
- [README_CORS.md](./README_CORS.md) - CORS configuration

## Next Steps

1. ✅ API documentation enhanced with detailed descriptions
2. ✅ Swagger UI available at `/docs`
3. ✅ ReDoc available at `/redoc`
4. ⏳ Generate Postman collection from OpenAPI spec (PLANT-004 remaining)
5. ⏳ Add integration tests (Phase 2)
6. ⏳ Deploy Plant to Demo environment (After Phase 1 complete)
