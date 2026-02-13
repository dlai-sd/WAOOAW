"""
Custom domain exceptions for Plant backend
Used for business logic errors with clear semantics
"""


class PlantException(Exception):
    """Base exception for all Plant-specific errors."""
    pass


# ========== AUTHENTICATION & JWT ERRORS ==========

class AuthenticationError(PlantException):
    """Base exception for authentication failures."""
    pass


class JWTTokenExpiredError(AuthenticationError):
    """
    Raised when JWT token has expired.
    
    Provides actionable guidance on token refresh.
    """
    def __init__(self, expired_at: str = None):
        self.expired_at = expired_at
        message = self._build_message()
        super().__init__(message)
    
    def _build_message(self) -> str:
        msg = "❌ JWT Token Expired\n\n"
        if self.expired_at:
            msg += f"Token expired at: {self.expired_at}\n\n"
        
        msg += "REQUIRED ACTIONS:\n"
        msg += "1. Obtain a new token from the authentication provider\n"
        msg += "2. For Google OAuth: Re-authenticate through the login flow\n"
        msg += "3. Ensure your client handles token refresh before expiration\n\n"
        
        msg += "PREVENTION:\n"
        msg += "- Tokens typically expire after 1 hour\n"
        msg += "- Implement token refresh 5-10 minutes before expiration\n"
        msg += "- Store exp claim and monitor: decode JWT to check 'exp' field\n\n"
        
        msg += "DOCUMENTATION:\n"
        msg += "- Token refresh guide: https://docs.waooaw.com/auth/token-refresh\n"
        msg += "- OAuth flow: https://docs.waooaw.com/auth/oauth"
        
        return msg


class JWTInvalidSignatureError(AuthenticationError):
    """
    Raised when JWT signature verification fails.
    
    Indicates token tampering or wrong secret key.
    """
    def __init__(self):
        message = self._build_message()
        super().__init__(message)
    
    def _build_message(self) -> str:
        msg = "❌ JWT Invalid Signature\n\n"
        msg += "PROBLEM:\n"
        msg += "Token signature verification failed. This indicates:\n"
        msg += "- Token has been tampered with, OR\n"
        msg += "- Token was signed with a different secret key, OR\n"
        msg += "- Token format is corrupted\n\n"
        
        msg += "REQUIRED ACTIONS:\n"
        msg += "1. Obtain a fresh token from the authentication provider\n"
        msg += "2. DO NOT manually edit or modify JWT tokens\n"
        msg += "3. Ensure you're using tokens from the correct environment\n\n"
        
        msg += "FOR DEVELOPERS:\n"
        msg += "If you manage the auth service:\n"
        msg += "- Verify SECRET_KEY matches between token issuer and validator\n"
        msg += "- Check ALGORITHM setting (HS256, RS256, etc.)\n"
        msg += "- Ensure base64 encoding is consistent\n\n"
        
        msg += "SECURITY NOTE:\n"
        msg += "This error is logged for security monitoring. Repeated failures\n"
        msg += "may indicate an attack attempt.\n\n"
        
        msg += "DOCUMENTATION:\n"
        msg += "- JWT security: https://docs.waooaw.com/auth/jwt-security"
        
        return msg


class JWTInvalidTokenError(AuthenticationError):
    """
    Raised when JWT token is malformed or invalid.
    
    Indicates structural problems with the token.
    """
    def __init__(self, reason: str = None):
        self.reason = reason
        message = self._build_message()
        super().__init__(message)
    
    def _build_message(self) -> str:
        msg = "❌ JWT Invalid Token Format\n\n"
        if self.reason:
            msg += f"Reason: {self.reason}\n\n"
        
        msg += "PROBLEM:\n"
        msg += "Token format is invalid. Common causes:\n"
        msg += "- Token is not a valid JWT (must have 3 parts: header.payload.signature)\n"
        msg += "- Token encoding is corrupted\n"
        msg += "- Token contains invalid characters\n"
        msg += "- Token was truncated or modified\n\n"
        
        msg += "REQUIRED ACTIONS:\n"
        msg += "1. Verify token format: should be xxxxx.yyyyy.zzzzz\n"
        msg += "2. Check for accidental newlines or spaces in token\n"
        msg += "3. Obtain a fresh token from authentication provider\n\n"
        
        msg += "CORRECT FORMAT:\n"
        msg += "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U\n\n"
        
        msg += "DEBUG:\n"
        msg += "- Decode token at: https://jwt.io (NEVER paste real tokens on public sites)\n"
        msg += "- Verify token has exactly 2 dots (.)\n"
        msg += "- Check token is base64url encoded\n\n"
        
        msg += "DOCUMENTATION:\n"
        msg += "- JWT format: https://docs.waooaw.com/auth/jwt-format"
        
        return msg


