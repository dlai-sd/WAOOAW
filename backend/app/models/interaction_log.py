"""
Interaction Log database model.

SQLAlchemy model for permanent interaction history.
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from app.database import Base


class InteractionLog(Base):
    """
    Permanent log of all agent interactions.
    
    Used for:
    - Customer interaction history
    - Analytics and reporting
    - Pattern detection and improvement
    - GDPR compliance (2-year retention)
    """
    __tablename__ = "interaction_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    agent_id = Column(String(100), nullable=False, index=True)
    
    # Task details
    task_type = Column(String(100), nullable=False, index=True)
    task_input = Column(Text, nullable=False)
    agent_output = Column(Text, nullable=False)
    
    # Metrics
    rating = Column(Integer, nullable=True)  # 1-5 stars
    duration_ms = Column(Integer, nullable=True)
    success = Column(Boolean, default=True, nullable=False, index=True)
    
    # Additional context (use extra_data instead of metadata)
    extra_data = Column(JSONB, nullable=False, default=dict)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f"<InteractionLog(id={self.id}, customer={self.customer_id}, agent={self.agent_id}, success={self.success})>"
