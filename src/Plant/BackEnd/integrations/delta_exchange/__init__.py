"""Delta Exchange India integration layer (MVP).

This package provides a minimal, testable HTTP client wrapper with:
- strict endpoint allowlist
- request signing helper
- retry/backoff
- redaction of secrets in errors

Execution is approval-gated elsewhere (hook plane).
"""
