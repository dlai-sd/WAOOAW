"""Plan limits loader.

Goal 4: resolve plan budget limits from the canonical template.

This is read-only and cached; enforcement logic lives in API/services.
"""

from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path
from typing import Dict, Optional

import yaml


@lru_cache(maxsize=1)
def _financials() -> Dict:
    configured_path = os.getenv("FINANCIALS_YAML_PATH") or os.getenv("WAOOAW_FINANCIALS_PATH")
    if configured_path:
        path = Path(configured_path)
        if path.is_file():
            return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    # Dev fallback: when running from the repo checkout (non-container).
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "main" / "Foundation" / "template" / "financials.yml"
        if candidate.is_file():
            return yaml.safe_load(candidate.read_text(encoding="utf-8")) or {}

    return {}


def get_query_budget_monthly_usd(plan_id: str) -> Optional[float]:
    data = _financials()
    tiers = (
        data.get("iteration_3", {})
        .get("subscription_plan_limits", {})
        .get("plan_tiers", {})
    )

    for _tier_name, tier in (tiers or {}).items():
        if (tier or {}).get("plan_id") == plan_id:
            limits = (tier or {}).get("limits") or {}
            budget = limits.get("query_budget_monthly_usd")
            return float(budget) if budget is not None else None

    return None
