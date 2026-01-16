# Plant CORS Configuration Guide

## Overview

Plant backend uses strict CORS (Cross-Origin Resource Sharing) configuration to allow CP/PP frontends to make browser-based API calls while blocking unauthorized origins.

## Allowed Origins

### Local Development
- `http://localhost:3000` - CP frontend (React dev server)
- `http://localhost:5173` - PP frontend (Vite dev server)
- `http://localhost:8080` - CP frontend (alternative port)
- `http://localhost:8006` - PP frontend (alternative port)
- `http://localhost:8015` - CP frontend (FastAPI dev server)

### Demo Environment
- `https://cp.demo.waooaw.com` - CP demo
- `https://pp.demo.waooaw.com` - PP demo

### UAT Environment
- `https://cp.uat.waooaw.com` - CP UAT
- `https://pp.uat.waooaw.com` - PP UAT

### Production Environment
- `https://cp.waooaw.com` - CP production
- `https://pp.waooaw.com` - PP production

## Configuration

### Environment-Based Origins (Future Enhancement)

To make CORS origins configurable per environment, add to `.env` file:

```bash
# .env.local
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080

# .env.demo
CORS_ORIGINS=https://cp.demo.waooaw.com,https://pp.demo.waooaw.com,http://localhost:3000

# .env.prod
CORS_ORIGINS=https://cp.waooaw.com,https://pp.waooaw.com
```

Update `core/config.py` to load from environment:

```python
class Settings(BaseSettings):
    cors_origins_str: str = "http://localhost:3000,http://localhost:5173"
    
    @property
    def cors_origins(self) -> list:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins_str.split(',')]
```

## CORS Headers

### Request Headers Allowed
- `Authorization` - JWT bearer tokens (future)
- `Content-Type` - Request payload type (application/json)
- `X-Correlation-ID` - Request correlation ID for tracing
- `X-Causation-ID` - Causation ID for event sourcing (future)
- `X-Request-ID` - Unique request identifier

### Response Headers Exposed
- `X-Correlation-ID` - Echoed back for client-side tracing
- `X-Causation-ID` - Event causation chain (future)
- `X-Request-ID` - Request identifier for debugging

### Credentials Allowed
- `allow_credentials=True` - Allow cookies, Authorization headers, TLS client certificates

### Methods Allowed
- `GET` - Read operations
- `POST` - Create operations
- `PUT` - Full update operations (future)
- `PATCH` - Partial update operations (future)
- `DELETE` - Delete operations (future)
- `OPTIONS` - Preflight requests

## Preflight Requests

Browsers send OPTIONS requests before actual requests (for POST/PUT/DELETE/PATCH with custom headers).

### Example Preflight Request
```http
OPTIONS /api/v1/agents HTTP/1.1
Host: localhost:8000
Origin: http://localhost:3000
Access-Control-Request-Method: POST
Access-Control-Request-Headers: content-type, x-correlation-id
```

### Example Preflight Response
```http
HTTP/1.1 200 OK
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, PATCH, OPTIONS
Access-Control-Allow-Headers: Authorization, Content-Type, X-Correlation-ID, X-Causation-ID, X-Request-ID
Access-Control-Allow-Credentials: true
Access-Control-Max-Age: 600
```

Plant's CORS middleware caches preflight responses for 10 minutes (`max_age=600`).

## Frontend Integration

### Fetch API (Vanilla JavaScript)

```javascript
// CP frontend making request to Plant
const response = await fetch('http://localhost:8000/api/v1/agents', {
  method: 'GET',
  credentials: 'include',  // Send cookies (future: JWT in cookies)
  headers: {
    'Content-Type': 'application/json',
    'X-Correlation-ID': crypto.randomUUID()
  }
});

// CORS headers automatically validated by browser
// No CORS error if origin matches allowed list
const agents = await response.json();
```

### Axios (React/TypeScript)

