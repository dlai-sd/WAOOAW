# Plant API Error Handling Guide

## Overview

Plant backend uses **RFC 7807 Problem Details** format for all error responses. This provides consistent, machine-readable error information that CP/PP frontends can parse and display.

## RFC 7807 Format

All error responses follow this structure:

```json
{
  "type": "https://waooaw.com/errors/constitutional-alignment",
  "title": "Constitutional Alignment Error",
  "status": 422,
  "detail": "governance_agent_id required (L0-01: Single Governor)",
  "instance": "/api/v1/agents",
  "correlation_id": "abc-123-def-456",
  "violations": ["L0-01: governance_agent_id missing"]
}
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string (URI) | ✅ | URI reference identifying the error type |
| `title` | string | ✅ | Short, human-readable summary |
| `status` | integer | ✅ | HTTP status code (same as response status) |
| `detail` | string | ✅ | Human-readable explanation specific to this error |
| `instance` | string (URI) | ✅ | URI of the request that caused the error |
| `correlation_id` | string | ❌ | Request correlation ID for tracing (from X-Correlation-ID header) |
| `violations` | array[string] | ❌ | List of specific violations (for validation/constitutional errors) |

## HTTP Status Codes

| Code | Type | When Used | Example |
|------|------|-----------|---------|
| **400** | Bad Request | Client error (malformed request, invalid input) | Invalid UUID format |
| **401** | Unauthorized | Missing or invalid JWT token (future) | No Authorization header |
| **403** | Forbidden | Valid JWT but insufficient permissions (future) | Non-Genesis user trying to certify skill |
| **404** | Not Found | Entity doesn't exist | Agent ID not found |
| **409** | Conflict | Duplicate entity already exists | Skill name already taken |
| **422** | Unprocessable Entity | Constitutional alignment failure or validation error | L0-01 violation, missing required field |
| **500** | Internal Server Error | Unexpected server error | Database connection failed |
| **503** | Service Unavailable | Service dependency unavailable (future) | OPA policy service down |

## Error Types

### 1. Constitutional Alignment Errors (422)

**Type:** `https://waooaw.com/errors/constitutional-alignment`

Constitutional principle violations (L0-01 through L0-07).

**Example Request:**
```bash
POST /api/v1/agents
{
  "name": "Agent without governance",
  "skill_id": "550e8400-e29b-41d4-a716-446655440000",
  "job_role_id": "660e8400-e29b-41d4-a716-446655440001",
  "industry_id": "770e8400-e29b-41d4-a716-446655440002"
  # Missing: governance_agent_id (L0-01 violation!)
}
```

**Response:**
```json
{
  "type": "https://waooaw.com/errors/constitutional-alignment",
  "title": "Constitutional Alignment Error",
  "status": 422,
  "detail": "governance_agent_id required (L0-01: Single Governor)",
  "instance": "/api/v1/agents",
  "correlation_id": "abc-123",
  "violations": [
    "L0-01: Single Governor - governance_agent_id required"
  ]
}
```

**Frontend Handling:**
```typescript
try {
  const agent = await plantAPI.createAgent(data);
} catch (error) {
  if (error.status === 422 && error.type.includes('constitutional-alignment')) {
    // Display constitutional violations
    error.violations.forEach(violation => {
      console.error(`Constitutional error: ${violation}`);
      showToast('error', violation);
    });
  }
}
```

---

### 2. Validation Errors (422)

**Type:** `https://waooaw.com/errors/validation-error`

Pydantic schema validation failures (missing required fields, wrong types).

**Example Request:**
```bash
POST /api/v1/genesis/skills
{
  "name": "Python",
  "category": "invalid_category",  # Should be: technical, soft_skill, domain_expertise
  "description": ""  # Empty string
}
```

