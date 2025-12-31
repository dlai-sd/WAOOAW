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

__all__ = [
    # Enums
    "TaskTiming",
    "QualityPreference",
    "LearningStyle",
    "CommunicationTone",
    
    # Data classes
    "CustomerInteraction",
    "TaskPattern",
    "CustomerProfile",
    "BehaviorPrediction",
    
    # Main class
    "CustomerBehaviorModel",
]
