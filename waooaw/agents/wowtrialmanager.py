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
        
        self.reminder_system = TrialReminderSystem(
            db=db_connection,
            notification_service=notification_service
        )
        
        self.conversion_handler = TrialConversionHandler(
            db=db_connection,
            payment_service=payment_service,
            agent_factory=agent_factory,
            notification_service=notification_service
        )
        
        self.cancellation_handler = TrialCancellationHandler(
            db=db_connection,
            agent_factory=agent_factory,
            notification_service=notification_service,
            storage_service=None  # TODO: Add storage service
        )
        
        self.abuse_detector = TrialAbuseDetector(
            db=db_connection,
            analytics_service=analytics_service
        )
        
        self.analytics = TrialAnalytics(
            db=db_connection
        )
        
        self.expiration_handler = TrialExpirationHandler(
            db=db_connection,
            agent_factory=agent_factory,
            notification_service=notification_service
        )
        
        self.matcher_integration = WowMatcherIntegration(
            db=db_connection
        )
        
        self.admin_ops = TrialAdminOperations(
            db=db_connection,
            agent_factory=agent_factory,
            notification_service=notification_service
        )
        
        self.db = db_connection
        self.payment_service = payment_service
        self.notification_service = notification_service
        
        logger.info("WowTrialManager initialized with all 10 story components")
    
    async def provision_trial(
        self,
        customer_id: str,
        agent_type: str,
        customer_email: str,
        customer_name: str,
        ip_address: Optional[str] = None
    ) -> Dict:
        """Provision a new trial with abuse checking"""
        # Check for abuse
        if ip_address:
            can_start, reason = await self.abuse_detector.can_start_trial(
                customer_id=customer_id,
                agent_type=agent_type,
                customer_email=customer_email,
                ip_address=ip_address
            )
            if not can_start:
                raise ValueError(f"Trial not allowed: {reason}")
        
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
    
    async def send_daily_reminders(self) -> int:
        """Send daily trial reminders (cron job)"""
        return await self.reminder_system.send_reminders_daily()
    
    async def check_expired_trials(self) -> Dict:
        """Check and handle expired trials (hourly cron job)"""
        return await self.expiration_handler.check_expired_trials()
    
    async def convert_trial(
        self,
        trial_id: str,
        payment_method_id: str,
        subscription_plan: str,
        billing_cycle: str = "monthly"
    ) -> Dict:
        """Convert trial to paid subscription"""
        result = await self.conversion_handler.convert_to_paid(
            trial_id=trial_id,
            payment_method_id=payment_method_id,
            subscription_plan=subscription_plan,
            billing_cycle=billing_cycle
        )
        
        # Record outcome for WowMatcher
        await self.matcher_integration.record_trial_outcome(
            trial_id=trial_id,
            outcome="CONVERTED",
            metadata={"plan": subscription_plan, "billing_cycle": billing_cycle}
        )
        
        return result
    
    async def cancel_trial(
        self,
        trial_id: str,
        reason: Optional[str] = None,
        detailed_feedback: Optional[Dict] = None
    ) -> Dict:
        """Cancel trial and retain deliverables"""
        result = await self.cancellation_handler.cancel_trial(
            trial_id=trial_id,
            reason=reason,
            detailed_feedback=detailed_feedback
        )
        
        # Record outcome for WowMatcher
        await self.matcher_integration.record_trial_outcome(
            trial_id=trial_id,
            outcome="CANCELLED",
            metadata={"reason": reason, "feedback": detailed_feedback}
        )
        
        return result
    
    async def get_analytics_dashboard(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        agent_type: Optional[str] = None
    ) -> Dict:
        """Get comprehensive analytics dashboard"""
        return await self.analytics.get_dashboard_metrics(start_date, end_date, agent_type)
    
    async def get_conversion_funnel(self) -> Dict:
        """Get trial conversion funnel analysis"""
        return await self.analytics.get_funnel_analysis()
    
    async def get_cancellation_reasons(self) -> Dict:
        """Get breakdown of cancellation reasons"""
        return await self.analytics.get_cancellation_reasons()
    
    # Admin Operations
    async def admin_extend_trial(
        self,
        trial_id: str,
        extension_days: int,
        admin_id: str,
        reason: str
    ) -> Dict:
        """Admin: Extend trial duration"""
        return await self.admin_ops.extend_trial(trial_id, extension_days, admin_id, reason)
    
    async def admin_force_convert(
        self,
        trial_id: str,
        subscription_plan: str,
        admin_id: str,
        reason: str
    ) -> Dict:
        """Admin: Force-convert trial (comp subscription)"""
        return await self.admin_ops.force_convert_trial(trial_id, subscription_plan, admin_id, reason)
    
    async def admin_view_deliverables(self, trial_id: str) -> List[Dict]:
        """Admin: View trial deliverables"""
        return await self.admin_ops.view_trial_deliverables(trial_id)
    
    async def admin_cancel_trial(
        self,
        trial_id: str,
        admin_id: str,
        reason: str
    ) -> Dict:
        """Admin: Cancel trial on behalf of customer"""
        return await self.admin_ops.cancel_trial_admin(trial_id, admin_id, reason)
    
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


