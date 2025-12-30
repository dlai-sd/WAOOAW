"""
WowTrialManager - Trial Lifecycle Management Agent

Manages the complete trial experience from instant provisioning through
conversion or cancellation. Enables "Try Before Hire" marketplace model.

Epic 1.1: Trial Lifecycle Management (48 points)
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import uuid4
import logging

from waooaw.agents.base_agent import WAAOOWAgent

logger = logging.getLogger(__name__)


class TrialStatus:
    """Trial lifecycle states"""
    PROVISIONING = "PROVISIONING"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CONVERTED = "CONVERTED"
    CANCELLED = "CANCELLED"


class Trial:
    """Trial data model"""
    def __init__(
        self,
        trial_id: str,
        customer_id: str,
        agent_type: str,
        status: str,
        start_date: datetime,
        end_date: datetime,
        days_remaining: int,
        agent_id: Optional[str] = None,
        deliverables: Optional[List[Dict]] = None,
        tasks_completed: int = 0,
        customer_interactions: int = 0,
        satisfaction_score: Optional[float] = None,
        conversion_intent: Optional[str] = None,
        converted_at: Optional[datetime] = None,
        subscription_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.trial_id = trial_id
        self.customer_id = customer_id
        self.agent_type = agent_type
        self.agent_id = agent_id
        self.status = status
        self.start_date = start_date
        self.end_date = end_date
        self.days_remaining = days_remaining
        self.deliverables = deliverables or []
        self.tasks_completed = tasks_completed
        self.customer_interactions = customer_interactions
        self.satisfaction_score = satisfaction_score
        self.conversion_intent = conversion_intent
        self.converted_at = converted_at
        self.subscription_id = subscription_id
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "trial_id": self.trial_id,
            "customer_id": self.customer_id,
            "agent_type": self.agent_type,
            "agent_id": self.agent_id,
            "status": self.status,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "days_remaining": self.days_remaining,
            "deliverables": self.deliverables,
            "tasks_completed": self.tasks_completed,
            "customer_interactions": self.customer_interactions,
            "satisfaction_score": self.satisfaction_score,
            "conversion_intent": self.conversion_intent,
            "converted_at": self.converted_at.isoformat() if self.converted_at else None,
            "subscription_id": self.subscription_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class TrialProvisioningEngine:
    """
    Story 1.1.1: Trial Provisioning Engine (5 points)
    
    Provisions 7-day trials instantly (<5s):
    - Creates trial record in PostgreSQL
    - Provisions agent via WowAgentFactory
    - Generates credentials
    - Sends welcome email
    """
    
    def __init__(self, db, agent_factory, notification_service):
        self.db = db
        self.agent_factory = agent_factory
        self.notification_service = notification_service
    
    async def provision_trial(
        self,
        customer_id: str,
        agent_type: str,
        customer_email: str,
        customer_name: str
    ) -> Trial:
        """
        Provision a 7-day trial instantly.
        
        Args:
            customer_id: Unique customer identifier
            agent_type: Type of agent (e.g., "marketing-content", "education-math")
            customer_email: Customer email for notifications
            customer_name: Customer name for personalization
            
        Returns:
            Trial object with ACTIVE status
            
        Raises:
            ValueError: If validation fails
            Exception: If provisioning fails
        """
        start_time = datetime.now()
        
        try:
            # 1. Validate request
            await self._validate_trial_request(customer_id, agent_type)
            
            # 2. Create trial record
            trial = Trial(
                trial_id=str(uuid4()),
                customer_id=customer_id,
                agent_type=agent_type,
                status=TrialStatus.PROVISIONING,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=7),
                days_remaining=7
            )
            
            await self.db.trials.insert(trial.to_dict())
            logger.info(f"Trial record created: {trial.trial_id}")
            
            # 3. Provision agent (async, non-blocking)
            agent_instance = await self.agent_factory.create_instance(
                agent_type=agent_type,
                customer_id=customer_id,
                trial_mode=True,
                trial_id=trial.trial_id
            )
            
            # 4. Update trial with agent details
            trial.agent_id = agent_instance.get("agent_id")
            trial.status = TrialStatus.ACTIVE
            trial.updated_at = datetime.now()
            
            await self.db.trials.update(
                {"trial_id": trial.trial_id},
                trial.to_dict()
            )
            
            # 5. Send welcome notification (async, fire-and-forget)
            asyncio.create_task(
                self._send_welcome_email(
                    trial=trial,
                    customer_email=customer_email,
                    customer_name=customer_name,
                    agent_name=agent_instance.get("name"),
                    agent_url=f"/agents/{agent_instance.get('agent_id')}"
                )
            )
            
            # 6. Log metrics
            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
            logger.info(f"Trial provisioned in {elapsed_ms:.2f}ms: {trial.trial_id}")
            
            if elapsed_ms > 5000:
                logger.warning(f"Trial provisioning exceeded 5s target: {elapsed_ms:.2f}ms")
            
            return trial
            
        except Exception as e:
            logger.error(f"Trial provisioning failed: {e}", exc_info=True)
            # Cleanup: mark trial as failed if created
            if trial and trial.trial_id:
                await self.db.trials.update(
                    {"trial_id": trial.trial_id},
                    {"status": "FAILED", "error": str(e)}
                )
            raise
    
    async def _validate_trial_request(self, customer_id: str, agent_type: str):
        """Validate trial provisioning request"""
        # Check if customer exists
        customer = await self.db.customers.find_one({"customer_id": customer_id})
        if not customer:
            raise ValueError(f"Customer not found: {customer_id}")
        
        # Check if agent type is valid
        valid_types = [
            "marketing-content", "marketing-social", "marketing-seo",
            "education-math", "education-science", "education-english",
            "sales-sdr", "sales-account-exec"
        ]
        if agent_type not in valid_types:
            raise ValueError(f"Invalid agent type: {agent_type}")
        
        # Check for existing active trial
        active_trial = await self.db.trials.find_one({
            "customer_id": customer_id,
            "agent_type": agent_type,
            "status": TrialStatus.ACTIVE
        })
        if active_trial:
            raise ValueError(f"Customer already has active trial for {agent_type}")
    
    async def _send_welcome_email(
        self,
        trial: Trial,
        customer_email: str,
        customer_name: str,
        agent_name: str,
        agent_url: str
    ):
        """Send welcome email to customer"""
        try:
            await self.notification_service.send_email(
                to=customer_email,
                template="trial_welcome",
                data={
                    "customer_name": customer_name,
                    "agent_name": agent_name,
                    "agent_type": trial.agent_type,
                    "trial_id": trial.trial_id,
                    "end_date": trial.end_date.strftime("%B %d, %Y"),
                    "days_remaining": trial.days_remaining,
                    "agent_url": agent_url,
                    "support_email": "support@waooaw.com"
                }
            )
            logger.info(f"Welcome email sent for trial: {trial.trial_id}")
        except Exception as e:
            logger.error(f"Failed to send welcome email: {e}", exc_info=True)
            # Don't fail trial if email fails


class TrialUsageTracker:
    """
    Story 1.1.2: Usage Tracking System (5 points)
    
    Tracks trial agent usage:
    - Tasks completed
    - Deliverables created (with metadata)
    - Customer interactions
    - Satisfaction score
    """
    
    def __init__(self, db, analytics_service):
        self.db = db
        self.analytics_service = analytics_service
    
    async def track_task_completed(
        self,
        trial_id: str,
        task: Dict
    ):
        """
        Track a completed task during trial.
        
        Args:
            trial_id: Trial identifier
            task: Task details (id, type, output, metadata)
        """
        trial = await self.db.trials.find_one({"trial_id": trial_id})
        if not trial:
            raise ValueError(f"Trial not found: {trial_id}")
        
        # Update task counter
        tasks_completed = trial.get("tasks_completed", 0) + 1
        
        # Add deliverable
        deliverable = {
            "id": str(uuid4()),
            "task_id": task.get("id"),
            "type": task.get("deliverable_type", "unknown"),
            "created_at": datetime.now().isoformat(),
            "size_bytes": len(task.get("output", "")),
            "preview": task.get("output", "")[:200],
            "metadata": task.get("metadata", {})
        }
        
        deliverables = trial.get("deliverables", [])
        deliverables.append(deliverable)
        
        # Update trial
        await self.db.trials.update(
            {"trial_id": trial_id},
            {
                "tasks_completed": tasks_completed,
                "deliverables": deliverables,
                "updated_at": datetime.now().isoformat()
            }
        )
        
        # Log analytics event
        await self.analytics_service.log_event(
            "trial_task_completed",
            {
                "trial_id": trial_id,
                "task_id": task.get("id"),
                "task_type": task.get("deliverable_type"),
                "tasks_total": tasks_completed
            }
        )
        
        logger.info(f"Task tracked for trial {trial_id}: {tasks_completed} total")
    
    async def track_interaction(
        self,
        trial_id: str,
        interaction_type: str,
        duration_seconds: int,
        metadata: Optional[Dict] = None
    ):
        """
        Track customer-agent interaction.
        
        Args:
            trial_id: Trial identifier
            interaction_type: Type (chat, feedback, request, etc.)
            duration_seconds: Duration of interaction
            metadata: Additional context
        """
        trial = await self.db.trials.find_one({"trial_id": trial_id})
        if not trial:
            raise ValueError(f"Trial not found: {trial_id}")
        
        # Update interaction counter
        interactions = trial.get("customer_interactions", 0) + 1
        
        # Update satisfaction score (simple heuristic)
        satisfaction = trial.get("satisfaction_score", 4.0)
        if interaction_type == "feedback" and duration_seconds > 60:
            satisfaction = min(5.0, satisfaction + 0.1)
        elif interaction_type == "complaint":
            satisfaction = max(1.0, satisfaction - 0.3)
        
        # Update trial
        await self.db.trials.update(
            {"trial_id": trial_id},
            {
                "customer_interactions": interactions,
                "satisfaction_score": satisfaction,
                "updated_at": datetime.now().isoformat()
            }
        )
        
        # Log analytics event
        await self.analytics_service.log_event(
            "trial_interaction",
            {
                "trial_id": trial_id,
                "interaction_type": interaction_type,
                "duration_seconds": duration_seconds,
                "interactions_total": interactions,
                "satisfaction_score": satisfaction,
                "metadata": metadata or {}
            }
        )
        
        logger.info(f"Interaction tracked for trial {trial_id}: {interactions} total")
    
    async def get_usage_summary(self, trial_id: str) -> Dict:
        """Get usage summary for a trial"""
        trial = await self.db.trials.find_one({"trial_id": trial_id})
        if not trial:
            raise ValueError(f"Trial not found: {trial_id}")
        
        return {
            "trial_id": trial_id,
            "tasks_completed": trial.get("tasks_completed", 0),
            "deliverables_count": len(trial.get("deliverables", [])),
            "customer_interactions": trial.get("customer_interactions", 0),
            "satisfaction_score": trial.get("satisfaction_score"),
            "days_remaining": trial.get("days_remaining", 0),
            "status": trial.get("status")
        }


class WowTrialManager(WAAOOWAgent):
    """
    WowTrialManager - Trial Lifecycle Management Agent
    
    Manages complete trial experience:
    - Instant provisioning (<5s)
    - Usage tracking
    - Time management & reminders
    - Conversion flow
    - Cancellation handling
    - Analytics & insights
    
    Epic 1.1: 10 stories, 48 points
    """
    
    def __init__(
        self,
        db_connection,
        agent_factory,
        notification_service,
        analytics_service,
        payment_service
    ):
        super().__init__(
            name="WowTrialManager",
            version="1.0.0",
            capabilities=["trial_provisioning", "usage_tracking", "conversion_management"]
        )
        
        # Initialize components
        self.provisioning = TrialProvisioningEngine(
            db=db_connection,
            agent_factory=agent_factory,
            notification_service=notification_service
        )
        
        self.usage_tracker = TrialUsageTracker(
            db=db_connection,
            analytics_service=analytics_service
        )
        
        self.db = db_connection
        self.payment_service = payment_service
        self.notification_service = notification_service
        
        logger.info("WowTrialManager initialized")
    
    async def provision_trial(
        self,
        customer_id: str,
        agent_type: str,
        customer_email: str,
        customer_name: str
    ) -> Dict:
        """Provision a new trial"""
        trial = await self.provisioning.provision_trial(
            customer_id=customer_id,
            agent_type=agent_type,
            customer_email=customer_email,
            customer_name=customer_name
        )
        return trial.to_dict()
    
    async def track_task(self, trial_id: str, task: Dict):
        """Track a completed task"""
        await self.usage_tracker.track_task_completed(trial_id, task)
    
    async def track_interaction(
        self,
        trial_id: str,
        interaction_type: str,
        duration_seconds: int,
        metadata: Optional[Dict] = None
    ):
        """Track customer interaction"""
        await self.usage_tracker.track_interaction(
            trial_id, interaction_type, duration_seconds, metadata
        )
    
    async def get_trial_status(self, trial_id: str) -> Dict:
        """Get current trial status and usage"""
        return await self.usage_tracker.get_usage_summary(trial_id)
    
    async def list_trials(
        self,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """List trials with optional filters"""
        query = {}
        if customer_id:
            query["customer_id"] = customer_id
        if status:
            query["status"] = status
        
        trials = await self.db.trials.find(query, limit=limit)
        return [trial for trial in trials]
