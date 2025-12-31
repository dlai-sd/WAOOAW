"""
Interaction Logger - Permanent history storage.

Logs all agent interactions to PostgreSQL for analytics and pattern detection.

Epic: 5.1 Agent Memory & Context
Story: 5.1.3 Interaction Logging (8 points)
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, Integer, cast
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.interaction_log import InteractionLog as InteractionLogModel


class InteractionLogger:
    """
    Logs interactions permanently to PostgreSQL.
    
    Responsibilities:
    - Permanent storage of all interactions
    - Analytics queries (success rates, patterns)
    - Failure detection
    - GDPR-compliant retention
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.retention_days = 730  # 2 years
    
    async def log_interaction(
        self,
        customer_id: str,
        agent_id: str,
        task_type: str,
        task_input: str,
        agent_output: str,
        rating: Optional[int] = None,
        duration_ms: Optional[int] = None,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> InteractionLogModel:
        """
        Log agent interaction to database.
        
        Args:
            customer_id: UUID of customer
            agent_id: Agent that handled task
            task_type: Type of task (e.g., 'social_post', 'email_campaign')
            task_input: Customer's input/request
            agent_output: Agent's response
            rating: Customer rating 1-5 stars
            duration_ms: Processing time in milliseconds
            success: Whether task succeeded
            metadata: Additional context (JSON)
            
        Returns:
            Created InteractionLogModel
        """
        log = InteractionLogModel(
            customer_id=uuid.UUID(customer_id),
            agent_id=agent_id,
            task_type=task_type,
            task_input=task_input,
            agent_output=agent_output,
            rating=rating,
            duration_ms=duration_ms,
            success=success,
            extra_data=metadata or {}
        )
        
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        
        return log
    
    async def get_history(
        self,
        customer_id: str,
        limit: int = 100,
        offset: int = 0,
        task_type: Optional[str] = None,
        success_only: bool = False
    ) -> List[InteractionLogModel]:
        """
        Get interaction history for customer.
        
        Args:
            customer_id: UUID of customer
            limit: Maximum records to return
            offset: Pagination offset
            task_type: Filter by task type
            success_only: Only successful interactions
            
        Returns:
            List of InteractionLogModel objects
        """
        query = select(InteractionLogModel).where(
            InteractionLogModel.customer_id == uuid.UUID(customer_id)
        )
        
        if task_type:
            query = query.where(InteractionLogModel.task_type == task_type)
        
        if success_only:
            query = query.where(InteractionLogModel.success == True)
        
        query = query.order_by(InteractionLogModel.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_analytics(
        self,
        customer_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get analytics summary.
        
        Args:
            customer_id: Filter by customer (optional)
            agent_id: Filter by agent (optional)
            days: Number of days to analyze
            
        Returns:
            Dict with analytics: total, success_rate, avg_rating, etc.
        """
        since = datetime.utcnow() - timedelta(days=days)
        
        query = select(
            func.count(InteractionLogModel.id).label('total'),
            func.sum(cast(InteractionLogModel.success, Integer)).label('successful'),
            func.avg(InteractionLogModel.rating).label('avg_rating'),
            func.avg(InteractionLogModel.duration_ms).label('avg_duration')
        ).where(InteractionLogModel.created_at >= since)
        
        if customer_id:
            query = query.where(InteractionLogModel.customer_id == uuid.UUID(customer_id))
        
        if agent_id:
            query = query.where(InteractionLogModel.agent_id == agent_id)
        
        result = await self.db.execute(query)
        row = result.one()
        
        total = row.total or 0
        successful = row.successful or 0
        
        return {
            "total_interactions": total,
            "successful_interactions": successful,
            "failed_interactions": total - successful,
            "success_rate": (successful / total * 100) if total > 0 else 0.0,
            "avg_rating": float(row.avg_rating) if row.avg_rating else 0.0,
            "avg_duration_ms": float(row.avg_duration) if row.avg_duration else 0.0,
            "period_days": days
        }
    
    async def detect_failure_patterns(
        self,
        days: int = 7,
        min_failures: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Detect recurring failure patterns.
        
        Identifies task types or agents with high failure rates.
        
        Args:
            days: Analysis window
            min_failures: Minimum failures to report
            
        Returns:
            List of failure patterns with: task_type, agent_id, failure_count, failure_rate
        """
        since = datetime.utcnow() - timedelta(days=days)
        
        query = select(
            InteractionLogModel.task_type,
            InteractionLogModel.agent_id,
            func.count(InteractionLogModel.id).label('total'),
            func.sum(cast(~InteractionLogModel.success, Integer)).label('failures')
        ).where(
            InteractionLogModel.created_at >= since
        ).group_by(
            InteractionLogModel.task_type,
            InteractionLogModel.agent_id
        ).having(
            func.sum(cast(~InteractionLogModel.success, Integer)) >= min_failures
        )
        
        result = await self.db.execute(query)
        rows = result.all()
        
        patterns = []
        for row in rows:
            total = row.total
            failures = row.failures
            failure_rate = (failures / total * 100) if total > 0 else 0
            
            patterns.append({
                "task_type": row.task_type,
                "agent_id": row.agent_id,
                "total_attempts": total,
                "failure_count": failures,
                "failure_rate": failure_rate,
                "recommendation": self._generate_failure_recommendation(
                    row.task_type, row.agent_id, failure_rate
                )
            })
        
        # Sort by failure rate descending
        patterns.sort(key=lambda x: x['failure_rate'], reverse=True)
        
        return patterns
    
    async def get_trending_tasks(
        self,
        days: int = 7,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get most popular task types.
        
        Args:
            days: Analysis window
            limit: Top N tasks
            
        Returns:
            List with: task_type, count, success_rate
        """
        since = datetime.utcnow() - timedelta(days=days)
        
        query = select(
            InteractionLogModel.task_type,
            func.count(InteractionLogModel.id).label('count'),
            func.avg(cast(InteractionLogModel.success, Integer)).label('success_rate')
        ).where(
            InteractionLogModel.created_at >= since
        ).group_by(
            InteractionLogModel.task_type
        ).order_by(
            func.count(InteractionLogModel.id).desc()
        ).limit(limit)
        
        result = await self.db.execute(query)
        rows = result.all()
        
        return [
            {
                "task_type": row.task_type,
                "count": row.count,
                "success_rate": float(row.success_rate * 100) if row.success_rate else 0.0
            }
            for row in rows
        ]
    
    async def cleanup_old_logs(self) -> int:
        """
        Delete logs older than retention period (GDPR compliance).
        
        Returns:
            Number of logs deleted
        """
        cutoff = datetime.utcnow() - timedelta(days=self.retention_days)
        
        result = await self.db.execute(
            InteractionLogModel.__table__.delete().where(
                InteractionLogModel.created_at < cutoff
            )
        )
        
        await self.db.commit()
        
        return result.rowcount
    
    def _generate_failure_recommendation(
        self,
        task_type: str,
        agent_id: str,
        failure_rate: float
    ) -> str:
        """Generate actionable recommendation for failure pattern."""
        if failure_rate > 50:
            return f"CRITICAL: {agent_id} failing >50% on {task_type}. Review agent prompt and knowledge base urgently."
        elif failure_rate > 30:
            return f"WARNING: {agent_id} struggling with {task_type}. Consider adding examples or documentation."
        else:
            return f"Monitor: {agent_id} has elevated failures on {task_type}. Review if trend continues."