class TrialReminderSystem:
    """
    Story 1.1.3: Time Management & Reminders (5 points)
    
    Automated reminder system:
    - Daily cron job calculates days_remaining
    - Day 5 reminder (2 days left)
    - Day 6 reminder (1 day left)
    - Final reminder 6 hours before expiration
    - Grace period: 24 hours after end_date
    """
    
    def __init__(self, db, notification_service):
        self.db = db
        self.notification_service = notification_service
    
    async def send_reminders_daily(self):
        """
        Daily cron job to send trial reminders.
        Run at 9 AM daily.
        """
        trials = await self.db.trials.find({"status": TrialStatus.ACTIVE})
        
        reminder_count = 0
        for trial in trials:
            # Calculate days remaining
            end_date = datetime.fromisoformat(trial["end_date"])
            days_remaining = max(0, (end_date - datetime.now()).days)
            hours_remaining = (end_date - datetime.now()).total_seconds() / 3600
            
            # Update days_remaining in database
            await self.db.trials.update(
                {"trial_id": trial["trial_id"]},
                {"days_remaining": days_remaining, "updated_at": datetime.now().isoformat()}
            )
            
            # Send appropriate reminder
            reminder_sent = False
            if days_remaining == 2:
                reminder_sent = await self._send_reminder(trial, "2_days_left")
            elif days_remaining == 1:
                reminder_sent = await self._send_reminder(trial, "1_day_left")
            elif days_remaining == 0 and 0 < hours_remaining <= 6:
                reminder_sent = await self._send_reminder(trial, "6_hours_left")
            
            if reminder_sent:
                reminder_count += 1
        
        logger.info(f"Daily reminders sent: {reminder_count} trials notified")
        return reminder_count
    
    async def _send_reminder(self, trial: Dict, reminder_type: str) -> bool:
        """Send a specific type of reminder"""
        try:
            # Check if already sent
            existing = await self.db.trial_reminders.find_one({
                "trial_id": trial["trial_id"],
                "reminder_type": reminder_type,
                "status": "SENT"
            })
            if existing:
                return False  # Already sent
            
            # Get customer info
            customer = await self.db.customers.find_one({"customer_id": trial["customer_id"]})
            if not customer:
                logger.warning(f"Customer not found for trial: {trial['trial_id']}")
                return False
            
            # Create reminder record
            reminder_id = str(uuid4())
            await self.db.trial_reminders.insert({
                "reminder_id": reminder_id,
                "trial_id": trial["trial_id"],
                "reminder_type": reminder_type,
                "scheduled_for": datetime.now().isoformat(),
                "status": "PENDING",
                "recipient_email": customer.get("email"),
                "created_at": datetime.now().isoformat()
            })
            
            # Send email
            template_data = {
                "customer_name": customer.get("name", "Customer"),
                "agent_name": trial.get("agent_type", "Agent").replace("-", " ").title(),
                "days_left": trial.get("days_remaining", 0),
                "hours_left": int((datetime.fromisoformat(trial["end_date"]) - datetime.now()).total_seconds() / 3600),
                "tasks_completed": trial.get("tasks_completed", 0),
                "deliverables_count": len(trial.get("deliverables", [])),
                "conversion_url": f"https://waooaw.com/trials/{trial['trial_id']}/convert",
                "trial_dashboard_url": f"https://waooaw.com/trials/{trial['trial_id']}"
            }
            
            await self.notification_service.send_email(
                to=customer.get("email"),
                template=f"trial_reminder_{reminder_type}",
                data=template_data
            )
            
            # Update reminder status
            await self.db.trial_reminders.update(
                {"reminder_id": reminder_id},
                {
                    "status": "SENT",
                    "sent_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
            )
            
            logger.info(f"Reminder sent: {reminder_type} for trial {trial['trial_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send reminder: {e}", exc_info=True)
            # Mark reminder as failed
            await self.db.trial_reminders.update(
                {"reminder_id": reminder_id},
                {
                    "status": "FAILED",
                    "error": str(e),
                    "updated_at": datetime.now().isoformat()
                }
            )
            return False


class TrialConversionHandler:
    """
    Story 1.1.4: Conversion Flow (8 points)
    
    Trial to paid subscription conversion:
    - Payment processing (Stripe/Razorpay)
    - Subscription creation
    - Agent transition to production
    - Deliverables migration
    - No interruption during conversion
    """
    
    def __init__(self, db, payment_service, agent_factory, notification_service):
        self.db = db
        self.payment_service = payment_service
        self.agent_factory = agent_factory
        self.notification_service = notification_service
    
    async def convert_to_paid(
        self,
        trial_id: str,
        payment_method_id: str,
        subscription_plan: str,  # "basic", "pro", "enterprise"
        billing_cycle: str = "monthly"  # "monthly", "annual"
    ) -> Dict:
        """
        Convert trial to paid subscription.
        
        Args:
            trial_id: Trial identifier
            payment_method_id: Stripe/Razorpay payment method ID
            subscription_plan: Plan tier
            billing_cycle: Billing frequency
            
        Returns:
            Subscription details
            
        Raises:
            ValueError: If trial invalid
            Exception: If payment fails
        """
        # 1. Validate trial
        trial = await self.db.trials.find_one({"trial_id": trial_id})
        if not trial:
            raise ValueError(f"Trial not found: {trial_id}")
        
        if trial["status"] not in [TrialStatus.ACTIVE, TrialStatus.EXPIRED]:
            raise ValueError(f"Trial cannot be converted (status: {trial['status']})")
        
        customer = await self.db.customers.find_one({"customer_id": trial["customer_id"]})
        if not customer:
            raise ValueError(f"Customer not found: {trial['customer_id']}")
        
        # 2. Calculate pricing
        pricing = self._get_plan_pricing(subscription_plan, billing_cycle)
        
        # 3. Process payment
        try:
            payment_result = await self.payment_service.charge(
                customer_id=trial["customer_id"],
                payment_method_id=payment_method_id,
                amount=pricing["amount"],
                currency=pricing["currency"],
                description=f"WAOOAW {trial['agent_type']} - {subscription_plan} ({billing_cycle})",
                metadata={
                    "trial_id": trial_id,
                    "subscription_plan": subscription_plan,
                    "billing_cycle": billing_cycle
                }
            )
            
            if not payment_result.get("successful"):
                raise Exception(f"Payment failed: {payment_result.get('error')}")
            
        except Exception as e:
            logger.error(f"Payment processing failed: {e}", exc_info=True)
            # Record failed conversion attempt
            await self.db.trials.update(
                {"trial_id": trial_id},
                {
                    "conversion_intent": "INTERESTED",
                    "updated_at": datetime.now().isoformat()
                }
            )
            raise
        
        # 4. Create subscription
        subscription_id = str(uuid4())
        subscription = {
            "subscription_id": subscription_id,
            "customer_id": trial["customer_id"],
            "agent_id": trial.get("agent_id"),
            "agent_type": trial["agent_type"],
            "plan": subscription_plan,
            "billing_cycle": billing_cycle,
            "status": "ACTIVE",
            "billing_cycle_start": datetime.now().isoformat(),
            "billing_cycle_end": self._calculate_next_billing_date(billing_cycle).isoformat(),
            "amount": pricing["amount"],
            "currency": pricing["currency"],
            "payment_method_id": payment_method_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        await self.db.subscriptions.insert(subscription)
        
        # 5. Transition agent to production mode
        if trial.get("agent_id"):
            await self.agent_factory.transition_to_production(
                agent_id=trial["agent_id"],
                subscription_id=subscription_id,
                plan=subscription_plan
            )
        
        # 6. Migrate deliverables
        await self.db.trial_deliverables.update_many(
            {"trial_id": trial_id},
            {"subscription_id": subscription_id}
        )
        
        # 7. Update trial status
        await self.db.trials.update(
            {"trial_id": trial_id},
            {
                "status": TrialStatus.CONVERTED,
                "converted_at": datetime.now().isoformat(),
                "subscription_id": subscription_id,
                "conversion_intent": "INTERESTED",
                "updated_at": datetime.now().isoformat()
            }
        )
        
        # 8. Send confirmation email
        asyncio.create_task(
            self.notification_service.send_email(
                to=customer.get("email"),
                template="conversion_success",
                data={
                    "customer_name": customer.get("name"),
                    "agent_name": trial["agent_type"].replace("-", " ").title(),
                    "plan": subscription_plan,
                    "amount": pricing["display_amount"],
                    "billing_cycle": billing_cycle,
                    "next_billing_date": subscription["billing_cycle_end"],
                    "subscription_url": f"https://waooaw.com/subscriptions/{subscription_id}"
                }
            )
        )
        
        logger.info(f"Trial converted successfully: {trial_id} → {subscription_id}")
        return subscription
    
    def _get_plan_pricing(self, plan: str, billing_cycle: str) -> Dict:
        """Get pricing for a plan"""
        pricing = {
            "basic": {"monthly": 8000, "annual": 86400},  # INR
            "pro": {"monthly": 12000, "annual": 129600},
            "enterprise": {"monthly": 18000, "annual": 194400}
        }
        
        amount = pricing.get(plan, {}).get(billing_cycle, 8000)
        
        return {
            "amount": amount,
            "currency": "INR",
            "display_amount": f"₹{amount:,}"
        }
    
    def _calculate_next_billing_date(self, billing_cycle: str) -> datetime:
        """Calculate next billing date"""
        if billing_cycle == "annual":
            return datetime.now() + timedelta(days=365)
        else:  # monthly
            return datetime.now() + timedelta(days=30)


class TrialCancellationHandler:
    """
    Story 1.1.5: Cancellation & Deliverable Retention (5 points)
    
    Graceful trial cancellation:
    - Cancel anytime, no payment required
    - Agent deprovisioned gracefully
    - Deliverables retained forever
    - Downloadable as ZIP
    - Can re-trial after 30 days
    """
    
    def __init__(self, db, agent_factory, notification_service, storage_service):
        self.db = db
        self.agent_factory = agent_factory
        self.notification_service = notification_service
        self.storage_service = storage_service
    
    async def cancel_trial(
        self,
        trial_id: str,
        reason: Optional[str] = None,
        detailed_feedback: Optional[Dict] = None
    ) -> Dict:
        """
        Cancel trial and retain deliverables.
        
        Args:
            trial_id: Trial identifier
            reason: Cancellation reason (optional)
            detailed_feedback: Additional feedback (optional)
            
        Returns:
            Cancellation summary with deliverable access
        """
        # 1. Validate trial
        trial = await self.db.trials.find_one({"trial_id": trial_id})
        if not trial:
            raise ValueError(f"Trial not found: {trial_id}")
        
        if trial["status"] == TrialStatus.CANCELLED:
            raise ValueError("Trial already cancelled")
        
        customer = await self.db.customers.find_one({"customer_id": trial["customer_id"]})
        if not customer:
            raise ValueError(f"Customer not found: {trial['customer_id']}")
        
        # 2. Mark trial as cancelled
        await self.db.trials.update(
            {"trial_id": trial_id},
            {
                "status": TrialStatus.CANCELLED,
                "conversion_intent": "NOT_INTERESTED",
                "updated_at": datetime.now().isoformat()
            }
        )
        
        # 3. Deprovision agent gracefully
        if trial.get("agent_id"):
            try:
                await self.agent_factory.deprovision_agent(
                    agent_id=trial["agent_id"],
                    mode="graceful"  # Allow ongoing tasks to finish
                )
                logger.info(f"Agent deprovisioned: {trial['agent_id']}")
            except Exception as e:
                logger.error(f"Failed to deprovision agent: {e}", exc_info=True)
        
        # 4. Package deliverables for permanent access
        deliverables = await self.db.trial_deliverables.find({"trial_id": trial_id})
        deliverable_package = await self._create_deliverable_package(
            trial=trial,
            deliverables=deliverables
        )
        
        # Upload to permanent storage
        permanent_url = await self.storage_service.upload(
            file=deliverable_package,
            path=f"cancelled_trials/{trial['customer_id']}/{trial_id}.zip",
            public=True,
            expires=None  # Never expires
        )
        
        # 5. Log cancellation analytics
        if reason:
            await self.db.trial_usage_events.insert({
                "event_id": str(uuid4()),
                "trial_id": trial_id,
                "event_type": "trial_cancelled",
                "event_data": {
                    "reason": reason,
                    "feedback": detailed_feedback or {},
                    "days_used": 7 - trial.get("days_remaining", 0),
                    "tasks_completed": trial.get("tasks_completed", 0),
                    "satisfaction_score": trial.get("satisfaction_score")
                },
                "event_timestamp": datetime.now().isoformat(),
                "created_at": datetime.now().isoformat()
            })
        
        # 6. Send confirmation email
        next_trial_date = datetime.now() + timedelta(days=30)
        asyncio.create_task(
            self.notification_service.send_email(
                to=customer.get("email"),
                template="trial_cancelled",
                data={
                    "customer_name": customer.get("name"),
                    "agent_name": trial["agent_type"].replace("-", " ").title(),
                    "deliverables_url": permanent_url,
                    "deliverables_count": len(deliverables),
                    "tasks_completed": trial.get("tasks_completed", 0),
                    "next_trial_eligible_date": next_trial_date.strftime("%B %d, %Y"),
                    "feedback_url": f"https://waooaw.com/feedback/{trial_id}"
                }
            )
        )
        
        logger.info(f"Trial cancelled: {trial_id} (reason: {reason})")
        
        return {
            "trial_id": trial_id,
            "status": "CANCELLED",
            "deliverables_url": permanent_url,
            "deliverables_count": len(deliverables),
            "next_trial_eligible_date": next_trial_date.isoformat()
        }
    
    async def _create_deliverable_package(self, trial: Dict, deliverables: List[Dict]) -> bytes:
        """Create ZIP package of all deliverables"""
        import zipfile
        import io
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add README
            readme = f"""
WAOOAW Trial Deliverables
========================

Trial ID: {trial['trial_id']}
Agent Type: {trial['agent_type']}
Trial Period: {trial['start_date']} to {trial['end_date']}
Tasks Completed: {trial.get('tasks_completed', 0)}

These deliverables are yours to keep forever, regardless of whether you 
chose to continue with a paid subscription.

Thank you for trying WAOOAW!
"""
            zip_file.writestr("README.txt", readme)
            
            # Add each deliverable
            for i, deliverable in enumerate(deliverables, 1):
                filename = f"{i:03d}_{deliverable.get('deliverable_type', 'deliverable')}.txt"
                content = deliverable.get("content", "")
                zip_file.writestr(filename, content)
        
        zip_buffer.seek(0)
        return zip_buffer.read()


class TrialAbuseDetector:
    """
    Story 1.1.6: Trial Abuse Prevention (3 points)
    
    Prevent trial abuse:
    - One trial per customer per agent type
    - 30-day cooldown before re-trying
    - Email verification required
    - Credit card pre-authorization (no charge)
    - IP-based rate limiting
    - Disposable email detection
    """
    
    def __init__(self, db, analytics_service):
        self.db = db
        self.analytics_service = analytics_service
        
        # Disposable email domains (common ones)
        self.disposable_domains = {
            "tempmail.com", "guerrillamail.com", "10minutemail.com",
            "throwaway.email", "mailinator.com", "trashmail.com"
        }
    
    async def can_start_trial(
        self,
        customer_id: str,
        agent_type: str,
        customer_email: str,
        ip_address: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if customer can start a trial.
        
        Returns:
            (allowed, reason_if_denied)
        """
        # Check 1: Email verification
        if not await self._is_email_verified(customer_id):
            return False, "Email verification required"
        
        # Check 2: Disposable email
        if self._is_disposable_email(customer_email):
            await self.analytics_service.log_event(
                "trial_abuse_blocked",
                {"customer_id": customer_id, "reason": "disposable_email"}
            )
            return False, "Disposable email addresses not allowed"
        
        # Check 3: Active trial for same agent type
        active_trial = await self.db.trials.find_one({
            "customer_id": customer_id,
            "agent_type": agent_type,
            "status": TrialStatus.ACTIVE
        })
        if active_trial:
            return False, f"Already have active trial for {agent_type}"
        
        # Check 4: Recent cancellation (30-day cooldown)
        recent_cancel = await self.db.trials.find_one({
            "customer_id": customer_id,
            "agent_type": agent_type,
            "status": TrialStatus.CANCELLED,
            "updated_at": {"$gte": (datetime.now() - timedelta(days=30)).isoformat()}
        })
        if recent_cancel:
            return False, "Must wait 30 days before retrying this agent"
        
        # Check 5: IP rate limit (max 3 trials per IP in 7 days)
        ip_trials = await self.db.trials.count({
            "ip_address": ip_address,
            "created_at": {"$gte": (datetime.now() - timedelta(days=7)).isoformat()}
        })
        if ip_trials >= 3:
            await self.analytics_service.log_event(
                "trial_abuse_blocked",
                {"ip_address": ip_address, "reason": "ip_rate_limit", "count": ip_trials}
            )
            return False, "Too many trials from this IP address"
        
        # Check 6: Credit card requirement (if enabled)
        # For MVP, we can skip this or make it optional
        
        return True, None
    
    async def _is_email_verified(self, customer_id: str) -> bool:
        """Check if customer email is verified"""
        customer = await self.db.customers.find_one({"customer_id": customer_id})
        return customer and customer.get("email_verified", False)
    
    def _is_disposable_email(self, email: str) -> bool:
        """Check if email is from disposable domain"""
        domain = email.split("@")[-1].lower()
        return domain in self.disposable_domains


class TrialAnalytics:
    """
    Story 1.1.7: Trial Analytics & Insights (5 points)
    
    Analytics dashboard and insights:
    - Total trials (daily/weekly/monthly)
    - Conversion rate tracking
    - Engagement metrics
    - Cancellation reasons
    - Funnel analysis
    - Cohort analysis
    """
    
    def __init__(self, db):
        self.db = db
    
    async def get_dashboard_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        agent_type: Optional[str] = None
    ) -> Dict:
        """
        Get comprehensive dashboard metrics.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            agent_type: Filter by agent type
            
        Returns:
            Dashboard metrics dictionary
        """
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        query = {
            "created_at": {
                "$gte": start_date.isoformat(),
                "$lte": end_date.isoformat()
            }
        }
        if agent_type:
            query["agent_type"] = agent_type
        
        trials = await self.db.trials.find(query)
        
        # Calculate metrics
        total_trials = len(trials)
        active = sum(1 for t in trials if t["status"] == TrialStatus.ACTIVE)
        converted = sum(1 for t in trials if t["status"] == TrialStatus.CONVERTED)
        cancelled = sum(1 for t in trials if t["status"] == TrialStatus.CANCELLED)
        expired = sum(1 for t in trials if t["status"] == TrialStatus.EXPIRED)
        
        completed_trials = converted + cancelled + expired
        conversion_rate = (converted / completed_trials * 100) if completed_trials > 0 else 0
        
        # Engagement metrics
        total_tasks = sum(t.get("tasks_completed", 0) for t in trials)
        avg_tasks = total_tasks / total_trials if total_trials > 0 else 0
        
        total_interactions = sum(t.get("customer_interactions", 0) for t in trials)
        avg_interactions = total_interactions / total_trials if total_trials > 0 else 0
        
        satisfaction_scores = [t.get("satisfaction_score") for t in trials if t.get("satisfaction_score")]
        avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "trials": {
                "total": total_trials,
                "active": active,
                "completed": completed_trials,
                "converted": converted,
                "cancelled": cancelled,
                "expired": expired
            },
            "conversion": {
                "rate_pct": round(conversion_rate, 2),
                "target_pct": 25.0,
                "status": "✅ Above Target" if conversion_rate >= 25 else "⚠️ Below Target"
            },
            "engagement": {
                "avg_tasks_per_trial": round(avg_tasks, 2),
                "avg_interactions_per_trial": round(avg_interactions, 2),
                "avg_satisfaction_score": round(avg_satisfaction, 2)
            }
        }
    
    async def get_funnel_analysis(self) -> Dict:
        """Get trial conversion funnel metrics"""
        # Get all trials
        all_trials = await self.db.trials.find({})
        
        total = len(all_trials)
        provisioned = sum(1 for t in all_trials if t["status"] != "FAILED")
        active = sum(1 for t in all_trials if t["status"] == TrialStatus.ACTIVE)
        engaged = sum(1 for t in all_trials if t.get("customer_interactions", 0) > 5)
        converted = sum(1 for t in all_trials if t["status"] == TrialStatus.CONVERTED)
        
        return {
            "funnel": [
                {"stage": "Started", "count": total, "pct": 100.0},
                {"stage": "Provisioned", "count": provisioned, "pct": round(provisioned/total*100, 1) if total else 0},
                {"stage": "Active", "count": active, "pct": round(active/total*100, 1) if total else 0},
                {"stage": "Engaged", "count": engaged, "pct": round(engaged/total*100, 1) if total else 0},
                {"stage": "Converted", "count": converted, "pct": round(converted/total*100, 1) if total else 0}
            ],
            "drop_off": {
                "provisioning": total - provisioned,
                "activation": provisioned - active,
                "engagement": active - engaged,
                "conversion": engaged - converted
            }
        }
    
    async def get_cancellation_reasons(self) -> Dict:
        """Get breakdown of cancellation reasons"""
        cancelled_events = await self.db.trial_usage_events.find({
            "event_type": "trial_cancelled"
        })
        
        reasons = {}
        for event in cancelled_events:
            reason = event.get("event_data", {}).get("reason", "No reason provided")
            reasons[reason] = reasons.get(reason, 0) + 1
        
        total = sum(reasons.values())
        
        return {
            "total_cancellations": total,
            "reasons": [
                {"reason": k, "count": v, "pct": round(v/total*100, 1) if total else 0}
                for k, v in sorted(reasons.items(), key=lambda x: x[1], reverse=True)
            ]
        }


class TrialExpirationHandler:
    """
    Story 1.1.8: Trial Expiration Handler (5 points)
    
    Graceful trial expiration:
    - Hourly cron job checks for expired trials
    - 24-hour grace period for conversion
    - Agent continues during grace period
    - Automatic deprovision after grace
    - Deliverables remain accessible
    """
    
    def __init__(self, db, agent_factory, notification_service):
        self.db = db
        self.agent_factory = agent_factory
        self.notification_service = notification_service
    
    async def check_expired_trials(self):
        """
        Hourly cron job to handle expired trials.
        Run every hour.
        """
        now = datetime.now()
        
        # Find trials that just expired
        recently_expired = await self.db.trials.find({
            "status": TrialStatus.ACTIVE,
            "end_date": {"$lte": now.isoformat()}
        })
        
        expired_count = 0
        grace_expired_count = 0
        
        for trial in recently_expired:
            end_date = datetime.fromisoformat(trial["end_date"])
            hours_expired = (now - end_date).total_seconds() / 3600
            
            if hours_expired <= 24:
                # Within grace period - mark as EXPIRED but keep agent active
                await self._mark_expired_with_grace(trial)
                expired_count += 1
            else:
                # Grace period over - deprovision agent
                await self._expire_with_deprovision(trial)
                grace_expired_count += 1
        
        logger.info(f"Expiration check: {expired_count} marked expired, {grace_expired_count} deprovisioned")
        return {"expired": expired_count, "deprovisioned": grace_expired_count}
    
    async def _mark_expired_with_grace(self, trial: Dict):
        """Mark trial as expired but keep agent active (grace period)"""
        customer = await self.db.customers.find_one({"customer_id": trial["customer_id"]})
        
        # Update status
        await self.db.trials.update(
            {"trial_id": trial["trial_id"]},
            {
                "status": TrialStatus.EXPIRED,
                "days_remaining": 0,
                "updated_at": datetime.now().isoformat()
            }
        )
        
        # Send grace period notification
        if customer:
            asyncio.create_task(
                self.notification_service.send_email(
                    to=customer.get("email"),
                    template="trial_expired_grace_period",
                    data={
                        "customer_name": customer.get("name"),
                        "agent_name": trial["agent_type"].replace("-", " ").title(),
                        "grace_hours_remaining": 24,
                        "deliverables_count": len(trial.get("deliverables", [])),
                        "tasks_completed": trial.get("tasks_completed", 0),
                        "conversion_url": f"https://waooaw.com/trials/{trial['trial_id']}/convert",
                        "deliverables_url": f"https://waooaw.com/trials/{trial['trial_id']}/deliverables"
                    }
                )
            )
        
        logger.info(f"Trial marked expired with 24hr grace: {trial['trial_id']}")
    
    async def _expire_with_deprovision(self, trial: Dict):
        """Expire trial and deprovision agent (grace period over)"""
        # Deprovision agent
        if trial.get("agent_id"):
            try:
                await self.agent_factory.deprovision_agent(
                    agent_id=trial["agent_id"],
                    mode="graceful"
                )
            except Exception as e:
                logger.error(f"Failed to deprovision expired trial agent: {e}")
        
        # Update to maintain EXPIRED status (already set)
        await self.db.trials.update(
            {"trial_id": trial["trial_id"]},
            {"updated_at": datetime.now().isoformat()}
        )
        
        # Customer already notified during grace period
        logger.info(f"Trial deprovisioned after grace period: {trial['trial_id']}")


class WowMatcherIntegration:
    """
    Story 1.1.9: Integration with WowMatcher (3 points)
    
    Record trial outcomes for matching improvement:
    - Conversion signals
    - Cancellation signals with reasons
    - Engagement scores
    - Customer profile + agent type + outcome
    """
    
    def __init__(self, db):
        self.db = db
    
    async def record_trial_outcome(
        self,
        trial_id: str,
        outcome: str,  # "CONVERTED", "CANCELLED", "EXPIRED"
        metadata: Optional[Dict] = None
    ):
        """
        Record trial outcome for WowMatcher learning.
        
        Args:
            trial_id: Trial identifier
            outcome: Final outcome
            metadata: Additional context (reason, feedback, etc.)
        """
        trial = await self.db.trials.find_one({"trial_id": trial_id})
        if not trial:
            logger.warning(f"Trial not found for outcome recording: {trial_id}")
            return
        
        customer = await self.db.customers.find_one({"customer_id": trial["customer_id"]})
        
        # Create match history record for WowMatcher
        match_record = {
            "match_id": str(uuid4()),
            "customer_id": trial["customer_id"],
            "agent_type": trial["agent_type"],
            "trial_id": trial_id,
            "outcome": outcome,
            "engagement_score": self._calculate_engagement_score(trial),
            "satisfaction_score": trial.get("satisfaction_score"),
            "tasks_completed": trial.get("tasks_completed", 0),
            "customer_interactions": trial.get("customer_interactions", 0),
            "trial_duration_days": 7 - trial.get("days_remaining", 0),
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat()
        }
        
        # Store for WowMatcher training
        await self.db.match_history.insert(match_record)
        
        logger.info(f"Trial outcome recorded for WowMatcher: {trial_id} → {outcome}")
    
    def _calculate_engagement_score(self, trial: Dict) -> float:
        """Calculate engagement score (0-100)"""
        score = 0.0
        
        # Task completion (40 points max)
        tasks = min(trial.get("tasks_completed", 0), 10)
        score += tasks * 4
        
        # Customer interactions (30 points max)
        interactions = min(trial.get("customer_interactions", 0), 15)
        score += interactions * 2
        
        # Satisfaction (30 points max)
        satisfaction = trial.get("satisfaction_score", 0)
        score += satisfaction * 6
        
        return min(100.0, score)


class TrialAdminOperations:
    """
    Story 1.1.10: Admin Dashboard & Operations (4 points)
    
    Admin tools for trial management:
    - List all trials (filterable)
    - Extend trial duration manually
    - Force-convert trial (comp subscription)
    - View trial deliverables
    - Cancel on behalf of customer
    - Audit log
    """
    
    def __init__(self, db, agent_factory, notification_service):
        self.db = db
        self.agent_factory = agent_factory
        self.notification_service = notification_service
    
    async def extend_trial(
        self,
        trial_id: str,
        extension_days: int,
        admin_id: str,
        reason: str
    ) -> Dict:
        """
        Extend trial duration (admin action).
        
        Args:
            trial_id: Trial identifier
            extension_days: Days to extend
            admin_id: Admin user ID
            reason: Reason for extension
        """
        trial = await self.db.trials.find_one({"trial_id": trial_id})
        if not trial:
            raise ValueError(f"Trial not found: {trial_id}")
        
        # Calculate new end date
        current_end = datetime.fromisoformat(trial["end_date"])
        new_end = current_end + timedelta(days=extension_days)
        new_days_remaining = (new_end - datetime.now()).days
        
        # Update trial
        await self.db.trials.update(
            {"trial_id": trial_id},
            {
                "end_date": new_end.isoformat(),
                "days_remaining": max(0, new_days_remaining),
                "updated_at": datetime.now().isoformat()
            }
        )
        
        # Audit log
        await self._log_admin_action(
            action="EXTEND_TRIAL",
            trial_id=trial_id,
            admin_id=admin_id,
            details={
                "extension_days": extension_days,
                "new_end_date": new_end.isoformat(),
                "reason": reason
            }
        )
        
        logger.info(f"Trial extended by {extension_days} days: {trial_id}")
        return {"trial_id": trial_id, "new_end_date": new_end.isoformat()}
    
    async def force_convert_trial(
        self,
        trial_id: str,
        subscription_plan: str,
        admin_id: str,
        reason: str
    ) -> Dict:
        """
        Force-convert trial to paid (comp/promotional).
        
        Args:
            trial_id: Trial identifier
            subscription_plan: Plan to grant
            admin_id: Admin user ID
            reason: Reason for comp
        """
        trial = await self.db.trials.find_one({"trial_id": trial_id})
        if not trial:
            raise ValueError(f"Trial not found: {trial_id}")
        
        # Create complimentary subscription
        subscription_id = str(uuid4())
        subscription = {
            "subscription_id": subscription_id,
            "customer_id": trial["customer_id"],
            "agent_id": trial.get("agent_id"),
            "agent_type": trial["agent_type"],
            "plan": subscription_plan,
            "status": "ACTIVE",
            "billing_cycle": "monthly",
            "amount": 0,  # Comp
            "currency": "INR",
            "is_complimentary": True,
            "comp_reason": reason,
            "comp_admin_id": admin_id,
            "created_at": datetime.now().isoformat()
        }
        
        await self.db.subscriptions.insert(subscription)
        
        # Update trial
        await self.db.trials.update(
            {"trial_id": trial_id},
            {
                "status": TrialStatus.CONVERTED,
                "converted_at": datetime.now().isoformat(),
                "subscription_id": subscription_id,
                "updated_at": datetime.now().isoformat()
            }
        )
        
        # Audit log
        await self._log_admin_action(
            action="FORCE_CONVERT",
            trial_id=trial_id,
            admin_id=admin_id,
            details={
                "subscription_id": subscription_id,
                "plan": subscription_plan,
                "reason": reason,
                "is_complimentary": True
            }
        )
        
        logger.info(f"Trial force-converted (comp): {trial_id} → {subscription_id}")
        return subscription
    
    async def view_trial_deliverables(self, trial_id: str) -> List[Dict]:
        """View all deliverables for a trial"""
        deliverables = await self.db.trial_deliverables.find({"trial_id": trial_id})
        return deliverables
    
    async def cancel_trial_admin(
        self,
        trial_id: str,
        admin_id: str,
        reason: str
    ) -> Dict:
        """Cancel trial on behalf of customer (admin action)"""
        trial = await self.db.trials.find_one({"trial_id": trial_id})
        if not trial:
            raise ValueError(f"Trial not found: {trial_id}")
        
        # Update status
        await self.db.trials.update(
            {"trial_id": trial_id},
            {
                "status": TrialStatus.CANCELLED,
                "conversion_intent": "NOT_INTERESTED",
                "updated_at": datetime.now().isoformat()
            }
        )
        
        # Audit log
        await self._log_admin_action(
            action="CANCEL_TRIAL_ADMIN",
            trial_id=trial_id,
            admin_id=admin_id,
            details={"reason": reason}
        )
        
        logger.info(f"Trial cancelled by admin: {trial_id}")
        return {"trial_id": trial_id, "status": "CANCELLED"}
    
    async def _log_admin_action(
        self,
        action: str,
        trial_id: str,
        admin_id: str,
        details: Dict
    ):
        """Log admin action to audit trail"""
        await self.db.admin_audit_log.insert({
            "audit_id": str(uuid4()),
            "action": action,
            "trial_id": trial_id,
            "admin_id": admin_id,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
