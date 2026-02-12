"""Usage Analytics Dashboard API - AGP2-PP-3.5

PP admin API for analyzing usage patterns, token consumption, cost projections,
and identifying heavy users for capacity planning and billing analysis.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from typing import List, Optional, Literal
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from api.deps import get_authorization_header
from api.security import require_admin
from clients.plant_client import PlantAPIClient, get_plant_client


router = APIRouter(prefix="/usage-analytics", tags=["usage-analytics"])


class TokenUsageSummary(BaseModel):
    """Token usage summary for a time period."""
    
    customer_id: str
    customer_name: Optional[str] = None
    
    # Token metrics
    total_tokens: int = 0
    avg_tokens_per_day: float = 0.0
    peak_tokens_day: int = 0
    peak_date: Optional[datetime] = None
    
    # Cost metrics
    total_cost_usd: float = 0.0
    avg_cost_per_day: float = 0.0
    projected_monthly_cost: float = 0.0
    
    # Activity metrics
    total_requests: int = 0
    unique_agents: int = 0
    active_days: int = 0
    
    # Trial info
    trial_mode: bool = False
    trial_ends_at: Optional[datetime] = None


class PlatformUsageBreakdown(BaseModel):
    """Usage breakdown by platform/service."""
    
    platform: str  # "instagram", "delta_exchange", "openai_gpt4", etc.
    request_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    avg_latency_ms: Optional[float] = None


class AgentTypeUsageBreakdown(BaseModel):
    """Usage breakdown by agent type."""
    
    agent_id: str
    agent_name: Optional[str]
    instance_count: int = 0  # How many instances of this agent
    request_count: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    active_instances: int = 0


class UsageTrend(BaseModel):
    """Daily usage trend data point."""
    
    date: datetime
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    request_count: int = 0
    unique_customers: int = 0
    error_rate: float = 0.0


class UsageAnalyticsDashboard(BaseModel):
    """Complete usage analytics dashboard."""
    
    # Time period
    period_start: datetime
    period_end: datetime
    period_days: int
    
    # Aggregate metrics
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    total_requests: int = 0
    unique_customers: int = 0
    
    # Growth metrics
    daily_avg_tokens: float = 0.0
    daily_avg_cost: float = 0.0
    projected_monthly_cost: float = 0.0
    
    # Top customers by usage
    top_customers: List[TokenUsageSummary] = Field(default_factory=list)
    
    # Usage by platform
    platform_breakdown: List[PlatformUsageBreakdown] = Field(default_factory=list)
    
    # Usage by agent type
    agent_type_breakdown: List[AgentTypeUsageBreakdown] = Field(default_factory=list)
    
    # Trend data
    daily_trends: List[UsageTrend] = Field(default_factory=list)


class HeavyUserAlert(BaseModel):
    """Alert for heavy usage customers."""
    
    customer_id: str
    customer_name: Optional[str]
    
    alert_type: Literal["high_usage", "rapid_growth", "cost_threshold", "error_spike"]
    severity: Literal["info", "warning", "critical"]
    
    # Metrics
    current_usage: float
    threshold: float
    over_threshold_by: float
    
    # Context
    period: str  # "day", "week", "month"
    message: str
    suggested_action: Optional[str]
    
    detected_at: datetime


class CostProjection(BaseModel):
    """Cost projection for budgeting."""
    
    current_daily_avg: float
    projected_monthly: float
    projected_quarterly: float
    projected_yearly: float
    
    # Trends
    trend_direction: Literal["increasing", "stable", "decreasing"]
    trend_percentage: float  # +15% increasing
    
    # Breakdown
    trial_users_cost: float = 0.0
    paid_users_cost: float = 0.0
    
    # Capacity warning
    at_risk_of_budget_overrun: bool = False
    budget_limit: Optional[float] = None


@router.get(
    "/dashboard",
    response_model=UsageAnalyticsDashboard,
    summary="Get usage analytics dashboard"
)
async def get_usage_analytics_dashboard(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    top_n: int = Query(10, ge=1, le=100, description="Number of top customers to show"),
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Get comprehensive usage analytics dashboard.
    
    **Provides**:
    - Aggregate token and cost metrics
    - Top customers by usage
    - Platform/service breakdown
    - Agent type breakdown
    - Daily trend data
    
    **Use Cases**:
    - Monitor platform usage growth
    - Identify heavy users for upsell
    - Capacity planning
    - Cost projection
    - Budget management
    """
    
    try:
        from datetime import timezone
        now = datetime.now(timezone.utc)
        period_start = now - timedelta(days=days)
        
        # In production, query usage_events table and aggregate
        
        dashboard = UsageAnalyticsDashboard(
            period_start=period_start,
            period_end=now,
            period_days=days,
            total_tokens=0,
            total_cost_usd=0.0,
            total_requests=0,
            unique_customers=0,
            daily_avg_tokens=0.0,
            daily_avg_cost=0.0,
            projected_monthly_cost=0.0,
            top_customers=[],
            platform_breakdown=[],
            agent_type_breakdown=[],
            daily_trends=[],
        )
        
        return dashboard
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch usage analytics: {str(e)}")


