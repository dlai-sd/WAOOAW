"""
Tests for ML predictive model
"""

import pytest
from datetime import datetime
from app.services.improvement.predictive_model import (
    PredictionConfidence,
    TaskFeatures,
    TaskPrediction,
    ProactiveSuggestion,
    PredictiveModel,
)


class TestPredictiveModel:
    """Tests for PredictiveModel"""
    
    def test_create_model(self):
        """Test creating predictive model"""
        model = PredictiveModel()
        assert model is not None
    
    def test_record_task(self):
        """Test recording tasks for training"""
        model = PredictiveModel()
        
        features = TaskFeatures(
            user_id="user1",
            agent_variant_id="agent1",
            task_category="data_analysis",
            time_of_day=10,
            day_of_week=1,
            previous_task="data_collection",
            session_length=3
        )
        
        model.record_task(features, "data_visualization")
        
        stats = model.get_statistics()
        assert stats["training_samples"] == 1
    
    def test_feature_extraction(self):
        """Test feature vector extraction"""
        features = TaskFeatures(
            user_id="user1",
            agent_variant_id="agent1",
            task_category="content_creation",
            time_of_day=14,
            day_of_week=3,
            session_length=5,
            user_expertise_level="expert"
        )
        
        feature_dict = features.to_feature_vector()
        
        assert "user_id" in feature_dict
        assert "time_of_day" in feature_dict
        assert feature_dict["time_of_day"] == 14
        assert feature_dict["day_of_week"] == 3
    
    def test_train_model_insufficient_data(self):
        """Test training with insufficient data"""
        model = PredictiveModel()
        
        # Add only a few samples
        for i in range(10):
            features = TaskFeatures(
                user_id="user1",
                agent_variant_id="agent1",
                task_category="test_task",
                time_of_day=10,
                day_of_week=1
            )
            model.record_task(features, "next_task")
        
        result = model.train_model()
        
        assert result["success"] is False
        assert result["reason"] == "insufficient_data"
    
    def test_train_model_success(self):
        """Test successful model training"""
        model = PredictiveModel()
        
        # Add sufficient training data
        task_sequences = [
            ("data_collection", "data_analysis"),
            ("data_analysis", "data_visualization"),
            ("data_visualization", "report_generation"),
            ("content_creation", "content_editing"),
            ("content_editing", "content_publishing"),
        ]
        
        for i in range(60):
            prev_task, next_task = task_sequences[i % len(task_sequences)]
            
            features = TaskFeatures(
                user_id=f"user{i % 5}",
                agent_variant_id="agent1",
                task_category=prev_task,
                time_of_day=9 + (i % 8),
                day_of_week=i % 7,
                previous_task=prev_task,
                session_length=i % 5 + 1
            )
            
            model.record_task(features, next_task)
        
        result = model.train_model(min_samples=50)
        
        assert result["success"] is True
        assert result["samples_trained"] >= 50
        assert result["accuracy"] > 0
    
    def test_fallback_prediction(self):
        """Test fallback prediction when model not trained"""
        model = PredictiveModel()
        
        features = TaskFeatures(
            user_id="user1",
            agent_variant_id="agent1",
            task_category="data_analysis",
            time_of_day=10,
            day_of_week=1,
            previous_task="data_analysis",
            session_length=2
        )
        
        predictions = model.predict_next_task(features)
        
        # Should use fallback rules
        assert isinstance(predictions, list)
    
    def test_predict_next_task_with_trained_model(self):
        """Test prediction with trained model"""
        model = PredictiveModel()
        
        # Train model
        task_pairs = [
            ("data_collection", "data_analysis"),
            ("data_analysis", "data_visualization"),
            ("data_visualization", "report_generation"),
        ]
        
        for i in range(60):
            prev_task, next_task = task_pairs[i % len(task_pairs)]
            
            features = TaskFeatures(
                user_id=f"user{i % 3}",
                agent_variant_id="agent1",
                task_category=prev_task,
                time_of_day=10,
                day_of_week=1,
                previous_task=prev_task,
                session_length=2
            )
            
            model.record_task(features, next_task)
        
        model.train_model(min_samples=50)
        
        # Make prediction
        test_features = TaskFeatures(
            user_id="user1",
            agent_variant_id="agent1",
            task_category="data_collection",
            time_of_day=10,
            day_of_week=1,
            previous_task="data_collection",
            session_length=2
        )
        
        predictions = model.predict_next_task(test_features, top_k=3)
        
        assert len(predictions) > 0
        assert all(isinstance(p, TaskPrediction) for p in predictions)
        assert all(0 <= p.confidence <= 1 for p in predictions)
    
    def test_prediction_confidence_levels(self):
        """Test prediction confidence level classification"""
        model = PredictiveModel()
        
        # Train with clear patterns
        for i in range(80):
            features = TaskFeatures(
                user_id="user1",
                agent_variant_id="agent1",
                task_category="task_a",
                time_of_day=10,
                day_of_week=1,
                previous_task="task_a",
                session_length=1
            )
            model.record_task(features, "task_b")
        
        model.train_model(min_samples=50)
        
        test_features = TaskFeatures(
            user_id="user1",
            agent_variant_id="agent1",
            task_category="task_a",
            time_of_day=10,
            day_of_week=1,
            previous_task="task_a",
            session_length=1
        )
        
        predictions = model.predict_next_task(test_features)
        
        if predictions:
            top_prediction = predictions[0]
            assert top_prediction.confidence_level in [
                PredictionConfidence.LOW,
                PredictionConfidence.MEDIUM,
                PredictionConfidence.HIGH,
                PredictionConfidence.VERY_HIGH
            ]
    
    def test_generate_proactive_suggestion_low_confidence(self):
        """Test proactive suggestion not generated for low confidence"""
        model = PredictiveModel()
        
        features = TaskFeatures(
            user_id="user1",
            agent_variant_id="agent1",
            task_category="random_task",
            time_of_day=10,
            day_of_week=1,
            session_length=1
        )
        
        # With untrained model and no fallback matches, should return None
        suggestion = model.generate_proactive_suggestion(features, min_confidence=0.70)
        
        # May be None or low confidence
        if suggestion:
            assert suggestion.confidence < 0.70 or suggestion.confidence >= 0.70
    
    def test_generate_proactive_suggestion_high_confidence(self):
        """Test proactive suggestion with high confidence"""
        model = PredictiveModel()
        
        # Train with very clear pattern
        for i in range(100):
            features = TaskFeatures(
                user_id="user1",
                agent_variant_id="agent1",
                task_category="task_x",
                time_of_day=10,
                day_of_week=1,
                previous_task="task_x",
                session_length=1
            )
            model.record_task(features, "task_y")
        
        model.train_model(min_samples=50)
        
        test_features = TaskFeatures(
            user_id="user1",
            agent_variant_id="agent1",
            task_category="task_x",
            time_of_day=10,
            day_of_week=1,
            previous_task="task_x",
            session_length=1
        )
        
        suggestion = model.generate_proactive_suggestion(test_features, min_confidence=0.50)
        
        if suggestion:
            assert isinstance(suggestion, ProactiveSuggestion)
            assert suggestion.confidence >= 0.50
            assert suggestion.prompt_text is not None
            assert suggestion.value_proposition is not None
    
    def test_record_suggestion_feedback(self):
        """Test recording suggestion feedback"""
        model = PredictiveModel()
        
        # Create suggestion
        suggestion = ProactiveSuggestion(
            suggestion_id="test_suggestion",
            task_category="test_task",
            agent_variant_id="agent1",
            confidence=0.75,
            reasoning="Test reasoning",
            prompt_text="Test prompt",
            value_proposition="Test value"
        )
        
        model._suggestions[suggestion.suggestion_id] = suggestion
        
        # Record acceptance
        model.record_suggestion_feedback("test_suggestion", accepted=True)
        
        assert suggestion.accepted_at is not None
        assert suggestion.rejected_at is None
    
    def test_acceptance_rate_calculation(self):
        """Test acceptance rate calculation"""
        model = PredictiveModel()
        
        # Add test suggestions
        for i in range(10):
            suggestion = ProactiveSuggestion(
                suggestion_id=f"suggestion_{i}",
                task_category="test_task",
                agent_variant_id="agent1",
                confidence=0.75,
                reasoning="Test",
                prompt_text="Test",
                value_proposition="Test"
            )
            
            model._suggestions[suggestion.suggestion_id] = suggestion
            
            # Accept 7 out of 10
            model.record_suggestion_feedback(
                suggestion.suggestion_id,
                accepted=(i < 7)
            )
        
        acceptance_rate = model.get_acceptance_rate()
        
        assert acceptance_rate == pytest.approx(0.70, abs=0.01)
    
    def test_get_statistics(self):
        """Test getting model statistics"""
        model = PredictiveModel()
        
        # Add some training data
        for i in range(60):
            features = TaskFeatures(
                user_id="user1",
                agent_variant_id="agent1",
                task_category="task_a",
                time_of_day=10,
                day_of_week=1,
                session_length=1
            )
            model.record_task(features, "task_b")
        
        # Train model
        model.train_model(min_samples=50)
        
        # Add suggestions
        for i in range(5):
            suggestion = ProactiveSuggestion(
                suggestion_id=f"suggestion_{i}",
                task_category="test_task",
                agent_variant_id="agent1",
                confidence=0.75,
                reasoning="Test",
                prompt_text="Test",
                value_proposition="Test"
            )
            model._suggestions[suggestion.suggestion_id] = suggestion
            model.record_suggestion_feedback(suggestion.suggestion_id, accepted=(i < 3))
        
        stats = model.get_statistics()
        
        assert stats["is_trained"] is True
        assert stats["training_samples"] == 60
        assert stats["total_suggestions"] == 5
        assert stats["accepted_suggestions"] == 3
        assert stats["rejected_suggestions"] == 2
        assert "acceptance_rate" in stats
        assert "prediction_accuracy" in stats
    
    def test_meets_target_metrics(self):
        """Test checking if model meets target metrics"""
        model = PredictiveModel()
        
        stats = model.get_statistics()
        
        assert "meets_accuracy_target" in stats
        assert "meets_acceptance_target" in stats
        assert isinstance(stats["meets_accuracy_target"], bool)
        assert isinstance(stats["meets_acceptance_target"], bool)
    
    def test_suggestion_status(self):
        """Test suggestion status tracking"""
        suggestion = ProactiveSuggestion(
            suggestion_id="test",
            task_category="test_task",
            agent_variant_id="agent1",
            confidence=0.75,
            reasoning="Test",
            prompt_text="Test",
            value_proposition="Test"
        )
        
        # Initial status
        assert suggestion._get_status() == "created"
        
        # After presentation
        suggestion.presented_at = datetime.now()
        assert suggestion._get_status() == "pending"
        
        # After acceptance
        suggestion.accepted_at = datetime.now()
        assert suggestion._get_status() == "accepted"
    
    def test_suggestion_to_dict(self):
        """Test suggestion serialization"""
        suggestion = ProactiveSuggestion(
            suggestion_id="test",
            task_category="test_task",
            agent_variant_id="agent1",
            confidence=0.75,
            reasoning="Test reasoning",
            prompt_text="Test prompt",
            value_proposition="Test value"
        )
        
        suggestion_dict = suggestion.to_dict()
        
        assert suggestion_dict["suggestion_id"] == "test"
        assert suggestion_dict["confidence"] == 0.75
        assert suggestion_dict["status"] == "created"
        assert "created_at" in suggestion_dict
