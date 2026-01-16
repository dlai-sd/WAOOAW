# Plant API Contract & Type Generation

## Overview

Plant backend exposes a fully documented OpenAPI 3.0 specification for type-safe integration with CP/PP frontends. This document explains how to:
- Export OpenAPI spec from Plant
- Generate TypeScript types for frontend consumption
- Keep types synchronized across stack

## Exporting OpenAPI Spec

Plant's FastAPI application automatically generates OpenAPI 3.0 specification at `/openapi.json` endpoint.

### Manual Export (Local Development)

```bash
# Start Plant backend
cd /workspaces/WAOOAW/src/Plant/BackEnd
source /workspaces/WAOOAW/.venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000

# Export OpenAPI spec (from another terminal)
curl http://localhost:8000/openapi.json > openapi.json

# Pretty print (optional)
cat openapi.json | python -m json.tool > openapi-formatted.json
```

### CI/CD Export

GitHub Actions workflow automatically exports OpenAPI spec on Plant backend changes:

```yaml
# .github/workflows/sync-api-types.yml (to be created)
name: Sync API Types
on:
  push:
    paths:
      - 'src/Plant/BackEnd/**'
      - 'src/Plant/BackEnd/models/schemas.py'
      - 'src/Plant/BackEnd/api/**'

jobs:
  export-openapi:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd src/Plant/BackEnd
          pip install -r requirements.txt
      - name: Export OpenAPI spec
        run: |
          cd src/Plant/BackEnd
          uvicorn main:app --host 0.0.0.0 --port 8000 &
          sleep 5
          curl http://localhost:8000/openapi.json > openapi.json
      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: plant-openapi-spec
          path: src/Plant/BackEnd/openapi.json
```

## Generating TypeScript Types

Use `openapi-typescript` package to generate TypeScript types from OpenAPI spec.

### CP Frontend (Customer Portal)

```bash
cd /workspaces/WAOOAW/src/CP/FrontEnd

# Install openapi-typescript (one-time)
npm install --save-dev openapi-typescript

# Add npm script to package.json
# "scripts": {
#   "generate-types": "openapi-typescript http://localhost:8000/openapi.json --output src/types/plant-api.generated.ts"
# }

# Generate types (Plant backend must be running)
npm run generate-types

# Or manually:
npx openapi-typescript http://localhost:8000/openapi.json \
  --output src/types/plant-api.generated.ts
```

### PP Frontend (Platform Portal)

```bash
cd /workspaces/WAOOAW/src/PP/FrontEnd

# Install openapi-typescript (one-time)
npm install --save-dev openapi-typescript

# Generate types
npx openapi-typescript http://localhost:8000/openapi.json \
  --output src/types/plant-api.generated.ts
```

## Using Generated Types

### TypeScript Type Imports

```typescript
// src/CP/FrontEnd/services/plant-api.service.ts
import type { paths, components } from '../types/plant-api.generated';

// Extract request/response types from OpenAPI spec
type AgentCreateRequest = components['schemas']['AgentCreate'];
type AgentResponse = components['schemas']['AgentResponse'];
type SkillResponse = components['schemas']['SkillResponse'];

// Type-safe API client
export class PlantAPIClient {
  private baseUrl = 'http://localhost:8000';

  async createAgent(data: AgentCreateRequest): Promise<AgentResponse> {
    const response = await fetch(`${this.baseUrl}/api/v1/agents`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail);
    }
    
    return response.json() as Promise<AgentResponse>;
  }

  async listAgents(filters?: {
    industry_id?: string;
    job_role_id?: string;
    limit?: number;
  }): Promise<AgentResponse[]> {
    const params = new URLSearchParams();
    if (filters?.industry_id) params.append('industry_id', filters.industry_id);
    if (filters?.job_role_id) params.append('job_role_id', filters.job_role_id);
    if (filters?.limit) params.append('limit', filters.limit.toString());
    
    const response = await fetch(`${this.baseUrl}/api/v1/agents?${params}`);
    if (!response.ok) throw new Error('Failed to list agents');
    
    return response.json() as Promise<AgentResponse[]>;
  }
}

// Usage in React component
const plantAPI = new PlantAPIClient();

// TypeScript ensures we pass correct shape
const agent = await plantAPI.createAgent({
  name: "Email Marketing Agent",
  skill_id: "550e8400-e29b-41d4-a716-446655440000",
  job_role_id: "660e8400-e29b-41d4-a716-446655440001",
  industry_id: "770e8400-e29b-41d4-a716-446655440002",
  governance_agent_id: "genesis"
});

// TypeScript knows agent.id is string (UUID), agent.status is string, etc.
console.log(agent.id);  // ✅ Type-safe
console.log(agent.name);  // ✅ Type-safe
console.log(agent.invalidField);  // ❌ Compile error
```

