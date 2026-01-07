"""
Dynamic Communication Adaptation - Story 5.5.2

Agents adjust tone, detail level, format based on customer context and preferences.
Enables truly personalized communication that matches customer's current state and needs.

Epic 5.5: Hyper-Personalization & Adaptation (68 points)
Story Points: 21
"""

from dataclasses import dataclass, field
from datetime import datetime, time
from enum import Enum
from typing import Dict, List, Optional, Any
from .customer_behavior_model import (
    CustomerProfile,
    CommunicationTone,
    LearningStyle,
    QualityPreference,
    TaskTiming,
)


class OutputFormat(Enum):
    """Output format preferences"""
    BULLET_POINTS = "bullet_points"
    NARRATIVE = "narrative"
    STRUCTURED = "structured"  # Headings with sections
    MIXED = "mixed"  # Combination of formats


class UrgencyLevel(Enum):
    """Task urgency levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class CustomerStatus(Enum):
    """Customer subscription status"""
    TRIAL = "trial"
    PAID = "paid"
    ENTERPRISE = "enterprise"
    CHURNED = "churned"


@dataclass
class CommunicationContext:
    """Context for adapting communication style"""
    customer_id: str
    task_category: str
    task_description: str
    
    # Context signals
    time_of_day: TaskTiming
    customer_status: CustomerStatus
    urgency: UrgencyLevel = UrgencyLevel.NORMAL
    
    # Task characteristics
    task_complexity: float = 0.5  # 0.0 (simple) to 1.0 (complex)
    estimated_length: int = 500  # Estimated output length in words
    
    # Customer state
    available_time_minutes: Optional[int] = None  # How much time customer has
    domain_expertise_level: str = "intermediate"  # beginner, intermediate, expert
    
    # Past behavior with this task type
    previous_requests_count: int = 0
    previous_satisfaction: Optional[float] = None  # 1.0 to 5.0
    
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AdaptedStyle:
    """Adapted communication style for specific context"""
    style_id: str
    customer_id: str
    
    # Style dimensions
    tone: CommunicationTone
    tone_score: float  # 0.0 (formal) to 1.0 (casual)
    
    detail_level: float  # 0.0 (minimal) to 1.0 (maximum)
    include_explanations: bool
    explanation_depth: float  # 0.0 (brief) to 1.0 (thorough)
    
    output_format: OutputFormat
    
    # Technical level
    technical_level: float  # 0.0 (simple) to 1.0 (technical)
    include_examples: bool
    example_count: int = 2
    
    # Structure
    use_headings: bool = True
    use_bullet_points: bool = True
    max_length_words: int = 500
    
    # Reasoning
    reasoning: str = ""
    confidence: float = 0.0  # 0.0 to 1.0
    
    adapted_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "style_id": self.style_id,
            "customer_id": self.customer_id,
            "tone": self.tone.value,
            "tone_score": self.tone_score,
            "detail_level": self.detail_level,
            "include_explanations": self.include_explanations,
            "explanation_depth": self.explanation_depth,
            "output_format": self.output_format.value,
            "technical_level": self.technical_level,
            "include_examples": self.include_examples,
            "example_count": self.example_count,
            "use_headings": self.use_headings,
            "use_bullet_points": self.use_bullet_points,
            "max_length_words": self.max_length_words,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "adapted_at": self.adapted_at.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class StyleTemplate:
    """Template for applying adapted style to content"""
    template_id: str
    template_name: str
    description: str
    
    # Template structure
    includes_intro: bool = True
    intro_length_words: int = 50
    
    includes_main_content: bool = True
    main_content_structure: str = "structured"  # structured, narrative, bullet_points
    
    includes_examples: bool = False
    example_placement: str = "inline"  # inline, separate_section, appendix
    
    includes_summary: bool = True
    summary_length_words: int = 100
    
    includes_next_steps: bool = False
    
    # Formatting
    heading_style: str = "bold"  # bold, numbered, markdown
    emphasis_style: str = "italic"  # italic, bold, underline
    
    metadata: Dict[str, Any] = field(default_factory=dict)


class CommunicationAdapter:
    """
    Dynamic communication adaptation engine.
    
    Adapts agent communication style based on customer context, preferences,
    and real-time signals (time, urgency, status, etc.).
    """
    
    def __init__(self):
        """Initialize communication adapter"""
        self._adaptations: Dict[str, List[AdaptedStyle]] = {}
        self._templates: Dict[str, StyleTemplate] = {}
        self._default_styles: Dict[str, AdaptedStyle] = {}
        
        # Adaptation rules and weights
        self._urgency_weights = {
            UrgencyLevel.CRITICAL: {"detail_reduction": 0.5, "explanation_reduction": 0.7},
            UrgencyLevel.HIGH: {"detail_reduction": 0.3, "explanation_reduction": 0.4},
            UrgencyLevel.NORMAL: {"detail_reduction": 0.0, "explanation_reduction": 0.0},
            UrgencyLevel.LOW: {"detail_reduction": -0.2, "explanation_reduction": -0.1},
        }
        
        self._time_of_day_adjustments = {
            TaskTiming.MORNING: {"brevity_preference": 0.2, "formality": 0.1},  # More brief in morning
            TaskTiming.AFTERNOON: {"brevity_preference": 0.0, "formality": 0.0},
            TaskTiming.EVENING: {"brevity_preference": -0.1, "formality": -0.1},  # More casual/detailed in evening
            TaskTiming.NIGHT: {"brevity_preference": 0.3, "formality": -0.2},  # Brief and casual at night
        }
        
        self._status_adjustments = {
            CustomerStatus.TRIAL: {"education_level": 0.3, "explanation_bonus": 0.2, "formality": 0.0},  # More educational
            CustomerStatus.PAID: {"education_level": 0.0, "explanation_bonus": 0.0, "formality": 0.0},
            CustomerStatus.ENTERPRISE: {"formality": 0.2, "detail_level": 0.1, "education_level": 0.0, "explanation_bonus": 0.0},  # More formal/detailed
            CustomerStatus.CHURNED: {"formality": 0.1, "explanation_bonus": 0.1, "education_level": 0.0},
        }
        
        self._initialize_default_templates()
    
    def _initialize_default_templates(self):
        """Initialize default style templates"""
        # Executive summary template (brief, high-level)
        self._templates["executive"] = StyleTemplate(
            template_id="executive",
            template_name="Executive Summary",
            description="Brief, high-level overview for busy executives",
            includes_intro=False,
            intro_length_words=0,
            includes_main_content=True,
            main_content_structure="bullet_points",
            includes_examples=False,
            includes_summary=True,
            summary_length_words=150,
            includes_next_steps=True
        )
        
        # Comprehensive template (detailed, thorough)
        self._templates["comprehensive"] = StyleTemplate(
            template_id="comprehensive",
            template_name="Comprehensive Analysis",
            description="Detailed, thorough analysis with examples",
            includes_intro=True,
            intro_length_words=100,
            includes_main_content=True,
            main_content_structure="structured",
            includes_examples=True,
            example_placement="inline",
            includes_summary=True,
            summary_length_words=200,
            includes_next_steps=True
        )
        
        # Quick reference template (actionable, concise)
        self._templates["quick_reference"] = StyleTemplate(
            template_id="quick_reference",
            template_name="Quick Reference",
            description="Actionable, concise guidance",
            includes_intro=False,
            includes_main_content=True,
            main_content_structure="bullet_points",
            includes_examples=True,
            example_placement="inline",
            includes_summary=False,
            includes_next_steps=True
        )
    
    def adapt_style(
        self,
        context: CommunicationContext,
        customer_profile: Optional[CustomerProfile] = None
    ) -> AdaptedStyle:
        """
        Adapt communication style based on context and profile.
        
        Args:
            context: Current communication context
            customer_profile: Optional customer profile for personalization
            
        Returns:
            Adapted communication style
        """
        style_id = f"style_{context.customer_id}_{datetime.now().timestamp()}"
        
        # Start with base preferences from profile (or defaults)
        if customer_profile:
            base_tone = customer_profile.communication_tone
            base_detail = customer_profile.detail_level_preference
            base_explanations = customer_profile.prefers_explanations
            learning_style = customer_profile.learning_style
            quality_pref = customer_profile.quality_preference
        else:
            base_tone = CommunicationTone.FORMAL
            base_detail = 0.5
            base_explanations = True
            learning_style = LearningStyle.TEXTUAL
            quality_pref = QualityPreference.BALANCED
        
        # Apply context-based adjustments
        adjusted_detail = self._adjust_detail_level(
            base_detail, context, customer_profile
        )
        
        adjusted_tone, tone_score = self._adjust_tone(
            base_tone, context, customer_profile
        )
        
        explanation_depth = self._calculate_explanation_depth(
            base_explanations, context, customer_profile
        )
        
        output_format = self._determine_output_format(
            learning_style, context, customer_profile
        )
        
        technical_level = self._determine_technical_level(
            context, customer_profile
        )
        
        # Determine optimal length
        max_length = self._calculate_max_length(
            adjusted_detail, context, customer_profile
        )
        
        # Structure preferences
        use_headings = adjusted_detail > 0.3
        use_bullet_points = output_format in [
            OutputFormat.BULLET_POINTS, OutputFormat.MIXED, OutputFormat.STRUCTURED
        ]
        
        # Example preferences
        include_examples = (
            learning_style == LearningStyle.EXAMPLE_BASED or
            context.domain_expertise_level == "beginner" or
            adjusted_detail > 0.6
        )
        example_count = 3 if adjusted_detail > 0.7 else 2 if adjusted_detail > 0.4 else 1
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            context, customer_profile, adjusted_tone, adjusted_detail
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(context, customer_profile)
        
        adapted_style = AdaptedStyle(
            style_id=style_id,
            customer_id=context.customer_id,
            tone=adjusted_tone,
            tone_score=tone_score,
            detail_level=adjusted_detail,
            include_explanations=explanation_depth > 0.3,
            explanation_depth=explanation_depth,
            output_format=output_format,
            technical_level=technical_level,
            include_examples=include_examples,
            example_count=example_count,
            use_headings=use_headings,
            use_bullet_points=use_bullet_points,
            max_length_words=max_length,
            reasoning=reasoning,
            confidence=confidence
        )
        
        # Store adaptation
        if context.customer_id not in self._adaptations:
            self._adaptations[context.customer_id] = []
        self._adaptations[context.customer_id].append(adapted_style)
        
        return adapted_style
    
    def _adjust_detail_level(
        self,
        base_detail: float,
        context: CommunicationContext,
        profile: Optional[CustomerProfile]
    ) -> float:
        """Adjust detail level based on context"""
        adjusted = base_detail
        
        # Urgency adjustments
        urgency_reduction = self._urgency_weights[context.urgency]["detail_reduction"]
        adjusted -= urgency_reduction
        
        # Time availability
        if context.available_time_minutes:
            if context.available_time_minutes < 5:
                adjusted *= 0.5  # Very brief
            elif context.available_time_minutes < 15:
                adjusted *= 0.7  # Somewhat brief
            elif context.available_time_minutes > 60:
                adjusted = min(1.0, adjusted * 1.2)  # More detail
        
        # Time of day
        time_adj = self._time_of_day_adjustments[context.time_of_day]["brevity_preference"]
        adjusted -= time_adj * 0.3
        
        # Task complexity
        if context.task_complexity > 0.7:
            adjusted = min(1.0, adjusted + 0.2)  # Complex tasks need more detail
        
        # Expertise level
        if context.domain_expertise_level == "beginner":
            adjusted = min(1.0, adjusted + 0.2)  # Beginners need more detail
        elif context.domain_expertise_level == "expert":
            adjusted = max(0.2, adjusted - 0.2)  # Experts need less detail
        
        # Customer status
        if context.customer_status == CustomerStatus.TRIAL:
            adjusted = min(1.0, adjusted + 0.1)  # More detail for trial users
        
        return max(0.0, min(1.0, adjusted))
    
    def _adjust_tone(
        self,
        base_tone: CommunicationTone,
        context: CommunicationContext,
        profile: Optional[CustomerProfile]
    ) -> tuple[CommunicationTone, float]:
        """Adjust communication tone based on context"""
        # Convert tone to numeric score
        tone_scores = {
            CommunicationTone.FORMAL: 0.0,
            CommunicationTone.TECHNICAL: 0.3,
            CommunicationTone.SIMPLE: 0.7,
            CommunicationTone.CASUAL: 1.0,
        }
        score = tone_scores.get(base_tone, 0.5)
        
        # Time of day adjustments
        time_formality = self._time_of_day_adjustments[context.time_of_day]["formality"]
        score -= time_formality * 0.2  # Negative formality = more casual
        
        # Status adjustments
        status_formality = self._status_adjustments[context.customer_status]["formality"]
        score -= status_formality * 0.3
        
        # Urgency (critical = more formal/direct)
        if context.urgency in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]:
            score = max(0.0, score - 0.2)
        
        # Task complexity (complex = more formal)
        if context.task_complexity > 0.7:
            score = max(0.0, score - 0.1)
        
        score = max(0.0, min(1.0, score))
        
        # Convert back to enum
        if score < 0.25:
            adjusted_tone = CommunicationTone.FORMAL
        elif score < 0.5:
            adjusted_tone = CommunicationTone.TECHNICAL
        elif score < 0.75:
            adjusted_tone = CommunicationTone.SIMPLE
        else:
            adjusted_tone = CommunicationTone.CASUAL
        
        return adjusted_tone, score
    
    def _calculate_explanation_depth(
        self,
        base_prefers_explanations: bool,
        context: CommunicationContext,
        profile: Optional[CustomerProfile]
    ) -> float:
        """Calculate how much explanation to include"""
        if not base_prefers_explanations:
            depth = 0.3  # Minimal explanations
        else:
            depth = 0.7  # Default explanations
        
        # Urgency (reduce explanations when urgent)
        urgency_reduction = self._urgency_weights[context.urgency]["explanation_reduction"]
        depth -= urgency_reduction
        
        # Expertise level
        if context.domain_expertise_level == "beginner":
            depth = min(1.0, depth + 0.3)
        elif context.domain_expertise_level == "expert":
            depth = max(0.0, depth - 0.3)
        
        # Customer status (trial users get more explanations)
        if context.customer_status == CustomerStatus.TRIAL:
            explanation_bonus = self._status_adjustments[CustomerStatus.TRIAL]["explanation_bonus"]
            depth = min(1.0, depth + explanation_bonus)
        
        # Previous satisfaction (if low, add more explanations)
        if context.previous_satisfaction and context.previous_satisfaction < 3.5:
            depth = min(1.0, depth + 0.2)
        
        return max(0.0, min(1.0, depth))
    
    def _determine_output_format(
        self,
        learning_style: LearningStyle,
        context: CommunicationContext,
        profile: Optional[CustomerProfile]
    ) -> OutputFormat:
        """Determine optimal output format"""
        # Learning style preferences
        if learning_style == LearningStyle.VISUAL:
            return OutputFormat.STRUCTURED  # Headings and sections
        elif learning_style == LearningStyle.HANDS_ON:
            return OutputFormat.BULLET_POINTS  # Action-oriented
        elif learning_style == LearningStyle.THEORY_BASED:
            return OutputFormat.NARRATIVE  # Flowing explanation
        
        # Urgency
        if context.urgency in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]:
            return OutputFormat.BULLET_POINTS  # Quick to scan
        
        # Time availability
        if context.available_time_minutes and context.available_time_minutes < 10:
            return OutputFormat.BULLET_POINTS
        
        # Default
        return OutputFormat.MIXED
    
    def _determine_technical_level(
        self,
        context: CommunicationContext,
        profile: Optional[CustomerProfile]
    ) -> float:
        """Determine technical level of language"""
        # Start with expertise level
        expertise_levels = {
            "beginner": 0.2,
            "intermediate": 0.5,
            "expert": 0.8
        }
        technical = expertise_levels.get(context.domain_expertise_level, 0.5)
        
        # Adjust for customer status
        if context.customer_status == CustomerStatus.TRIAL:
            technical = max(0.0, technical - 0.2)  # Simpler for trials
        elif context.customer_status == CustomerStatus.ENTERPRISE:
            technical = min(1.0, technical + 0.1)  # Can be more technical
        
        return technical
    
    def _calculate_max_length(
        self,
        detail_level: float,
        context: CommunicationContext,
        profile: Optional[CustomerProfile]
    ) -> int:
        """Calculate maximum output length in words"""
        # Base length from detail level
        base_length = int(300 + (detail_level * 700))  # 300-1000 words
        
        # Adjust for urgency
        if context.urgency == UrgencyLevel.CRITICAL:
            base_length = int(base_length * 0.5)
        elif context.urgency == UrgencyLevel.HIGH:
            base_length = int(base_length * 0.7)
        
        # Adjust for time availability
        if context.available_time_minutes:
            words_per_minute = 200  # Average reading speed
            max_by_time = context.available_time_minutes * words_per_minute
            base_length = min(base_length, max_by_time)
        
        # Adjust for task complexity
        if context.task_complexity > 0.7:
            base_length = int(base_length * 1.2)
        
        return max(200, min(2000, base_length))
    
    def _generate_reasoning(
        self,
        context: CommunicationContext,
        profile: Optional[CustomerProfile],
        tone: CommunicationTone,
        detail_level: float
    ) -> str:
        """Generate human-readable reasoning for adaptations"""
        reasons = []
        
        # Urgency
        if context.urgency == UrgencyLevel.CRITICAL:
            reasons.append("critical urgency → brief, direct communication")
        elif context.urgency == UrgencyLevel.HIGH:
            reasons.append("high urgency → reduced detail")
        
        # Time of day
        if context.time_of_day == TaskTiming.MORNING:
            reasons.append("morning timing → more concise")
        elif context.time_of_day == TaskTiming.EVENING:
            reasons.append("evening timing → can be more detailed")
        
        # Expertise
        if context.domain_expertise_level == "beginner":
            reasons.append("beginner level → more explanations")
        elif context.domain_expertise_level == "expert":
            reasons.append("expert level → skip basics")
        
        # Status
        if context.customer_status == CustomerStatus.TRIAL:
            reasons.append("trial user → educational approach")
        elif context.customer_status == CustomerStatus.ENTERPRISE:
            reasons.append("enterprise customer → formal tone")
        
        # Time constraint
        if context.available_time_minutes and context.available_time_minutes < 15:
            reasons.append(f"limited time ({context.available_time_minutes} mins) → concise format")
        
        # Detail level
        detail_desc = "minimal" if detail_level < 0.3 else "moderate" if detail_level < 0.7 else "comprehensive"
        reasons.append(f"{detail_desc} detail level")
        
        if not reasons:
            reasons.append("standard communication style")
        
        return "Adapted based on: " + ", ".join(reasons)
    
    def _calculate_confidence(
        self,
        context: CommunicationContext,
        profile: Optional[CustomerProfile]
    ) -> float:
        """Calculate confidence in adaptation"""
        confidence = 0.5  # Base confidence
        
        # Higher confidence with customer profile
        if profile:
            confidence += 0.2
            if profile.total_interactions > 20:
                confidence += 0.1
            if profile.profile_confidence > 0.7:
                confidence += 0.1
        
        # Higher confidence with more context
        if context.previous_requests_count > 5:
            confidence += 0.1
        
        if context.previous_satisfaction:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def get_template(self, template_id: str) -> Optional[StyleTemplate]:
        """Get style template by ID"""
        return self._templates.get(template_id)
    
    def get_customer_adaptations(self, customer_id: str) -> List[AdaptedStyle]:
        """Get all adaptations for a customer"""
        return self._adaptations.get(customer_id, [])
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get adapter statistics"""
        total_customers = len(self._adaptations)
        total_adaptations = sum(len(styles) for styles in self._adaptations.values())
        
        return {
            "total_customers_adapted": total_customers,
            "total_adaptations": total_adaptations,
            "average_adaptations_per_customer": total_adaptations / total_customers if total_customers > 0 else 0,
            "available_templates": len(self._templates),
            "template_ids": list(self._templates.keys())
        }
