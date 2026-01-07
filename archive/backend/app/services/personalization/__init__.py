"""
Personalization Services - Epic 5.5: Hyper-Personalization & Adaptation

Customer behavior modeling, dynamic communication adaptation, predictive automation,
and contextual error recovery for deeply personalized agent experiences.
"""

from .customer_behavior_model import (
    TaskTiming,
    QualityPreference,
    LearningStyle,
    CommunicationTone,
    CustomerInteraction,
    TaskPattern,
    CustomerProfile,
    BehaviorPrediction,
    CustomerBehaviorModel,
)

from .communication_adapter import (
    OutputFormat,
    UrgencyLevel,
    CustomerStatus,
    CommunicationContext,
    AdaptedStyle,
    StyleTemplate,
    CommunicationAdapter,
)

from .task_automation import (
    AutomationType,
    ApprovalMode,
    AutomationStatus,
    ExecutionStatus,
    ScheduleConfig,
    PatternTrigger,
    CalendarTrigger,
    EventTrigger,
    AutomationRule,
    AutomationExecution,
    TaskAutomationEngine,
)

from .error_recovery import (
    ErrorSeverity,
    ErrorCategory,
    RecoveryStrategy,
    RecoveryStatus,
    ErrorContext,
    ErrorDiagnosis,
    RecoveryAttempt,
    RecoveryCase,
    ErrorRecoveryEngine,
)

__all__ = [
    # Enums
    "TaskTiming",
    "QualityPreference",
    "LearningStyle",
    "CommunicationTone",
    "OutputFormat",
    "UrgencyLevel",
    "CustomerStatus",
    "AutomationType",
    "ApprovalMode",
    "AutomationStatus",
    "ExecutionStatus",
    "ErrorSeverity",
    "ErrorCategory",
    "RecoveryStrategy",
    "RecoveryStatus",
    
    # Data classes
    "CustomerInteraction",
    "TaskPattern",
    "CustomerProfile",
    "BehaviorPrediction",
    "CommunicationContext",
    "AdaptedStyle",
    "StyleTemplate",
    "ScheduleConfig",
    "PatternTrigger",
    "CalendarTrigger",
    "EventTrigger",
    "AutomationRule",
    "AutomationExecution",
    "ErrorContext",
    "ErrorDiagnosis",
    "RecoveryAttempt",
    "RecoveryCase",
    
    # Main classes
    "CustomerBehaviorModel",
    "CommunicationAdapter",
    "TaskAutomationEngine",
    "ErrorRecoveryEngine",
]