### React Component Example

```typescript
// src/CP/FrontEnd/components/AgentCard.tsx
import type { components } from '../types/plant-api.generated';

type AgentResponse = components['schemas']['AgentResponse'];

interface AgentCardProps {
  agent: AgentResponse;  // Type-safe props
}

export function AgentCard({ agent }: AgentCardProps) {
  return (
    <div className="agent-card">
      <h3>{agent.name}</h3>
      <p>Status: {agent.status}</p>
      <p>Industry: {agent.industry_id}</p>
      {/* TypeScript ensures we only access valid fields */}
    </div>
  );
}
```

## Type Safety Benefits

### Compile-Time Validation

```typescript
// ❌ Compile error: Property 'invalid_field' doesn't exist
const agent = await plantAPI.createAgent({
  name: "Agent",
  invalid_field: "value"  // TypeScript catches this!
});

// ✅ Type-safe: All required fields present
const agent = await plantAPI.createAgent({
  name: "Email Marketing Agent",
  skill_id: "550e8400-e29b-41d4-a716-446655440000",
  job_role_id: "660e8400-e29b-41d4-a716-446655440001",
  industry_id: "770e8400-e29b-41d4-a716-446655440002",
  governance_agent_id: "genesis"
});
```

### IDE Autocomplete

- ✅ IDE shows available properties from AgentResponse
- ✅ IDE shows required/optional fields in AgentCreate
- ✅ IDE shows endpoint paths and parameters
- ✅ Hover over types to see OpenAPI descriptions

### Runtime Safety

While TypeScript provides compile-time safety, runtime validation still needed:

```typescript
// Add runtime validation with Zod (optional)
import { z } from 'zod';

const AgentResponseSchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  skill_id: z.string().uuid(),
  job_role_id: z.string().uuid(),
  industry_id: z.string().uuid(),
  status: z.enum(['active', 'inactive', 'suspended']),
  created_at: z.string().datetime()
});

// Validate response at runtime
const response = await fetch('/api/v1/agents');
const data = await response.json();
const agent = AgentResponseSchema.parse(data);  // Throws if invalid
```

## Keeping Types Synchronized

### Option 1: Manual Regeneration (Development)

```bash
# When Plant schema changes, regenerate types
cd /workspaces/WAOOAW/src/CP/FrontEnd
npm run generate-types
```

### Option 2: Git Pre-Commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash
# Regenerate types if Plant schemas changed

if git diff --cached --name-only | grep -q "src/Plant/BackEnd/models/schemas.py"; then
  echo "Plant schema changed, regenerating TypeScript types..."
  cd src/CP/FrontEnd && npm run generate-types
  cd src/PP/FrontEnd && npm run generate-types
  git add src/*/FrontEnd/src/types/plant-api.generated.ts
fi
```

### Option 3: CI/CD Workflow (Recommended)

```yaml
# .github/workflows/sync-api-types.yml
name: Sync API Types
on:
  push:
    paths:
      - 'src/Plant/BackEnd/models/schemas.py'
      - 'src/Plant/BackEnd/api/**'

jobs:
  sync-types:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      # Export Plant OpenAPI spec
      - name: Start Plant backend
        run: |
          cd src/Plant/BackEnd
          pip install -r requirements.txt
          uvicorn main:app --host 0.0.0.0 --port 8000 &
          sleep 5
      
      # Generate CP types
      - name: Generate CP types
        run: |
          cd src/CP/FrontEnd
          npm install
          npm run generate-types
      
      # Generate PP types
      - name: Generate PP types
        run: |
          cd src/PP/FrontEnd
          npm install
          npm run generate-types
      
      # Commit updated types
      - name: Commit updated types
        run: |
          git config --global user.name "GitHub Actions"
          git config --global user.email "actions@github.com"
          git add src/*/FrontEnd/src/types/plant-api.generated.ts
          git commit -m "chore: Regenerate TypeScript types from Plant OpenAPI spec" || true
          git push
