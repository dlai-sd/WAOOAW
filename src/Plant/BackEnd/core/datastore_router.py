"""
DatastoreRouter — INFRA-ROUTING-1 policy-driven data path selector.

Reads DATA_ROUTER_MODE from Settings and provides routing helpers
that service code calls instead of raw SQLAlchemy sessions.

Modes:
  sql          — 100% SQLAlchemy (default, safe rollback point)
  dual_write   — write SQL + async Firestore; reads from SQL
  shadow_read  — dual_write + background Firestore read comparison
  firestore    — reads+writes to Firestore only for routed entities

Usage:
  router = DatastoreRouter()
  if router.reads_from_firestore("agent_performance"):
      return await firestore_client.get_agent_performance(hired_agent_id)
  # else fall through to SQL path
"""

from __future__ import annotations

import logging

import core.config as _config
from core.logging import PiiMaskingFilter

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())

# Collections that are eligible for Firestore routing.
# Transactional entities (customer, hired_agent, deliverable, payment) are
# NOT in this set — they are SQL-only forever.
_ROUTABLE_COLLECTIONS = frozenset(
    {
        "agent_performance",   # PerformanceStat model → performance_stats table
        "agent_availability",  # HiredAgent status column (read-only Firestore path)
        "exchange_credentials",   # TRADER-FULL-1 S2
        "trade_results",          # TRADER-FULL-1 S5
    }
)


class DatastoreRouter:
    """
    Stateless routing policy helper.  Instantiate per-request or as a singleton.
    Reads DATA_ROUTER_MODE from settings at call time (no caching) so a
    Cloud Run env-var flip takes effect on the next request with no restart.
    """

    def __init__(self) -> None:
        self._mode = _config.settings.data_router_mode

    @property
    def mode(self) -> str:
        # Re-read via module attribute each time so monkeypatch and env-var
        # hot-reload both work — _config.settings is re-bound by tests and by
        # Cloud Run env-var flips; a direct name binding would stay stale.
        return _config.settings.data_router_mode

    def is_routable(self, collection: str) -> bool:
        """True if this collection participates in the routing policy."""
        return collection in _ROUTABLE_COLLECTIONS

    def reads_from_firestore(self, collection: str) -> bool:
        """True when the read path for this collection should use Firestore."""
        return self.mode == "firestore" and self.is_routable(collection)

    def writes_to_firestore(self, collection: str) -> bool:
        """True when a secondary Firestore write should be triggered."""
        return self.mode in {"dual_write", "shadow_read", "firestore"} and self.is_routable(collection)

    def shadow_mode(self, collection: str) -> bool:
        """True when background read comparison should be triggered."""
        return self.mode == "shadow_read" and self.is_routable(collection)


# Module-level singleton — callers import and use directly.
datastore_router = DatastoreRouter()