**Response:**
```json
{
  "type": "https://waooaw.com/errors/validation-error",
  "title": "Request Validation Error",
  "status": 422,
  "detail": "Request validation failed: 2 error(s)",
  "instance": "/api/v1/genesis/skills",
  "correlation_id": "def-456",
  "violations": [
    "category: value is not a valid enumeration member",
    "description: ensure this value has at least 10 characters"
  ]
}
```

**Frontend Handling:**
```typescript
try {
  const skill = await plantAPI.createSkill(data);
} catch (error) {
  if (error.status === 422 && error.type.includes('validation-error')) {
    // Map violations to form fields
    error.violations.forEach(violation => {
      const [field, message] = violation.split(': ');
      setFieldError(field, message);
    });
  }
}
```

---

### 3. Entity Not Found Errors (404)

**Type:** `https://waooaw.com/errors/not-found`

Requested entity doesn't exist in database.

**Example Request:**
```bash
GET /api/v1/agents/999e8400-e29b-41d4-a716-446655440000
```

**Response:**
```json
{
  "type": "https://waooaw.com/errors/not-found",
  "title": "Entity Not Found",
  "status": 404,
  "detail": "Agent with ID 999e8400-e29b-41d4-a716-446655440000 not found",
  "instance": "/api/v1/agents/999e8400-e29b-41d4-a716-446655440000",
  "correlation_id": "ghi-789"
}
```

**Frontend Handling:**
```typescript
try {
  const agent = await plantAPI.getAgent(agentId);
} catch (error) {
  if (error.status === 404) {
    navigate('/404');
    showToast('error', 'Agent not found');
  }
}
```

---

### 4. Duplicate Entity Errors (409)

**Type:** `https://waooaw.com/errors/duplicate-entity`

Attempt to create entity that already exists (unique constraint violation).

**Example Request:**
```bash
POST /api/v1/genesis/skills
{
  "name": "Python 3.11",
  "category": "technical",
  "description": "Python programming"
}
# Skill with same name+category already exists!
```

**Response:**
```json
{
  "type": "https://waooaw.com/errors/duplicate-entity",
  "title": "Duplicate Entity Error",
  "status": 409,
  "detail": "Skill 'Python 3.11' already exists in category 'technical'",
  "instance": "/api/v1/genesis/skills",
  "correlation_id": "jkl-012"
}
```

**Frontend Handling:**
```typescript
try {
  const skill = await plantAPI.createSkill(data);
} catch (error) {
  if (error.status === 409) {
    setFieldError('name', 'A skill with this name already exists');
  }
}
```

---

### 5. Hash Chain Integrity Errors (500)

**Type:** `https://waooaw.com/errors/hash-chain-broken`

Version hash chain compromised (data tampering detected).

**Response:**
```json
{
  "type": "https://waooaw.com/errors/hash-chain-broken",
  "title": "Hash Chain Integrity Error",
  "status": 500,
  "detail": "Version hash mismatch detected for entity abc-123",
  "instance": "/api/v1/agents/abc-123",
  "correlation_id": "mno-345",
  "violations": ["L0-06: Version Control - hash chain compromised"]
}
```

**Frontend Handling:**
```typescript
try {
  const agent = await plantAPI.getAgent(agentId);
} catch (error) {
  if (error.status === 500 && error.type.includes('hash-chain')) {
    // Critical security issue - alert admins
    showToast('error', 'Data integrity error detected. Admin notified.');
    reportSecurityIncident(error);
  }
}
```

---

### 6. Amendment Signature Errors (422)

**Type:** `https://waooaw.com/errors/amendment-signature`

Amendment signature verification failed (L0-07 violation).

**Response:**
```json
{
  "type": "https://waooaw.com/errors/amendment-signature",
  "title": "Amendment Signature Error",
  "status": 422,
  "detail": "Amendment signature verification failed for agent abc-123",
  "instance": "/api/v1/agents/abc-123/amend",
  "correlation_id": "pqr-678",
  "violations": ["L0-07: Amendment History - signature verification failed"]
}
```

