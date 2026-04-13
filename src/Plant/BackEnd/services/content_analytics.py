"""Content analytics — reads performance_stats to recommend content improvements.

PLANT-DMA-2 E3-S1

Queries last 30 days of PerformanceStatModel for a hired agent,
identifies top-performing dimensions and posting times,
and returns structured recommendations for the content creator.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date, timedelta

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.performance_stat import PerformanceStatModel

logger = logging.getLogger(__name__)


class ContentRecommendation(BaseModel):
    """Structured recommendation for content creator prompts."""

    top_dimensions: list[str] = Field(
        default_factory=list,
        description="Content dimensions sorted by engagement rate (best first)",
    )
    best_posting_hours: list[int] = Field(
        default_factory=list,
        description="UTC hours that historically got highest impressions",
    )
    avg_engagement_rate: float = Field(
        0.0, description="Average engagement rate over the analysis window"
    )
    total_posts_analyzed: int = Field(0)
    recommendation_text: str = Field(
        "",
        description="Human-readable summary for injection into content prompts",
    )


async def get_content_recommendations(
    hired_instance_id: str,
    db: AsyncSession,
    lookback_days: int = 30,
) -> ContentRecommendation:
    """Analyze recent performance and return content recommendations.

    Returns empty recommendation if no data exists (never raises).
    Callers should pass a read-session for this read-only query path.
    """
    cutoff = date.today() - timedelta(days=lookback_days)

    stmt = (
        select(PerformanceStatModel)
        .where(
            PerformanceStatModel.hired_instance_id == hired_instance_id,
            PerformanceStatModel.platform_key == "youtube",
            PerformanceStatModel.stat_date >= cutoff,
        )
        .order_by(PerformanceStatModel.stat_date.desc())
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()

    if not rows:
        return ContentRecommendation(
            recommendation_text="No historical data yet — use default content strategy."
        )

    engagement_rates: list[float] = []
    impressions_by_hour: defaultdict[int, int] = defaultdict(int)
    total_posts = 0
    dimension_engagement: defaultdict[str, list[float]] = defaultdict(list)

    for row in rows:
        metrics = row.metrics or {}
        er = float(metrics.get("engagement_rate", 0.0) or 0.0)
        impressions = int(metrics.get("impressions", 0) or 0)
        posts = int(metrics.get("posts_published", 0) or 0)

        engagement_rates.append(er)
        total_posts += posts

        if row.collected_at:
            impressions_by_hour[row.collected_at.hour] += impressions

        dim = metrics.get("dimension")
        if dim:
            dimension_engagement[str(dim)].append(er)

    avg_er = sum(engagement_rates) / len(engagement_rates) if engagement_rates else 0.0
    best_hours = sorted(
        impressions_by_hour,
        key=impressions_by_hour.get,
        reverse=True,
    )[:3]
    ranked_dims = sorted(
        dimension_engagement,
        key=lambda dimension: (
            sum(dimension_engagement[dimension]) / len(dimension_engagement[dimension])
        ),
        reverse=True,
    )
    top_dims = ranked_dims[:5] if ranked_dims else []

    recommendation_text = (
        f"Based on {total_posts} posts over the last {lookback_days} days: "
        f"average engagement rate is {avg_er:.2%}. "
        f"Best posting hours (UTC): {best_hours}. "
        f"Focus on content that drives engagement"
        f"{' — prioritize ' + ', '.join(top_dims[:2]) if top_dims else ''}."
    )
    logger.info(
        "Generated content recommendations for hired_instance_id=%s with %s rows",
        hired_instance_id,
        len(rows),
    )

    return ContentRecommendation(
        top_dimensions=top_dims,
        best_posting_hours=best_hours,
        avg_engagement_rate=avg_er,
        total_posts_analyzed=total_posts,
        recommendation_text=recommendation_text,
    )


# Industry-standard posting time defaults by industry
_INDUSTRY_POSTING_DEFAULTS = {
    "marketing": [
        {"day": "Tuesday", "time": "10:00 AM", "reason": "Highest B2B engagement window"},
        {"day": "Thursday", "time": "2:00 PM", "reason": "Pre-weekend content consumption spike"},
        {"day": "Saturday", "time": "9:00 AM", "reason": "Weekend discovery browsing"},
    ],
    "education": [
        {"day": "Monday", "time": "8:00 AM", "reason": "Start-of-week study planning"},
        {"day": "Wednesday", "time": "4:00 PM", "reason": "After-school content peak"},
        {"day": "Sunday", "time": "7:00 PM", "reason": "Weekend revision session"},
    ],
    "sales": [
        {"day": "Tuesday", "time": "9:00 AM", "reason": "Decision-maker morning email window"},
        {"day": "Wednesday", "time": "11:00 AM", "reason": "Mid-week pipeline review"},
        {"day": "Thursday", "time": "3:00 PM", "reason": "Pre-Friday urgency window"},
    ],
}


async def get_posting_time_suggestions(
    industry: str,
    channel: str = "youtube",
    audience_profile: str = "",
) -> list[dict[str, str]]:
    """Return posting-time recommendations for the given industry and channel.
    
    Args:
        industry: Industry category (marketing, education, sales)
        channel: Platform channel (youtube, linkedin, etc.) - reserved for future use
        audience_profile: Audience description - reserved for future use
        
    Returns:
        List of posting-time recommendations with day, time, and reason.
        Falls back to marketing defaults for unknown industries.
    """
    defaults = _INDUSTRY_POSTING_DEFAULTS.get(
        industry.lower(),
        _INDUSTRY_POSTING_DEFAULTS["marketing"]
    )
    return defaults