```typescript
// src/CP/FrontEnd/services/plant-api.service.ts
import axios from 'axios';

const plantAPI = axios.create({
  baseURL: 'http://localhost:8000',
  withCredentials: true,  // Include cookies
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add correlation ID interceptor
plantAPI.interceptors.request.use(config => {
  config.headers['X-Correlation-ID'] = crypto.randomUUID();
  return config;
});

// Use the client
const response = await plantAPI.get('/api/v1/agents');
// No CORS error if origin in allowed list
```

### React Query (Recommended)

```typescript
// src/CP/FrontEnd/hooks/useAgents.ts
import { useQuery } from '@tanstack/react-query';
import { plantAPI } from '../services/plant-api.service';

export function useAgents(filters?: { industry_id?: string }) {
  return useQuery({
    queryKey: ['agents', filters],
    queryFn: async () => {
      const response = await plantAPI.get('/api/v1/agents', {
        params: filters,
        headers: {
          'X-Correlation-ID': crypto.randomUUID()
        }
      });
      return response.data;
    }
  });
}

// Usage in component
function AgentList() {
  const { data: agents, error, isLoading } = useAgents();
  
  if (error) {
    // Check if CORS error
    if (error.message.includes('CORS')) {
      return <div>CORS error - check Plant CORS configuration</div>;
    }
  }
  
  return <div>{/* Render agents */}</div>;
}
```

## Troubleshooting

### CORS Error in Browser Console

**Symptom:**
```
Access to fetch at 'http://localhost:8000/api/v1/agents' from origin 'http://localhost:3001' 
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present.
```

**Cause:** Frontend origin (`http://localhost:3001`) not in Plant's allowed origins list.

**Solution:**
1. Add origin to `core/config.py` cors_origins list
2. Restart Plant backend
3. Verify origin added: `curl http://localhost:8000/` (check CORS headers in response)

```bash
# Verify CORS headers
curl -H "Origin: http://localhost:3001" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     -v \
     http://localhost:8000/api/v1/agents

# Should return:
# Access-Control-Allow-Origin: http://localhost:3001
# Access-Control-Allow-Methods: GET, POST, PUT, DELETE, PATCH, OPTIONS
```

---

### Credentials Not Sent (No Cookies/JWT)

**Symptom:** Cookies or Authorization header not sent with request.

**Cause:** Missing `credentials: 'include'` or `withCredentials: true`.

**Solution:**

```javascript
// ❌ Wrong - credentials not sent
fetch('http://localhost:8000/api/v1/agents');

// ✅ Correct - credentials sent
fetch('http://localhost:8000/api/v1/agents', {
  credentials: 'include'
});

// Axios
axios.get('/api/v1/agents', {
  withCredentials: true
});
```

---

### Preflight Request Failed

**Symptom:**
```
Access to fetch at 'http://localhost:8000/api/v1/agents' from origin 'http://localhost:3000'
has been blocked by CORS policy: Response to preflight request doesn't pass access control check.
```

**Cause:** OPTIONS request not handled properly.

**Solution:** FastAPI's CORSMiddleware handles OPTIONS automatically. Check Plant logs for errors:

```bash
# Start Plant with debug logging
cd src/Plant/BackEnd
uvicorn main:app --host 0.0.0.0 --port 8000 --log-level debug

# In another terminal, trigger preflight
curl -X OPTIONS \
     -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     http://localhost:8000/api/v1/agents

# Check Plant logs for CORS middleware processing
```

---

### Correlation ID Not Returned

**Symptom:** Error response missing `correlation_id` field.

**Cause:** Frontend not sending `X-Correlation-ID` header.

**Solution:** Add correlation ID to all requests:

```typescript
// Global fetch interceptor
const originalFetch = window.fetch;
window.fetch = function(url, options = {}) {
  options.headers = {
    ...options.headers,
    'X-Correlation-ID': crypto.randomUUID()
  };
  return originalFetch(url, options);
};
```

---

### CORS Working Locally but Not in Demo/Prod

**Symptom:** CORS works on localhost but fails in deployed environments.

**Cause:** Demo/prod origins not added to allowed list, or environment variable not loaded.

**Solution:**

