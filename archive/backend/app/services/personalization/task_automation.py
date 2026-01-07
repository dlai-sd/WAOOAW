"""
Predictive Task Automation - Story 5.5.3

Agents automatically complete recurring tasks without being asked.
Enables proactive value delivery and reduces customer cognitive load.

Epic 5.5: Hyper-Personalization & Adaptation (68 points)
Story Points: 13
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from .customer_behavior_model import TaskPattern


class AutomationType(Enum):
    """Type of task automation"""
    SCHEDULED = "scheduled"  # Cron-like schedule (every Monday 9am)
    PATTERN_BASED = "pattern_based"  # After task X, do task Y
    CALENDAR_DRIVEN = "calendar_driven"  # End of month, quarter, etc.
    EVENT_TRIGGERED = "event_triggered"  # External event triggers task


class ApprovalMode(Enum):
    """How automation requires approval"""
    AUTO_EXECUTE = "auto_execute"  # Execute automatically (pre-approved)
    SUGGEST = "suggest"  # Suggest to customer, wait for approval
    SILENT_PREPARE = "silent_prepare"  # Prepare in background, notify when ready


class AutomationStatus(Enum):
    """Status of automation rule"""
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    EXPIRED = "expired"


class ExecutionStatus(Enum):
    """Status of automation execution"""
    PENDING = "pending"
    SUGGESTED = "suggested"  # Waiting for customer approval
    APPROVED = "approved"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScheduleConfig:
    """Configuration for scheduled automation"""
    cron_expression: str  # e.g., "0 9 * * 1" (Every Monday 9am)
    timezone: str = "UTC"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cron_expression": self.cron_expression,
            "timezone": self.timezone,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None
        }


@dataclass
class PatternTrigger:
    """Trigger based on task patterns"""
    preceding_task_category: str  # Task that triggers automation
    wait_time_minutes: int = 60  # Wait time after preceding task
    condition: Optional[str] = None  # Optional condition (e.g., "if rating >= 4")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "preceding_task_category": self.preceding_task_category,
            "wait_time_minutes": self.wait_time_minutes,
            "condition": self.condition
        }


@dataclass
class CalendarTrigger:
    """Trigger based on calendar events"""
    trigger_type: str  # "end_of_month", "end_of_quarter", "end_of_year", "day_of_month"
    day_of_month: Optional[int] = None  # For "day_of_month" type
    time_of_day: str = "09:00"  # HH:MM format
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trigger_type": self.trigger_type,
            "day_of_month": self.day_of_month,
            "time_of_day": self.time_of_day
        }


@dataclass
class EventTrigger:
    """Trigger based on external events"""
    event_type: str  # "product_launch", "campaign_start", "deadline_approaching", etc.
    event_source: str = "platform"  # Where event comes from
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_source": self.event_source
        }


@dataclass
class AutomationRule:
    """Rule defining task automation"""
    rule_id: str
    customer_id: str
    automation_type: AutomationType
    
    # Task to automate
    task_category: str
    task_template: str  # Template for task description
    agent_variant_id: str
    
    # Trigger configuration
    schedule: Optional[ScheduleConfig] = None
    pattern_trigger: Optional[PatternTrigger] = None
    calendar_trigger: Optional[CalendarTrigger] = None
    event_trigger: Optional[EventTrigger] = None
    
    # Approval settings
    approval_mode: ApprovalMode = ApprovalMode.SUGGEST
    
    # Status and metadata
    status: AutomationStatus = AutomationStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    last_executed: Optional[datetime] = None
    execution_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "rule_id": self.rule_id,
            "customer_id": self.customer_id,
            "automation_type": self.automation_type.value,
            "task_category": self.task_category,
            "task_template": self.task_template,
            "agent_variant_id": self.agent_variant_id,
            "schedule": self.schedule.to_dict() if self.schedule else None,
            "pattern_trigger": self.pattern_trigger.to_dict() if self.pattern_trigger else None,
            "calendar_trigger": self.calendar_trigger.to_dict() if self.calendar_trigger else None,
            "event_trigger": self.event_trigger.to_dict() if self.event_trigger else None,
            "approval_mode": self.approval_mode.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_executed": self.last_executed.isoformat() if self.last_executed else None,
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "metadata": self.metadata
        }


@dataclass
class AutomationExecution:
    """Single execution of an automation rule"""
    execution_id: str
    rule_id: str
    customer_id: str
    
    # Task details
    task_category: str
    task_description: str
    agent_variant_id: str
    
    # Execution status
    status: ExecutionStatus
    triggered_at: datetime = field(default_factory=datetime.now)
    suggested_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Results
    output: Optional[str] = None
    error_message: Optional[str] = None
    customer_feedback: Optional[str] = None
    rating: Optional[float] = None
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "execution_id": self.execution_id,
            "rule_id": self.rule_id,
            "customer_id": self.customer_id,
            "task_category": self.task_category,
            "task_description": self.task_description,
            "agent_variant_id": self.agent_variant_id,
            "status": self.status.value,
            "triggered_at": self.triggered_at.isoformat(),
            "suggested_at": self.suggested_at.isoformat() if self.suggested_at else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "output": self.output,
            "error_message": self.error_message,
            "customer_feedback": self.customer_feedback,
            "rating": self.rating,
            "metadata": self.metadata
        }


class TaskAutomationEngine:
    """
    Predictive task automation engine.
    
    Automatically completes recurring tasks based on patterns, schedules,
    calendar events, or external triggers.
    """
    
    def __init__(self):
        """Initialize automation engine"""
        self._rules: Dict[str, AutomationRule] = {}
        self._executions: Dict[str, AutomationExecution] = {}
        self._customer_rules: Dict[str, List[str]] = {}  # customer_id -> [rule_ids]
        
        # Task tracking for pattern detection
        self._recent_tasks: Dict[str, List[Dict[str, Any]]] = {}  # customer_id -> recent tasks
        
        # Event listeners (would connect to event bus in production)
        self._event_listeners: Dict[str, List[Callable]] = {}
    
    def create_automation_rule(
        self,
        customer_id: str,
        automation_type: AutomationType,
        task_category: str,
        task_template: str,
        agent_variant_id: str,
        approval_mode: ApprovalMode = ApprovalMode.SUGGEST,
        **trigger_config
    ) -> AutomationRule:
        """
        Create a new automation rule.
        
        Args:
            customer_id: Customer identifier
            automation_type: Type of automation
            task_category: Category of task to automate
            task_template: Template for task description (can include {variables})
            agent_variant_id: Agent to execute task
            approval_mode: How to handle approval
            **trigger_config: Trigger-specific configuration
            
        Returns:
            Created automation rule
        """
        rule_id = f"rule_{customer_id}_{datetime.now().timestamp()}"
        
        # Parse trigger configuration based on type
        schedule = None
        pattern_trigger = None
        calendar_trigger = None
        event_trigger = None
        
        if automation_type == AutomationType.SCHEDULED:
            schedule = ScheduleConfig(**trigger_config)
        elif automation_type == AutomationType.PATTERN_BASED:
            pattern_trigger = PatternTrigger(**trigger_config)
        elif automation_type == AutomationType.CALENDAR_DRIVEN:
            calendar_trigger = CalendarTrigger(**trigger_config)
        elif automation_type == AutomationType.EVENT_TRIGGERED:
            event_trigger = EventTrigger(**trigger_config)
        
        rule = AutomationRule(
            rule_id=rule_id,
            customer_id=customer_id,
            automation_type=automation_type,
            task_category=task_category,
            task_template=task_template,
            agent_variant_id=agent_variant_id,
            schedule=schedule,
            pattern_trigger=pattern_trigger,
            calendar_trigger=calendar_trigger,
            event_trigger=event_trigger,
            approval_mode=approval_mode
        )
        
        # Store rule
        self._rules[rule_id] = rule
        
        if customer_id not in self._customer_rules:
            self._customer_rules[customer_id] = []
        self._customer_rules[customer_id].append(rule_id)
        
        return rule
    
    def record_task_completion(
        self,
        customer_id: str,
        task_category: str,
        agent_variant_id: str,
        rating: Optional[float] = None
    ) -> None:
        """
        Record task completion for pattern-based automation detection.
        
        Args:
            customer_id: Customer identifier
            task_category: Task category
            agent_variant_id: Agent that completed task
            rating: Optional task rating
        """
        if customer_id not in self._recent_tasks:
            self._recent_tasks[customer_id] = []
        
        task_record = {
            "task_category": task_category,
            "agent_variant_id": agent_variant_id,
            "completed_at": datetime.now(),
            "rating": rating
        }
        
        self._recent_tasks[customer_id].append(task_record)
        
        # Keep only last 50 tasks per customer
        self._recent_tasks[customer_id] = self._recent_tasks[customer_id][-50:]
        
        # Check if this triggers any pattern-based rules
        self._check_pattern_triggers(customer_id, task_category, rating)
    
    def _check_pattern_triggers(
        self,
        customer_id: str,
        completed_task_category: str,
        rating: Optional[float]
    ) -> None:
        """Check if completed task triggers any pattern-based automation"""
        customer_rules = self._customer_rules.get(customer_id, [])
        
        for rule_id in customer_rules:
            rule = self._rules[rule_id]
            
            # Only check pattern-based rules that are active
            if (rule.automation_type != AutomationType.PATTERN_BASED or
                rule.status != AutomationStatus.ACTIVE or
                not rule.pattern_trigger):
                continue
            
            # Check if preceding task matches
            if rule.pattern_trigger.preceding_task_category != completed_task_category:
                continue
            
            # Check condition if specified
            if rule.pattern_trigger.condition:
                if "rating >= " in rule.pattern_trigger.condition:
                    min_rating = float(rule.pattern_trigger.condition.split(">=")[1].strip())
                    if not rating or rating < min_rating:
                        continue
            
            # Trigger the automation (with wait time if specified)
            self._trigger_automation(rule, wait_minutes=rule.pattern_trigger.wait_time_minutes)
    
    def _trigger_automation(
        self,
        rule: AutomationRule,
        wait_minutes: int = 0
    ) -> AutomationExecution:
        """
        Trigger an automation rule execution.
        
        Args:
            rule: Automation rule to execute
            wait_minutes: Minutes to wait before execution
            
        Returns:
            Created execution
        """
        execution_id = f"exec_{rule.rule_id}_{datetime.now().timestamp()}"
        
        # Generate task description from template
        task_description = self._generate_task_description(rule)
        
        # Determine initial status based on approval mode
        if rule.approval_mode == ApprovalMode.AUTO_EXECUTE:
            status = ExecutionStatus.PENDING
        elif rule.approval_mode == ApprovalMode.SUGGEST:
            status = ExecutionStatus.SUGGESTED
        else:  # SILENT_PREPARE
            status = ExecutionStatus.PENDING
        
        execution = AutomationExecution(
            execution_id=execution_id,
            rule_id=rule.rule_id,
            customer_id=rule.customer_id,
            task_category=rule.task_category,
            task_description=task_description,
            agent_variant_id=rule.agent_variant_id,
            status=status,
            metadata={"wait_minutes": wait_minutes}
        )
        
        if status == ExecutionStatus.SUGGESTED:
            execution.suggested_at = datetime.now()
        
        # Store execution
        self._executions[execution_id] = execution
        
        # Update rule statistics
        rule.execution_count += 1
        rule.last_executed = datetime.now()
        
        return execution
    
    def _generate_task_description(self, rule: AutomationRule) -> str:
        """Generate task description from template with context"""
        # In production, this would fill in template variables with customer context
        # For now, return template as-is
        description = rule.task_template
        
        # Add timestamp context
        now = datetime.now()
        description = description.replace("{date}", now.strftime("%Y-%m-%d"))
        description = description.replace("{week}", now.strftime("%U"))
        description = description.replace("{month}", now.strftime("%B"))
        description = description.replace("{year}", str(now.year))
        
        return description
    
    def approve_execution(self, execution_id: str) -> bool:
        """
        Approve a suggested automation execution.
        
        Args:
            execution_id: Execution identifier
            
        Returns:
            True if approved successfully
        """
        execution = self._executions.get(execution_id)
        if not execution or execution.status != ExecutionStatus.SUGGESTED:
            return False
        
        execution.status = ExecutionStatus.APPROVED
        execution.approved_at = datetime.now()
        
        return True
    
    def cancel_execution(self, execution_id: str) -> bool:
        """
        Cancel a pending or suggested execution.
        
        Args:
            execution_id: Execution identifier
            
        Returns:
            True if cancelled successfully
        """
        execution = self._executions.get(execution_id)
        if not execution or execution.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]:
            return False
        
        execution.status = ExecutionStatus.CANCELLED
        execution.completed_at = datetime.now()
        
        return True
    
    def record_execution_result(
        self,
        execution_id: str,
        success: bool,
        output: Optional[str] = None,
        error_message: Optional[str] = None,
        rating: Optional[float] = None,
        feedback: Optional[str] = None
    ) -> bool:
        """
        Record the result of an execution.
        
        Args:
            execution_id: Execution identifier
            success: Whether execution succeeded
            output: Task output (if successful)
            error_message: Error message (if failed)
            rating: Customer rating
            feedback: Customer feedback
            
        Returns:
            True if recorded successfully
        """
        execution = self._executions.get(execution_id)
        if not execution:
            return False
        
        execution.status = ExecutionStatus.COMPLETED if success else ExecutionStatus.FAILED
        execution.completed_at = datetime.now()
        execution.output = output
        execution.error_message = error_message
        execution.rating = rating
        execution.customer_feedback = feedback
        
        # Update rule statistics
        rule = self._rules.get(execution.rule_id)
        if rule:
            if success:
                rule.success_count += 1
            else:
                rule.failure_count += 1
        
        return True
    
    def get_customer_rules(self, customer_id: str) -> List[AutomationRule]:
        """Get all automation rules for a customer"""
        rule_ids = self._customer_rules.get(customer_id, [])
        return [self._rules[rid] for rid in rule_ids]
    
    def get_pending_executions(self, customer_id: str) -> List[AutomationExecution]:
        """Get pending/suggested executions for a customer"""
        return [
            exec for exec in self._executions.values()
            if exec.customer_id == customer_id and
            exec.status in [ExecutionStatus.PENDING, ExecutionStatus.SUGGESTED, ExecutionStatus.APPROVED]
        ]
    
    def pause_rule(self, rule_id: str) -> bool:
        """Pause an automation rule"""
        rule = self._rules.get(rule_id)
        if not rule or rule.status == AutomationStatus.DISABLED:
            return False
        
        rule.status = AutomationStatus.PAUSED
        return True
    
    def resume_rule(self, rule_id: str) -> bool:
        """Resume a paused automation rule"""
        rule = self._rules.get(rule_id)
        if not rule or rule.status != AutomationStatus.PAUSED:
            return False
        
        rule.status = AutomationStatus.ACTIVE
        return True
    
    def disable_rule(self, rule_id: str) -> bool:
        """Permanently disable an automation rule"""
        rule = self._rules.get(rule_id)
        if not rule:
            return False
        
        rule.status = AutomationStatus.DISABLED
        return True
    
    def get_rule_performance(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """Get performance statistics for a rule"""
        rule = self._rules.get(rule_id)
        if not rule:
            return None
        
        success_rate = rule.success_count / rule.execution_count if rule.execution_count > 0 else 0.0
        
        # Get ratings for this rule's executions
        rule_executions = [e for e in self._executions.values() if e.rule_id == rule_id]
        ratings = [e.rating for e in rule_executions if e.rating is not None]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0.0
        
        return {
            "rule_id": rule_id,
            "execution_count": rule.execution_count,
            "success_count": rule.success_count,
            "failure_count": rule.failure_count,
            "success_rate": success_rate,
            "average_rating": avg_rating,
            "last_executed": rule.last_executed.isoformat() if rule.last_executed else None,
            "status": rule.status.value
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get engine statistics"""
        total_rules = len(self._rules)
        active_rules = sum(1 for r in self._rules.values() if r.status == AutomationStatus.ACTIVE)
        total_executions = len(self._executions)
        completed_executions = sum(1 for e in self._executions.values() if e.status == ExecutionStatus.COMPLETED)
        
        # Automation type breakdown
        type_counts = {}
        for rule in self._rules.values():
            type_name = rule.automation_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        return {
            "total_rules": total_rules,
            "active_rules": active_rules,
            "paused_rules": sum(1 for r in self._rules.values() if r.status == AutomationStatus.PAUSED),
            "disabled_rules": sum(1 for r in self._rules.values() if r.status == AutomationStatus.DISABLED),
            "total_executions": total_executions,
            "completed_executions": completed_executions,
            "pending_executions": sum(1 for e in self._executions.values() if e.status == ExecutionStatus.PENDING),
            "suggested_executions": sum(1 for e in self._executions.values() if e.status == ExecutionStatus.SUGGESTED),
            "automation_types": type_counts,
            "customers_with_automation": len(self._customer_rules)
        }
