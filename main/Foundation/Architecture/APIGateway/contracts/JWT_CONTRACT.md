# JWT Contract Specification

**Version**: 1.0  
**Status**: DRAFT  
**Owner**: Platform Team  
**Last Updated**: 2026-01-17

## Purpose

This document defines the JWT token contract used across WAOOAW platform for authentication and authorization. All services (CP Frontend, PP Backend, API Gateway, Plant Backend) MUST adhere to this contract.

## Scope

- **CP (Customer Platform)**: Issues JWT tokens for customer users
- **PP (Partner Platform)**: Issues JWT tokens for partner users with role-based access
- **API Gateway**: Validates JWT tokens and enforces policy
- **Plant Backend**: Receives validated requests with JWT claims

## Token Structure

### Required Claims (11 Fields)

```json
{
  "user_id": "string",
  "email": "string",
  "customer_id": "string",
  "roles": ["string"],
  "governor_agent_id": "string | null",
  "trial_mode": "boolean",
  "trial_expires_at": "ISO8601 | null",
  "iat": "unix_timestamp",
  "exp": "unix_timestamp",
  "iss": "string",
  "sub": "string"
}
```

### Field Definitions

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `user_id` | string | Yes | Unique user identifier (UUID) | `"550e8400-e29b-41d4-a716-446655440000"` |
| `email` | string | Yes | User email address | `"user@company.com"` |
| `customer_id` | string | Yes | Customer/organization identifier | `"cust_abc123"` |
| `roles` | array[string] | Yes | User roles (see Role Definitions) | `["agent_orchestrator"]` |
| `governor_agent_id` | string/null | Yes | Governor agent ID if user is Governor | `"gov_agent_001"` or `null` |
| `trial_mode` | boolean | Yes | Whether user is in trial period | `true` or `false` |
| `trial_expires_at` | ISO8601/null | Yes | Trial expiration timestamp | `"2026-01-24T23:59:59Z"` or `null` |
| `iat` | integer | Yes | Issued at timestamp (seconds) | `1705449600` |
| `exp` | integer | Yes | Expiration timestamp (seconds) | `1705536000` |
| `iss` | string | Yes | Issuer identifier | `"cp.waooaw.com"` or `"pp.waooaw.com"` |
| `sub` | string | Yes | Subject (same as user_id) | `"550e8400-e29b-41d4-a716-446655440000"` |

### Role Definitions

**CP Roles** (Customer Platform):
- `customer_user` - Standard customer user
- `customer_admin` - Customer administrator

**PP Roles** (Partner Platform - 7-role hierarchy):
- `admin` - Full system access
- `subscription_manager` - Manages subscriptions
- `agent_orchestrator` - Orchestrates agents
- `infrastructure_engineer` - Manages infrastructure
- `helpdesk_agent` - Customer support
- `industry_manager` - Manages industry verticals
- `viewer` - Read-only access

### Validation Rules

1. **Expiration**: `exp` MUST be future timestamp, token expires after this time
2. **Issued At**: `iat` MUST be past timestamp, not future-dated
3. **Trial Mode**: If `trial_mode=true`, `trial_expires_at` MUST be present and future
4. **Governor**: If any role is `admin`, `governor_agent_id` MAY be present
5. **Email Format**: `email` MUST be valid email format (RFC 5322)
6. **Roles**: MUST contain at least 1 role, roles MUST be from defined list
7. **Token Lifetime**: Max 24 hours (`exp - iat <= 86400`)

## Token Generation

### CP Token Generation

```python
import jwt
from datetime import datetime, timedelta

def generate_cp_token(user_id: str, email: str, customer_id: str, trial_mode: bool, trial_expires_at: str = None) -> str:
    """Generate JWT token for Customer Platform users."""
    now = datetime.utcnow()
    payload = {
        "user_id": user_id,
        "email": email,
        "customer_id": customer_id,
        "roles": ["customer_user"],
        "governor_agent_id": None,
        "trial_mode": trial_mode,
        "trial_expires_at": trial_expires_at,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=24)).timestamp()),
        "iss": "cp.waooaw.com",
        "sub": user_id
    }
    return jwt.encode(payload, os.getenv("JWT_SECRET_CP"), algorithm="HS256")
```

### PP Token Generation

```python
def generate_pp_token(user_id: str, email: str, customer_id: str, roles: list[str], governor_agent_id: str = None) -> str:
    """Generate JWT token for Partner Platform users."""
    now = datetime.utcnow()
    payload = {
        "user_id": user_id,
        "email": email,
        "customer_id": customer_id,
        "roles": roles,
        "governor_agent_id": governor_agent_id,
        "trial_mode": False,  # PP users never in trial
        "trial_expires_at": None,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=24)).timestamp()),
        "iss": "pp.waooaw.com",
        "sub": user_id
    }
    return jwt.encode(payload, os.getenv("JWT_SECRET_PP"), algorithm="HS256")
```

