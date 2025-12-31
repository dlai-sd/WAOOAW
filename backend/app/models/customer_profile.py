"""
Customer Profile database models.

SQLAlchemy models for customer profiles and enrichment.
"""

from datetime import datetime
from typing import Dict, Any
from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class CustomerProfile(Base):
    """
    Customer profile for personalized agent interactions.
    
    Stores enriched information extracted from signup and interactions.
    """
    __tablename__ = "customer_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    
    # Basic information
    industry = Column(String(100), nullable=True, index=True)
    company_name = Column(String(200), nullable=True)
    company_size = Column(String(50), nullable=True)  # '1-10', '11-50', '51-200', etc.
    role = Column(String(100), nullable=True)  # Job title/role
    
    # Enriched data (JSONB for flexibility)
    preferences = Column(JSONB, nullable=False, default=dict)
    goals = Column(Text, nullable=True)
    pain_points = Column(Text, nullable=True)
    communication_style = Column(String(50), nullable=True)  # 'formal', 'casual', 'technical'
    timezone = Column(String(50), nullable=True)
    
    # Behavioral insights
    preferred_agents = Column(JSONB, nullable=False, default=list)  # Agent IDs customer uses most
    frequent_task_types = Column(JSONB, nullable=False, default=list)  # Most common tasks
    usage_patterns = Column(JSONB, nullable=False, default=dict)  # Time of day, frequency, etc.
    
    # Enrichment metadata
    enrichment_status = Column(String(20), default='pending')  # 'pending', 'enriched', 'failed'
    enrichment_attempts = Column(String, default=0)
    last_enrichment_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<CustomerProfile(id={self.id}, customer_id={self.customer_id}, industry={self.industry})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "customer_id": str(self.customer_id),
            "industry": self.industry,
            "company_name": self.company_name,
            "company_size": self.company_size,
            "role": self.role,
            "preferences": self.preferences,
            "goals": self.goals,
            "pain_points": self.pain_points,
            "communication_style": self.communication_style,
            "timezone": self.timezone,
            "preferred_agents": self.preferred_agents,
            "frequent_task_types": self.frequent_task_types,
            "usage_patterns": self.usage_patterns,
            "enrichment_status": self.enrichment_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ProfileEnrichmentLog(Base):
    """
    Log of profile enrichment operations.
    
    Tracks when and how profiles were enriched via LLM.
    """
    __tablename__ = "profile_enrichment_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey('customer_profiles.id'), nullable=False)
    
    source = Column(String(50), nullable=False)  # 'signup', 'interaction', 'manual'
    source_data = Column(JSONB, nullable=False)  # Input that triggered enrichment
    extracted_fields = Column(JSONB, nullable=False)  # What was extracted
    
    llm_model = Column(String(50), nullable=True)  # 'gpt-4o-mini', etc.
    llm_tokens = Column(String, default=0)
    llm_cost = Column(String, default=0.0)
    
    status = Column(String(20), nullable=False)  # 'success', 'failed', 'partial'
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<ProfileEnrichmentLog(id={self.id}, profile_id={self.profile_id}, status={self.status})>"
