"""Repository for HiredAgent database operations.

Provides async CRUD operations for hired_agents and goal_instances tables.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.hired_agent import HiredAgentModel, GoalInstanceModel


class HiredAgentRepository:
    """Repository for HiredAgent persistence operations."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with async database session.
        
        Args:
            session: SQLAlchemy async session for database operations
        """
        self.session = session
    
    async def get_by_id(self, hired_instance_id: str) -> HiredAgentModel | None:
        """Get a hired agent instance by hired_instance_id.
        
        Args:
            hired_instance_id: Unique identifier for hired agent (e.g., "HAI-...")
            
        Returns:
            HiredAgentModel instance or None if not found
        """
        stmt = select(HiredAgentModel).where(
            HiredAgentModel.hired_instance_id == hired_instance_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_subscription_id(self, subscription_id: str) -> HiredAgentModel | None:
        """Get a hired agent instance by subscription_id.
        
        Args:
            subscription_id: Subscription identifier
            
        Returns:
            HiredAgentModel instance or None if not found
        """
        stmt = select(HiredAgentModel).where(
            HiredAgentModel.subscription_id == subscription_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def draft_upsert(
        self,
        subscription_id: str,
        agent_id: str,
        customer_id: str,
        nickname: str | None = None,
        theme: str | None = None,
        config: dict[str, Any] | None = None,
    ) -> HiredAgentModel:
        """Create or update a hired agent instance draft.
        
        This method implements "upsert" semantics:
        - If hired agent exists for subscription_id, update it
        - Otherwise, create new hired agent instance
        
        Args:
            subscription_id: Billing subscription ID (unique index)
            agent_id: Agent type identifier
            customer_id: Customer who hired the agent
            nickname: Optional agent nickname
            theme: Optional theme preference
            config: Optional configuration dictionary (JSONB)
            
        Returns:
            Created or updated HiredAgentModel instance
        """
        now = datetime.now(timezone.utc)
        
        # Check if record exists by subscription_id
        existing = await self.get_by_subscription_id(subscription_id)
        
        if existing:
            # Update existing record
            existing.agent_id = agent_id
            existing.customer_id = customer_id
            
            if nickname is not None:
                existing.nickname = nickname
            if theme is not None:
                existing.theme = theme
            if config is not None:
                existing.config = config
            
            # Note: configured flag should be computed by service layer
            # based on nickname, theme, and config completeness
            existing.active = True
            existing.updated_at = now
            
            await self.session.flush()
            await self.session.refresh(existing)
            return existing
        
        # Create new record
        hired_instance_id = f"HAI-{uuid4()}"
        new_record = HiredAgentModel(
            hired_instance_id=hired_instance_id,
            subscription_id=subscription_id,
            agent_id=agent_id,
            customer_id=customer_id,
            nickname=nickname,
            theme=theme,
            config=config or {},
            configured=False,  # Service layer should update after validation
            goals_completed=False,
            active=True,
            trial_status="not_started",
            trial_start_at=None,
            trial_end_at=None,
            created_at=now,
            updated_at=now,
        )
        
        self.session.add(new_record)
        await self.session.flush()
        await self.session.refresh(new_record)
        return new_record
    
    async def finalize(
        self,
        hired_instance_id: str,
        goals_completed: bool,
        configured: bool,
        trial_status: str | None = None,
        trial_start: datetime | None = None,
        trial_end: datetime | None = None,
    ) -> HiredAgentModel:
        """Finalize a hired agent instance (mark configured/goals_completed, start trial).
        
        Args:
            hired_instance_id: Unique identifier for hired agent
            goals_completed: Whether goal setup is complete
            configured: Whether configuration is complete
            trial_status: Optional trial status to set (e.g., "active")
            trial_start: Optional trial start timestamp
            trial_end: Optional trial end timestamp
            
        Returns:
            Updated HiredAgentModel instance
            
        Raises:
            ValueError: If hired_instance_id not found
        """
        existing = await self.get_by_id(hired_instance_id)
        if not existing:
            raise ValueError(f"Hired agent instance {hired_instance_id} not found")
        
        now = datetime.now(timezone.utc)
        
        existing.configured = configured
        existing.goals_completed = goals_completed
        
        if trial_status is not None:
            existing.trial_status = trial_status
        if trial_start is not None:
            existing.trial_start = trial_start
        if trial_end is not None:
            existing.trial_end = trial_end
        
        existing.updated_at = now
        
        await self.session.flush()
        await self.session.refresh(existing)
        return existing
    
    async def list_by_customer(self, customer_id: str) -> list[HiredAgentModel]:
        """List all hired agent instances for a customer.
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            List of HiredAgentModel instances
        """
        stmt = (
            select(HiredAgentModel)
            .where(HiredAgentModel.customer_id == customer_id)
            .order_by(HiredAgentModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def update_trial_status(
        self,
        hired_instance_id: str,
        trial_status: str,
    ) -> HiredAgentModel:
        """Update trial status for a hired agent instance.
        
        Args:
            hired_instance_id: Unique identifier for hired agent
            trial_status: New trial status
            
        Returns:
            Updated HiredAgentModel instance
            
        Raises:
            ValueError: If hired_instance_id not found
        """
        existing = await self.get_by_id(hired_instance_id)
        if not existing:
            raise ValueError(f"Hired agent instance {hired_instance_id} not found")
        
        now = datetime.now(timezone.utc)
        existing.trial_status = trial_status
        existing.updated_at = now
        
        await self.session.flush()
        await self.session.refresh(existing)
        return existing
    
    async def deactivate(self, hired_instance_id: str) -> HiredAgentModel:
        """Deactivate a hired agent instance.
        
        Args:
            hired_instance_id: Unique identifier for hired agent
            
        Returns:
            Updated HiredAgentModel instance
            
        Raises:
            ValueError: If hired_instance_id not found
        """
        existing = await self.get_by_id(hired_instance_id)
        if not existing:
            raise ValueError(f"Hired agent instance {hired_instance_id} not found")
        
        now = datetime.now(timezone.utc)
        existing.active = False
        existing.updated_at = now
        
        await self.session.flush()
        await self.session.refresh(existing)
        return existing


class GoalInstanceRepository:
    """Repository for GoalInstance persistence operations."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with async database session.
        
        Args:
            session: SQLAlchemy async session for database operations
        """
        self.session = session
    
    async def get_by_id(self, goal_instance_id: str) -> GoalInstanceModel | None:
        """Get a goal instance by goal_instance_id.
        
        Args:
            goal_instance_id: Unique identifier for goal
            
        Returns:
            GoalInstanceModel instance or None if not found
        """
        stmt = select(GoalInstanceModel).where(
            GoalInstanceModel.goal_instance_id == goal_instance_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list_by_hired_instance(
        self, hired_instance_id: str
    ) -> list[GoalInstanceModel]:
        """List all goals for a hired agent instance.
        
        Args:
            hired_instance_id: Parent hired agent identifier
            
        Returns:
            List of GoalInstanceModel instances
        """
        stmt = (
            select(GoalInstanceModel)
            .where(GoalInstanceModel.hired_instance_id == hired_instance_id)
            .order_by(GoalInstanceModel.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def upsert_goal(
        self,
        hired_instance_id: str,
        goal_template_id: str,
        frequency: str,
        settings: dict[str, Any] | None = None,
        goal_instance_id: str | None = None,
    ) -> GoalInstanceModel:
        """Create or update a goal instance.
        
        Args:
            hired_instance_id: Parent hired agent identifier
            goal_template_id: Reference to goal template
            frequency: Execution frequency (daily, weekly, monthly, on_demand)
            settings: Optional goal-specific settings (JSONB)
            goal_instance_id: Optional existing goal ID for updates
            
        Returns:
            Created or updated GoalInstanceModel instance
        """
        now = datetime.now(timezone.utc)
        
        if goal_instance_id:
            # Update existing goal
            existing = await self.get_by_id(goal_instance_id)
            if existing:
                existing.goal_template_id = goal_template_id
                existing.frequency = frequency
                if settings is not None:
                    existing.settings = settings
                existing.updated_at = now
                
                await self.session.flush()
                await self.session.refresh(existing)
                return existing
        
        # Create new goal
        new_goal_id = goal_instance_id or f"GI-{uuid4()}"
        new_goal = GoalInstanceModel(
            goal_instance_id=new_goal_id,
            hired_instance_id=hired_instance_id,
            goal_template_id=goal_template_id,
            frequency=frequency,
            settings=settings or {},
            created_at=now,
            updated_at=now,
        )
        
        self.session.add(new_goal)
        await self.session.flush()
        await self.session.refresh(new_goal)
        return new_goal
    
    async def delete_goal(self, goal_instance_id: str) -> bool:
        """Delete a goal instance.
        
        Args:
            goal_instance_id: Unique identifier for goal
            
        Returns:
            True if deleted, False if not found
        """
        existing = await self.get_by_id(goal_instance_id)
        if not existing:
            return False
        
        await self.session.delete(existing)
        await self.session.flush()
        return True
