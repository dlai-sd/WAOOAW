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

from .knowledge_synthesis import (
    PatternType,
    FrameworkType,
    KnowledgeStatus,
    DiscoveredPattern,
    CreatedFramework,
    BestPractice,
    CaseStudy,
    KnowledgeSynthesisEngine,
)

from .problem_decomposition import (
    TaskPriority,
    TaskStatus,
    RiskLevel,
    MilestoneType,
    ProjectTask,
    ProjectMilestone,
    ProjectRisk,
    ProjectPlan,
    ProblemDecompositionEngine,
)

__all__ = [
    # Reflection engine - Enums
    "PerformanceMetric",
    "StrengthArea",
    "WeaknessArea",
    "ImprovementPriority",
    
    # Reflection engine - Data classes
    "TaskReflection",
    "PerformanceAnalysis",
    "GapAnalysis",
    "ImprovementGoal",
    "LearningTask",
    
    # Reflection engine - Main class
    "ReflectionEngine",
    
    # Knowledge synthesis - Enums
    "PatternType",
    "FrameworkType",
    "KnowledgeStatus",
    
    # Knowledge synthesis - Data classes
    "DiscoveredPattern",
    "CreatedFramework",
    "BestPractice",
    "CaseStudy",
    
    # Knowledge synthesis - Main class
    "KnowledgeSynthesisEngine",
    
    # Problem decomposition - Enums
    "TaskPriority",
    "TaskStatus",
    "RiskLevel",
    "MilestoneType",
    
    # Problem decomposition - Data classes
    "ProjectTask",
    "ProjectMilestone",
    "ProjectRisk",
    "ProjectPlan",
    
    # Problem decomposition - Main class
    "ProblemDecompositionEngine",
]
