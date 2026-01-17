# Plant API Contract Specification

**Version**: 1.0  
**Status**: DRAFT  
**Owner**: Plant Team  
**Last Updated**: 2026-01-17

## Purpose

This document defines the stable API contract between the API Gateway and Plant Backend service. This contract ensures backward compatibility and manages breaking changes through versioning.

## Base URL

- **Production**: `https://plant.waooaw.com`
- **Demo**: `https://plant.demo.waooaw.com`
- **Sandbox (Trial)**: `https://plant.sandbox.waooaw.com`
- **Local Development**: `http://localhost:8000`

## API Versioning

### Current Version: v1

All Plant API endpoints use `/api/v1/` prefix:

```
https://plant.waooaw.com/api/v1/{resource}
```

### Versioning Strategy

- **Major Version** (v1, v2, v3): Breaking changes
- **Minor Updates**: Non-breaking additions (no version bump)
- **Path-based versioning**: `/api/v1/`, `/api/v2/`

### Breaking Change Policy

**Definition of Breaking Change**:
- Removing an endpoint
- Removing a required field
- Changing field data type
- Renaming fields
- Changing authentication requirements
- Changing error response format

**Non-Breaking Changes** (allowed in same version):
- Adding new endpoints
- Adding optional fields
- Adding new response fields
- Deprecating (but not removing) endpoints
- Performance improvements
- Bug fixes

**Migration Timeline**:
1. **T+0**: Announce breaking change via `X-API-Deprecation` header
2. **T+30 days**: Deploy v2 alongside v1 (both active)
3. **T+90 days**: Remove v1 endpoints

### Version Support Matrix

| Version | Status | Release Date | EOL Date | Notes |
|---------|--------|--------------|----------|-------|
| v1 | Current | 2025-12-01 | - | Stable, recommended |
| v2 | Planned | 2026-Q3 | - | Gateway integration features |

## Required HTTP Headers

### Request Headers

All requests to Plant API MUST include:

```http
Authorization: Bearer <jwt_token>
X-Correlation-ID: <uuid>
X-Request-ID: <uuid>
Content-Type: application/json
X-API-Version: v1
```

| Header | Required | Description | Example |
|--------|----------|-------------|---------|
| `Authorization` | Yes | JWT bearer token | `Bearer eyJhbGc...` |
| `X-Correlation-ID` | Yes | Request correlation ID for audit trail | `550e8400-e29b-41d4-a716-446655440000` |
| `X-Request-ID` | Yes | Unique request identifier | `550e8400-e29b-41d4-a716-446655440001` |
| `Content-Type` | Yes (POST/PUT) | Request content type | `application/json` |
| `X-API-Version` | No | Explicit API version (defaults to v1) | `v1` |
| `X-Causation-ID` | No | Parent request ID (for nested calls) | `550e8400-e29b-41d4-a716-446655440002` |

### Response Headers

Plant API MUST return:

```http
X-Correlation-ID: <same_as_request>
X-Request-ID: <same_as_request>
X-API-Version: v1
X-RateLimit-Remaining: 950
X-RateLimit-Limit: 1000
X-Response-Time-Ms: 123
```

| Header | Always Returned | Description |
|--------|-----------------|-------------|
| `X-Correlation-ID` | Yes | Echo correlation ID from request |
| `X-Request-ID` | Yes | Echo request ID from request |
| `X-API-Version` | Yes | API version used for response |
| `X-RateLimit-Remaining` | Yes | Remaining requests in current window |
| `X-RateLimit-Limit` | Yes | Total requests allowed per window |
| `X-Response-Time-Ms` | Yes | Server processing time in milliseconds |
| `X-API-Deprecation` | When applicable | Deprecation warning with timeline |

## Endpoint Categories

### 1. Agent Management (`/api/v1/agents`)

**List Agents**:
```http
GET /api/v1/agents
Query Parameters:
  - industry: string (marketing, education, sales)
  - min_rating: float (0.0 to 5.0)
  - specialty: string
  - status: string (available, working, offline)
  - limit: integer (1-100, default 20)
  - offset: integer (default 0)

Response 200:
{
  "agents": [
    {
      "agent_id": "agent_001",
      "name": "Content Marketing Agent",
      "industry": "marketing",
      "specialty": "Healthcare specialist",
      "rating": 4.8,
      "status": "available",
      "pricing": {
        "monthly": 12000,
        "currency": "INR"
      }
    }
  ],
  "total": 19,
  "limit": 20,
  "offset": 0
}
```

**Get Agent Details**:
```http
GET /api/v1/agents/{agent_id}

Response 200:
{
  "agent_id": "agent_001",
  "name": "Content Marketing Agent",
  "description": "...",
  "industry": "marketing",
  "specialty": "Healthcare specialist",
  "capabilities": ["blog_posts", "social_content", "email_campaigns"],
  "rating": 4.8,
  "retention_rate": 0.98,
  "response_time_hours": 2,
  "status": "available",
  "pricing": {...}
}

Response 404:
{
  "error": "agent_not_found",
  "message": "Agent with ID agent_999 not found",
  "status": 404
}
```

### 2. Trial Management (`/api/v1/trials`)

**Start Trial**:
```http
POST /api/v1/trials
Body:
{
  "agent_id": "agent_001",
  "customer_id": "cust_abc123",
  "trial_duration_days": 7
}

Response 201:
{
  "trial_id": "trial_xyz789",
  "agent_id": "agent_001",
  "customer_id": "cust_abc123",
  "status": "active",
  "started_at": "2026-01-17T10:00:00Z",
  "expires_at": "2026-01-24T10:00:00Z",
  "task_limit_per_day": 10,
  "tasks_used_today": 0
}
```