```

## Versioning Strategy

### Semantic Versioning for API Changes

- **Patch (1.0.1)**: Bug fixes, no schema changes
- **Minor (1.1.0)**: New endpoints, new optional fields (backward compatible)
- **Major (2.0.0)**: Breaking changes (removed fields, renamed fields, changed types)

### Backward Compatibility

- ✅ **Safe**: Add new optional fields to request schemas
- ✅ **Safe**: Add new fields to response schemas (frontend ignores unknowns)
- ✅ **Safe**: Add new endpoints
- ❌ **Breaking**: Remove required fields from request schemas
- ❌ **Breaking**: Change field types (string → number)
- ❌ **Breaking**: Remove fields from response schemas (if frontend uses them)

### Deprecation Strategy

```python
# Plant schema with deprecated field
class AgentResponse(BaseModel):
    id: UUID
    name: str
    old_status: Optional[str] = Field(
        None,
        deprecated=True,
        description="DEPRECATED: Use 'status' field instead. Will be removed in v2.0.0"
    )
    status: str  # New field
```

TypeScript types will include deprecation warning:
```typescript
type AgentResponse = {
  id: string;
  name: string;
  /** @deprecated Use 'status' field instead. Will be removed in v2.0.0 */
  old_status?: string;
  status: string;
}
```

## Troubleshooting

### Types Out of Sync

**Symptom:** TypeScript errors about missing/unknown fields

**Solution:**
```bash
# Regenerate types
cd src/CP/FrontEnd
npm run generate-types

# Check git diff
git diff src/types/plant-api.generated.ts
```

### Plant Backend Not Running

**Symptom:** `openapi-typescript` fails with connection error

**Solution:**
```bash
# Start Plant backend first
cd src/Plant/BackEnd
uvicorn main:app --host 0.0.0.0 --port 8000

# Then generate types (from another terminal)
cd src/CP/FrontEnd
npm run generate-types
```

### CORS Error in Browser

**Symptom:** Frontend can't call Plant API (CORS blocked)

**Solution:** See PLANT-003 story - update Plant CORS middleware to allow CP/PP origins

### OpenAPI Spec Missing Fields

**Symptom:** Generated types missing expected properties

**Solution:** Ensure Plant Pydantic models have all fields with type hints:
```python
# ❌ Missing fields in generated types
class AgentResponse(BaseModel):
    id: UUID
    name: str
    # Missing other fields!

# ✅ All fields present
class AgentResponse(BaseModel):
    id: UUID
    name: str
    skill_id: UUID
    job_role_id: UUID
    industry_id: UUID
    status: str
    created_at: datetime
```

## References

- [OpenAPI 3.0 Specification](https://swagger.io/specification/)
- [FastAPI OpenAPI Docs](https://fastapi.tiangolo.com/tutorial/metadata/)
- [openapi-typescript Package](https://github.com/drwpow/openapi-typescript)
- [PLANT-001 Story](../../../main/Foundation/Architecture/APIGateway/IMPLEMENTATION_PLAN.md#plant-001-api-contract-publication--type-safety)

## Next Steps

1. ✅ Plant OpenAPI spec enhanced with descriptions and examples
2. ⏳ Add `npm run generate-types` script to CP/PP package.json (PLANT-001 remaining)
3. ⏳ Create CI/CD workflow for automatic type sync (PLANT-001 remaining)
4. ⏳ Update CP/PP frontends to use generated types (CP-001, PP-002)
