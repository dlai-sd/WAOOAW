"""
Message Audit Trail - Compliance and Tracking

Provides persistent audit logging for all agent communications:
- Store messages in PostgreSQL for compliance
- Query interface for audit logs
- Retention policies (GDPR compliance)
- Message search and filtering
- Audit statistics and reporting
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, String, DateTime, Text, Integer, Index, select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from waooaw.communication.messaging import Message, MessageStatus, MessageType


Base = declarative_base()


class MessageAuditLog(Base):
    """Database model for message audit trail."""
    
    __tablename__ = "message_audit_log"
    
    message_id = Column(String(36), primary_key=True)
    from_agent = Column(String(100), nullable=False, index=True)
    to_agent = Column(String(100), nullable=False, index=True)
    message_type = Column(String(20), nullable=False)
    priority = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, index=True)
    correlation_id = Column(String(36), nullable=True, index=True)
    reply_to = Column(String(100), nullable=True)
    payload_json = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    delivered_at = Column(DateTime, nullable=True)
    ttl_seconds = Column(Integer, nullable=False)
    retry_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    __table_args__ = (
        Index('idx_timestamp_status', 'timestamp', 'status'),
        Index('idx_correlation', 'correlation_id'),
        Index('idx_agents', 'from_agent', 'to_agent'),
    )


class RetentionPolicy(str, Enum):
    """Data retention policies."""
    DAYS_30 = "30_days"  # Keep for 30 days
    DAYS_90 = "90_days"  # Keep for 90 days (default)
    DAYS_365 = "365_days"  # Keep for 1 year
    FOREVER = "forever"  # Never delete


@dataclass
class AuditQuery:
    """Query parameters for audit log search."""
    
    from_agent: Optional[str] = None
    to_agent: Optional[str] = None
    message_type: Optional[MessageType] = None
    status: Optional[MessageStatus] = None
    correlation_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = 100
    offset: int = 0


@dataclass
class AuditStatistics:
    """Statistics about message audit trail."""
    
    total_messages: int = 0
    messages_by_status: Dict[str, int] = field(default_factory=dict)
    messages_by_type: Dict[str, int] = field(default_factory=dict)
    top_senders: List[Dict[str, Any]] = field(default_factory=list)
    top_receivers: List[Dict[str, Any]] = field(default_factory=list)
    avg_delivery_time_seconds: float = 0.0
    error_rate: float = 0.0


class MessageAuditTrail:
    """
    Message audit trail for compliance tracking.
    
    Stores all agent communications in PostgreSQL with:
    - Full message history
    - Query interface
    - Retention policies
    - Statistics and reporting
    """
    
    def __init__(
        self,
        database_url: str,
        retention_policy: RetentionPolicy = RetentionPolicy.DAYS_90,
    ):
        """
        Initialize audit trail.
        
        Args:
            database_url: PostgreSQL connection URL
            retention_policy: How long to keep messages
        """
        self.database_url = database_url
        self.retention_policy = retention_policy
        
        # Create async engine (SQLite doesn't support pooling parameters)
        engine_args = {"echo": False}
        if not database_url.startswith("sqlite"):
            engine_args.update({"pool_size": 5, "max_overflow": 10})
        
        self.engine = create_async_engine(database_url, **engine_args)
        
        # Create session maker
        self.async_session = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        self._initialized = False
    
    async def initialize(self):
        """Initialize database tables."""
        if self._initialized:
            return
        
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        self._initialized = True
    
    async def log_message(self, message: Message):
        """
        Log message to audit trail.
        
        Args:
            message: Message to log
        """
        if not self._initialized:
            await self.initialize()
        
        async with self.async_session() as session:
            # Convert payload to JSON string
            import json
            payload_json = json.dumps(message.payload)
            
            # Create audit log entry
            audit_log = MessageAuditLog(
                message_id=message.message_id,
                from_agent=message.from_agent,
                to_agent=message.to_agent,
                message_type=message.message_type.value,
                priority=message.priority.value,
                status=message.status.value,
                correlation_id=message.correlation_id,
                reply_to=message.reply_to,
                payload_json=payload_json,
                timestamp=datetime.fromisoformat(message.timestamp),
                ttl_seconds=message.ttl_seconds,
                retry_count=message.retry_count,
            )
            
            session.add(audit_log)
            await session.commit()
    
    async def update_message_status(
        self,
        message_id: str,
        status: MessageStatus,
        delivered_at: Optional[datetime] = None,
        error_message: Optional[str] = None,
    ):
        """
        Update message status in audit trail.
        
        Args:
            message_id: Message ID to update
            status: New status
            delivered_at: Delivery timestamp
            error_message: Error message if failed
        """
        if not self._initialized:
            await self.initialize()
        
        async with self.async_session() as session:
            result = await session.execute(
                select(MessageAuditLog).where(MessageAuditLog.message_id == message_id)
            )
            audit_log = result.scalar_one_or_none()
            
            if audit_log:
                audit_log.status = status.value
                if delivered_at:
                    audit_log.delivered_at = delivered_at
                if error_message:
                    audit_log.error_message = error_message
                
                await session.commit()
    
    async def query_messages(self, query: AuditQuery) -> List[Dict[str, Any]]:
        """
        Query audit log with filters.
        
        Args:
            query: Query parameters
            
        Returns:
            List of message audit logs matching filters
        """
        if not self._initialized:
            await self.initialize()
        
        async with self.async_session() as session:
            # Build query
            stmt = select(MessageAuditLog)
            
            if query.from_agent:
                stmt = stmt.where(MessageAuditLog.from_agent == query.from_agent)
            if query.to_agent:
                stmt = stmt.where(MessageAuditLog.to_agent == query.to_agent)
            if query.message_type:
                stmt = stmt.where(MessageAuditLog.message_type == query.message_type.value)
            if query.status:
                stmt = stmt.where(MessageAuditLog.status == query.status.value)
            if query.correlation_id:
                stmt = stmt.where(MessageAuditLog.correlation_id == query.correlation_id)
            if query.start_time:
                stmt = stmt.where(MessageAuditLog.timestamp >= query.start_time)
            if query.end_time:
                stmt = stmt.where(MessageAuditLog.timestamp <= query.end_time)
            
            # Order by timestamp descending (newest first)
            stmt = stmt.order_by(MessageAuditLog.timestamp.desc())
            
            # Pagination
            stmt = stmt.limit(query.limit).offset(query.offset)
            
            result = await session.execute(stmt)
            rows = result.scalars().all()
            
            # Convert to dict
            import json
            messages = []
            for row in rows:
                messages.append({
                    "message_id": row.message_id,
                    "from_agent": row.from_agent,
                    "to_agent": row.to_agent,
                    "message_type": row.message_type,
                    "priority": row.priority,
                    "status": row.status,
                    "correlation_id": row.correlation_id,
                    "reply_to": row.reply_to,
                    "payload": json.loads(row.payload_json),
                    "timestamp": row.timestamp.isoformat(),
                    "delivered_at": row.delivered_at.isoformat() if row.delivered_at else None,
                    "ttl_seconds": row.ttl_seconds,
                    "retry_count": row.retry_count,
                    "error_message": row.error_message,
                })
            
            return messages
    
    async def get_conversation_history(
        self,
        correlation_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Get full conversation history by correlation ID.
        
        Args:
            correlation_id: Correlation ID linking messages
            
        Returns:
            List of messages in conversation, ordered by timestamp
        """
        query = AuditQuery(
            correlation_id=correlation_id,
            limit=1000,  # Large limit for full conversation
        )
        
        messages = await self.query_messages(query)
        
        # Sort by timestamp ascending for conversation flow
        messages.sort(key=lambda m: m["timestamp"])
        
        return messages
    
    async def get_agent_communication_history(
        self,
        agent_id: str,
        days: int = 7,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get communication history for an agent.
        
        Args:
            agent_id: Agent ID
            days: Number of days to look back
            limit: Maximum messages to return
            
        Returns:
            List of messages sent/received by agent
        """
        if not self._initialized:
            await self.initialize()
        
        start_time = datetime.utcnow() - timedelta(days=days)
        
        async with self.async_session() as session:
            # Messages from or to agent
            stmt = select(MessageAuditLog).where(
                (MessageAuditLog.from_agent == agent_id) |
                (MessageAuditLog.to_agent == agent_id)
            ).where(
                MessageAuditLog.timestamp >= start_time
            ).order_by(
                MessageAuditLog.timestamp.desc()
            ).limit(limit)
            
            result = await session.execute(stmt)
            rows = result.scalars().all()
            
            import json
            messages = []
            for row in rows:
                messages.append({
                    "message_id": row.message_id,
                    "from_agent": row.from_agent,
                    "to_agent": row.to_agent,
                    "message_type": row.message_type,
                    "status": row.status,
                    "timestamp": row.timestamp.isoformat(),
                    "payload": json.loads(row.payload_json),
                })
            
            return messages
    
    async def get_statistics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> AuditStatistics:
        """
        Get audit trail statistics.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            Statistics about messages
        """
        if not self._initialized:
            await self.initialize()
        
        if not start_time:
            start_time = datetime.utcnow() - timedelta(days=7)
        if not end_time:
            end_time = datetime.utcnow()
        
        async with self.async_session() as session:
            # Total messages
            total_stmt = select(func.count()).select_from(MessageAuditLog).where(
                MessageAuditLog.timestamp.between(start_time, end_time)
            )
            total_result = await session.execute(total_stmt)
            total_messages = total_result.scalar()
            
            # Messages by status
            status_stmt = select(
                MessageAuditLog.status,
                func.count(MessageAuditLog.message_id)
            ).where(
                MessageAuditLog.timestamp.between(start_time, end_time)
            ).group_by(MessageAuditLog.status)
            status_result = await session.execute(status_stmt)
            messages_by_status = {row[0]: row[1] for row in status_result}
            
            # Messages by type
            type_stmt = select(
                MessageAuditLog.message_type,
                func.count(MessageAuditLog.message_id)
            ).where(
                MessageAuditLog.timestamp.between(start_time, end_time)
            ).group_by(MessageAuditLog.message_type)
            type_result = await session.execute(type_stmt)
            messages_by_type = {row[0]: row[1] for row in type_result}
            
            # Top senders
            sender_stmt = select(
                MessageAuditLog.from_agent,
                func.count(MessageAuditLog.message_id).label('count')
            ).where(
                MessageAuditLog.timestamp.between(start_time, end_time)
            ).group_by(
                MessageAuditLog.from_agent
            ).order_by(
                func.count(MessageAuditLog.message_id).desc()
            ).limit(10)
            sender_result = await session.execute(sender_stmt)
            top_senders = [
                {"agent": row[0], "count": row[1]}
                for row in sender_result
            ]
            
            # Top receivers
            receiver_stmt = select(
                MessageAuditLog.to_agent,
                func.count(MessageAuditLog.message_id).label('count')
            ).where(
                MessageAuditLog.timestamp.between(start_time, end_time)
            ).group_by(
                MessageAuditLog.to_agent
            ).order_by(
                func.count(MessageAuditLog.message_id).desc()
            ).limit(10)
            receiver_result = await session.execute(receiver_stmt)
            top_receivers = [
                {"agent": row[0], "count": row[1]}
                for row in receiver_result
            ]
            
            # Average delivery time (for delivered messages)
            delivery_stmt = select(
                func.avg(
                    func.extract('epoch', MessageAuditLog.delivered_at - MessageAuditLog.timestamp)
                )
            ).where(
                MessageAuditLog.timestamp.between(start_time, end_time),
                MessageAuditLog.delivered_at.isnot(None)
            )
            delivery_result = await session.execute(delivery_stmt)
            avg_delivery = delivery_result.scalar() or 0.0
            
            # Error rate
            failed_count = messages_by_status.get("failed", 0)
            error_rate = (failed_count / total_messages * 100) if total_messages > 0 else 0.0
            
            return AuditStatistics(
                total_messages=total_messages,
                messages_by_status=messages_by_status,
                messages_by_type=messages_by_type,
                top_senders=top_senders,
                top_receivers=top_receivers,
                avg_delivery_time_seconds=avg_delivery,
                error_rate=error_rate,
            )
    
    async def apply_retention_policy(self) -> int:
        """
        Apply retention policy by deleting old messages.
        
        Returns:
            Number of messages deleted
        """
        if not self._initialized:
            await self.initialize()
        
        if self.retention_policy == RetentionPolicy.FOREVER:
            return 0
        
        # Calculate cutoff date
        days_map = {
            RetentionPolicy.DAYS_30: 30,
            RetentionPolicy.DAYS_90: 90,
            RetentionPolicy.DAYS_365: 365,
        }
        
        days = days_map.get(self.retention_policy, 90)
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        async with self.async_session() as session:
            # Count messages to delete
            count_stmt = select(func.count()).select_from(MessageAuditLog).where(
                MessageAuditLog.timestamp < cutoff_date
            )
            count_result = await session.execute(count_stmt)
            delete_count = count_result.scalar()
            
            # Delete old messages
            delete_stmt = delete(MessageAuditLog).where(
                MessageAuditLog.timestamp < cutoff_date
            )
            await session.execute(delete_stmt)
            await session.commit()
            
            return delete_count
    
    async def close(self):
        """Close database connection."""
        await self.engine.dispose()
