"""
WAOOAW Common Components: Resource Manager

Provides budget tracking, rate limiting, and resource allocation.

Usage:
    # Basic resource management:
    manager = ResourceManager(agent_id="wowvision-prime")
    
    # Set budget:
    manager.set_budget("llm_calls", limit=1000, period="daily")
    
    # Check budget:
    allowed = manager.check_budget("llm_calls", cost=1)
    
    # Consume budget:
    manager.consume_budget("llm_calls", cost=1)
    
    # Rate limiting:
    allowed = manager.check_rate_limit("api_calls", count=1)

Vision Compliance:
    ✅ Zero Risk: Budget limits prevent cost overruns
    ✅ Agentic: Per-agent resource isolation
    ✅ Simplicity: Auto-enforcement, transparent tracking
"""

import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class Budget:
    """
    Budget definition.
    
    Attributes:
        resource: Resource type (e.g., "llm_calls", "api_requests")
        limit: Maximum allowed in period
        period: Time period ("hourly", "daily", "monthly")
        consumed: Amount consumed in current period
        reset_at: When budget resets
    """
    resource: str
    limit: float
    period: str
    consumed: float = 0.0
    reset_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        if self.reset_at:
            result['reset_at'] = self.reset_at.isoformat()
        return result


@dataclass
class RateLimitWindow:
    """
    Sliding window for rate limiting.
    
    Attributes:
        resource: Resource type
        max_requests: Maximum requests in window
        window_seconds: Window size in seconds
        requests: Request timestamps (deque)
    """
    resource: str
    max_requests: int
    window_seconds: int
    requests: deque
    
    def __post_init__(self):
        if not isinstance(self.requests, deque):
            self.requests = deque(self.requests, maxlen=self.max_requests)


