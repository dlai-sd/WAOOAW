"""
Trial Service Layer

Business logic for trial management.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.trial import Trial, TrialStatus, TrialDeliverable
from schemas.trial import TrialCreate, TrialUpdate
from core.logging import get_logger

logger = get_logger(__name__)


class TrialService:
    """
    Service for managing customer trials.
    
    Handles:
    - Trial creation (7-day duration)
    - Trial listing/filtering
    - Status updates (convert, cancel, expire)
    - Automatic expiry checking
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize service with database session."""
        self.db = db
    
    async def create_trial(self, trial_data: TrialCreate) -> Trial:
        """
        Create a new 7-day trial.
        
        Args:
            trial_data: Trial creation data
            
        Returns:
            Created trial
            
        Raises:
            ValueError: If agent_id doesn't exist
        """
        logger.info(f"Creating trial for agent {trial_data.agent_id}, customer {trial_data.customer_email}")
        
        # TODO: Validate agent exists (after Agent model update)
        # agent = await self.db.get(Agent, trial_data.agent_id)
        # if not agent:
        #     raise ValueError(f"Agent {trial_data.agent_id} not found")
        
        # Create trial with 7-day duration
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=7)
        
        trial = Trial(
            agent_id=trial_data.agent_id,
            customer_name=trial_data.customer_name,
            customer_email=trial_data.customer_email,
            company=trial_data.company,
            phone=trial_data.phone,
            start_date=start_date,
            end_date=end_date,
            status=TrialStatus.ACTIVE.value
        )
        
        self.db.add(trial)
        await self.db.commit()
        await self.db.refresh(trial)
        
        logger.info(f"Trial {trial.id} created for customer {trial_data.customer_email}")
        
        return trial
    
    async def get_trial(self, trial_id: UUID) -> Optional[Trial]:
        """
        Get trial by ID.
        
        Args:
            trial_id: Trial UUID
            
        Returns:
            Trial or None if not found
        """
        result = await self.db.execute(
            select(Trial).where(Trial.id == trial_id)
        )
        return result.scalar_one_or_none()
    
    async def list_trials(
        self,
        customer_email: Optional[str] = None,
        status: Optional[TrialStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Trial], int]:
        """
        List trials with optional filters.
        
        Args:
            customer_email: Filter by customer email
            status: Filter by status
            skip: Number of records to skip (pagination)
            limit: Max records to return
            
        Returns:
            Tuple of (trials list, total count)
        """
        # Build query with filters
        query = select(Trial)
        
        if customer_email:
            query = query.where(Trial.customer_email == customer_email)
        
        if status:
            query = query.where(Trial.status == status.value)
        
        # Get total count (before pagination)
        count_query = select(func.count()).select_from(Trial)
        if customer_email:
            count_query = count_query.where(Trial.customer_email == customer_email)
        if status:
            count_query = count_query.where(Trial.status == status.value)
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination and ordering
        query = query.order_by(Trial.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        trials = result.scalars().all()
        
        return list(trials), total
    
    async def update_trial_status(self, trial_id: UUID, status_update: TrialUpdate) -> Optional[Trial]:
        """
        Update trial status.
        
        Args:
            trial_id: Trial UUID
            status_update: New status
            
        Returns:
            Updated trial or None if not found
            
        Raises:
            ValueError: If status transition is invalid
        """
        trial = await self.get_trial(trial_id)
        if not trial:
            return None
        
        old_status = trial.status
        new_status = status_update.status.value
        
        # Validate status transitions
        valid_transitions = {
            TrialStatus.ACTIVE.value: [
                TrialStatus.CONVERTED.value,
                TrialStatus.CANCELLED.value,
                TrialStatus.EXPIRED.value
            ],
            TrialStatus.CONVERTED.value: [],  # Final state
            TrialStatus.CANCELLED.value: [],  # Final state
            TrialStatus.EXPIRED.value: []     # Final state
        }
        
        if new_status not in valid_transitions.get(old_status, []):
            raise ValueError(
                f"Invalid status transition: {old_status} → {new_status}. "
                f"Valid transitions from {old_status}: {valid_transitions.get(old_status, [])}"
            )
        
        logger.info(f"Updating trial {trial_id} status: {old_status} → {new_status}")
        
        trial.status = new_status
        trial.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(trial)
        
        return trial
    
    async def cancel_trial(self, trial_id: UUID) -> Optional[Trial]:
        """
        Cancel a trial.
        
        Args:
            trial_id: Trial UUID
            
        Returns:
            Cancelled trial or None if not found
        """
        return await self.update_trial_status(
            trial_id,
            TrialUpdate(status=TrialStatus.CANCELLED)
        )
    
    async def convert_trial(self, trial_id: UUID) -> Optional[Trial]:
        """
        Convert trial to paid subscription.
        
        Args:
            trial_id: Trial UUID
            
        Returns:
            Converted trial or None if not found
        """
        return await self.update_trial_status(
            trial_id,
            TrialUpdate(status=TrialStatus.CONVERTED)
        )
    
    async def check_and_expire_trials(self) -> int:
        """
        Check for expired active trials and mark them as expired.
        
        Should be called periodically (e.g., daily cron job).
        
        Returns:
            Number of trials expired
        """
        logger.info("Checking for expired trials...")
        
        # Find active trials past end_date
        query = select(Trial).where(
            Trial.status == TrialStatus.ACTIVE.value,
            Trial.end_date < datetime.utcnow()
        )
        
        result = await self.db.execute(query)
        expired_trials = result.scalars().all()
        
        count = 0
        for trial in expired_trials:
            logger.info(f"Expiring trial {trial.id} (customer: {trial.customer_email})")
            trial.status = TrialStatus.EXPIRED.value
            trial.updated_at = datetime.utcnow()
            count += 1
        
        if count > 0:
            await self.db.commit()
            logger.info(f"Expired {count} trials")
        else:
            logger.info("No trials to expire")
        
        return count
    
    async def add_deliverable(
        self,
        trial_id: UUID,
        file_name: str,
        file_path: str,
        file_size: Optional[int] = None,
        mime_type: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[TrialDeliverable]:
        """
        Add a deliverable to a trial.
        
        Args:
            trial_id: Trial UUID
            file_name: Name of file
            file_path: Storage path (S3/GCS)
            file_size: File size in bytes
            mime_type: MIME type
            description: Optional description
            
        Returns:
            Created deliverable or None if trial not found
        """
        trial = await self.get_trial(trial_id)
        if not trial:
            return None
        
        deliverable = TrialDeliverable(
            trial_id=trial_id,
            file_name=file_name,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            description=description
        )
        
        self.db.add(deliverable)
        await self.db.commit()
        await self.db.refresh(deliverable)
        
        logger.info(f"Added deliverable {deliverable.id} to trial {trial_id}: {file_name}")
        
        return deliverable
    
    async def get_trial_deliverables(self, trial_id: UUID) -> List[TrialDeliverable]:
        """
        Get all deliverables for a trial.
        
        Args:
            trial_id: Trial UUID
            
        Returns:
            List of deliverables
        """
        result = await self.db.execute(
            select(TrialDeliverable)
            .where(TrialDeliverable.trial_id == trial_id)
            .order_by(TrialDeliverable.created_at.desc())
        )
        return list(result.scalars().all())
