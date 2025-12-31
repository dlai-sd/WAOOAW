"""
Agent Improvement Services

Provides pattern detection, feedback analysis, and continuous learning capabilities.
"""

from .pattern_detection import (
    InteractionPattern,
    PatternType,
    PatternDetector,
    SuccessPattern,
    FailurePattern,
)

from .feedback_analysis import (
    FeedbackType,
    FeedbackEntry,
    FeedbackAnalyzer,
    FeedbackInsight,
)

from .performance_analysis import (
    PerformanceMetric,
    PerformanceAnalyzer,
    PerformanceReport,
    Bottleneck,
)

from .prompt_optimizer import (
    OptimizationStrategy,
    PromptVersion,
    PromptVariant,
    ABTest,
    PromptTemplate,
    PromptOptimizer,
)

from .continuous_learning import (
    AnalysisFrequency,
    ImprovementAction,
    ImprovementEvent,
    AnalysisSchedule,
    ContinuousLearningPipeline,
)

__all__ = [
    # Pattern Detection
    "InteractionPattern",
    "PatternType",
    "PatternDetector",
    "SuccessPattern",
    "FailurePattern",
    # Feedback Analysis
    "FeedbackType",
    "FeedbackEntry",
    "FeedbackAnalyzer",
    "FeedbackInsight",
    # Performance Analysis
    "PerformanceMetric",
    "PerformanceAnalyzer",
    "PerformanceReport",
    "Bottleneck",
    # Prompt Optimization
    "OptimizationStrategy",
    "PromptVersion",
    "PromptVariant",
    "ABTest",
    "PromptTemplate",
    "PromptOptimizer",
    # Continuous Learning
    "AnalysisFrequency",
    "ImprovementAction",
    "ImprovementEvent",
    "AnalysisSchedule",
    "ContinuousLearningPipeline",
]
