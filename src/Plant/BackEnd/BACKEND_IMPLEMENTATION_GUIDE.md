# Plant Backend Implementation Guide - Phase 1

**Document:** Backend Services Architecture & API Implementation  
**Date:** 2026-01-14  
**Status:** Implementation Ready  
**Target:** Complete Agent/Skill/JobRole services + API endpoints  

---

## Overview

The Plant Backend is built with a layered architecture:

```
Layer 1: API Routes (FastAPI endpoints)
         ↓
Layer 2: Services (Business logic, validation)
         ↓
Layer 3: Models (Data entities, schemas)
         ↓
Layer 4: Database (PostgreSQL with async SQLAlchemy)
         ↓
Layer 5: Security/Validation (Constitutional alignment, hash chains)
```

---

## Current Status

### ✅ Complete
- Database connector (async SQLAlchemy)
- Base entity model (inheritance foundation)
- Security layer (password hashing, JWT)
- Exception handling
- Logging infrastructure

### 🔄 In Progress
- Model layer (Agent, Skill, JobRole, Team, Industry)
- Service layer (Business logic)
- API endpoints (REST routes)

### ⏳ Ready for Implementation
- Comprehensive API documentation
- Full test suite for services
- Performance benchmarks
- Monitoring setup

---

## Service Layer Implementations

### 1. Agent Service

**Purpose:** Manage AI agents (creation, discovery, status)

**Key Methods:**

```python
class AgentService:
    # CRUD Operations
    async def create_agent(agent_data: AgentCreate) -> Agent
    async def get_agent(agent_id: UUID) -> Agent
    async def list_agents(
        industry: Optional[str],
        specialization: Optional[str],
        status: Optional[str],
        skip: int,
        limit: int
    ) -> List[Agent]
    async def update_agent(agent_id: UUID, update_data: AgentUpdate) -> Agent
    async def delete_agent(agent_id: UUID) -> bool
    
    # Business Logic
    async def get_available_agents(industry: Optional[str], limit: int) -> List[Agent]
    async def search_agents(query: str, industry: Optional[str]) -> List[Agent]
    async def update_agent_status(agent_id: UUID, status: str) -> Agent
    async def get_agent_metrics(agent_id: UUID) -> AgentMetrics
    
    # Constitutional Alignment
    async def validate_agent_alignment(agent_id: UUID) -> bool
    async def enforce_l0_compliance(agent_id: UUID) -> bool
```

**API Endpoints:**

```
POST   /api/v1/agents/               # Create agent
GET    /api/v1/agents/               # List agents (with filters)
GET    /api/v1/agents/{agent_id}     # Get single agent
PUT    /api/v1/agents/{agent_id}     # Update agent
DELETE /api/v1/agents/{agent_id}     # Delete agent
GET    /api/v1/agents/search         # Search agents
GET    /api/v1/agents/available      # Get available agents
GET    /api/v1/agents/{agent_id}/metrics  # Get metrics
```

### 2. Skill Service

**Purpose:** Manage skills (technical, soft, domain)

**Key Methods:**

```python
class SkillService:
    async def create_skill(skill_data: SkillCreate) -> Skill
    async def get_skill(skill_id: UUID) -> Skill
    async def list_skills(
        category: Optional[str],
        skip: int,
        limit: int
    ) -> List[Skill]
    async def search_skills(query: str) -> List[Skill]
    async def get_skill_embedding(skill_id: UUID) -> List[float]
    async def similarity_search(embedding: List[float], limit: int) -> List[Skill]
```

**API Endpoints:**

```
POST   /api/v1/skills/               # Create skill
GET    /api/v1/skills/               # List skills
GET    /api/v1/skills/{skill_id}     # Get skill
PUT    /api/v1/skills/{skill_id}     # Update skill
DELETE /api/v1/skills/{skill_id}     # Delete skill
GET    /api/v1/skills/search         # Search by name
POST   /api/v1/skills/similarity    # Semantic search by embedding
```

### 3. JobRole Service

**Purpose:** Manage job roles (SDR, Manager, Consultant, etc.)

**Key Methods:**

```python
class JobRoleService:
    async def create_job_role(role_data: JobRoleCreate) -> JobRole
    async def get_job_role(role_id: UUID) -> JobRole
    async def list_job_roles(
        industry: Optional[str],
        skip: int,
        limit: int
    ) -> List[JobRole]
    async def get_required_skills(role_id: UUID) -> List[Skill]
```

**API Endpoints:**

```
POST   /api/v1/job-roles/            # Create role
GET    /api/v1/job-roles/            # List roles
GET    /api/v1/job-roles/{role_id}   # Get role
PUT    /api/v1/job-roles/{role_id}   # Update role
GET    /api/v1/job-roles/{role_id}/skills  # Get required skills
```

### 4. Marketplace Service

**Purpose:** Agent discovery, search, browsing (CP/PP integration)

**Key Methods:**

```python
class MarketplaceService:
    async def get_marketplace_summary() -> MarketplaceSummary
    async def get_trending_agents(limit: int) -> List[Agent]
    async def get_agents_by_industry(industry: str) -> List[Agent]
    async def get_agents_by_specialty(specialty: str) -> List[Agent]
    async def get_agent_recommendations(company_type: str) -> List[Agent]
```

