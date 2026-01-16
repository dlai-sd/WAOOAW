"""
Trial Pydantic Schemas

Request/response schemas for trial management API.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator

from models.trial import TrialStatus


# Base schemas
class TrialBase(BaseModel):
    """Base trial schema with common fields."""
    customer_name: str = Field(..., min_length=1, max_length=255, description="Customer full name")
    customer_email: EmailStr = Field(..., description="Customer email address")
    company: str = Field(..., min_length=1, max_length=255, description="Company name")
    phone: Optional[str] = Field(None, max_length=50, description="Customer phone number (optional)")


# Request schemas
class TrialCreate(TrialBase):
    """Schema for creating a new trial."""
    agent_id: UUID = Field(..., description="ID of the agent to trial")
    
    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "550e8400-e29b-41d4-a716-446655440000",
                "customer_name": "John Doe",
                "customer_email": "john@example.com",
                "company": "Example Corp",
                "phone": "+91 98765 43210"
            }
        }


class TrialUpdate(BaseModel):
    """Schema for updating trial status."""
    status: TrialStatus = Field(..., description="New trial status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "converted"
            }
        }


# Response schemas
class TrialResponse(TrialBase):
    """Schema for trial response."""
    id: UUID
    agent_id: UUID
    start_date: datetime
    end_date: datetime
    status: TrialStatus
    days_remaining: int = Field(..., description="Days remaining in trial (computed)")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "agent_id": "550e8400-e29b-41d4-a716-446655440000",
                "customer_name": "John Doe",
                "customer_email": "john@example.com",
                "company": "Example Corp",
                "phone": "+91 98765 43210",
                "start_date": "2026-01-16T10:00:00Z",
                "end_date": "2026-01-23T10:00:00Z",
                "status": "active",
                "days_remaining": 7,
                "created_at": "2026-01-16T10:00:00Z",
                "updated_at": "2026-01-16T10:00:00Z"
            }
        }
    
    @validator("days_remaining", pre=False, always=True)
    def compute_days_remaining(cls, v, values):
        """Compute days remaining if not already set."""
        if v is not None:
            return v
        
        # If days_remaining not provided, compute from dates
        if "end_date" in values and values.get("status") == TrialStatus.ACTIVE:
            now = datetime.utcnow()
            end_date = values["end_date"]
            if now > end_date:
                return 0
            delta = end_date - now
            return max(0, delta.days)
        
        return 0


class TrialDeliverableBase(BaseModel):
    """Base deliverable schema."""
    file_name: str = Field(..., max_length=255, description="File name")
    file_path: str = Field(..., description="Storage path (S3/GCS)")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    mime_type: Optional[str] = Field(None, max_length=100, description="MIME type")
    description: Optional[str] = Field(None, description="Deliverable description")


class TrialDeliverableCreate(TrialDeliverableBase):
    """Schema for creating a deliverable."""
    trial_id: UUID = Field(..., description="Trial ID")


class TrialDeliverableResponse(TrialDeliverableBase):
    """Schema for deliverable response."""
    id: UUID
    trial_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


# List response schemas
class TrialListParams(BaseModel):
    """Query parameters for listing trials."""
    customer_email: Optional[EmailStr] = Field(None, description="Filter by customer email")
    status: Optional[TrialStatus] = Field(None, description="Filter by status")
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=1000, description="Max records to return")
    
    class Config:
        json_schema_extra = {
            "example": {
                "customer_email": "john@example.com",
                "status": "active",
                "skip": 0,
                "limit": 50
            }
        }


class TrialListResponse(BaseModel):
    """Response for list trials endpoint."""
    trials: list[TrialResponse]
    total: int = Field(..., description="Total number of trials matching filters")
    skip: int
    limit: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "trials": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "agent_id": "550e8400-e29b-41d4-a716-446655440000",
                        "customer_name": "John Doe",
                        "customer_email": "john@example.com",
                        "company": "Example Corp",
                        "start_date": "2026-01-16T10:00:00Z",
                        "end_date": "2026-01-23T10:00:00Z",
                        "status": "active",
                        "days_remaining": 7,
                        "created_at": "2026-01-16T10:00:00Z",
                        "updated_at": "2026-01-16T10:00:00Z"
                    }
                ],
                "total": 1,
                "skip": 0,
                "limit": 100
            }
        }
