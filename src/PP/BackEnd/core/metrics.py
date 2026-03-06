"""PP BackEnd — optional Prometheus metrics.

All imports guarded with try/except so the app starts without prometheus-client.
Counters and histograms are no-op stubs when prometheus-client is not installed.
"""
from __future__ import annotations

_PROM_AVAILABLE = False

try:
    from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
    _PROM_AVAILABLE = True
except ImportError:
    pass

if _PROM_AVAILABLE:
    pp_login_counter = Counter(
        "pp_login_total",
        "PP admin login attempts",
        ["outcome"],             # outcome: success | failure
    )
    pp_agent_ops_counter = Counter(
        "pp_agent_ops_total",
        "PP agent CRUD operations",
        ["operation", "outcome"],  # operation: create|update|status; outcome: success|failure
    )
    pp_approval_counter = Counter(
        "pp_approval_minted_total",
        "PP approvals minted",
        ["outcome"],
    )
    pp_request_latency = Histogram(
        "pp_request_duration_seconds",
        "PP request latency",
        ["route"],
    )
else:
    # No-op stubs so import never fails
    class _Noop:
        def labels(self, **_): return self
        def inc(self): pass
        def observe(self, _): pass

    pp_login_counter = _Noop()         # type: ignore[assignment]
    pp_agent_ops_counter = _Noop()     # type: ignore[assignment]
    pp_approval_counter = _Noop()      # type: ignore[assignment]
    pp_request_latency = _Noop()       # type: ignore[assignment]


def get_metrics_response():
    """Return (body_bytes, content_type) for /metrics endpoint."""
    if not _PROM_AVAILABLE:
        return None, None
    return generate_latest(), CONTENT_TYPE_LATEST
