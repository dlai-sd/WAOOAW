# User Story: [US-391-2] API Request Pipeline

**Story Issue**: #394

---

**As a** systems architect
**I want** centralized request validation and routing layer
**So that** all API calls go through consistent security checks

**Acceptance Criteria**:
- [ ] All requests validated against OpenAPI schema
- [ ] Automatic tenant isolation injection
- [ ] Request logging with correlation IDs
- [ ] Circuit breaker for Plant API (fail after 3 errors in 10s)
- [ ] Performance: Middleware overhead < 5ms
- [ ] Integration test demonstrates actual validation (not mocked)
- [ ] OpenAPI schema validation working (not commented out)
- [ ] Circuit breaker tested with failure scenarios
- [ ] Unit tests written with >80% coverage
- [ ] No TODO/pseudo-code in src/ files

**Priority**: Must Have
**RICE Score**: (5000 × 3 × 0.85) / 3 = 4250
**Effort**: XL

**Test Collaboration**:
- Edge Cases: Malformed JSON, schema violations, Plant API down
- Performance Target: P95 < 5ms middleware overhead

**Epic**: #391