class BearerTokenMissingError(AuthenticationError):
    """
    Raised when Authorization header is missing or doesn't contain Bearer token.
    
    Provides examples of correct header format.
    """
    def __init__(self, header_value: str = None):
        self.header_value = header_value
        message = self._build_message()
        super().__init__(message)
    
    def _build_message(self) -> str:
        msg = "❌ Bearer Token Missing or Malformed\n\n"
        
        if self.header_value:
            msg += f"Received Authorization header: {self.header_value[:50]}...\n\n"
        else:
            msg += "No Authorization header found in request\n\n"
        
        msg += "REQUIRED ACTIONS:\n"
        msg += "1. Include Authorization header in your HTTP request\n"
        msg += "2. Use Bearer token format (see examples below)\n\n"
        
        msg += "CORRECT FORMATS:\n"
        msg += "Header name: Authorization (or X-Original-Authorization via gateway)\n"
        msg += "Header value: Bearer <your_jwt_token>\n\n"
        
        msg += "EXAMPLES:\n"
        msg += "curl:\n"
        msg += '  curl -H "Authorization: Bearer eyJhbGc..." https://api.waooaw.com/v1/agents\n\n'
        
        msg += "JavaScript (fetch):\n"
        msg += "  fetch('/api/v1/agents', {\n"
        msg += "    headers: { 'Authorization': `Bearer ${token}` }\n"
        msg += "  })\n\n"
        
        msg += "Python (requests):\n"
        msg += "  headers = {'Authorization': f'Bearer {token}'}\n"
        msg += "  requests.get(url, headers=headers)\n\n"
        
        msg += "COMMON MISTAKES:\n"
        msg += "❌ Missing 'Bearer ' prefix\n"
        msg += "❌ Extra spaces: 'Bearer  token' (double space)\n"
        msg += "❌ Wrong header name: 'Auth' instead of 'Authorization'\n"
        msg += "❌ Sending token without 'Bearer ' prefix\n\n"
        
        msg += "DOCUMENTATION:\n"
        msg += "- Authentication guide: https://docs.waooaw.com/auth/bearer-token"
        
        return msg


class JWTMissingClaimError(AuthenticationError):
    """
    Raised when required claim is missing from JWT payload.
    """
    def __init__(self, claim: str):
        self.claim = claim
        message = f"JWT token missing required claim: {claim}\n\n"
        message += "The token payload must include this claim for authentication.\n"
        message += "Obtain a new token with all required claims from auth provider."
        super().__init__(message)


# ========== CONSTITUTIONAL & ENTITY ERRORS ==========

class ConstitutionalAlignmentError(PlantException):
    """
    Raised when entity fails L0/L1 constitutional alignment checks.
    
    Example:
        raise ConstitutionalAlignmentError(
            f"L0-02 violation: amendment_history not tracked for {entity_id}"
        )
    """
    pass


class HashChainBrokenError(PlantException):
    """
    Raised when audit trail hash chain is broken (tampering detected).
    
    Example:
        raise HashChainBrokenError(
            f"Hash chain broken: expected {expected_hash}, got {computed_hash}"
        )
    """
    pass


class AmendmentSignatureError(PlantException):
    """
    Raised when RSA signature verification fails.
    
    Example:
        raise AmendmentSignatureError(
            "RSA signature verification failed: data may have been tampered"
        )
    """
    pass