class ResourceManager:
    """
    Budget tracking, rate limiting, and resource allocation.
    
    Features:
    - Budget management (hourly/daily/monthly)
    - Rate limiting (sliding window)
    - Resource quotas
    - Cost tracking
    - Auto-reset on period end
    - Alerts on threshold
    
    Example:
        manager = ResourceManager(
            agent_id="wowvision-prime",
            db_connection=db
        )
        
        # Set budget:
        manager.set_budget("llm_calls", limit=1000, period="daily")
        
        # Check budget:
        allowed = manager.check_budget("llm_calls", cost=1)
        
        # Consume budget:
        manager.consume_budget("llm_calls", cost=1)
        
        # Rate limiting:
        manager.set_rate_limit("api_calls", max_requests=100, window_seconds=60)
        allowed = manager.check_rate_limit("api_calls")
        
        # Get usage:
        usage = manager.get_usage("llm_calls")
    """
    
    def __init__(
        self,
        agent_id: str,
        db_connection: Optional[Any] = None,
        alert_threshold: float = 0.8
    ):
        """
        Initialize resource manager.
        
        Args:
            agent_id: Unique agent identifier
            db_connection: Database connection (optional)
            alert_threshold: Alert when usage exceeds this fraction (0.8 = 80%)
        """
        self.agent_id = agent_id
        self.db_connection = db_connection
        self.alert_threshold = alert_threshold
        
        self._budgets: Dict[str, Budget] = {}
        self._rate_limits: Dict[str, RateLimitWindow] = {}
        self._usage_history: List[Dict[str, Any]] = []
        
        # Load budgets from DB
        self._load_from_db()
        
        logger.info(
            f"ResourceManager initialized for agent '{agent_id}' "
            f"(alert_threshold={alert_threshold})"
        )
    
    # Budget Management
    
    def set_budget(
        self,
        resource: str,
        limit: float,
        period: str = "daily"
    ):
        """
        Set budget for resource.
        
        Args:
            resource: Resource type (e.g., "llm_calls")
            limit: Maximum allowed in period
            period: "hourly", "daily", or "monthly"
        """
        if period not in ["hourly", "daily", "monthly"]:
            raise ValueError(f"Invalid period: {period}")
        
        reset_at = self._calculate_reset_time(period)
        
        budget = Budget(
            resource=resource,
            limit=limit,
            period=period,
            consumed=0.0,
            reset_at=reset_at
        )
        
        self._budgets[resource] = budget
        
        # Persist to DB
        if self.db_connection:
            self._persist_budget_to_db(budget)
        
        logger.info(f"Budget set: {resource} = {limit}/{period}")
    
    def check_budget(
        self,
        resource: str,
        cost: float = 1.0
    ) -> bool:
        """
        Check if resource usage is within budget.
        
        Args:
            resource: Resource type
            cost: Cost of operation (default: 1.0)
            
        Returns:
            True if within budget
        """
        budget = self._budgets.get(resource)
        
        if not budget:
            # No budget set = unlimited
            return True
        
        # Check if budget needs reset
        self._maybe_reset_budget(budget)
        
        # Check if operation would exceed budget
        would_exceed = (budget.consumed + cost) > budget.limit
        
        if would_exceed:
            logger.warning(
                f"Budget exceeded: {resource} "
                f"({budget.consumed + cost}/{budget.limit})"
            )
        
        return not would_exceed
    
    def consume_budget(
        self,
        resource: str,
        cost: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Consume budget for resource.
        
        Args:
            resource: Resource type
            cost: Cost of operation
            metadata: Optional metadata (e.g., operation details)
            
        Returns:
            True if consumption successful
        """
        if not self.check_budget(resource, cost):
            return False
        
        budget = self._budgets.get(resource)
        
        if budget:
            budget.consumed += cost
            
            # Check alert threshold
            usage_fraction = budget.consumed / budget.limit
            if usage_fraction >= self.alert_threshold:
                logger.warning(
                    f"Budget alert: {resource} at {usage_fraction:.0%} "
                    f"({budget.consumed}/{budget.limit})"
                )
            
            # Persist to DB
            if self.db_connection:
                self._persist_budget_to_db(budget)
        
        # Track usage history
        self._usage_history.append({
            'timestamp': datetime.now(),
            'resource': resource,
            'cost': cost,
            'metadata': metadata
        })
        
        logger.debug(f"Budget consumed: {resource} -{cost} ({budget.consumed}/{budget.limit})")
        return True
    
    def get_budget(self, resource: str) -> Optional[Budget]:
        """
        Get budget for resource.
        
        Args:
            resource: Resource type
            
        Returns:
            Budget object or None
        """
        budget = self._budgets.get(resource)
        
        if budget:
            self._maybe_reset_budget(budget)
        
        return budget
    
    def get_remaining_budget(self, resource: str) -> Optional[float]:
        """
        Get remaining budget.
        
        Args:
            resource: Resource type
            
        Returns:
            Remaining budget or None if no budget set
        """
        budget = self.get_budget(resource)
        
        if not budget:
            return None
        
        return max(0, budget.limit - budget.consumed)
    
    def reset_budget(self, resource: str):
        """
        Manually reset budget.
        
        Args:
            resource: Resource type
        """
        budget = self._budgets.get(resource)
        
        if not budget:
            return
        
        budget.consumed = 0.0
        budget.reset_at = self._calculate_reset_time(budget.period)
        
        if self.db_connection:
            self._persist_budget_to_db(budget)
        
        logger.info(f"Budget reset: {resource}")
    
    # Rate Limiting
    
    def set_rate_limit(
        self,
        resource: str,
        max_requests: int,
        window_seconds: int = 60
    ):
        """
        Set rate limit for resource.
        
        Args:
            resource: Resource type
            max_requests: Maximum requests in window
            window_seconds: Window size in seconds (default: 60)
        """
        window = RateLimitWindow(
            resource=resource,
            max_requests=max_requests,
            window_seconds=window_seconds,
            requests=deque(maxlen=max_requests)
        )
        
        self._rate_limits[resource] = window
        
        logger.info(f"Rate limit set: {resource} = {max_requests}/{window_seconds}s")
    
    def check_rate_limit(
        self,
        resource: str,
        count: int = 1
    ) -> bool:
        """
        Check if request is within rate limit.
        
        Args:
            resource: Resource type
            count: Number of requests (default: 1)
            
        Returns:
            True if within rate limit
        """
        window = self._rate_limits.get(resource)
        
        if not window:
            # No rate limit = unlimited
            return True
        
        now = time.time()
        
        # Remove requests outside window
        cutoff = now - window.window_seconds
        while window.requests and window.requests[0] < cutoff:
            window.requests.popleft()
        
        # Check if adding count would exceed limit
        current_count = len(window.requests)
        would_exceed = (current_count + count) > window.max_requests
        
        if would_exceed:
            logger.warning(
                f"Rate limit exceeded: {resource} "
                f"({current_count + count}/{window.max_requests} in {window.window_seconds}s)"
            )
        
        return not would_exceed
    
    def record_request(self, resource: str, count: int = 1):
        """
        Record request for rate limiting.
        
        Args:
            resource: Resource type
            count: Number of requests to record
        """
        if not self.check_rate_limit(resource, count):
            raise RuntimeError(f"Rate limit exceeded for {resource}")
        
        window = self._rate_limits.get(resource)
        
        if window:
            now = time.time()
            for _ in range(count):
                window.requests.append(now)
            
            logger.debug(f"Request recorded: {resource} ({len(window.requests)}/{window.max_requests})")
    
    def get_rate_limit_status(self, resource: str) -> Dict[str, Any]:
        """
        Get rate limit status.
        
        Args:
            resource: Resource type
            
        Returns:
            Dict with current count, max, window, etc.
        """
        window = self._rate_limits.get(resource)
        
        if not window:
            return {'error': 'No rate limit set'}
        
        now = time.time()
        cutoff = now - window.window_seconds
        
        # Remove old requests
        while window.requests and window.requests[0] < cutoff:
            window.requests.popleft()
        
        return {
            'resource': resource,
            'current_count': len(window.requests),
            'max_requests': window.max_requests,
            'window_seconds': window.window_seconds,
            'remaining': window.max_requests - len(window.requests)
        }
    
    # Usage Tracking
    
    def get_usage(
        self,
        resource: Optional[str] = None,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get usage history.
        
        Args:
            resource: Filter by resource (optional)
            hours: Last N hours (default: 24)
            
        Returns:
            List of usage records
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        
        history = self._usage_history
        
        if resource:
            history = [h for h in history if h['resource'] == resource]
        
        history = [h for h in history if h['timestamp'] > cutoff]
        
        return history
    
    def get_usage_stats(self, resource: str) -> Dict[str, Any]:
        """
        Get usage statistics for resource.
        
        Args:
            resource: Resource type
            
        Returns:
            Dict with total, average, peak, etc.
        """
        usage = self.get_usage(resource)
        
        if not usage:
            return {'error': 'No usage data'}
        
        costs = [u['cost'] for u in usage]
        
        return {
            'resource': resource,
            'total_cost': sum(costs),
            'average_cost': sum(costs) / len(costs),
            'peak_cost': max(costs),
            'request_count': len(usage),
            'period_hours': 24
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get resource manager statistics.
        
        Returns:
            Dict with budget count, rate limit count, usage count, etc.
        """
        return {
            'agent_id': self.agent_id,
            'budget_count': len(self._budgets),
            'rate_limit_count': len(self._rate_limits),
            'usage_record_count': len(self._usage_history),
            'alert_threshold': self.alert_threshold
        }
    
    # Private methods
    
    def _calculate_reset_time(self, period: str) -> datetime:
        """Calculate next reset time based on period."""
        now = datetime.now()
        
        if period == "hourly":
            return now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        elif period == "daily":
            return now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        elif period == "monthly":
            # Reset on first day of next month
            if now.month == 12:
                return now.replace(year=now.year+1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                return now.replace(month=now.month+1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            raise ValueError(f"Invalid period: {period}")
    
    def _maybe_reset_budget(self, budget: Budget):
        """Reset budget if period has elapsed."""
        if budget.reset_at and datetime.now() >= budget.reset_at:
            logger.info(f"Budget auto-reset: {budget.resource} (period={budget.period})")
            budget.consumed = 0.0
            budget.reset_at = self._calculate_reset_time(budget.period)
            
            if self.db_connection:
                self._persist_budget_to_db(budget)
    
    def _load_from_db(self):
        """Load budgets from database."""
        if not self.db_connection:
            return
        
        try:
            import json
            cursor = self.db_connection.cursor()
            
            cursor.execute(
                """
                SELECT resource, budget_limit, period, consumed, reset_at
                FROM resource_budgets
                WHERE agent_id = %s
                """,
                (self.agent_id,)
            )
            
            for row in cursor.fetchall():
                resource, limit, period, consumed, reset_at = row
                
                budget = Budget(
                    resource=resource,
                    limit=limit,
                    period=period,
                    consumed=consumed,
                    reset_at=reset_at
                )
                
                self._budgets[resource] = budget
            
            cursor.close()
            
        except Exception as e:
            logger.error(f"Failed to load budgets from database: {e}")
    
    def _persist_budget_to_db(self, budget: Budget):
        """Persist budget to database."""
        if not self.db_connection:
            return
        
        try:
            cursor = self.db_connection.cursor()
            
            cursor.execute(
                """
                INSERT INTO resource_budgets 
                (agent_id, resource, budget_limit, period, consumed, reset_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (agent_id, resource)
                DO UPDATE SET
                    budget_limit = EXCLUDED.budget_limit,
                    period = EXCLUDED.period,
                    consumed = EXCLUDED.consumed,
                    reset_at = EXCLUDED.reset_at,
                    updated_at = EXCLUDED.updated_at
                """,
                (self.agent_id, budget.resource, budget.limit, budget.period, 
                 budget.consumed, budget.reset_at, datetime.now())
            )
            
            self.db_connection.commit()
            cursor.close()
            
        except Exception as e:
            logger.error(f"Failed to persist budget to database: {e}")