**Get Trial Status**:
```http
GET /api/v1/trials/{trial_id}

Response 200:
{
  "trial_id": "trial_xyz789",
  "status": "active",
  "tasks_used_today": 3,
  "task_limit_per_day": 10,
  "days_remaining": 6,
  "expires_at": "2026-01-24T10:00:00Z"
}
```

### 3. Task Execution (`/api/v1/tasks`)

**Create Task**:
```http
POST /api/v1/tasks
Body:
{
  "agent_id": "agent_001",
  "task_type": "create_blog_post",
  "parameters": {
    "topic": "AI in Healthcare",
    "word_count": 1000,
    "tone": "professional"
  }
}

Response 202:
{
  "task_id": "task_12345",
  "agent_id": "agent_001",
  "status": "queued",
  "created_at": "2026-01-17T10:05:00Z",
  "estimated_completion": "2026-01-17T12:05:00Z"
}
```

**Get Task Status**:
```http
GET /api/v1/tasks/{task_id}

Response 200:
{
  "task_id": "task_12345",
  "agent_id": "agent_001",
  "status": "completed",
  "result": {
    "blog_post": "...",
    "word_count": 1024,
    "seo_score": 85
  },
  "created_at": "2026-01-17T10:05:00Z",
  "completed_at": "2026-01-17T11:30:00Z"
}
```

### 4. Budget Management (`/api/v1/budgets`)

**Get Agent Budget**:
```http
GET /api/v1/budgets/agent/{agent_id}

Response 200:
{
  "agent_id": "agent_001",
  "daily_cap_usd": 1.00,
  "spent_today_usd": 0.45,
  "remaining_today_usd": 0.55,
  "resets_at": "2026-01-18T00:00:00Z"
}
```

**Get Platform Budget**:
```http
GET /api/v1/budgets/platform

Response 200:
{
  "monthly_cap_usd": 100.00,
  "spent_this_month_usd": 67.23,
  "remaining_usd": 32.77,
  "resets_at": "2026-02-01T00:00:00Z",
  "alert_threshold_80": false,
  "alert_threshold_95": false
}
```

## Authentication

### JWT Validation

Plant Backend MUST:
1. Validate JWT signature using shared secret
2. Check token expiration (`exp` claim)
3. Verify issuer (`iss` claim)
4. Extract user claims for authorization

### Authorization

Plant Backend relies on Gateway for authorization but SHOULD verify:
- User has access to requested agent
- Trial users cannot exceed task limits
- Budget caps are enforced

## Error Response Format

All errors follow RFC 7807 Problem Details format:

```json
{
  "type": "https://waooaw.com/errors/budget-exceeded",
  "title": "Daily budget exceeded",
  "status": 429,
  "detail": "Agent agent_001 has exceeded daily budget of $1.00",
  "instance": "/api/v1/tasks",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-01-17T10:30:00Z"
}
```

### Standard Error Codes

| HTTP Code | Error Type | Description |
|-----------|------------|-------------|
| 400 | `invalid_request` | Malformed request body/parameters |
| 401 | `unauthorized` | Missing or invalid JWT token |
| 403 | `forbidden` | User lacks permission for resource |
| 404 | `not_found` | Resource does not exist |
| 409 | `conflict` | Resource conflict (duplicate trial) |
| 429 | `rate_limit_exceeded` | Rate limit exceeded |
| 429 | `budget_exceeded` | Budget cap exceeded |
| 500 | `internal_error` | Server error |
| 503 | `service_unavailable` | Service temporarily unavailable |

## Rate Limiting

Plant API enforces rate limits per customer:

| Tier | Requests/Hour | Burst |
|------|---------------|-------|
| Trial | 100 | 10 |
| Paid | 1000 | 50 |
| Enterprise | 10000 | 200 |

Rate limit headers returned:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1705453200
```

## Performance SLAs

| Metric | Target | Notes |
|--------|--------|-------|
| Response Time (p50) | < 200ms | Simple GET requests |
| Response Time (p95) | < 500ms | Complex queries |
| Response Time (p99) | < 1000ms | Task creation |
| Availability | 99.9% | Excluding planned maintenance |
| Error Rate | < 0.1% | 5xx errors |

## Audit Trail

Plant Backend MUST log all requests:

```json
{
  "timestamp": "2026-01-17T10:30:00Z",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "request_id": "550e8400-e29b-41d4-a716-446655440001",
  "method": "POST",
  "path": "/api/v1/tasks",
  "user_id": "user_123",
  "customer_id": "cust_abc",
  "status_code": 202,
  "response_time_ms": 123,
  "ip_address": "10.0.1.5"
}
```

## Deprecation Policy

When deprecating endpoints:

1. **Add header** to responses:
   ```http
   X-API-Deprecation: Endpoint deprecated, use /api/v2/tasks instead. EOL: 2026-04-17
   ```

2. **Update documentation** with migration guide

3. **Send notifications** to all customers using deprecated endpoints

4. **Maintain for 90 days** before removal

## Testing Support

### Health Check

```http
GET /health

Response 200:
{
  "status": "healthy",
  "version": "v1",
  "timestamp": "2026-01-17T10:00:00Z",
  "dependencies": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```

### Readiness Check

```http
GET /ready

Response 200:
{
  "status": "ready",
  "dependencies_ready": true
}

Response 503:
{
  "status": "not_ready",
  "reason": "database_migration_in_progress"
}
```

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-17 | Plant Team | Initial contract definition |

## References

- JWT_CONTRACT.md
- Gateway Final IMPLEMENTATION_PLAN.md (GW-00P)
- RFC 7807: Problem Details for HTTP APIs