class CustomerNotFoundError(PlantException):
    """
    Raised when customer is not found in database.
    
    Includes actionable information for resolution.
    """
    def __init__(self, email: str, details: dict = None):
        self.email = email
        self.details = details or {}
        message = self._build_message()
        super().__init__(message)
    
    def _build_message(self) -> str:
        """Build detailed, actionable error message."""
        msg = [
            f"Customer account not found for email: {self.email}",
            "",
            "⚠️  REQUIRED ACTION:",
            "1. Create customer record in database:",
            "   - Table: customer_entity (customer details)",
            "   - Table: base_entity (entity metadata)",
            "",
            "2. Required SQL:",
            "   ```sql",
            "   -- Step 1: Insert base entity with correct entity_type",
            "   INSERT INTO base_entity (id, entity_type, status)",
            "   VALUES (gen_random_uuid(), 'Customer', 'active');",
            "   ",
            "   -- Step 2: Insert customer entity",
            "   INSERT INTO customer_entity (id, email, phone, full_name, ...)",
            "   VALUES (<uuid_from_step_1>, '{email}', '+91-...', 'Name', ...);",
            "   ```",
            "",
            "3. CRITICAL: entity_type must be 'Customer' (capital C)",
            "   - NOT 'customer' (lowercase) - causes polymorphic identity error",
            "",
            "4. Email must match Google OAuth login exactly (case-insensitive)",
        ]
        
        if self.details.get("similar_emails"):
            msg.extend([
                "",
                f"💡 Similar emails found: {', '.join(self.details['similar_emails'][:3])}",
                "   (Check for typos in email address)",
            ])
        
        msg.extend([
            "",
            "📖 Documentation: /docs/runbooks/customer-onboarding.md",
        ])
        
        return "\n".join(msg).format(email=self.email)


class PolymorphicIdentityError(PlantException):
    """
    Raised when SQLAlchemy polymorphic identity doesn't match model definition.
    
    This happens when entity_type in database doesn't match __mapper_args__.
    """
    def __init__(self, entity_type: str, expected: str, entity_id: str = None):
        self.entity_type = entity_type
        self.expected = expected
        self.entity_id = entity_id
        message = self._build_message()
        super().__init__(message)
    
    def _build_message(self) -> str:
        msg = [
            f"Database polymorphic identity mismatch!",
            "",
            f"❌ Found in database: entity_type = '{self.entity_type}'",
            f"✅ Expected by model:  entity_type = '{self.expected}'",
        ]
        
        if self.entity_id:
            msg.extend([
                "",
                f"📍 Entity ID: {self.entity_id}",
            ])
        
        msg.extend([
            "",
            "⚠️  REQUIRED FIX:",
            f"   UPDATE base_entity",
            f"   SET entity_type = '{self.expected}'",
            f"   WHERE entity_type = '{self.entity_type}';",
            "",
            "🔍 Root Cause:",
            "   - SQLAlchemy uses entity_type for polymorphic inheritance",
            f"   - Model expects: __mapper_args__ = {{\"polymorphic_identity\": \"{self.expected}\"}}",
            "   - Database has different value (case-sensitive)",
            "",
            "💡 Prevention:",
            "   - Always use capital first letter for entity types: 'Customer', 'Agent', 'Team'",
            "   - Validate entity_type before INSERT",
        ])
        
        return "\n".join(msg)


class EntityNotFoundError(PlantException):
    """
    Raised when entity is not found in database.
    
    Example:
        raise EntityNotFoundError(f"Skill {skill_id} not found")
    """
    pass


class DuplicateEntityError(PlantException):
    """
    Raised when attempting to create duplicate entity (unique constraint).
    
    Example:
        raise DuplicateEntityError(f"Skill with name '{name}' already exists")
    """
    pass


class ValidationError(PlantException):
    """
    Raised when entity validation fails.
    
    Example:
        raise ValidationError("JobRole must have at least one required skill")
    """
    pass


class ConstitutionalDriftError(PlantException):
    """
    Raised when entity drifts from constitutional principles.
    
    Example:
        raise ConstitutionalDriftError(
            f"Skill embedding stability {stability_score} < threshold {threshold}"
        )
    """
    pass


class SchemaEvolutionError(PlantException):
    """
    Raised when schema migration violates evolution rules.
    
    Example:
        raise SchemaEvolutionError("Breaking change without 3-gate approval")
    """
    pass


class CostGovernanceError(PlantException):
    """
    Raised when query would exceed customer budget.
    
    Example:
        raise CostGovernanceError(
            f"Query cost ${query_cost} exceeds budget ${remaining_budget}"
        )
    """
    pass


class PolicyEnforcementError(PlantException):
    """Raised when hook/policy enforcement denies an operation."""

    def __init__(self, message: str, *, reason: str | None = None, details: dict | None = None):
        super().__init__(message)
        self.reason = reason
        self.details = details or {}


class UsageLimitError(PlantException):
    """Raised when metering (trial caps, budgets) denies an operation."""

    def __init__(self, message: str, *, reason: str | None = None, details: dict | None = None):
        super().__init__(message)
        self.reason = reason
        self.details = details or {}
