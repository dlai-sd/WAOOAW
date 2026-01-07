"""
ML-based predictive model for proactive task suggestions
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple
import uuid
import pickle
import json

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import LabelEncoder
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    # Fallback implementation without sklearn


class PredictionConfidence(Enum):
    """Confidence levels for predictions"""
    LOW = "low"       # < 50%
    MEDIUM = "medium" # 50-70%
    HIGH = "high"     # 70-85%
    VERY_HIGH = "very_high"  # > 85%


@dataclass
class TaskFeatures:
    """Features extracted from task for prediction"""
    user_id: str
    agent_variant_id: str
    task_category: str
    time_of_day: int  # 0-23 hour
    day_of_week: int  # 0-6 (Monday=0)
    previous_task: Optional[str] = None
    session_length: int = 0  # Number of tasks in session
    user_expertise_level: str = "intermediate"  # beginner, intermediate, expert
    
    def to_feature_vector(self) -> Dict[str, any]:
        """Convert to feature vector for ML"""
        return {
            "user_id": self.user_id,
            "agent_variant_id": self.agent_variant_id,
            "task_category": self.task_category,
            "time_of_day": self.time_of_day,
            "day_of_week": self.day_of_week,
            "previous_task": self.previous_task or "none",
            "session_length": self.session_length,
            "user_expertise_level": self.user_expertise_level,
        }


@dataclass
class TaskPrediction:
    """Predicted task with confidence"""
    prediction_id: str
    predicted_task_category: str
    predicted_agent_variant: str
    confidence: float  # 0-1
    confidence_level: PredictionConfidence
    features_used: Dict
    reasoning: str
    suggested_prompt: Optional[str] = None
    predicted_at: datetime = field(default_factory=datetime.now)
    accepted: Optional[bool] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class ProactiveSuggestion:
    """Proactive task suggestion for user"""
    suggestion_id: str
    task_category: str
    agent_variant_id: str
    confidence: float
    reasoning: str
    prompt_text: str
    value_proposition: str  # Why this would be valuable
    created_at: datetime = field(default_factory=datetime.now)
    presented_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "suggestion_id": self.suggestion_id,
            "task_category": self.task_category,
            "agent_variant_id": self.agent_variant_id,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "prompt_text": self.prompt_text,
            "value_proposition": self.value_proposition,
            "created_at": self.created_at.isoformat(),
            "presented_at": self.presented_at.isoformat() if self.presented_at else None,
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "rejected_at": self.rejected_at.isoformat() if self.rejected_at else None,
            "status": self._get_status(),
        }
    
    def _get_status(self) -> str:
        """Get suggestion status"""
        if self.accepted_at:
            return "accepted"
        elif self.rejected_at:
            return "rejected"
        elif self.presented_at:
            return "pending"
        else:
            return "created"


class PredictiveModel:
    """
    ML-based predictive model for task suggestions.
    
    Uses RandomForest classifier to predict next task based on:
    - User behavior patterns
    - Time of day/week
    - Previous task sequences
    - Agent performance history
    
    Target: 70%+ prediction accuracy, 60%+ acceptance rate
    """
    
    def __init__(self):
        self._training_data: List[Tuple[TaskFeatures, str]] = []
        self._predictions: Dict[str, TaskPrediction] = {}
        self._suggestions: Dict[str, ProactiveSuggestion] = {}
        
        # Encoders for categorical features
        self._label_encoders: Dict[str, LabelEncoder] = {}
        self._task_encoder: Optional[LabelEncoder] = None
        
        # Model
        self._model: Optional[RandomForestClassifier] = None
        self._is_trained = False
        self._min_training_samples = 50
        
        # Performance tracking
        self._accuracy_history: List[float] = []
        self._acceptance_rate_history: List[float] = []
    
    def record_task(
        self,
        features: TaskFeatures,
        actual_task_category: str
    ):
        """Record task for training"""
        self._training_data.append((features, actual_task_category))
    
    def train_model(self, min_samples: Optional[int] = None) -> Dict:
        """
        Train the predictive model.
        
        Returns training metrics.
        """
        if not SKLEARN_AVAILABLE:
            return {"error": "sklearn not available", "success": False}
        
        min_samples = min_samples or self._min_training_samples
        
        if len(self._training_data) < min_samples:
            return {
                "success": False,
                "reason": "insufficient_data",
                "samples": len(self._training_data),
                "required": min_samples
            }
        
        # Prepare training data
        X = []
        y = []
        
        for features, task_category in self._training_data:
            X.append(self._encode_features(features))
            y.append(task_category)
        
        # Encode target labels
        if self._task_encoder is None:
            self._task_encoder = LabelEncoder()
            y_encoded = self._task_encoder.fit_transform(y)
        else:
            y_encoded = self._task_encoder.transform(y)
        
        # Train model
        X_array = np.array(X)
        
        self._model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42
        )
        
        self._model.fit(X_array, y_encoded)
        self._is_trained = True
        
        # Calculate accuracy on training data (in production, use cross-validation)
        predictions = self._model.predict(X_array)
        accuracy = np.mean(predictions == y_encoded)
        self._accuracy_history.append(accuracy)
        
        return {
            "success": True,
            "samples_trained": len(self._training_data),
            "accuracy": accuracy,
            "features": len(X[0]) if X else 0,
            "unique_tasks": len(self._task_encoder.classes_) if self._task_encoder else 0
        }
    
    def _encode_features(self, features: TaskFeatures) -> List[float]:
        """Encode features for ML model"""
        feature_vector = []
        feature_dict = features.to_feature_vector()
        
        # Encode categorical features
        for key, value in feature_dict.items():
            if key in ["time_of_day", "day_of_week", "session_length"]:
                # Numerical features
                feature_vector.append(float(value))
            else:
                # Categorical features
                if key not in self._label_encoders:
                    self._label_encoders[key] = LabelEncoder()
                    self._label_encoders[key].fit([str(value)])
                
                # Handle unseen labels
                try:
                    encoded = self._label_encoders[key].transform([str(value)])[0]
                except ValueError:
                    # Unseen label, use 0
                    encoded = 0
                
                feature_vector.append(float(encoded))
        
        return feature_vector
    
    def predict_next_task(
        self,
        features: TaskFeatures,
        top_k: int = 3
    ) -> List[TaskPrediction]:
        """
        Predict next task based on features.
        
        Returns top K predictions with confidence scores.
        """
        if not self._is_trained or self._model is None:
            # Fallback: rule-based prediction
            return self._fallback_prediction(features, top_k)
        
        # Encode features
        X = np.array([self._encode_features(features)])
        
        # Get prediction probabilities
        probabilities = self._model.predict_proba(X)[0]
        
        # Get top K predictions
        top_k_indices = np.argsort(probabilities)[-top_k:][::-1]
        
        predictions = []
        for idx in top_k_indices:
            confidence = probabilities[idx]
            
            if confidence < 0.3:  # Skip very low confidence
                continue
            
            task_category = self._task_encoder.inverse_transform([idx])[0]
            
            # Determine confidence level
            if confidence >= 0.85:
                conf_level = PredictionConfidence.VERY_HIGH
            elif confidence >= 0.70:
                conf_level = PredictionConfidence.HIGH
            elif confidence >= 0.50:
                conf_level = PredictionConfidence.MEDIUM
            else:
                conf_level = PredictionConfidence.LOW
            
            prediction = TaskPrediction(
                prediction_id=str(uuid.uuid4()),
                predicted_task_category=task_category,
                predicted_agent_variant=features.agent_variant_id,
                confidence=float(confidence),
                confidence_level=conf_level,
                features_used=features.to_feature_vector(),
                reasoning=self._generate_reasoning(features, task_category, confidence)
            )
            
            self._predictions[prediction.prediction_id] = prediction
            predictions.append(prediction)
        
        return predictions
    
    def _fallback_prediction(
        self,
        features: TaskFeatures,
        top_k: int
    ) -> List[TaskPrediction]:
        """Fallback rule-based prediction when model not trained"""
        # Simple heuristics based on previous task and time
        predictions = []
        
        # Common sequences
        sequences = {
            "data_analysis": ["data_visualization", "report_generation"],
            "content_creation": ["content_editing", "content_publishing"],
            "customer_support": ["follow_up", "feedback_collection"],
        }
        
        if features.previous_task and features.previous_task in sequences:
            for i, next_task in enumerate(sequences[features.previous_task][:top_k]):
                confidence = 0.6 - (i * 0.1)  # Decreasing confidence
                
                prediction = TaskPrediction(
                    prediction_id=str(uuid.uuid4()),
                    predicted_task_category=next_task,
                    predicted_agent_variant=features.agent_variant_id,
                    confidence=confidence,
                    confidence_level=PredictionConfidence.MEDIUM,
                    features_used=features.to_feature_vector(),
                    reasoning=f"Common sequence after {features.previous_task}",
                    metadata={"fallback": True}
                )
                
                predictions.append(prediction)
        
        return predictions
    
    def _generate_reasoning(
        self,
        features: TaskFeatures,
        predicted_task: str,
        confidence: float
    ) -> str:
        """Generate human-readable reasoning for prediction"""
        reasons = []
        
        if features.previous_task:
            reasons.append(f"follows {features.previous_task}")
        
        if features.time_of_day < 12:
            reasons.append("typical morning task")
        elif features.time_of_day < 18:
            reasons.append("common afternoon task")
        else:
            reasons.append("evening task pattern")
        
        if features.session_length > 3:
            reasons.append("longer session indicates complex workflow")
        
        reasoning = f"Predicted {predicted_task} ({confidence:.0%} confidence) based on: "
        reasoning += ", ".join(reasons)
        
        return reasoning
    
    def generate_proactive_suggestion(
        self,
        features: TaskFeatures,
        min_confidence: float = 0.70
    ) -> Optional[ProactiveSuggestion]:
        """
        Generate proactive suggestion for user.
        
        Only suggests if confidence >= min_confidence (default 70%).
        """
        predictions = self.predict_next_task(features, top_k=1)
        
        if not predictions:
            return None
        
        top_prediction = predictions[0]
        
        if top_prediction.confidence < min_confidence:
            return None
        
        # Generate suggestion
        suggestion = ProactiveSuggestion(
            suggestion_id=str(uuid.uuid4()),
            task_category=top_prediction.predicted_task_category,
            agent_variant_id=top_prediction.predicted_agent_variant,
            confidence=top_prediction.confidence,
            reasoning=top_prediction.reasoning,
            prompt_text=self._generate_prompt_text(top_prediction),
            value_proposition=self._generate_value_proposition(top_prediction)
        )
        
        self._suggestions[suggestion.suggestion_id] = suggestion
        
        return suggestion
    
    def _generate_prompt_text(self, prediction: TaskPrediction) -> str:
        """Generate prompt text for suggestion"""
        task = prediction.predicted_task_category.replace("_", " ").title()
        return f"Would you like me to help with {task}?"
    
    def _generate_value_proposition(self, prediction: TaskPrediction) -> str:
        """Generate value proposition for suggestion"""
        confidence_pct = int(prediction.confidence * 100)
        
        value_props = {
            "data_analysis": "Get insights from your data faster",
            "data_visualization": "Create compelling visualizations",
            "report_generation": "Generate comprehensive reports",
            "content_creation": "Create engaging content",
            "content_editing": "Polish and improve your content",
            "customer_support": "Resolve customer issues efficiently",
            "follow_up": "Maintain customer relationships",
        }
        
        task = prediction.predicted_task_category
        base_value = value_props.get(task, "Complete your task efficiently")
        
        return f"{base_value} (Based on your workflow, {confidence_pct}% match)"
    
    def record_suggestion_feedback(
        self,
        suggestion_id: str,
        accepted: bool,
        presented_at: Optional[datetime] = None
    ):
        """Record user feedback on suggestion"""
        if suggestion_id not in self._suggestions:
            raise ValueError(f"Suggestion {suggestion_id} not found")
        
        suggestion = self._suggestions[suggestion_id]
        
        if presented_at:
            suggestion.presented_at = presented_at
        
        if accepted:
            suggestion.accepted_at = datetime.now()
        else:
            suggestion.rejected_at = datetime.now()
    
    def get_acceptance_rate(self) -> float:
        """Calculate suggestion acceptance rate"""
        total = 0
        accepted = 0
        
        for suggestion in self._suggestions.values():
            if suggestion.accepted_at or suggestion.rejected_at:
                total += 1
                if suggestion.accepted_at:
                    accepted += 1
        
        if total == 0:
            return 0.0
        
        rate = accepted / total
        self._acceptance_rate_history.append(rate)
        
        return rate
    
    def get_prediction_accuracy(self) -> float:
        """Calculate prediction accuracy"""
        if not self._accuracy_history:
            return 0.0
        
        return self._accuracy_history[-1] if self._accuracy_history else 0.0
    
    def get_statistics(self) -> Dict:
        """Get model statistics"""
        acceptance_rate = self.get_acceptance_rate()
        accuracy = self.get_prediction_accuracy()
        
        total_suggestions = len(self._suggestions)
        accepted_suggestions = sum(
            1 for s in self._suggestions.values()
            if s.accepted_at is not None
        )
        rejected_suggestions = sum(
            1 for s in self._suggestions.values()
            if s.rejected_at is not None
        )
        pending_suggestions = total_suggestions - accepted_suggestions - rejected_suggestions
        
        return {
            "is_trained": self._is_trained,
            "training_samples": len(self._training_data),
            "total_predictions": len(self._predictions),
            "prediction_accuracy": accuracy,
            "accuracy_trend": self._accuracy_history[-5:] if self._accuracy_history else [],
            "total_suggestions": total_suggestions,
            "accepted_suggestions": accepted_suggestions,
            "rejected_suggestions": rejected_suggestions,
            "pending_suggestions": pending_suggestions,
            "acceptance_rate": acceptance_rate,
            "acceptance_trend": self._acceptance_rate_history[-5:] if self._acceptance_rate_history else [],
            "meets_accuracy_target": accuracy >= 0.70,
            "meets_acceptance_target": acceptance_rate >= 0.60,
        }
    
    def save_model(self, filepath: str):
        """Save model to file"""
        if not self._is_trained:
            raise ValueError("Model not trained yet")
        
        model_data = {
            "model": self._model,
            "task_encoder": self._task_encoder,
            "label_encoders": self._label_encoders,
            "training_samples": len(self._training_data),
            "accuracy_history": self._accuracy_history,
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load_model(self, filepath: str):
        """Load model from file"""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self._model = model_data["model"]
        self._task_encoder = model_data["task_encoder"]
        self._label_encoders = model_data["label_encoders"]
        self._accuracy_history = model_data.get("accuracy_history", [])
        self._is_trained = True
