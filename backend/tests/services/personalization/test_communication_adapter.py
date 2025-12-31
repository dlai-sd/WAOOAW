"""
Tests for Dynamic Communication Adaptation - Story 5.5.2

Epic 5.5: Hyper-Personalization & Adaptation
Story Points: 21
"""

import pytest
from datetime import datetime
from app.services.personalization import (
    TaskTiming,
    QualityPreference,
    LearningStyle,
    CommunicationTone,
    CustomerProfile,
    OutputFormat,
    UrgencyLevel,
    CustomerStatus,
    CommunicationContext,
    AdaptedStyle,
    StyleTemplate,
    CommunicationAdapter,
)


class TestCommunicationAdapter:
    """Test suite for dynamic communication adaptation"""
    
    def test_create_adapter(self):
        """Test adapter instantiation"""
        adapter = CommunicationAdapter()
        
        assert adapter is not None
        stats = adapter.get_statistics()
        assert stats["total_customers_adapted"] == 0
        assert stats["total_adaptations"] == 0
        assert stats["available_templates"] > 0
    
    def test_adapt_style_basic(self):
        """Test basic style adaptation without profile"""
        adapter = CommunicationAdapter()
        
        context = CommunicationContext(
            customer_id="cust_001",
            task_category="content_creation",
            task_description="Create blog post",
            time_of_day=TaskTiming.AFTERNOON,
            customer_status=CustomerStatus.PAID,
            urgency=UrgencyLevel.NORMAL
        )
        
        adapted_style = adapter.adapt_style(context)
        
        assert adapted_style is not None
        assert adapted_style.customer_id == "cust_001"
        assert 0.0 <= adapted_style.detail_level <= 1.0
        assert 0.0 <= adapted_style.tone_score <= 1.0
        assert adapted_style.reasoning != ""
        assert 0.0 <= adapted_style.confidence <= 1.0
    
    def test_adapt_style_with_profile(self):
        """Test adaptation with customer profile"""
        adapter = CommunicationAdapter()
        
        # Create a customer profile
        profile = CustomerProfile(
            customer_id="cust_001",
            communication_tone=CommunicationTone.CASUAL,
            detail_level_preference=0.7,
            prefers_explanations=True,
            learning_style=LearningStyle.EXAMPLE_BASED,
            quality_preference=QualityPreference.DEPTH,
            total_interactions=25,
            profile_confidence=0.8
        )
        
        context = CommunicationContext(
            customer_id="cust_001",
            task_category="content_creation",
            task_description="Task",
            time_of_day=TaskTiming.AFTERNOON,
            customer_status=CustomerStatus.PAID
        )
        
        adapted_style = adapter.adapt_style(context, profile)
        
        assert adapted_style is not None
        # Should have higher confidence with profile
        assert adapted_style.confidence > 0.6
        # Should include examples (learning style preference)
        assert adapted_style.include_examples is True
    
    def test_urgency_adaptation(self):
        """Test adaptation for different urgency levels"""
        adapter = CommunicationAdapter()
        
        profile = CustomerProfile(
            customer_id="cust_001",
            detail_level_preference=0.8,  # Normally wants detail
            prefers_explanations=True
        )
        
        # Critical urgency
        context_critical = CommunicationContext(
            customer_id="cust_001",
            task_category="content_creation",
            task_description="Urgent task",
            time_of_day=TaskTiming.AFTERNOON,
            customer_status=CustomerStatus.PAID,
            urgency=UrgencyLevel.CRITICAL
        )
        
        # Normal urgency
        context_normal = CommunicationContext(
            customer_id="cust_001",
            task_category="content_creation",
            task_description="Normal task",
            time_of_day=TaskTiming.AFTERNOON,
            customer_status=CustomerStatus.PAID,
            urgency=UrgencyLevel.NORMAL
        )
        
        style_critical = adapter.adapt_style(context_critical, profile)
        style_normal = adapter.adapt_style(context_normal, profile)
        
        # Critical should reduce detail
        assert style_critical.detail_level < style_normal.detail_level
        # Critical should reduce explanations
        assert style_critical.explanation_depth < style_normal.explanation_depth
        # Critical should have shorter max length
        assert style_critical.max_length_words < style_normal.max_length_words
    
    def test_time_of_day_adaptation(self):
        """Test adaptation based on time of day"""
        adapter = CommunicationAdapter()
        
        profile = CustomerProfile(
            customer_id="cust_001",
            detail_level_preference=0.6
        )
        
        # Morning (should be more brief)
        context_morning = CommunicationContext(
            customer_id="cust_001",
            task_category="content_creation",
            task_description="Task",
            time_of_day=TaskTiming.MORNING,
            customer_status=CustomerStatus.PAID
        )
        
        # Evening (can be more detailed)
        context_evening = CommunicationContext(
            customer_id="cust_001",
            task_category="content_creation",
            task_description="Task",
            time_of_day=TaskTiming.EVENING,
            customer_status=CustomerStatus.PAID
        )
        
        style_morning = adapter.adapt_style(context_morning, profile)
        style_evening = adapter.adapt_style(context_evening, profile)
        
        # Morning should be more brief
        assert style_morning.detail_level <= style_evening.detail_level
    
    def test_customer_status_adaptation(self):
        """Test adaptation for different customer statuses"""
        adapter = CommunicationAdapter()
        
        profile = CustomerProfile(
            customer_id="cust_001",
            prefers_explanations=False,  # Normally doesn't want explanations
            detail_level_preference=0.5
        )
        
        # Trial user (should get more education)
        context_trial = CommunicationContext(
            customer_id="cust_001",
            task_category="content_creation",
            task_description="Task",
            time_of_day=TaskTiming.AFTERNOON,
            customer_status=CustomerStatus.TRIAL
        )
        
        # Enterprise user (should get more formal/detailed)
        context_enterprise = CommunicationContext(
            customer_id="cust_001",
            task_category="content_creation",
            task_description="Task",
            time_of_day=TaskTiming.AFTERNOON,
            customer_status=CustomerStatus.ENTERPRISE
        )
        
        style_trial = adapter.adapt_style(context_trial, profile)
        style_enterprise = adapter.adapt_style(context_enterprise, profile)
        
        # Trial should get more explanations (educational)
        assert style_trial.explanation_depth > 0.3
        # Enterprise should be more formal
        assert style_enterprise.tone_score < 0.5  # More formal
    
    def test_expertise_level_adaptation(self):
        """Test adaptation for different expertise levels"""
        adapter = CommunicationAdapter()
        
        profile = CustomerProfile(
            customer_id="cust_001",
            detail_level_preference=0.5
        )
        
        # Beginner (needs more detail and examples)
        context_beginner = CommunicationContext(
            customer_id="cust_001",
            task_category="content_creation",
            task_description="Task",
            time_of_day=TaskTiming.AFTERNOON,
            customer_status=CustomerStatus.PAID,
            domain_expertise_level="beginner"
        )
        
        # Expert (needs less detail)
        context_expert = CommunicationContext(
            customer_id="cust_001",
            task_category="content_creation",
            task_description="Task",
            time_of_day=TaskTiming.AFTERNOON,
            customer_status=CustomerStatus.PAID,
            domain_expertise_level="expert"
        )
        
        style_beginner = adapter.adapt_style(context_beginner, profile)
        style_expert = adapter.adapt_style(context_expert, profile)
        
        # Beginner should get more detail
        assert style_beginner.detail_level > style_expert.detail_level
        # Beginner should get more explanations
        assert style_beginner.explanation_depth > style_expert.explanation_depth
        # Beginner should get lower technical level
        assert style_beginner.technical_level < style_expert.technical_level
    
    def test_time_constraint_adaptation(self):
        """Test adaptation when customer has limited time"""
        adapter = CommunicationAdapter()
        
        profile = CustomerProfile(
            customer_id="cust_001",
            detail_level_preference=0.7  # Normally wants detail
        )
        
        # Very limited time (5 minutes)
        context_short = CommunicationContext(
            customer_id="cust_001",
            task_category="content_creation",
            task_description="Task",
            time_of_day=TaskTiming.AFTERNOON,
            customer_status=CustomerStatus.PAID,
            available_time_minutes=5
        )
        
        # Plenty of time (60 minutes)
        context_long = CommunicationContext(
            customer_id="cust_001",
            task_category="content_creation",
            task_description="Task",
            time_of_day=TaskTiming.AFTERNOON,
            customer_status=CustomerStatus.PAID,
            available_time_minutes=60
        )
        
        style_short = adapter.adapt_style(context_short, profile)
        style_long = adapter.adapt_style(context_long, profile)
        
        # Short time should drastically reduce detail
        assert style_short.detail_level < style_long.detail_level
        # Short time should use bullet points (quick to scan)
        assert style_short.output_format == OutputFormat.BULLET_POINTS
        # Short time should have much shorter max length
        assert style_short.max_length_words < style_long.max_length_words
    
    def test_task_complexity_adaptation(self):
        """Test adaptation for complex vs simple tasks"""
        adapter = CommunicationAdapter()
        
        profile = CustomerProfile(
            customer_id="cust_001",
            detail_level_preference=0.5
        )
        
        # Complex task
        context_complex = CommunicationContext(
            customer_id="cust_001",
            task_category="data_analysis",
            task_description="Complex analysis",
            time_of_day=TaskTiming.AFTERNOON,
            customer_status=CustomerStatus.PAID,
            task_complexity=0.9
        )
        
        # Simple task
        context_simple = CommunicationContext(
            customer_id="cust_001",
            task_category="data_analysis",
            task_description="Simple analysis",
            time_of_day=TaskTiming.AFTERNOON,
            customer_status=CustomerStatus.PAID,
            task_complexity=0.2
        )
        
        style_complex = adapter.adapt_style(context_complex, profile)
        style_simple = adapter.adapt_style(context_simple, profile)
        
        # Complex tasks need more detail
        assert style_complex.detail_level > style_simple.detail_level
        # Complex tasks allow longer content
        assert style_complex.max_length_words > style_simple.max_length_words
    
    def test_learning_style_adaptation(self):
        """Test adaptation for different learning styles"""
        adapter = CommunicationAdapter()
        
        # Visual learner
        profile_visual = CustomerProfile(
            customer_id="cust_001",
            learning_style=LearningStyle.VISUAL
        )
        
        # Hands-on learner
        profile_hands_on = CustomerProfile(
            customer_id="cust_002",
            learning_style=LearningStyle.HANDS_ON
        )
        
        # Theory-based learner
        profile_theory = CustomerProfile(
            customer_id="cust_003",
            learning_style=LearningStyle.THEORY_BASED
        )
        
        context = CommunicationContext(
            customer_id="cust_001",
            task_category="content_creation",
            task_description="Task",
            time_of_day=TaskTiming.AFTERNOON,
            customer_status=CustomerStatus.PAID
        )
        
        style_visual = adapter.adapt_style(context, profile_visual)
        
        context.customer_id = "cust_002"
        style_hands_on = adapter.adapt_style(context, profile_hands_on)
        
        context.customer_id = "cust_003"
        style_theory = adapter.adapt_style(context, profile_theory)
        
        # Visual should use structured format
        assert style_visual.output_format == OutputFormat.STRUCTURED
        # Hands-on should use bullet points
        assert style_hands_on.output_format == OutputFormat.BULLET_POINTS
        # Theory should use narrative
        assert style_theory.output_format == OutputFormat.NARRATIVE
    
    def test_example_inclusion(self):
        """Test when examples should be included"""
        adapter = CommunicationAdapter()
        
        # Example-based learner
        profile_examples = CustomerProfile(
            customer_id="cust_001",
            learning_style=LearningStyle.EXAMPLE_BASED
        )
        
        # Beginner
        context_beginner = CommunicationContext(
            customer_id="cust_002",
            task_category="content_creation",
            task_description="Task",
            time_of_day=TaskTiming.AFTERNOON,
            customer_status=CustomerStatus.PAID,
            domain_expertise_level="beginner"
        )
        
        # High detail preference
        profile_detail = CustomerProfile(
            customer_id="cust_003",
            detail_level_preference=0.9
        )
        
        context1 = CommunicationContext(
            customer_id="cust_001",
            task_category="content_creation",
            task_description="Task",
            time_of_day=TaskTiming.AFTERNOON,
            customer_status=CustomerStatus.PAID
        )
        
        context3 = CommunicationContext(
            customer_id="cust_003",
            task_category="content_creation",
            task_description="Task",
            time_of_day=TaskTiming.AFTERNOON,
            customer_status=CustomerStatus.PAID
        )
        
        style1 = adapter.adapt_style(context1, profile_examples)
        style2 = adapter.adapt_style(context_beginner)
        style3 = adapter.adapt_style(context3, profile_detail)
        
        # All should include examples
        assert style1.include_examples is True
        assert style2.include_examples is True
        assert style3.include_examples is True
        
        # High detail should get more examples
        assert style3.example_count >= style1.example_count
    
    def test_previous_satisfaction_adaptation(self):
        """Test adaptation based on previous satisfaction"""
        adapter = CommunicationAdapter()
        
        profile = CustomerProfile(
            customer_id="cust_001",
            prefers_explanations=False  # Normally doesn't want explanations
        )
        
        # Low previous satisfaction (should add more explanations)
        context_low_sat = CommunicationContext(
            customer_id="cust_001",
            task_category="content_creation",
            task_description="Task",
            time_of_day=TaskTiming.AFTERNOON,
            customer_status=CustomerStatus.PAID,
            previous_satisfaction=3.0  # Low rating
        )
        
        # High previous satisfaction
        context_high_sat = CommunicationContext(
            customer_id="cust_001",
            task_category="content_creation",
            task_description="Task",
            time_of_day=TaskTiming.AFTERNOON,
            customer_status=CustomerStatus.PAID,
            previous_satisfaction=4.8  # High rating
        )
        
        style_low = adapter.adapt_style(context_low_sat, profile)
        style_high = adapter.adapt_style(context_high_sat, profile)
        
        # Low satisfaction should get more explanations
        assert style_low.explanation_depth > style_high.explanation_depth
    
    def test_reasoning_generation(self):
        """Test that reasoning is generated"""
        adapter = CommunicationAdapter()
        
        context = CommunicationContext(
            customer_id="cust_001",
            task_category="content_creation",
            task_description="Task",
            time_of_day=TaskTiming.MORNING,
            customer_status=CustomerStatus.TRIAL,
            urgency=UrgencyLevel.HIGH,
            domain_expertise_level="beginner",
            available_time_minutes=10
        )
        
        style = adapter.adapt_style(context)
        
        assert style.reasoning != ""
        assert "Adapted based on:" in style.reasoning
        # Should mention multiple factors
        assert "urgency" in style.reasoning.lower() or "high" in style.reasoning.lower()
    
    def test_confidence_calculation(self):
        """Test confidence scoring"""
        adapter = CommunicationAdapter()
        
        # Without profile (lower confidence)
        context1 = CommunicationContext(
            customer_id="cust_001",
            task_category="content_creation",
            task_description="Task",
            time_of_day=TaskTiming.AFTERNOON,
            customer_status=CustomerStatus.PAID
        )
        
        # With detailed profile (higher confidence)
        profile = CustomerProfile(
            customer_id="cust_002",
            total_interactions=50,
            profile_confidence=0.9
        )
        
        context2 = CommunicationContext(
            customer_id="cust_002",
            task_category="content_creation",
            task_description="Task",
            time_of_day=TaskTiming.AFTERNOON,
            customer_status=CustomerStatus.PAID,
            previous_requests_count=10,
            previous_satisfaction=4.5
        )
        
        style1 = adapter.adapt_style(context1)
        style2 = adapter.adapt_style(context2, profile)
        
        # With profile and history should have higher confidence
        assert style2.confidence > style1.confidence
    
    def test_style_to_dict_serialization(self):
        """Test adapted style serialization"""
        adapter = CommunicationAdapter()
        
        context = CommunicationContext(
            customer_id="cust_001",
            task_category="content_creation",
            task_description="Task",
            time_of_day=TaskTiming.AFTERNOON,
            customer_status=CustomerStatus.PAID
        )
        
        style = adapter.adapt_style(context)
        style_dict = style.to_dict()
        
        assert isinstance(style_dict, dict)
        assert "style_id" in style_dict
        assert "customer_id" in style_dict
        assert "tone" in style_dict
        assert "detail_level" in style_dict
        assert "output_format" in style_dict
        assert "reasoning" in style_dict
        assert "confidence" in style_dict
    
    def test_get_template(self):
        """Test template retrieval"""
        adapter = CommunicationAdapter()
        
        # Get default templates
        executive = adapter.get_template("executive")
        comprehensive = adapter.get_template("comprehensive")
        quick_ref = adapter.get_template("quick_reference")
        
        assert executive is not None
        assert executive.template_id == "executive"
        assert executive.includes_main_content is True
        
        assert comprehensive is not None
        assert comprehensive.includes_examples is True
        
        assert quick_ref is not None
        assert quick_ref.includes_next_steps is True
    
    def test_get_customer_adaptations(self):
        """Test retrieval of customer adaptation history"""
        adapter = CommunicationAdapter()
        
        # Create multiple adaptations for same customer
        for i in range(3):
            context = CommunicationContext(
                customer_id="cust_001",
                task_category="content_creation",
                task_description=f"Task {i}",
                time_of_day=TaskTiming.AFTERNOON,
                customer_status=CustomerStatus.PAID
            )
            adapter.adapt_style(context)
        
        adaptations = adapter.get_customer_adaptations("cust_001")
        
        assert len(adaptations) == 3
        assert all(a.customer_id == "cust_001" for a in adaptations)
    
    def test_get_statistics(self):
        """Test statistics retrieval"""
        adapter = CommunicationAdapter()
        
        # Create adaptations for multiple customers
        for customer_num in range(3):
            for i in range(2):
                context = CommunicationContext(
                    customer_id=f"cust_{customer_num:03d}",
                    task_category="content_creation",
                    task_description=f"Task {i}",
                    time_of_day=TaskTiming.AFTERNOON,
                    customer_status=CustomerStatus.PAID
                )
                adapter.adapt_style(context)
        
        stats = adapter.get_statistics()
        
        assert stats["total_customers_adapted"] == 3
        assert stats["total_adaptations"] == 6
        assert stats["average_adaptations_per_customer"] == 2.0
        assert stats["available_templates"] > 0
        assert "template_ids" in stats
    
    def test_multiple_context_factors(self):
        """Test adaptation with multiple context factors"""
        adapter = CommunicationAdapter()
        
        profile = CustomerProfile(
            customer_id="cust_001",
            communication_tone=CommunicationTone.CASUAL,
            detail_level_preference=0.8,
            prefers_explanations=True,
            learning_style=LearningStyle.VISUAL,
            total_interactions=30,
            profile_confidence=0.85
        )
        
        # Context with many constraints
        context = CommunicationContext(
            customer_id="cust_001",
            task_category="data_analysis",
            task_description="Urgent analysis needed",
            time_of_day=TaskTiming.MORNING,
            customer_status=CustomerStatus.ENTERPRISE,
            urgency=UrgencyLevel.HIGH,
            task_complexity=0.8,
            available_time_minutes=15,
            domain_expertise_level="intermediate",
            previous_requests_count=5,
            previous_satisfaction=4.2
        )
        
        style = adapter.adapt_style(context, profile)
        
        # Should balance multiple factors
        assert style is not None
        # High urgency + limited time should reduce detail despite preference
        assert style.detail_level < 0.8
        # Enterprise should make more formal despite casual preference
        assert style.tone_score < 0.8
        # Should have high confidence with good profile
        assert style.confidence > 0.7
        # Complex task should still get structured format
        assert style.output_format in [OutputFormat.STRUCTURED, OutputFormat.MIXED]
