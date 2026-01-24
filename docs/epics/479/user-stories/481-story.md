# User Story: [US-479-1] Secure API Authentication

**Story Issue**: #481

---

**As a** CP/PP portal developer
**I want** OAuth2 JWT authentication for Plant API
**So that** all requests are authenticated and tenant-isolated

**Acceptance Criteria**:
- [ ] OAuth2 token endpoint returns valid JWT
- [ ] JWT includes tenant_id and user_id claims
- [ ] Token expiry = 1 hour with refresh capability
- [ ] Rate limit: 100 req/min per tenant
- [ ] Performance: Token validation < 10ms
- [ ] Unit tests written with >80% coverage
- [ ] pytest report shows passing tests
- [ ] No TODO/pseudo-code in src/ files
- [ ] All dependencies in requirements.txt

**Priority**: Must Have
**RICE Score**: (5000 × 3 × 0.9) / 2 = 6750
  - Reach: 5000 API calls/month
  - Impact: 3 (critical security)
  - Confidence: 90%
  - Effort: 2 person-weeks

**Effort**: L

**Test Collaboration**:
- Testable: Yes
- Edge Cases: Expired token, invalid signature, missing claims, replay attack
- Performance Target: P95 < 10ms

**Epic**: #479