@router.get(
    "/heavy-users",
    response_model=List[TokenUsageSummary],
    summary="Get heavy usage customers"
)
async def get_heavy_users(
    days: int = Query(30, ge=1, le=365),
    min_tokens: int = Query(100000, ge=0, description="Minimum total tokens"),
    min_cost_usd: float = Query(None, ge=0, description="Minimum total cost"),
    limit: int = Query(20, ge=1, le=100),
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Get customers with heavy token/cost usage.
    
    **Filters**:
    - `min_tokens`: Customers with ≥ this many tokens
    - `min_cost_usd`: Customers with ≥ this much cost
    - `days`: Time period to analyze
    
    **Use Cases**:
    - Identify customers for upsell to higher plans
    - Monitor for abuse/anomalies
    - Account management outreach
    """
    
    try:
        # In production, query and aggregate usage_events
        return []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch heavy users: {str(e)}")


@router.get(
    "/alerts",
    response_model=List[HeavyUserAlert],
    summary="Get usage alerts"
)
async def get_usage_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity: info, warning, critical"),
    alert_type: Optional[str] = Query(None),
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Get active usage alerts for heavy users or anomalies.
    
    **Alert Types**:
    - `high_usage`: Usage significantly above average
    - `rapid_growth`: Usage growing >50% week-over-week
    - `cost_threshold`: Cost exceeded predefined threshold
    - `error_spike`: High error rate indicating issues
    
    **Severity Levels**:
    - `info`: FYI, no action needed
    - `warning`: Monitor, may need follow-up
    - `critical`: Immediate attention required
    """
    
    try:
        # In production, calculate alerts based on usage patterns
        alerts: List[HeavyUserAlert] = []
        
        # Filter by severity and type
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if alert_type:
            alerts = [a for a in alerts if a.alert_type == alert_type]
        
        return alerts
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch alerts: {str(e)}")


@router.get(
    "/customer/{customer_id}",
    response_model=TokenUsageSummary,
    summary="Get usage for specific customer"
)
async def get_customer_usage(
    customer_id: str,
    days: int = Query(30, ge=1, le=365),
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Get detailed usage analytics for a specific customer.
    
    **Includes**:
    - Token and cost totals
    - Daily averages
    - Peak usage day
    - Cost projections
    - Activity patterns
    """
    
    try:
        from datetime import timezone
        now = datetime.now(timezone.utc)
        period_start = now - timedelta(days=days)
        
        # In production, query usage_events for this customer
        
        return TokenUsageSummary(
            customer_id=customer_id,
            customer_name=None,
            total_tokens=0,
            avg_tokens_per_day=0.0,
            peak_tokens_day=0,
            peak_date=None,
            total_cost_usd=0.0,
            avg_cost_per_day=0.0,
            projected_monthly_cost=0.0,
            total_requests=0,
            unique_agents=0,
            active_days=0,
            trial_mode=False,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch customer usage: {str(e)}")


@router.get(
    "/cost-projection",
    response_model=CostProjection,
    summary="Get cost projections"
)
async def get_cost_projection(
    based_on_days: int = Query(30, ge=7, le=90, description="Base projection on this many days"),
    budget_limit: Optional[float] = Query(None, ge=0, description="Monthly budget limit for warnings"),
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Get cost projections for budgeting and planning.
    
    **Calculates**:
    - Current daily average cost
    - Projected monthly, quarterly, yearly costs
    - Trend direction and percentage
    - Trial vs paid user cost breakdown
    - Budget overrun warnings
    
    **Use Cases**:
    - Financial planning
    - Budget monitoring
    - Capacity planning
    - Provider cost management
    """
    
    try:
        # In production, calculate from usage_events
        
        # Calculate daily average from recent period
        current_daily_avg = 0.0
        projected_monthly = current_daily_avg * 30
        projected_quarterly = current_daily_avg * 90
        projected_yearly = current_daily_avg * 365
        
        # Determine trend
        # Compare recent week vs previous week
        trend_direction: Literal["increasing", "stable", "decreasing"] = "stable"
        trend_percentage = 0.0
        
        # Budget warning
        at_risk = False
        if budget_limit and projected_monthly > budget_limit:
            at_risk = True
        
        return CostProjection(
            current_daily_avg=current_daily_avg,
            projected_monthly=projected_monthly,
            projected_quarterly=projected_quarterly,
            projected_yearly=projected_yearly,
            trend_direction=trend_direction,
            trend_percentage=trend_percentage,
            trial_users_cost=0.0,
            paid_users_cost=0.0,
            at_risk_of_budget_overrun=at_risk,
            budget_limit=budget_limit,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate cost projection: {str(e)}")


@router.get(
    "/export/csv",
    summary="Export usage data to CSV"
)
async def export_usage_csv(
    start_date: datetime = Query(..., description="Start date for export"),
    end_date: datetime = Query(..., description="End date for export"),
    customer_id: Optional[str] = Query(None, description="Export for specific customer"),
    group_by: str = Query("day", description="Grouping: day, week, month, customer, agent"),
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Export usage data to CSV for offline analysis.
    
    **Grouping Options**:
    - `day`: Daily aggregation
    - `week`: Weekly aggregation
    - `month`: Monthly aggregation
    - `customer`: Per customer totals
    - `agent`: Per agent type totals
    
    **CSV Columns** (day grouping):
    - date
    - customer_id
    - agent_id
    - total_tokens
    - total_cost_usd
    - request_count
    - success_count
    - error_count
    """
    
    try:
        # In production:
        # 1. Query usage_events with filters
        # 2. Aggregate by group_by
        # 3. Generate CSV
        # 4. Return as downloadable file
        
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write headers
        if group_by == "day":
            writer.writerow(["date", "customer_id", "agent_id", "total_tokens", "total_cost_usd", "request_count", "success_count", "error_count"])
        elif group_by == "customer":
            writer.writerow(["customer_id", "customer_name", "total_tokens", "total_cost_usd", "request_count", "unique_agents", "active_days"])
        elif group_by == "agent":
            writer.writerow(["agent_id", "agent_name", "instance_count", "total_tokens", "total_cost_usd", "request_count"])
        
        # Write data (placeholder)
        # writer.writerow([...])
        
        csv_content = output.getvalue()
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=usage_export_{start_date.date()}_{end_date.date()}.csv"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export CSV: {str(e)}")


@router.get(
    "/platform-costs",
    summary="Get cost breakdown by platform"
)
async def get_platform_costs(
    days: int = Query(30, ge=1, le=365),
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Get cost breakdown by external platform/service.
    
    **Shows**:
    - OpenAI API costs (GPT-4, GPT-3.5)
    - Social platform costs (if any)
    - Delta Exchange API costs (if any)
    - Total external service costs
    
    **Use Case**:
    - Understand provider cost allocation
    - Optimize service selection
    - Negotiate better rates
    """
    
    try:
        # In production, aggregate usage_events by platform
        
        platform_costs: List[PlatformUsageBreakdown] = []
        
        total_cost = sum(p.total_cost_usd for p in platform_costs)
        
        return {
            "period_days": days,
            "total_cost_usd": total_cost,
            "platforms": platform_costs,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch platform costs: {str(e)}")


@router.get(
    "/trial-conversion-analysis",
    summary="Analyze trial user usage patterns"
)
async def analyze_trial_usage(
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Analyze usage patterns of trial users for conversion insights.
    
    **Provides**:
    - Average usage by trial users
    - Correlation between usage and conversion
    - Engaged vs unengaged trial users
    - Optimal conversion timing insights
    
    **Use Cases**:
    - Improve trial-to-paid conversion
    - Identify engagement patterns
    - Optimize trial limits
    """
    
    try:
        # In production, analyze trial user behavior
        
        return {
            "total_trial_users": 0,
            "active_trial_users": 0,
            "avg_usage_per_trial_user": 0.0,
            "high_engagement_trials": 0,
            "low_engagement_trials": 0,
            "conversion_rate": 0.0,
            "high_usage_correlation_with_conversion": 0.0,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze trial usage: {str(e)}")