---

## API Response Schemas

### Agent Response

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Sarah Marketing Expert",
  "specialization": "healthcare",
  "industry": "marketing",
  "status": "available",
  "hourly_rate": 85.0,
  "avg_rating": 4.8,
  "total_jobs": 127,
  "completed_jobs": 125,
  "response_time_seconds": 300,
  "retention_rate": 0.98,
  "created_at": "2025-01-01T10:00:00Z",
  "last_active_at": "2026-01-14T15:30:00Z"
}
```

### Skill Response

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "name": "Healthcare Marketing",
  "category": "domain_expertise",
  "description": "Marketing strategies specific to healthcare industry",
  "certification_level": "advanced",
  "embedding_384": [0.12, -0.45, ...],
  "agents_with_skill": 23,
  "created_at": "2025-01-01T10:00:00Z"
}
```

### JobRole Response

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "name": "Social Media Manager",
  "description": "Manage social media presence across platforms",
  "industry": "marketing",
  "base_salary": 65000,
  "required_skills": [
    "660e8400-e29b-41d4-a716-446655440001",
    "660e8400-e29b-41d4-a716-446655440003"
  ],
  "specializations": ["b2b", "healthcare"],
  "created_at": "2025-01-01T10:00:00Z"
}
```

---

## Implementation Roadmap (Phase 1)

### Week 1: Core Services
- [ ] Complete AgentService implementation (CRUD + business logic)
- [ ] Complete SkillService implementation
- [ ] Complete JobRoleService implementation
- [ ] Write integration tests for each service

### Week 2: API Endpoints
- [ ] Implement Agent API routes (/api/v1/agents)
- [ ] Implement Skill API routes (/api/v1/skills)
- [ ] Implement JobRole API routes (/api/v1/job-roles)
- [ ] Add request/response validation (Pydantic schemas)
- [ ] Add error handling & logging

### Week 3: Search & Discovery
- [ ] Implement agent search functionality
- [ ] Implement skill semantic search (pgvector embeddings)
- [ ] Implement marketplace browsing endpoints
- [ ] Add sorting & filtering logic

### Week 4: Testing & Documentation
- [ ] Write unit tests for all services
- [ ] Write integration tests for all endpoints
- [ ] Generate OpenAPI documentation
- [ ] Create API client library

---

## Database Schema (Reference)

### agents table
```sql
CREATE TABLE agents (
  id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  specialization VARCHAR(100),
  industry VARCHAR(50),
  status VARCHAR(20),  -- available, working, offline
  hourly_rate DECIMAL(8,2),
  avg_rating DECIMAL(3,1),
  total_jobs INTEGER,
  completed_jobs INTEGER,
  response_time_seconds INTEGER,
  retention_rate DECIMAL(3,2),
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  deleted_at TIMESTAMP  -- soft delete
);
```

### skills table
```sql
CREATE TABLE skills (
  id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL UNIQUE,
  category VARCHAR(50),
  description TEXT,
  certification_level VARCHAR(20),
  embedding_384 vector(384),  -- pgvector
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

### job_roles table
```sql
CREATE TABLE job_roles (
  id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  industry VARCHAR(50),
  base_salary INTEGER,
  specializations VARCHAR[],
  required_skills UUID[],
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

---

## Example: Creating an Agent through the API

### Request
```bash
curl -X POST http://localhost:8000/api/v1/agents/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sarah Marketing Expert",
    "specialization": "healthcare",
    "industry": "marketing",
    "hourly_rate": 85.0,
    "skill_id": "660e8400-e29b-41d4-a716-446655440001",
    "job_role_id": "770e8400-e29b-41d4-a716-446655440002"
  }'
```

### Response
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Sarah Marketing Expert",
  "specialization": "healthcare",
  "industry": "marketing",
  "status": "available",
  "hourly_rate": 85.0,
  "created_at": "2026-01-14T16:00:00Z"
}
```

---

## Testing Strategy

### Unit Tests (Services)
- Test CRUD operations
- Test validation logic
- Test error handling
- Test business logic (available agents, search, etc.)

**Run:** `pytest tests/unit/test_agent_service.py -v`

### Integration Tests (API)
- Test API endpoints
- Test request/response validation
- Test error responses
- Test pagination & filtering
- Test database transactions

**Run:** `pytest tests/integration/test_agent_api.py -v`

### Performance Tests
- Load test each endpoint (100+ concurrent requests)
- Measure response time P95 <500ms
- Test with 1000+ agents in database
- Test search/filter performance

**Run:** `pytest tests/performance/ -v --benchmark-only`

---

## Next Steps

1. **Today:** Database fixes & service implementations
2. **Tomorrow:** API endpoint implementation + validation
3. **Next 2 Days:** Testing & documentation
4. **Week 2:** Infrastructure deployment (Cloud Run + PostgreSQL)

---

## Key Files

- Services: `/src/Plant/BackEnd/services/`
- API Routes: `/src/Plant/BackEnd/api/v1/`
- Models: `/src/Plant/BackEnd/models/`
- Tests: `/src/Plant/BackEnd/tests/`
- Database: `/src/Plant/BackEnd/core/database.py`

---

**Status:** Ready for Phase 1 implementation ✅