---

### 7. Internal Server Errors (500)

**Type:** `https://waooaw.com/errors/internal-server-error`

Unexpected server errors (database failures, unhandled exceptions).

**Response:**
```json
{
  "type": "https://waooaw.com/errors/internal-server-error",
  "title": "Internal Server Error",
  "status": 500,
  "detail": "An unexpected error occurred. Please try again later.",
  "instance": "/api/v1/agents",
  "correlation_id": "stu-901"
}
```

**Frontend Handling:**
```typescript
try {
  const result = await plantAPI.someOperation();
} catch (error) {
  if (error.status === 500) {
    showToast('error', 'Server error. Please try again.');
    logToSentry(error);  // Log to error tracking service
  }
}
```

---

## Correlation IDs

Correlation IDs enable request tracing across services.

### Client Sends Correlation ID

```bash
# Client generates UUID and sends in header
curl -X POST http://localhost:8000/api/v1/agents \
  -H "X-Correlation-ID: abc-123-def-456" \
  -H "Content-Type: application/json" \
  -d '{"name": "Agent", ...}'
```

### Server Returns Correlation ID

```json
{
  "type": "https://waooaw.com/errors/validation-error",
  "status": 422,
  "detail": "Validation failed",
  "correlation_id": "abc-123-def-456"  # Same ID returned
}
```

### Frontend Implementation

```typescript
// Add correlation ID middleware to fetch
const originalFetch = window.fetch;
window.fetch = function(url, options = {}) {
  const correlationId = crypto.randomUUID();
  options.headers = {
    ...options.headers,
    'X-Correlation-ID': correlationId
  };
  
  return originalFetch(url, options).catch(error => {
    console.error(`Request failed [${correlationId}]:`, error);
    throw error;
  });
};
```

---

## Frontend Error Handling Patterns

### React Hook for Error Handling

```typescript
// src/hooks/usePlantAPI.ts
import { useState } from 'react';
import type { components } from '../types/plant-api.generated';

type ErrorResponse = components['schemas']['ErrorResponse'];

export function usePlantAPI<T>() {
  const [error, setError] = useState<ErrorResponse | null>(null);
  const [loading, setLoading] = useState(false);

  async function execute(apiCall: () => Promise<T>): Promise<T | null> {
    setLoading(true);
    setError(null);
    
    try {
      const result = await apiCall();
      return result;
    } catch (err: any) {
      const errorResponse: ErrorResponse = await err.response.json();
      setError(errorResponse);
      
      // Display user-friendly message
      if (errorResponse.status === 422) {
        toast.error(errorResponse.detail);
        errorResponse.violations?.forEach(violation => {
          toast.error(violation, { duration: 5000 });
        });
      } else if (errorResponse.status === 404) {
        toast.error('Not found');
      } else if (errorResponse.status === 500) {
        toast.error('Server error. Please try again.');
      }
      
      return null;
    } finally {
      setLoading(false);
    }
  }

  return { execute, error, loading };
}

// Usage in component
const { execute, error, loading } = usePlantAPI<AgentResponse>();

const handleCreateAgent = async () => {
  const agent = await execute(() => plantAPI.createAgent(formData));
  if (agent) {
    navigate(`/agents/${agent.id}`);
  }
  // Error automatically displayed by hook
};
```

### Error Display Component

```typescript
// src/components/ErrorAlert.tsx
import type { components } from '../types/plant-api.generated';

type ErrorResponse = components['schemas']['ErrorResponse'];

interface ErrorAlertProps {
  error: ErrorResponse;
  onDismiss?: () => void;
}

export function ErrorAlert({ error, onDismiss }: ErrorAlertProps) {
  return (
    <div className="error-alert">
      <h4>{error.title}</h4>
      <p>{error.detail}</p>
      
      {error.violations && error.violations.length > 0 && (
        <ul>
          {error.violations.map((violation, index) => (
            <li key={index}>{violation}</li>
          ))}
        </ul>
      )}
      
      {error.correlation_id && (
        <p className="text-muted">
          Error ID: {error.correlation_id}
        </p>
      )}
      
      {onDismiss && (
        <button onClick={onDismiss}>Dismiss</button>
      )}
    </div>
  );
}
```