1. Verify Plant's deployed CORS config:
```bash
# Check Plant health endpoint
curl https://plant.demo.waooaw.com/

# Response includes cors_origins (future enhancement)
{
  "service": "WAOOAW Plant Phase API",
  "cors_origins": ["https://cp.demo.waooaw.com", "https://pp.demo.waooaw.com"]
}
```

2. Add missing origins to `core/config.py` or `.env.demo`

3. Redeploy Plant backend

---

## Security Considerations

### Why Not Use `allow_origins=["*"]`?

**❌ Wildcard (`*`) is insecure:**
- Allows any website to call Plant API
- Exposes customer data to malicious sites
- Cannot use with `allow_credentials=True` (browser blocks this)

**✅ Explicit origin list is secure:**
- Only CP/PP can call Plant API
- Other websites blocked by browser
- Allows credentials (cookies, JWT tokens)

### Localhost CORS in Production

In production, localhost origins should be **removed** from allowed list:

```python
# prod.env
CORS_ORIGINS=https://cp.waooaw.com,https://pp.waooaw.com
# No localhost origins!
```

Alternatively, use environment-based config:

```python
class Settings(BaseSettings):
    @property
    def cors_origins(self) -> list:
        if self.environment == "production":
            return [
                "https://cp.waooaw.com",
                "https://pp.waooaw.com"
            ]
        elif self.environment == "demo":
            return [
                "https://cp.demo.waooaw.com",
                "https://pp.demo.waooaw.com",
                "http://localhost:3000"  # Allow local dev to call demo Plant
            ]
        else:  # development
            return [
                "http://localhost:3000",
                "http://localhost:5173",
                "http://localhost:8080",
                "http://localhost:8006",
                "http://localhost:8015"
            ]
```

## Testing CORS

### Manual Test (Browser DevTools)

1. Open CP frontend: `http://localhost:3000`
2. Open Browser DevTools (F12) → Network tab
3. Make API request to Plant (e.g., list agents)
4. Check request headers:
   - `Origin: http://localhost:3000`
5. Check response headers:
   - `Access-Control-Allow-Origin: http://localhost:3000`
   - `Access-Control-Allow-Credentials: true`
6. If preflight sent, check OPTIONS request:
   - Status: 200 OK
   - Headers: `Access-Control-Allow-Methods`, `Access-Control-Allow-Headers`

### Automated Test (Pytest)

```python
# tests/test_cors.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_cors_allowed_origin():
    """Test CORS allows requests from CP frontend."""
    response = client.get(
        "/api/v1/agents",
        headers={"Origin": "http://localhost:3000"}
    )
    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:3000"
    assert response.headers["Access-Control-Allow-Credentials"] == "true"

def test_cors_blocked_origin():
    """Test CORS blocks requests from unknown origin."""
    response = client.get(
        "/api/v1/agents",
        headers={"Origin": "http://evil.com"}
    )
    # FastAPI CORSMiddleware doesn't return CORS headers for blocked origins
    assert "Access-Control-Allow-Origin" not in response.headers

def test_cors_preflight():
    """Test CORS preflight request (OPTIONS)."""
    response = client.options(
        "/api/v1/agents",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type, X-Correlation-ID"
        }
    )
    assert response.status_code == 200
    assert "POST" in response.headers["Access-Control-Allow-Methods"]
    assert "Content-Type" in response.headers["Access-Control-Allow-Headers"]
```

## References

- [MDN: CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [FastAPI CORS Middleware](https://fastapi.tiangolo.com/tutorial/cors/)
- [PLANT-003 Story](../../../main/Foundation/Architecture/APIGateway/IMPLEMENTATION_PLAN.md#plant-003-cors-configuration-for-cppp-origins)

## Next Steps

1. ✅ CORS middleware configured with explicit origin list
2. ✅ Allow credentials enabled for future JWT auth
3. ✅ Preflight caching enabled (10 minutes)
4. ⏳ Add environment-based CORS origins (`.env` file) - Future enhancement
5. ⏳ Add CORS tests to integration test suite - PLANT-003 remaining
6. ⏳ Verify CORS in deployed environments (Demo/UAT/Prod) - After deployment