## Token Validation

### Gateway Validation Logic

```python
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

def validate_jwt(token: str, issuer: str) -> dict:
    """
    Validate JWT token and return decoded claims.
    
    Args:
        token: JWT token string
        issuer: Expected issuer ("cp.waooaw.com" or "pp.waooaw.com")
        
    Returns:
        Decoded token claims
        
    Raises:
        ExpiredSignatureError: Token expired
        InvalidTokenError: Invalid token format/signature
    """
    secret = os.getenv("JWT_SECRET_CP") if issuer == "cp.waooaw.com" else os.getenv("JWT_SECRET_PP")
    
    try:
        claims = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            issuer=issuer,
            options={
                "require": ["user_id", "email", "customer_id", "roles", "iat", "exp", "iss", "sub"],
                "verify_exp": True,
                "verify_iat": True
            }
        )
        
        # Additional validation
        if claims["exp"] - claims["iat"] > 86400:
            raise InvalidTokenError("Token lifetime exceeds 24 hours")
        
        if claims["trial_mode"] and not claims.get("trial_expires_at"):
            raise InvalidTokenError("trial_mode=true requires trial_expires_at")
        
        if not claims["roles"]:
            raise InvalidTokenError("roles array cannot be empty")
        
        return claims
        
    except ExpiredSignatureError:
        raise
    except Exception as e:
        raise InvalidTokenError(f"Token validation failed: {str(e)}")
```

## Token Transmission

### HTTP Header Format

```http
Authorization: Bearer <jwt_token>
```

### Example Request

```http
GET /api/v1/agents HTTP/1.1
Host: plant.waooaw.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

## Security Requirements

1. **Secret Management**: JWT secrets MUST be stored in GCP Secret Manager
   - `jwt-secret-cp` for Customer Platform
   - `jwt-secret-pp` for Partner Platform
   
2. **Secret Rotation**: Secrets SHOULD be rotated every 90 days

3. **Algorithm**: MUST use HS256 (HMAC-SHA256)

4. **HTTPS Only**: Tokens MUST only be transmitted over HTTPS

5. **No Storage in Logs**: Tokens MUST NOT be logged in plain text

## Token Lifecycle

```mermaid
sequenceDiagram
    participant U as User
    participant CP as CP Frontend
    participant GW as API Gateway
    participant Plant as Plant Backend
    
    U->>CP: Login (email/password)
    CP->>CP: Authenticate user
    CP->>CP: Generate JWT (24hr)
    CP->>U: Return JWT
    U->>GW: API Request + JWT
    GW->>GW: Validate JWT
    GW->>Plant: Forward request + claims
    Plant->>Plant: Process request
    Plant->>GW: Response
    GW->>U: Response
```

## Error Responses

### Expired Token

```json
{
  "error": "token_expired",
  "message": "JWT token has expired",
  "status": 401
}
```

### Invalid Token

```json
{
  "error": "invalid_token",
  "message": "JWT token is invalid or malformed",
  "status": 401
}
```

### Missing Token

```json
{
  "error": "missing_token",
  "message": "Authorization header with Bearer token required",
  "status": 401
}
```

## Testing

### Valid Token Examples

**CP Trial User**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "trial@startup.com",
  "customer_id": "cust_trial_001",
  "roles": ["customer_user"],
  "governor_agent_id": null,
  "trial_mode": true,
  "trial_expires_at": "2026-01-24T23:59:59Z",
  "iat": 1705449600,
  "exp": 1705536000,
  "iss": "cp.waooaw.com",
  "sub": "550e8400-e29b-41d4-a716-446655440000"
}
```

**PP Governor Admin**:
```json
{
  "user_id": "admin-001",
  "email": "governor@waooaw.com",
  "customer_id": "internal",
  "roles": ["admin"],
  "governor_agent_id": "gov_agent_supreme",
  "trial_mode": false,
  "trial_expires_at": null,
  "iat": 1705449600,
  "exp": 1705536000,
  "iss": "pp.waooaw.com",
  "sub": "admin-001"
}
```

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-17 | Platform Team | Initial draft with 11-field schema |

## References

- RFC 7519: JSON Web Token (JWT)
- Gateway Final IMPLEMENTATION_PLAN.md (GW-00P)
- PEER_REVIEW_ENHANCEMENTS.md
