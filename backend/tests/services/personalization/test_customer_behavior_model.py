"""
Tests for Customer Behavior Modeling - Story 5.5.1

Epic 5.5: Hyper-Personalization & Adaptation
Story Points: 21
"""

import pytest
from datetime import datetime, timedelta
from app.services.personalization import (
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


class TestCustomerBehaviorModel:
    """Test suite for customer behavior modeling"""
    
    def test_create_model(self):
        """Test model instantiation"""
        model = CustomerBehaviorModel()
        
        assert model is not None
        stats = model.get_statistics()
        assert stats["total_customers"] == 0
        assert stats["total_interactions"] == 0
        assert stats["customers_with_profiles"] == 0
    
    def test_record_interaction(self):
        """Test recording customer interactions"""
        model = CustomerBehaviorModel()
        
        interaction = CustomerInteraction(
            interaction_id="int_001",
            customer_id="cust_001",
            agent_variant_id="agent_marketing",
            task_category="content_creation",
            task_description="Create blog post",
            timestamp=datetime.now(),
            time_of_day=TaskTiming.MORNING,
            rating=4.5,
            completion_time_minutes=45,
            output_used=True,
            accepted_quickly=True
        )
        
        model.record_interaction(interaction)
        
        stats = model.get_statistics()
        assert stats["total_customers"] == 1
        assert stats["total_interactions"] == 1
    
    def test_profile_creation_insufficient_data(self):
        """Test that profile is not created with insufficient data"""
        model = CustomerBehaviorModel()
        
        # Add only 5 interactions (need 10 for profile)
        for i in range(5):
            interaction = CustomerInteraction(
                interaction_id=f"int_{i}",
                customer_id="cust_001",
                agent_variant_id="agent_marketing",
                task_category="content_creation",
                task_description="Task",
                timestamp=datetime.now(),
                time_of_day=TaskTiming.MORNING
            )
            model.record_interaction(interaction)
        
        profile = model.get_customer_profile("cust_001")
        assert profile is None  # Not enough data yet
    
    def test_profile_creation_sufficient_data(self):
        """Test profile creation with sufficient data"""
        model = CustomerBehaviorModel()
        
        # Add 15 interactions
        for i in range(15):
            interaction = CustomerInteraction(
                interaction_id=f"int_{i}",
                customer_id="cust_001",
                agent_variant_id="agent_marketing",
                task_category="content_creation" if i % 2 == 0 else "seo_optimization",
                task_description="Task",
                timestamp=datetime.now() - timedelta(days=15 - i),
                time_of_day=TaskTiming.MORNING,
                rating=4.0 + (i % 3) * 0.3,
                completion_time_minutes=30 + i,
                output_used=i % 3 == 0,
                accepted_quickly=i % 2 == 0
            )
            model.record_interaction(interaction)
        
        profile = model.get_customer_profile("cust_001")
        
        assert profile is not None
        assert profile.customer_id == "cust_001"
        assert profile.total_interactions == 15
        assert len(profile.most_common_tasks) > 0
        assert profile.typical_timing == TaskTiming.MORNING
        assert profile.average_rating > 0
        assert profile.profile_confidence > 0
    
    def test_most_common_tasks(self):
        """Test identification of most common tasks"""
        model = CustomerBehaviorModel()
        
        # Add interactions with clear pattern: 10 content, 5 seo, 2 email
        tasks = (
            ["content_creation"] * 10 +
            ["seo_optimization"] * 5 +
            ["email_marketing"] * 2
        )
        
        for i, task in enumerate(tasks):
            interaction = CustomerInteraction(
                interaction_id=f"int_{i}",
                customer_id="cust_001",
                agent_variant_id="agent_marketing",
                task_category=task,
                task_description="Task",
                timestamp=datetime.now() - timedelta(hours=len(tasks) - i),
                time_of_day=TaskTiming.AFTERNOON
            )
            model.record_interaction(interaction)
        
        profile = model.get_customer_profile("cust_001")
        
        assert profile is not None
        assert len(profile.most_common_tasks) == 3
        # Most common should be content_creation
        assert profile.most_common_tasks[0][0] == "content_creation"
        # Frequency should be ~59% (10/17)
        assert 0.55 < profile.most_common_tasks[0][1] < 0.65
    
    def test_quality_preference_inference(self):
        """Test inference of quality preferences from behavior"""
        model = CustomerBehaviorModel()
        
        # Add high-rated interactions with long completion times (depth preference)
        for i in range(15):
            interaction = CustomerInteraction(
                interaction_id=f"int_{i}",
                customer_id="cust_depth",
                agent_variant_id="agent_marketing",
                task_category="content_creation",
                task_description="Task",
                timestamp=datetime.now() - timedelta(hours=15 - i),
                time_of_day=TaskTiming.AFTERNOON,
                rating=4.8,
                completion_time_minutes=75  # Long completion times
            )
            model.record_interaction(interaction)
        
        profile = model.get_customer_profile("cust_depth")
        
        assert profile is not None
        # Should infer DEPTH preference from long, high-rated tasks
        assert profile.quality_preference == QualityPreference.DEPTH
        
        # Now test SPEED preference
        model2 = CustomerBehaviorModel()
        for i in range(15):
            interaction = CustomerInteraction(
                interaction_id=f"int_{i}",
                customer_id="cust_speed",
                agent_variant_id="agent_marketing",
                task_category="content_creation",
                task_description="Task",
                timestamp=datetime.now() - timedelta(hours=15 - i),
                time_of_day=TaskTiming.AFTERNOON,
                rating=4.5,
                completion_time_minutes=15  # Short completion times
            )
            model2.record_interaction(interaction)
        
        profile2 = model2.get_customer_profile("cust_speed")
        
        assert profile2 is not None
        assert profile2.quality_preference == QualityPreference.SPEED
    
    def test_sequential_pattern_detection(self):
        """Test detection of sequential task patterns"""
        model = CustomerBehaviorModel()
        
        # Create clear sequential pattern: content_creation → seo_optimization
        # Repeat 8 times to establish pattern (needs 30%+ frequency)
        for i in range(8):
            # First task
            interaction1 = CustomerInteraction(
                interaction_id=f"int_{i * 2}",
                customer_id="cust_001",
                agent_variant_id="agent_marketing",
                task_category="content_creation",
                task_description="Create content",
                timestamp=datetime.now() - timedelta(hours=(8 - i) * 2),
                time_of_day=TaskTiming.MORNING
            )
            model.record_interaction(interaction1)
            
            # Second task (within 24 hours)
            interaction2 = CustomerInteraction(
                interaction_id=f"int_{i * 2 + 1}",
                customer_id="cust_001",
                agent_variant_id="agent_marketing",
                task_category="seo_optimization",
                task_description="Optimize SEO",
                timestamp=datetime.now() - timedelta(hours=(8 - i) * 2 - 1),
                time_of_day=TaskTiming.MORNING
            )
            model.record_interaction(interaction2)
        
        patterns = model.get_patterns("cust_001")
        
        # Should detect sequential pattern
        sequential_patterns = [p for p in patterns if p.pattern_type == "sequential"]
        assert len(sequential_patterns) > 0
        
        # Find the content → seo pattern
        content_seo_pattern = next(
            (p for p in sequential_patterns 
             if "content_creation" in p.task_categories 
             and "seo_optimization" in p.task_categories),
            None
        )
        assert content_seo_pattern is not None
        assert content_seo_pattern.frequency >= 0.3
        assert content_seo_pattern.confidence > 0.5
    
    def test_temporal_pattern_detection(self):
        """Test detection of temporal task patterns"""
        model = CustomerBehaviorModel()
        
        # Morning: Always content_creation (10 times)
        for i in range(10):
            interaction = CustomerInteraction(
                interaction_id=f"int_morning_{i}",
                customer_id="cust_001",
                agent_variant_id="agent_marketing",
                task_category="content_creation",
                task_description="Morning content",
                timestamp=datetime.now() - timedelta(days=10 - i, hours=9),
                time_of_day=TaskTiming.MORNING
            )
            model.record_interaction(interaction)
        
        # Afternoon: Always seo_optimization (8 times)
        for i in range(8):
            interaction = CustomerInteraction(
                interaction_id=f"int_afternoon_{i}",
                customer_id="cust_001",
                agent_variant_id="agent_marketing",
                task_category="seo_optimization",
                task_description="Afternoon SEO",
                timestamp=datetime.now() - timedelta(days=8 - i, hours=15),
                time_of_day=TaskTiming.AFTERNOON
            )
            model.record_interaction(interaction)
        
        patterns = model.get_patterns("cust_001")
        
        # Should detect temporal patterns
        temporal_patterns = [p for p in patterns if p.pattern_type == "temporal"]
        assert len(temporal_patterns) >= 2  # At least morning and afternoon patterns
        
        # Find morning content pattern
        morning_pattern = next(
            (p for p in temporal_patterns 
             if p.metadata.get("timing") == "morning" 
             and "content_creation" in p.task_categories),
            None
        )
        assert morning_pattern is not None
        assert morning_pattern.frequency >= 0.5  # 100% of morning tasks
    
    def test_predict_next_task_sequential(self):
        """Test next task prediction using sequential patterns"""
        model = CustomerBehaviorModel()
        
        # Establish pattern: data_analysis → data_visualization (repeat 10 times)
        for i in range(10):
            interaction1 = CustomerInteraction(
                interaction_id=f"int_{i * 2}",
                customer_id="cust_001",
                agent_variant_id="agent_data",
                task_category="data_analysis",
                task_description="Analyze data",
                timestamp=datetime.now() - timedelta(days=10 - i, hours=2),
                time_of_day=TaskTiming.AFTERNOON
            )
            model.record_interaction(interaction1)
            
            interaction2 = CustomerInteraction(
                interaction_id=f"int_{i * 2 + 1}",
                customer_id="cust_001",
                agent_variant_id="agent_data",
                task_category="data_visualization",
                task_description="Visualize data",
                timestamp=datetime.now() - timedelta(days=10 - i, hours=1),
                time_of_day=TaskTiming.AFTERNOON
            )
            model.record_interaction(interaction2)
        
        # Predict next task after data_analysis
        prediction = model.predict_next_task(
            "cust_001",
            current_context={"last_task": "data_analysis"}
        )
        
        assert prediction is not None
        assert prediction.prediction_type == "next_task"
        assert prediction.predicted_value == "data_visualization"
        assert prediction.confidence > 0.6
        assert "Pattern detected" in prediction.reasoning
    
    def test_predict_next_task_temporal(self):
        """Test next task prediction using temporal patterns"""
        model = CustomerBehaviorModel()
        
        # Morning: Always content_creation
        for i in range(12):
            interaction = CustomerInteraction(
                interaction_id=f"int_{i}",
                customer_id="cust_001",
                agent_variant_id="agent_marketing",
                task_category="content_creation",
                task_description="Morning content",
                timestamp=datetime.now() - timedelta(days=12 - i, hours=9),
                time_of_day=TaskTiming.MORNING
            )
            model.record_interaction(interaction)
        
        # Predict task for morning
        prediction = model.predict_next_task(
            "cust_001",
            current_context={"time_of_day": TaskTiming.MORNING}
        )
        
        assert prediction is not None
        assert prediction.predicted_value == "content_creation"
        assert prediction.confidence > 0.5
        assert "Time-based pattern" in prediction.reasoning
    
    def test_predict_satisfaction(self):
        """Test satisfaction prediction"""
        model = CustomerBehaviorModel()
        
        # Add interactions for specific task type with ratings
        for i in range(12):
            interaction = CustomerInteraction(
                interaction_id=f"int_{i}",
                customer_id="cust_001",
                agent_variant_id="agent_marketing",
                task_category="content_creation",
                task_description="Task",
                timestamp=datetime.now() - timedelta(days=12 - i),
                time_of_day=TaskTiming.AFTERNOON,
                rating=4.5 + (i % 3) * 0.1  # Ratings around 4.5-4.7
            )
            model.record_interaction(interaction)
        
        # Predict satisfaction for content_creation
        prediction = model.predict_satisfaction(
            "cust_001",
            task_context={"task_category": "content_creation"}
        )
        
        assert prediction is not None
        assert prediction.prediction_type == "satisfaction"
        assert 4.0 <= prediction.predicted_value <= 5.0
        assert prediction.confidence > 0.5
        assert "similar tasks" in prediction.reasoning.lower()
    
    def test_get_style_preference(self):
        """Test retrieval of style preferences"""
        model = CustomerBehaviorModel()
        
        # Add enough interactions to build profile
        for i in range(15):
            interaction = CustomerInteraction(
                interaction_id=f"int_{i}",
                customer_id="cust_001",
                agent_variant_id="agent_marketing",
                task_category="content_creation",
                task_description="Task",
                timestamp=datetime.now() - timedelta(hours=15 - i),
                time_of_day=TaskTiming.AFTERNOON,
                rating=4.5,
                completion_time_minutes=45,
                requested_changes=["add more detail"] if i % 3 == 0 else []
            )
            model.record_interaction(interaction)
        
        preferences = model.get_style_preference("cust_001")
        
        assert preferences is not None
        assert "communication_tone" in preferences
        assert "detail_level" in preferences
        assert "prefers_explanations" in preferences
        assert "learning_style" in preferences
        assert "quality_preference" in preferences
        assert "confidence" in preferences
        assert 0.0 <= preferences["detail_level"] <= 1.0
        assert 0.0 <= preferences["confidence"] <= 1.0
    
    def test_detail_level_preference_inference(self):
        """Test inference of detail level preferences"""
        model = CustomerBehaviorModel()
        
        # Customer who always requests more detail
        for i in range(15):
            interaction = CustomerInteraction(
                interaction_id=f"int_{i}",
                customer_id="cust_detail",
                agent_variant_id="agent_marketing",
                task_category="content_creation",
                task_description="Task",
                timestamp=datetime.now() - timedelta(hours=15 - i),
                time_of_day=TaskTiming.AFTERNOON,
                requested_changes=["add more detail", "need more information"]
            )
            model.record_interaction(interaction)
        
        profile = model.get_customer_profile("cust_detail")
        
        assert profile is not None
        # Should infer high detail preference
        assert profile.detail_level_preference > 0.7
    
    def test_profile_confidence_scoring(self):
        """Test profile confidence calculation"""
        model = CustomerBehaviorModel()
        
        # Add 50 interactions with ratings
        for i in range(50):
            interaction = CustomerInteraction(
                interaction_id=f"int_{i}",
                customer_id="cust_001",
                agent_variant_id="agent_marketing",
                task_category="content_creation",
                task_description="Task",
                timestamp=datetime.now() - timedelta(hours=50 - i),
                time_of_day=TaskTiming.AFTERNOON,
                rating=4.5
            )
            model.record_interaction(interaction)
        
        profile = model.get_customer_profile("cust_001")
        
        assert profile is not None
        # With 50 interactions and ratings, confidence should be high
        assert profile.profile_confidence > 0.6
    
    def test_profile_to_dict_serialization(self):
        """Test profile serialization"""
        model = CustomerBehaviorModel()
        
        # Add interactions
        for i in range(15):
            interaction = CustomerInteraction(
                interaction_id=f"int_{i}",
                customer_id="cust_001",
                agent_variant_id="agent_marketing",
                task_category="content_creation",
                task_description="Task",
                timestamp=datetime.now() - timedelta(hours=15 - i),
                time_of_day=TaskTiming.AFTERNOON,
                rating=4.5
            )
            model.record_interaction(interaction)
        
        profile = model.get_customer_profile("cust_001")
        profile_dict = profile.to_dict()
        
        assert isinstance(profile_dict, dict)
        assert profile_dict["customer_id"] == "cust_001"
        assert "most_common_tasks" in profile_dict
        assert "typical_timing" in profile_dict
        assert "quality_preference" in profile_dict
        assert "communication_tone" in profile_dict
        assert "profile_confidence" in profile_dict
    
    def test_pattern_to_dict_serialization(self):
        """Test pattern serialization"""
        model = CustomerBehaviorModel()
        
        # Create pattern
        for i in range(12):
            interaction = CustomerInteraction(
                interaction_id=f"int_{i}",
                customer_id="cust_001",
                agent_variant_id="agent_marketing",
                task_category="content_creation",
                task_description="Task",
                timestamp=datetime.now() - timedelta(hours=12 - i),
                time_of_day=TaskTiming.MORNING
            )
            model.record_interaction(interaction)
        
        patterns = model.get_patterns("cust_001")
        
        assert len(patterns) > 0
        pattern_dict = patterns[0].to_dict()
        
        assert isinstance(pattern_dict, dict)
        assert "pattern_id" in pattern_dict
        assert "pattern_type" in pattern_dict
        assert "task_categories" in pattern_dict
        assert "frequency" in pattern_dict
        assert "confidence" in pattern_dict
    
    def test_multiple_customers(self):
        """Test handling multiple customers independently"""
        model = CustomerBehaviorModel()
        
        # Customer 1: Prefers content_creation
        for i in range(15):
            interaction = CustomerInteraction(
                interaction_id=f"cust1_int_{i}",
                customer_id="cust_001",
                agent_variant_id="agent_marketing",
                task_category="content_creation",
                task_description="Task",
                timestamp=datetime.now() - timedelta(hours=15 - i),
                time_of_day=TaskTiming.MORNING
            )
            model.record_interaction(interaction)
        
        # Customer 2: Prefers data_analysis
        for i in range(15):
            interaction = CustomerInteraction(
                interaction_id=f"cust2_int_{i}",
                customer_id="cust_002",
                agent_variant_id="agent_data",
                task_category="data_analysis",
                task_description="Task",
                timestamp=datetime.now() - timedelta(hours=15 - i),
                time_of_day=TaskTiming.AFTERNOON
            )
            model.record_interaction(interaction)
        
        profile1 = model.get_customer_profile("cust_001")
        profile2 = model.get_customer_profile("cust_002")
        
        assert profile1 is not None
        assert profile2 is not None
        assert profile1.customer_id == "cust_001"
        assert profile2.customer_id == "cust_002"
        assert profile1.most_common_tasks[0][0] == "content_creation"
        assert profile2.most_common_tasks[0][0] == "data_analysis"
        assert profile1.typical_timing == TaskTiming.MORNING
        assert profile2.typical_timing == TaskTiming.AFTERNOON
    
    def test_get_statistics(self):
        """Test statistics retrieval"""
        model = CustomerBehaviorModel()
        
        # Add data for 3 customers
        for customer_num in range(3):
            for i in range(12):
                interaction = CustomerInteraction(
                    interaction_id=f"cust{customer_num}_int_{i}",
                    customer_id=f"cust_{customer_num:03d}",
                    agent_variant_id="agent_marketing",
                    task_category="content_creation",
                    task_description="Task",
                    timestamp=datetime.now() - timedelta(hours=12 - i),
                    time_of_day=TaskTiming.AFTERNOON
                )
                model.record_interaction(interaction)
        
        stats = model.get_statistics()
        
        assert stats["total_customers"] == 3
        assert stats["total_interactions"] == 36
        assert stats["customers_with_profiles"] == 3
        assert stats["average_interactions_per_customer"] == 12.0
        assert stats["total_patterns_detected"] > 0
        assert "sklearn_available" in stats
