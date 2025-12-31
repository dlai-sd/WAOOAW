"""
Contextual Error Recovery - Story 5.5.4

Epic 5.5: Hyper-Personalization & Adaptation

Intelligent mistake recovery when agents fail or customers are dissatisfied.
Provides error detection, self-diagnosis, alternative approaches, clarification
questions, and escalation mechanisms for continuous improvement.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
import re


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"           # Minor issues, agent can self-correct
    MEDIUM = "medium"     # Noticeable problems, needs alternative approach
    HIGH = "high"         # Significant failure, may need human review
    CRITICAL = "critical" # Complete failure, requires escalation


class ErrorCategory(Enum):
    """Types of errors that can occur"""
    QUALITY_ISSUE = "quality_issue"           # Output quality below standards
    MISUNDERSTANDING = "misunderstanding"     # Agent misunderstood requirement
    INCOMPLETE = "incomplete"                 # Task not fully completed
    INCORRECT_APPROACH = "incorrect_approach" # Wrong method/strategy used
    TECHNICAL_ERROR = "technical_error"       # System/tool failure
    TIMEOUT = "timeout"                       # Task took too long
    OUT_OF_SCOPE = "out_of_scope"            # Beyond agent capabilities


class RecoveryStrategy(Enum):
    """Recovery strategies available"""
    RETRY_SAME = "retry_same"                 # Retry with same approach
    ALTERNATIVE_APPROACH = "alternative"       # Try different method
    CLARIFY_REQUIREMENTS = "clarify"          # Ask clarifying questions
    SIMPLIFY_TASK = "simplify"                # Break into smaller subtasks
    ESCALATE_HUMAN = "escalate"               # Flag for human review
    SWITCH_AGENT = "switch_agent"             # Assign to different agent variant


class RecoveryStatus(Enum):
    """Status of recovery attempt"""
    PENDING = "pending"           # Recovery not yet attempted
    IN_PROGRESS = "in_progress"   # Currently attempting recovery
    CLARIFYING = "clarifying"     # Waiting for customer clarification
    RESOLVED = "resolved"         # Successfully recovered
    ESCALATED = "escalated"       # Escalated to human
    FAILED = "failed"            # Recovery attempt failed


@dataclass
class ErrorContext:
    """Context information about an error"""
    task_id: str
    customer_id: str
    agent_variant_id: str
    task_category: str
    task_description: str
    original_output: Optional[str]
    error_message: Optional[str]
    customer_rating: Optional[float]
    customer_feedback: Optional[str]
    execution_time_seconds: Optional[float]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "task_id": self.task_id,
            "customer_id": self.customer_id,
            "agent_variant_id": self.agent_variant_id,
            "task_category": self.task_category,
            "task_description": self.task_description,
            "original_output": self.original_output,
            "error_message": self.error_message,
            "customer_rating": self.customer_rating,
            "customer_feedback": self.customer_feedback,
            "execution_time_seconds": self.execution_time_seconds,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ErrorDiagnosis:
    """Diagnostic analysis of an error"""
    error_id: str
    error_category: ErrorCategory
    error_severity: ErrorSeverity
    root_cause: str
    contributing_factors: List[str]
    similar_successful_tasks: List[str]  # Task IDs of successful similar tasks
    recommended_strategy: RecoveryStrategy
    alternative_strategies: List[RecoveryStrategy]
    clarification_questions: List[str]
    confidence_score: float  # 0.0 to 1.0, how confident in diagnosis
    diagnosed_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "error_id": self.error_id,
            "error_category": self.error_category.value,
            "error_severity": self.error_severity.value,
            "root_cause": self.root_cause,
            "contributing_factors": self.contributing_factors,
            "similar_successful_tasks": self.similar_successful_tasks,
            "recommended_strategy": self.recommended_strategy.value,
            "alternative_strategies": [s.value for s in self.alternative_strategies],
            "clarification_questions": self.clarification_questions,
            "confidence_score": self.confidence_score,
            "diagnosed_at": self.diagnosed_at.isoformat(),
        }


@dataclass
class RecoveryAttempt:
    """A single recovery attempt"""
    attempt_id: str
    error_id: str
    strategy: RecoveryStrategy
    status: RecoveryStatus
    modified_task_description: Optional[str]
    alternative_approach_description: Optional[str]
    clarification_request: Optional[str]
    new_output: Optional[str]
    success: bool
    customer_rating: Optional[float]
    customer_feedback: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "attempt_id": self.attempt_id,
            "error_id": self.error_id,
            "strategy": self.strategy.value,
            "status": self.status.value,
            "modified_task_description": self.modified_task_description,
            "alternative_approach_description": self.alternative_approach_description,
            "clarification_request": self.clarification_request,
            "new_output": self.new_output,
            "success": self.success,
            "customer_rating": self.customer_rating,
            "customer_feedback": self.customer_feedback,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class RecoveryCase:
    """Complete recovery case from error to resolution"""
    error_id: str
    context: ErrorContext
    diagnosis: Optional[ErrorDiagnosis]
    attempts: List[RecoveryAttempt]
    final_status: RecoveryStatus
    lessons_learned: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "error_id": self.error_id,
            "context": self.context.to_dict(),
            "diagnosis": self.diagnosis.to_dict() if self.diagnosis else None,
            "attempts": [a.to_dict() for a in self.attempts],
            "final_status": self.final_status.value,
            "lessons_learned": self.lessons_learned,
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


class ErrorRecoveryEngine:
    """
    Intelligent error recovery and learning system.
    
    Detects errors, diagnoses root causes, attempts recovery with multiple
    strategies, and learns from outcomes to improve future performance.
    """
    
    def __init__(self):
        self._cases: Dict[str, RecoveryCase] = {}  # error_id -> RecoveryCase
        self._customer_cases: Dict[str, List[str]] = {}  # customer_id -> error_ids
        self._task_history: Dict[str, List[Dict]] = {}  # customer_id -> task history
        self._recovery_patterns: Dict[str, List[Dict]] = {}  # error_category -> successful recoveries
        
    def detect_error(
        self,
        task_id: str,
        customer_id: str,
        agent_variant_id: str,
        task_category: str,
        task_description: str,
        output: Optional[str] = None,
        error_message: Optional[str] = None,
        rating: Optional[float] = None,
        feedback: Optional[str] = None,
        execution_time_seconds: Optional[float] = None
    ) -> Optional[str]:
        """
        Detect if an error occurred based on various signals.
        
        Returns error_id if error detected, None otherwise.
        """
        # Error detection logic
        is_error = False
        
        # 1. Low rating (< 3.0 stars)
        if rating is not None and rating < 3.0:
            is_error = True
        
        # 2. Explicit error message
        if error_message:
            is_error = True
        
        # 3. Negative feedback keywords
        if feedback:
            negative_keywords = [
                "wrong", "incorrect", "mistake", "error", "bad", "poor",
                "disappointed", "unsatisfied", "not what I wanted",
                "misunderstood", "incomplete", "missing"
            ]
            if any(keyword in feedback.lower() for keyword in negative_keywords):
                is_error = True
        
        # 4. Re-request (same customer asking for same task category within short time)
        if customer_id in self._task_history:
            recent_tasks = self._task_history[customer_id][-5:]  # Last 5 tasks
            same_category_count = sum(
                1 for t in recent_tasks if t["category"] == task_category
            )
            if same_category_count >= 2:
                is_error = True
        
        if not is_error:
            return None
        
        # Create error case
        error_id = f"error_{customer_id}_{datetime.utcnow().timestamp()}"
        
        context = ErrorContext(
            task_id=task_id,
            customer_id=customer_id,
            agent_variant_id=agent_variant_id,
            task_category=task_category,
            task_description=task_description,
            original_output=output,
            error_message=error_message,
            customer_rating=rating,
            customer_feedback=feedback,
            execution_time_seconds=execution_time_seconds
        )
        
        case = RecoveryCase(
            error_id=error_id,
            context=context,
            diagnosis=None,
            attempts=[],
            final_status=RecoveryStatus.PENDING
        )
        
        self._cases[error_id] = case
        
        if customer_id not in self._customer_cases:
            self._customer_cases[customer_id] = []
        self._customer_cases[customer_id].append(error_id)
        
        return error_id
    
    def diagnose_error(self, error_id: str) -> Optional[ErrorDiagnosis]:
        """
        Diagnose the root cause of an error and recommend recovery strategy.
        """
        if error_id not in self._cases:
            return None
        
        case = self._cases[error_id]
        context = case.context
        
        # Determine error category and severity
        category, severity = self._categorize_error(context)
        
        # Analyze root cause
        root_cause = self._analyze_root_cause(context, category)
        
        # Find contributing factors
        contributing_factors = self._find_contributing_factors(context)
        
        # Find similar successful tasks
        similar_tasks = self._find_similar_successful_tasks(context)
        
        # Recommend recovery strategy
        recommended_strategy, alternatives = self._recommend_strategy(
            category, severity, context
        )
        
        # Generate clarification questions if needed
        clarification_questions = self._generate_clarification_questions(
            context, category
        )
        
        # Calculate confidence
        confidence = self._calculate_diagnosis_confidence(
            context, similar_tasks, category
        )
        
        diagnosis = ErrorDiagnosis(
            error_id=error_id,
            error_category=category,
            error_severity=severity,
            root_cause=root_cause,
            contributing_factors=contributing_factors,
            similar_successful_tasks=similar_tasks,
            recommended_strategy=recommended_strategy,
            alternative_strategies=alternatives,
            clarification_questions=clarification_questions,
            confidence_score=confidence
        )
        
        case.diagnosis = diagnosis
        return diagnosis
    
    def attempt_recovery(
        self,
        error_id: str,
        strategy: Optional[RecoveryStrategy] = None
    ) -> Optional[RecoveryAttempt]:
        """
        Attempt to recover from error using specified or recommended strategy.
        """
        if error_id not in self._cases:
            return None
        
        case = self._cases[error_id]
        
        # Use recommended strategy if none provided
        if strategy is None:
            if case.diagnosis is None:
                self.diagnose_error(error_id)
            strategy = case.diagnosis.recommended_strategy
        
        # Generate attempt_id
        attempt_id = f"attempt_{error_id}_{len(case.attempts) + 1}"
        
        # Create recovery attempt based on strategy
        attempt = self._create_recovery_attempt(
            attempt_id, error_id, strategy, case.context
        )
        
        case.attempts.append(attempt)
        
        return attempt
    
    def record_recovery_result(
        self,
        attempt_id: str,
        success: bool,
        new_output: Optional[str] = None,
        rating: Optional[float] = None,
        feedback: Optional[str] = None
    ) -> bool:
        """
        Record the result of a recovery attempt.
        """
        # Find the case containing this attempt
        case = None
        attempt = None
        
        for c in self._cases.values():
            for a in c.attempts:
                if a.attempt_id == attempt_id:
                    case = c
                    attempt = a
                    break
            if attempt:
                break
        
        if not attempt:
            return False
        
        # Update attempt
        attempt.success = success
        attempt.new_output = new_output
        attempt.customer_rating = rating
        attempt.customer_feedback = feedback
        attempt.completed_at = datetime.utcnow()
        
        if success:
            attempt.status = RecoveryStatus.RESOLVED
            case.final_status = RecoveryStatus.RESOLVED
            case.resolved_at = datetime.utcnow()
            
            # Learn from successful recovery
            self._learn_from_recovery(case, attempt)
        else:
            attempt.status = RecoveryStatus.FAILED
        
        return True
    
    def escalate_to_human(self, error_id: str, reason: str) -> bool:
        """
        Escalate error to human review.
        """
        if error_id not in self._cases:
            return False
        
        case = self._cases[error_id]
        case.final_status = RecoveryStatus.ESCALATED
        case.lessons_learned.append(f"Escalated: {reason}")
        
        return True
    
    def get_recovery_case(self, error_id: str) -> Optional[RecoveryCase]:
        """Get complete recovery case information"""
        return self._cases.get(error_id)
    
    def get_customer_recovery_history(self, customer_id: str) -> List[RecoveryCase]:
        """Get all recovery cases for a customer"""
        error_ids = self._customer_cases.get(customer_id, [])
        return [self._cases[eid] for eid in error_ids if eid in self._cases]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get recovery statistics"""
        total_cases = len(self._cases)
        
        resolved = sum(1 for c in self._cases.values() if c.final_status == RecoveryStatus.RESOLVED)
        escalated = sum(1 for c in self._cases.values() if c.final_status == RecoveryStatus.ESCALATED)
        pending = sum(1 for c in self._cases.values() if c.final_status == RecoveryStatus.PENDING)
        
        # Category breakdown
        category_counts = {}
        for case in self._cases.values():
            if case.diagnosis:
                cat = case.diagnosis.error_category.value
                category_counts[cat] = category_counts.get(cat, 0) + 1
        
        # Strategy effectiveness
        strategy_success = {}
        strategy_total = {}
        for case in self._cases.values():
            for attempt in case.attempts:
                strat = attempt.strategy.value
                strategy_total[strat] = strategy_total.get(strat, 0) + 1
                if attempt.success:
                    strategy_success[strat] = strategy_success.get(strat, 0) + 1
        
        strategy_effectiveness = {
            strat: (strategy_success.get(strat, 0) / total * 100 if total > 0 else 0)
            for strat, total in strategy_total.items()
        }
        
        return {
            "total_cases": total_cases,
            "resolved": resolved,
            "escalated": escalated,
            "pending": pending,
            "resolution_rate": (resolved / total_cases * 100) if total_cases > 0 else 0,
            "escalation_rate": (escalated / total_cases * 100) if total_cases > 0 else 0,
            "category_breakdown": category_counts,
            "strategy_effectiveness": strategy_effectiveness,
            "customers_with_errors": len(self._customer_cases)
        }
    
    # Private helper methods
    
    def _categorize_error(self, context: ErrorContext) -> tuple[ErrorCategory, ErrorSeverity]:
        """Categorize error type and severity"""
        # Default
        category = ErrorCategory.QUALITY_ISSUE
        severity = ErrorSeverity.MEDIUM
        
        # Check error message
        if context.error_message:
            error_lower = context.error_message.lower()
            if "timeout" in error_lower or "timed out" in error_lower:
                category = ErrorCategory.TIMEOUT
                severity = ErrorSeverity.HIGH
            elif "exception" in error_lower or "error" in error_lower:
                category = ErrorCategory.TECHNICAL_ERROR
                severity = ErrorSeverity.HIGH
        
        # Check feedback
        if context.customer_feedback:
            feedback_lower = context.customer_feedback.lower()
            if "misunderstood" in feedback_lower or "not what I asked" in feedback_lower:
                category = ErrorCategory.MISUNDERSTANDING
            elif "incomplete" in feedback_lower or "missing" in feedback_lower:
                category = ErrorCategory.INCOMPLETE
            elif "wrong approach" in feedback_lower or "different method" in feedback_lower:
                category = ErrorCategory.INCORRECT_APPROACH
        
        # Check rating for severity
        if context.customer_rating is not None:
            if context.customer_rating < 2.0:
                severity = ErrorSeverity.HIGH
            elif context.customer_rating < 2.5:
                severity = ErrorSeverity.MEDIUM
            else:
                severity = ErrorSeverity.LOW
        
        return category, severity
    
    def _analyze_root_cause(self, context: ErrorContext, category: ErrorCategory) -> str:
        """Analyze root cause of error"""
        if category == ErrorCategory.MISUNDERSTANDING:
            return "Agent misinterpreted customer requirements or lacked context"
        elif category == ErrorCategory.INCOMPLETE:
            return "Task scope was larger than agent anticipated or time constraints"
        elif category == ErrorCategory.INCORRECT_APPROACH:
            return "Agent chose suboptimal method for this specific customer/situation"
        elif category == ErrorCategory.TECHNICAL_ERROR:
            return "System or tool failure during execution"
        elif category == ErrorCategory.TIMEOUT:
            return "Task complexity exceeded allocated time budget"
        else:
            return "Output quality did not meet customer expectations"
    
    def _find_contributing_factors(self, context: ErrorContext) -> List[str]:
        """Find contributing factors to error"""
        factors = []
        
        if context.execution_time_seconds and context.execution_time_seconds > 300:
            factors.append("Long execution time (> 5 minutes)")
        
        if context.customer_feedback and len(context.customer_feedback) > 200:
            factors.append("Extensive customer feedback suggests multiple issues")
        
        # Would check task complexity, customer history, etc. in production
        
        return factors
    
    def _find_similar_successful_tasks(self, context: ErrorContext) -> List[str]:
        """Find similar tasks that succeeded"""
        similar = []
        
        # In production, would query database for same task_category with rating >= 4.0
        # For now, return placeholder
        
        return similar[:5]  # Top 5 similar successful tasks
    
    def _recommend_strategy(
        self,
        category: ErrorCategory,
        severity: ErrorSeverity,
        context: ErrorContext
    ) -> tuple[RecoveryStrategy, List[RecoveryStrategy]]:
        """Recommend primary and alternative recovery strategies"""
        
        # Strategy mapping by error category
        if category == ErrorCategory.MISUNDERSTANDING:
            primary = RecoveryStrategy.CLARIFY_REQUIREMENTS
            alternatives = [RecoveryStrategy.ALTERNATIVE_APPROACH, RecoveryStrategy.SIMPLIFY_TASK]
        elif category == ErrorCategory.INCOMPLETE:
            primary = RecoveryStrategy.RETRY_SAME
            alternatives = [RecoveryStrategy.SIMPLIFY_TASK, RecoveryStrategy.SWITCH_AGENT]
        elif category == ErrorCategory.INCORRECT_APPROACH:
            primary = RecoveryStrategy.ALTERNATIVE_APPROACH
            alternatives = [RecoveryStrategy.SWITCH_AGENT, RecoveryStrategy.CLARIFY_REQUIREMENTS]
        elif category == ErrorCategory.TECHNICAL_ERROR:
            primary = RecoveryStrategy.RETRY_SAME
            alternatives = [RecoveryStrategy.SWITCH_AGENT, RecoveryStrategy.ESCALATE_HUMAN]
        elif category == ErrorCategory.TIMEOUT:
            primary = RecoveryStrategy.SIMPLIFY_TASK
            alternatives = [RecoveryStrategy.SWITCH_AGENT, RecoveryStrategy.ESCALATE_HUMAN]
        else:
            primary = RecoveryStrategy.ALTERNATIVE_APPROACH
            alternatives = [RecoveryStrategy.CLARIFY_REQUIREMENTS, RecoveryStrategy.RETRY_SAME]
        
        # Escalate if severity is critical
        if severity == ErrorSeverity.CRITICAL:
            primary = RecoveryStrategy.ESCALATE_HUMAN
            alternatives = []
        
        return primary, alternatives
    
    def _generate_clarification_questions(
        self,
        context: ErrorContext,
        category: ErrorCategory
    ) -> List[str]:
        """Generate clarification questions for customer"""
        questions = []
        
        if category == ErrorCategory.MISUNDERSTANDING:
            questions.append("Could you provide more details about what you expected?")
            questions.append("Are there any specific requirements I missed?")
        elif category == ErrorCategory.INCOMPLETE:
            questions.append("Which parts of the task are still missing?")
            questions.append("Should I prioritize any specific aspects?")
        elif category == ErrorCategory.INCORRECT_APPROACH:
            questions.append("What approach would you prefer for this task?")
            questions.append("Are there examples of how you'd like this done?")
        
        return questions
    
    def _calculate_diagnosis_confidence(
        self,
        context: ErrorContext,
        similar_tasks: List[str],
        category: ErrorCategory
    ) -> float:
        """Calculate confidence in diagnosis"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence if we have explicit error message
        if context.error_message:
            confidence += 0.2
        
        # Increase if we have detailed feedback
        if context.customer_feedback and len(context.customer_feedback) > 50:
            confidence += 0.15
        
        # Increase if we have similar successful tasks to compare
        if len(similar_tasks) > 0:
            confidence += 0.15
        
        return min(confidence, 1.0)
    
    def _create_recovery_attempt(
        self,
        attempt_id: str,
        error_id: str,
        strategy: RecoveryStrategy,
        context: ErrorContext
    ) -> RecoveryAttempt:
        """Create a recovery attempt with specified strategy"""
        
        # Generate modified approach based on strategy
        modified_task = None
        alternative_approach = None
        clarification_request = None
        status = RecoveryStatus.IN_PROGRESS
        
        if strategy == RecoveryStrategy.RETRY_SAME:
            modified_task = context.task_description
            alternative_approach = "Retry with same approach, focus on accuracy"
        
        elif strategy == RecoveryStrategy.ALTERNATIVE_APPROACH:
            modified_task = context.task_description
            alternative_approach = "Try different method: more structured approach with step-by-step breakdown"
        
        elif strategy == RecoveryStrategy.CLARIFY_REQUIREMENTS:
            clarification_request = "Before proceeding, I need clarification on: " + \
                                  "1) Expected format/structure, 2) Key priorities, 3) Success criteria"
            status = RecoveryStatus.CLARIFYING
        
        elif strategy == RecoveryStrategy.SIMPLIFY_TASK:
            modified_task = f"Simplified version: {context.task_description} (focus on core requirements)"
            alternative_approach = "Break task into smaller subtasks, complete in phases"
        
        elif strategy == RecoveryStrategy.ESCALATE_HUMAN:
            status = RecoveryStatus.ESCALATED
        
        elif strategy == RecoveryStrategy.SWITCH_AGENT:
            alternative_approach = "Switch to different agent variant better suited for this task"
        
        return RecoveryAttempt(
            attempt_id=attempt_id,
            error_id=error_id,
            strategy=strategy,
            status=status,
            modified_task_description=modified_task,
            alternative_approach_description=alternative_approach,
            clarification_request=clarification_request,
            new_output=None,
            success=False,
            customer_rating=None,
            customer_feedback=None,
            started_at=datetime.utcnow()
        )
    
    def _learn_from_recovery(self, case: RecoveryCase, successful_attempt: RecoveryAttempt):
        """Learn from successful recovery to improve future performance"""
        
        if not case.diagnosis:
            return
        
        category = case.diagnosis.error_category.value
        
        # Store successful recovery pattern
        if category not in self._recovery_patterns:
            self._recovery_patterns[category] = []
        
        pattern = {
            "error_category": category,
            "strategy": successful_attempt.strategy.value,
            "context": {
                "task_category": case.context.task_category,
                "original_rating": case.context.customer_rating,
                "recovery_rating": successful_attempt.customer_rating
            },
            "lesson": f"For {category} errors in {case.context.task_category}, " + \
                     f"{successful_attempt.strategy.value} strategy was effective"
        }
        
        self._recovery_patterns[category].append(pattern)
        
        # Add to case lessons
        case.lessons_learned.append(pattern["lesson"])
