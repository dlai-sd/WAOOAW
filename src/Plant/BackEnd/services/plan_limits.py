"""Plan limits loader.

Goal 4: resolve plan budget limits from the canonical template.

This is read-only and cached; enforcement logic lives in API/services.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional

import yaml


@lru_cache(maxsize=1)
def _financials() -> Dict:
    # services/ -> BackEnd/ -> Plant/ -> src/ -> repo_root/
    root = Path(__file__).resolve().parents[4]
    path = root / "main" / "Foundation" / "template" / "financials.yml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return raw


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