---

## Testing Error Handling

### Unit Test (Backend)

```python
# tests/test_error_handling.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_constitutional_error_rfc7807_format():
    """Test constitutional error returns RFC 7807 format."""
    response = client.post(
        "/api/v1/agents",
        json={
            "name": "Test Agent",
            "skill_id": "550e8400-e29b-41d4-a716-446655440000",
            "job_role_id": "660e8400-e29b-41d4-a716-446655440001",
            "industry_id": "770e8400-e29b-41d4-a716-446655440002"
            # Missing: governance_agent_id
        },
        headers={"X-Correlation-ID": "test-123"}
    )
    
    assert response.status_code == 422
    error = response.json()
    
    # RFC 7807 required fields
    assert error["type"] == "https://waooaw.com/errors/constitutional-alignment"
    assert error["title"] == "Constitutional Alignment Error"
    assert error["status"] == 422
    assert "governance_agent_id" in error["detail"]
    assert error["instance"] == "/api/v1/agents"
    assert error["correlation_id"] == "test-123"
    assert "L0-01" in error["violations"][0]

def test_validation_error_rfc7807_format():
    """Test validation error returns RFC 7807 format."""
    response = client.post(
        "/api/v1/genesis/skills",
        json={
            "name": "Python",
            "category": "invalid",
            "description": ""
        }
    )
    
    assert response.status_code == 422
    error = response.json()
    
    assert error["type"] == "https://waooaw.com/errors/validation-error"
    assert error["status"] == 422
    assert len(error["violations"]) > 0
```

### Integration Test (Frontend)

```typescript
// src/__tests__/plantAPI.test.ts
import { describe, it, expect } from 'vitest';
import { PlantAPIClient } from '../services/plant-api.service';

describe('Plant API Error Handling', () => {
  const plantAPI = new PlantAPIClient();

  it('should handle constitutional error (422)', async () => {
    try {
      await plantAPI.createAgent({
        name: "Test Agent",
        skill_id: "550e8400-e29b-41d4-a716-446655440000",
        job_role_id: "660e8400-e29b-41d4-a716-446655440001",
        industry_id: "770e8400-e29b-41d4-a716-446655440002"
        // Missing: governance_agent_id
      });
      expect.fail('Should have thrown error');
    } catch (error: any) {
      expect(error.status).toBe(422);
      expect(error.type).toContain('constitutional-alignment');
      expect(error.violations).toContain('L0-01');
    }
  });

  it('should handle not found error (404)', async () => {
    try {
      await plantAPI.getAgent('999e8400-e29b-41d4-a716-446655440000');
      expect.fail('Should have thrown error');
    } catch (error: any) {
      expect(error.status).toBe(404);
      expect(error.type).toContain('not-found');
    }
  });
});
```

---

## References

- [RFC 7807 Problem Details for HTTP APIs](https://tools.ietf.org/html/rfc7807)
- [FastAPI Exception Handling](https://fastapi.tiangolo.com/tutorial/handling-errors/)
- [PLANT-002 Story](../../../main/Foundation/Architecture/APIGateway/IMPLEMENTATION_PLAN.md#plant-002-error-handling-standardization)

## Next Steps

1. ✅ Implemented RFC 7807 error format in Plant backend
2. ✅ Updated all exception handlers (constitutional, validation, not found, duplicate, etc.)
3. ⏳ Add integration tests for error responses (PLANT-002 remaining)
4. ⏳ Update CP/PP frontends to parse RFC 7807 errors (CP-001, PP-002)
