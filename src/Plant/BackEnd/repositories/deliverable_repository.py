"""Repository for Deliverable and Approval database operations.

Provides async CRUD operations for deliverables and approvals tables.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.deliverable import DeliverableModel, ApprovalModel


class DeliverableRepository:
    """Repository for Deliverable persistence operations."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with async database session.
        
        Args:
            session: SQLAlchemy async session for database operations
        """
        self.session = session
    
    async def get_by_id(self, deliverable_id: str) -> DeliverableModel | None:
        """Get a deliverable by deliverable_id.
        
        Args:
            deliverable_id: Unique identifier for deliverable
            
        Returns:
            DeliverableModel instance or None if not found
        """
        stmt = select(DeliverableModel).where(
            DeliverableModel.deliverable_id == deliverable_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list_by_hired_instance(
        self, hired_instance_id: str
    ) -> list[DeliverableModel]:
        """List all deliverables for a hired agent instance, ordered by recency.
        
        Args:
            hired_instance_id: Parent hired agent identifier
            
        Returns:
            List of DeliverableModel instances ordered by created_at desc
        """
        stmt = (
            select(DeliverableModel)
            .where(DeliverableModel.hired_instance_id == hired_instance_id)
            .order_by(DeliverableModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def create_deliverable(
        self,
        hired_instance_id: str,
        goal_instance_id: str,
        goal_template_id: str,
        title: str,
        payload: dict[str, Any],
        deliverable_id: str | None = None,
    ) -> DeliverableModel:
        """Create a new deliverable draft.
        
        Args:
            hired_instance_id: Parent hired agent identifier
            goal_instance_id: Parent goal identifier
            goal_template_id: Reference to goal template
            title: Deliverable title
            payload: Deliverable content (JSONB)
            deliverable_id: Optional explicit ID (for testing/idempotency)
            
        Returns:
            Created DeliverableModel instance
        """
        now = datetime.now(timezone.utc)
        
        new_deliverable = DeliverableModel(
            deliverable_id=deliverable_id or f"DEL-{uuid4()}",
            hired_instance_id=hired_instance_id,
            goal_instance_id=goal_instance_id,
            goal_template_id=goal_template_id,
            title=title,
            payload=payload,
            review_status="pending_review",
            review_notes=None,
            approval_id=None,
            execution_status="not_executed",
            executed_at=None,
            created_at=now,
            updated_at=now,
        )
        
        self.session.add(new_deliverable)
        await self.session.flush()
        await self.session.refresh(new_deliverable)
        return new_deliverable
    
    async def update_review_status(
        self,
        deliverable_id: str,
        review_status: str,
        approval_id: str | None = None,
        review_notes: str | None = None,
    ) -> DeliverableModel:
        """Update review status for a deliverable.
        
        Args:
            deliverable_id: Unique identifier for deliverable
            review_status: New review status (approved, rejected, pending_review)
            approval_id: Optional approval record ID
            review_notes: Optional review notes
            
        Returns:
            Updated DeliverableModel instance
            
        Raises:
            ValueError: If deliverable_id not found
        """
        existing = await self.get_by_id(deliverable_id)
        if not existing:
            raise ValueError(f"Deliverable {deliverable_id} not found")
        
        now = datetime.now(timezone.utc)
        existing.review_status = review_status
        existing.approval_id = approval_id
        if review_notes is not None:
            existing.review_notes = review_notes
        existing.updated_at = now
        
        await self.session.flush()
        await self.session.refresh(existing)
        return existing
    
    async def mark_executed(
        self, deliverable_id: str
    ) -> DeliverableModel:
        """Mark a deliverable as executed.
        
        Args:
            deliverable_id: Unique identifier for deliverable
            
        Returns:
            Updated DeliverableModel instance
            
        Raises:
            ValueError: If deliverable_id not found
        """
        existing = await self.get_by_id(deliverable_id)
        if not existing:
            raise ValueError(f"Deliverable {deliverable_id} not found")
        
        now = datetime.now(timezone.utc)
        existing.execution_status = "executed"
        existing.executed_at = now
        existing.updated_at = now
        
        await self.session.flush()
        await self.session.refresh(existing)
        return existing
    
    async def delete_deliverable(self, deliverable_id: str) -> bool:
        """Delete a deliverable.
        
        Args:
            deliverable_id: Unique identifier for deliverable
            
        Returns:
            True if deleted, False if not found
        """
        existing = await self.get_by_id(deliverable_id)
        if not existing:
            return False
        
        await self.session.delete(existing)
        await self.session.flush()
        return True


class ApprovalRepository:
    """Repository for Approval persistence operations."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with async database session.
        
        Args:
            session: SQLAlchemy async session for database operations
        """
        self.session = session
    
    async def get_by_id(self, approval_id: str) -> ApprovalModel | None:
        """Get an approval by approval_id.
        
        Args:
            approval_id: Unique identifier for approval
            
        Returns:
            ApprovalModel instance or None if not found
        """
        stmt = select(ApprovalModel).where(
            ApprovalModel.approval_id == approval_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_deliverable(
        self, deliverable_id: str
    ) -> ApprovalModel | None:
        """Get approval for a deliverable.
        
        Args:
            deliverable_id: Deliverable identifier
            
        Returns:
            ApprovalModel instance or None if not found
        """
        stmt = select(ApprovalModel).where(
            ApprovalModel.deliverable_id == deliverable_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_approval(
        self,
        deliverable_id: str,
        customer_id: str,
        decision: str,
        notes: str | None = None,
        approval_id: str | None = None,
    ) -> ApprovalModel:
        """Create an approval record (immutable after creation).
        
        Args:
            deliverable_id: Deliverable being approved/rejected
            customer_id: Customer making the decision
            decision: "approved" or "rejected"
            notes: Optional approval notes
            approval_id: Optional explicit ID (for idempotency)
            
        Returns:
            Created ApprovalModel instance
        """
        now = datetime.now(timezone.utc)
        
        new_approval = ApprovalModel(
            approval_id=approval_id or f"APR-{uuid4()}",
            deliverable_id=deliverable_id,
            customer_id=customer_id,
            decision=decision,
            notes=notes,
            created_at=now,
        )
        
        self.session.add(new_approval)
        await self.session.flush()
        await self.session.refresh(new_approval)
        return new_approval
    
    async def list_by_customer(
        self, customer_id: str
    ) -> list[ApprovalModel]:
        """List all approvals by a customer.
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            List of ApprovalModel instances ordered by created_at desc
        """
        stmt = (
            select(ApprovalModel)
            .where(ApprovalModel.customer_id == customer_id)
            .order_by(ApprovalModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
