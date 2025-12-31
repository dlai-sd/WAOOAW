"""
Evolution Services - Epic 5.6: Self-Evolving Agent System

Agent self-reflection, knowledge synthesis, problem decomposition, and meta-learning
for continuous autonomous improvement and evolution.
"""

from .reflection_engine import (
    PerformanceMetric,
    StrengthArea,
    WeaknessArea,
    ImprovementPriority,
    TaskReflection,
    PerformanceAnalysis,
    GapAnalysis,
    ImprovementGoal,
    LearningTask,
    ReflectionEngine,
)

__all__ = [
    # Enums
    "PerformanceMetric",
    "StrengthArea",
    "WeaknessArea",
    "ImprovementPriority",
    
    # Data classes
    "TaskReflection",
    "PerformanceAnalysis",
    "GapAnalysis",
    "ImprovementGoal",
    "LearningTask",
    
    # Main classes
    "ReflectionEngine",
]
