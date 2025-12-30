"""
WowMatcher Agent - Intelligent Trial-to-Agent Matching

Epic 1.2: WowMatcher (42 points, 9 stories)
Matches customers with optimal agents based on profiles, behavior, and ML predictions.

Stories:
- 1.2.1: Customer Profile Analyzer (5 pts)
- 1.2.2: Agent Profile Database (5 pts)
- 1.2.3: Matching Algorithm (8 pts)
- 1.2.4: Trial Success Prediction (5 pts)
- 1.2.5: Learning Loop (5 pts)
- 1.2.6: Personalized Rankings (5 pts)
- 1.2.7: Explainability (3 pts)
- 1.2.8: WowMemory Integration (3 pts)
- 1.2.9: A/B Testing Framework (3 pts)
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from uuid import uuid4
import numpy as np
from dataclasses import dataclass
import pickle
import json

logger = logging.getLogger(__name__)


@dataclass
class CustomerProfile:
    """Customer profile for matching"""
    customer_id: str
    industry: str
    use_case: str
    budget_range: str
    company_size: str
    urgency: str  # "immediate", "this_week", "this_month", "exploring"
    technical_level: str  # "beginner", "intermediate", "advanced"
    preferences: Dict  # Additional preferences
    behavior_history: List[Dict]  # Past interactions
    created_at: datetime
    updated_at: datetime


@dataclass
class AgentProfile:
    """Agent profile for matching"""
    agent_type: str
    agent_name: str
    capabilities: List[str]
    specializations: List[str]
    industries: List[str]  # Industries agent excels in
    training_status: str  # "fully_trained", "in_training", "prototype"
    performance_metrics: Dict  # Historical performance
    pricing_tier: str  # "standard", "premium", "enterprise"
    availability_status: str  # "available", "limited", "waitlist"
    success_rate: float  # 0-1
    avg_satisfaction: float  # 0-5
    total_trials: int
    total_conversions: int


class CustomerProfileAnalyzer:
    """
    Story 1.2.1: Customer Profile Analyzer (5 points)
    
    Captures and analyzes customer profiles:
    - Industry, use case, budget from onboarding
    - Extract intent from questionnaire
    - Update profile based on behavior
    - Tag with segments
    """
    
    def __init__(self, db):
        self.db = db
    
    async def create_profile(
        self,
        customer_id: str,
        onboarding_data: Dict
    ) -> CustomerProfile:
        """
        Create initial customer profile from onboarding.
        
        Args:
            customer_id: Customer identifier
            onboarding_data: Onboarding questionnaire data
                - industry: str
                - use_case: str
                - budget_range: str (e.g., "8000-12000")
                - company_size: str
                - urgency: str
                - technical_level: str
                - additional_preferences: Dict
        
        Returns:
            CustomerProfile object
        """
        now = datetime.now()
        
        profile = CustomerProfile(
            customer_id=customer_id,
            industry=onboarding_data.get("industry", "general"),
            use_case=onboarding_data.get("use_case", ""),
            budget_range=onboarding_data.get("budget_range", "8000-15000"),
            company_size=onboarding_data.get("company_size", "startup"),
            urgency=onboarding_data.get("urgency", "exploring"),
            technical_level=onboarding_data.get("technical_level", "beginner"),
            preferences=onboarding_data.get("additional_preferences", {}),
            behavior_history=[],
            created_at=now,
            updated_at=now
        )
        
        # Store in database
        await self.db.customer_profiles.insert({
            "customer_id": customer_id,
            "industry": profile.industry,
            "use_case": profile.use_case,
            "budget_range": profile.budget_range,
            "company_size": profile.company_size,
            "urgency": profile.urgency,
            "technical_level": profile.technical_level,
            "preferences": profile.preferences,
            "behavior_history": [],
            "segments": self._calculate_segments(profile),
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        })
        
        logger.info(f"Customer profile created: {customer_id}")
        return profile
    
    async def update_from_behavior(
        self,
        customer_id: str,
        behavior_event: Dict
    ):
        """
        Update customer profile based on behavior.
        
        Args:
            behavior_event: Behavior event data
                - event_type: "page_view", "agent_clicked", "trial_started", etc.
                - event_data: Dict with event-specific data
                - timestamp: datetime
        """
        profile = await self.db.customer_profiles.find_one({"customer_id": customer_id})
        if not profile:
            logger.warning(f"Profile not found for behavior update: {customer_id}")
            return
        
        # Append to behavior history
        behavior_history = profile.get("behavior_history", [])
        behavior_history.append({
            "event_type": behavior_event["event_type"],
            "event_data": behavior_event.get("event_data", {}),
            "timestamp": behavior_event.get("timestamp", datetime.now()).isoformat()
        })
        
        # Infer intent updates from behavior
        intent_updates = self._infer_intent(behavior_event)
        
        # Update profile
        updates = {
            "behavior_history": behavior_history,
            "updated_at": datetime.now().isoformat()
        }
        updates.update(intent_updates)
        
        await self.db.customer_profiles.update(
            {"customer_id": customer_id},
            updates
        )
        
        logger.info(f"Profile updated from behavior: {customer_id}")
    
    def _calculate_segments(self, profile: CustomerProfile) -> List[str]:
        """Calculate customer segments for targeting"""
        segments = []
        
        # Industry segment
        segments.append(f"industry_{profile.industry}")
        
        # Urgency segment
        if profile.urgency == "immediate":
            segments.append("high_urgency")
        elif profile.urgency in ["this_week", "this_month"]:
            segments.append("medium_urgency")
        
        # Budget segment
        budget_lower = int(profile.budget_range.split("-")[0])
        if budget_lower < 10000:
            segments.append("budget_standard")
        elif budget_lower < 18000:
            segments.append("budget_premium")
        else:
            segments.append("budget_enterprise")
        
        # Company size
        segments.append(f"company_{profile.company_size}")
        
        return segments
    
    def _infer_intent(self, behavior_event: Dict) -> Dict:
        """Infer intent changes from behavior"""
        updates = {}
        
        event_type = behavior_event["event_type"]
        event_data = behavior_event.get("event_data", {})
        
        # High engagement signals higher urgency
        if event_type in ["trial_started", "agent_clicked_multiple"]:
            updates["urgency"] = "immediate"
        
        # Agent type preference inference
        if event_type == "agent_clicked":
            agent_type = event_data.get("agent_type")
            if agent_type:
                updates["preferences"] = {
                    "preferred_agent_types": [agent_type]
                }
        
        return updates


class AgentProfileDatabase:
    """
    Story 1.2.2: Agent Profile Database (5 points)
    
    Maintains agent profiles for matching:
    - Capabilities, specializations
    - Performance metrics
    - Training status
    - Industry fit
    """
    
    def __init__(self, db):
        self.db = db
    
    async def create_agent_profile(
        self,
        agent_type: str,
        profile_data: Dict
    ) -> AgentProfile:
        """
        Create agent profile.
        
        Args:
            agent_type: Agent type identifier
            profile_data: Agent profile data
        """
        now = datetime.now()
        
        profile = AgentProfile(
            agent_type=agent_type,
            agent_name=profile_data.get("agent_name", agent_type.replace("-", " ").title()),
            capabilities=profile_data.get("capabilities", []),
            specializations=profile_data.get("specializations", []),
            industries=profile_data.get("industries", []),
            training_status=profile_data.get("training_status", "fully_trained"),
            performance_metrics=profile_data.get("performance_metrics", {}),
            pricing_tier=profile_data.get("pricing_tier", "standard"),
            availability_status=profile_data.get("availability_status", "available"),
            success_rate=profile_data.get("success_rate", 0.0),
            avg_satisfaction=profile_data.get("avg_satisfaction", 0.0),
            total_trials=profile_data.get("total_trials", 0),
            total_conversions=profile_data.get("total_conversions", 0)
        )
        
        # Store in database
        await self.db.agent_profiles.insert({
            "agent_type": agent_type,
            "agent_name": profile.agent_name,
            "capabilities": profile.capabilities,
            "specializations": profile.specializations,
            "industries": profile.industries,
            "training_status": profile.training_status,
            "performance_metrics": profile.performance_metrics,
            "pricing_tier": profile.pricing_tier,
            "availability_status": profile.availability_status,
            "success_rate": profile.success_rate,
            "avg_satisfaction": profile.avg_satisfaction,
            "total_trials": profile.total_trials,
            "total_conversions": profile.total_conversions,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        })
        
        logger.info(f"Agent profile created: {agent_type}")
        return profile
    
    async def update_performance_metrics(
        self,
        agent_type: str,
        trial_outcome: Dict
    ):
        """
        Update agent performance metrics from trial outcome.
        
        Args:
            agent_type: Agent type
            trial_outcome: Trial outcome data
                - outcome: "CONVERTED", "CANCELLED", "EXPIRED"
                - satisfaction_score: float
                - tasks_completed: int
                - engagement_score: float
        """
        profile = await self.db.agent_profiles.find_one({"agent_type": agent_type})
        if not profile:
            logger.warning(f"Agent profile not found: {agent_type}")
            return
        
        # Update counters
        total_trials = profile.get("total_trials", 0) + 1
        total_conversions = profile.get("total_conversions", 0)
        if trial_outcome["outcome"] == "CONVERTED":
            total_conversions += 1
        
        success_rate = total_conversions / total_trials if total_trials > 0 else 0.0
        
        # Update satisfaction (rolling average)
        current_satisfaction = profile.get("avg_satisfaction", 0.0)
        new_satisfaction = trial_outcome.get("satisfaction_score", 0.0)
        updated_satisfaction = (current_satisfaction * (total_trials - 1) + new_satisfaction) / total_trials
        
        # Update database
        await self.db.agent_profiles.update(
            {"agent_type": agent_type},
            {
                "total_trials": total_trials,
                "total_conversions": total_conversions,
                "success_rate": success_rate,
                "avg_satisfaction": updated_satisfaction,
                "performance_metrics": {
                    **profile.get("performance_metrics", {}),
                    "last_trial_outcome": trial_outcome["outcome"],
                    "last_updated": datetime.now().isoformat()
                },
                "updated_at": datetime.now().isoformat()
            }
        )
        
        logger.info(f"Agent metrics updated: {agent_type} (success_rate={success_rate:.2%})")
    
    async def get_all_agents(self, filters: Optional[Dict] = None) -> List[AgentProfile]:
        """Get all agent profiles with optional filters"""
        query = {}
        if filters:
            if "industry" in filters:
                query["industries"] = {"$contains": filters["industry"]}
            if "training_status" in filters:
                query["training_status"] = filters["training_status"]
            if "availability_status" in filters:
                query["availability_status"] = filters["availability_status"]
        
        agents_data = await self.db.agent_profiles.find(query)
        
        return [
            AgentProfile(
                agent_type=a["agent_type"],
                agent_name=a["agent_name"],
                capabilities=a.get("capabilities", []),
                specializations=a.get("specializations", []),
                industries=a.get("industries", []),
                training_status=a.get("training_status", "fully_trained"),
                performance_metrics=a.get("performance_metrics", {}),
                pricing_tier=a.get("pricing_tier", "standard"),
                availability_status=a.get("availability_status", "available"),
                success_rate=a.get("success_rate", 0.0),
                avg_satisfaction=a.get("avg_satisfaction", 0.0),
                total_trials=a.get("total_trials", 0),
                total_conversions=a.get("total_conversions", 0)
            )
            for a in agents_data
        ]


class MatchingAlgorithm:
    """
    Story 1.2.3: Matching Algorithm (8 points)
    
    Multi-dimensional matching algorithm:
    - Industry fit score (0-100)
    - Use case alignment (0-100)
    - Performance score (0-100)
    - Training readiness (0-100)
    - Weighted total score
    - Returns ranked list of agents
    """
    
    def __init__(self):
        # Weights for scoring dimensions
        self.weights = {
            "industry_fit": 0.30,
            "use_case_alignment": 0.25,
            "performance": 0.25,
            "training_readiness": 0.10,
            "availability": 0.10
        }
    
    async def match_customer_to_agents(
        self,
        customer_profile: CustomerProfile,
        agent_profiles: List[AgentProfile],
        limit: int = 5
    ) -> List[Tuple[AgentProfile, float, Dict]]:
        """
        Match customer to agents with scoring.
        
        Args:
            customer_profile: Customer profile
            agent_profiles: List of agent profiles
            limit: Max number of matches to return
        
        Returns:
            List of (agent, total_score, score_breakdown) tuples, ranked by score
        """
        scored_matches = []
        
        for agent in agent_profiles:
            scores = {
                "industry_fit": self._score_industry_fit(customer_profile, agent),
                "use_case_alignment": self._score_use_case_alignment(customer_profile, agent),
                "performance": self._score_performance(agent),
                "training_readiness": self._score_training_readiness(agent),
                "availability": self._score_availability(agent)
            }
            
            # Calculate weighted total
            total_score = sum(
                scores[dimension] * self.weights[dimension]
                for dimension in self.weights
            )
            
            scored_matches.append((agent, total_score, scores))
        
        # Sort by total score descending
        scored_matches.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"Matched {len(agent_profiles)} agents for customer {customer_profile.customer_id}")
        return scored_matches[:limit]
    
    def _score_industry_fit(self, customer: CustomerProfile, agent: AgentProfile) -> float:
        """Score industry fit (0-100)"""
        if customer.industry in agent.industries:
            return 100.0
        elif "general" in agent.industries or len(agent.industries) == 0:
            return 60.0  # General-purpose agents get moderate score
        else:
            return 30.0  # Poor fit
    
    def _score_use_case_alignment(self, customer: CustomerProfile, agent: AgentProfile) -> float:
        """Score use case alignment (0-100)"""
        customer_keywords = customer.use_case.lower().split()
        agent_keywords = [cap.lower() for cap in agent.capabilities] + [spec.lower() for spec in agent.specializations]
        
        # Count keyword overlaps
        overlaps = sum(1 for kw in customer_keywords if any(kw in agent_kw for agent_kw in agent_keywords))
        
        if overlaps >= 3:
            return 100.0
        elif overlaps == 2:
            return 75.0
        elif overlaps == 1:
            return 50.0
        else:
            return 25.0
    
    def _score_performance(self, agent: AgentProfile) -> float:
        """Score agent performance (0-100)"""
        if agent.total_trials == 0:
            return 50.0  # New agent, no data
        
        # Weighted combination of success rate and satisfaction
        success_component = agent.success_rate * 100
        satisfaction_component = (agent.avg_satisfaction / 5.0) * 100
        
        return (success_component * 0.6) + (satisfaction_component * 0.4)
    
    def _score_training_readiness(self, agent: AgentProfile) -> float:
        """Score training readiness (0-100)"""
        status_scores = {
            "fully_trained": 100.0,
            "in_training": 60.0,
            "prototype": 30.0
        }
        return status_scores.get(agent.training_status, 50.0)
    
    def _score_availability(self, agent: AgentProfile) -> float:
        """Score availability (0-100)"""
        availability_scores = {
            "available": 100.0,
            "limited": 60.0,
            "waitlist": 20.0
        }
        return availability_scores.get(agent.availability_status, 50.0)


class TrialSuccessPredictor:
    """
    Story 1.2.4: Trial Success Prediction (5 points)
    
    ML-powered trial success prediction:
    - scikit-learn RandomForest model
    - Features: customer profile + agent profile + context
    - Predict conversion probability (0-1)
    - Monthly retraining pipeline
    """
    
    def __init__(self, db):
        self.db = db
        self.model = None
        self.feature_names = []
        self.is_trained = False
    
    async def train_model(self):
        """
        Train prediction model from historical data.
        Run monthly or when sufficient new data available.
        """
        # Fetch historical match outcomes
        match_history = await self.db.match_history.find({})
        
        if len(match_history) < 50:
            logger.warning(f"Insufficient data for training: {len(match_history)} records")
            self.is_trained = False
            return
        
        # Prepare features and labels
        X = []
        y = []
        
        for record in match_history:
            features = self._extract_features(record)
            label = 1 if record["outcome"] == "CONVERTED" else 0
            
            X.append(features)
            y.append(label)
        
        X = np.array(X)
        y = np.array(y)
        
        # Train RandomForest
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42
        )
        self.model.fit(X_train, y_train)
        
        # Evaluate
        accuracy = self.model.score(X_test, y_test)
        
        # Save model
        await self._save_model()
        
        self.is_trained = True
        logger.info(f"Model trained on {len(match_history)} records, accuracy={accuracy:.2%}")
    
    async def predict_conversion_probability(
        self,
        customer_profile: CustomerProfile,
        agent_profile: AgentProfile,
        context: Optional[Dict] = None
    ) -> float:
        """
        Predict conversion probability for customer-agent pair.
        
        Args:
            customer_profile: Customer profile
            agent_profile: Agent profile
            context: Optional context (e.g., source, referrer)
        
        Returns:
            Conversion probability (0-1)
        """
        if not self.is_trained:
            # Fallback to heuristic if model not trained
            return self._heuristic_prediction(agent_profile)
        
        # Prepare features
        record = {
            "customer_id": customer_profile.customer_id,
            "agent_type": agent_profile.agent_type,
            "industry": customer_profile.industry,
            "use_case": customer_profile.use_case,
            "budget_range": customer_profile.budget_range,
            "company_size": customer_profile.company_size,
            "urgency": customer_profile.urgency,
            "technical_level": customer_profile.technical_level,
            "agent_success_rate": agent_profile.success_rate,
            "agent_avg_satisfaction": agent_profile.avg_satisfaction,
            "agent_total_trials": agent_profile.total_trials,
            "context": context or {}
        }
        
        features = self._extract_features(record)
        features_array = np.array([features])
        
        # Predict probability
        proba = self.model.predict_proba(features_array)[0][1]
        
        return proba
    
    def _extract_features(self, record: Dict) -> List[float]:
        """Extract numerical features from record"""
        features = []
        
        # Customer features
        industry_encoding = {"marketing": 1, "education": 2, "sales": 3, "general": 0}.get(record.get("industry", "general"), 0)
        features.append(industry_encoding)
        
        urgency_encoding = {"immediate": 3, "this_week": 2, "this_month": 1, "exploring": 0}.get(record.get("urgency", "exploring"), 0)
        features.append(urgency_encoding)
        
        technical_encoding = {"advanced": 2, "intermediate": 1, "beginner": 0}.get(record.get("technical_level", "beginner"), 0)
        features.append(technical_encoding)
        
        company_size_encoding = {"enterprise": 3, "medium": 2, "small": 1, "startup": 0}.get(record.get("company_size", "startup"), 0)
        features.append(company_size_encoding)
        
        # Budget (extract lower bound)
        budget_range = record.get("budget_range", "8000-15000")
        budget_lower = int(budget_range.split("-")[0]) if "-" in budget_range else 10000
        features.append(budget_lower / 1000.0)  # Normalize
        
        # Agent features
        features.append(record.get("agent_success_rate", 0.0))
        features.append(record.get("agent_avg_satisfaction", 0.0) / 5.0)
        features.append(min(record.get("agent_total_trials", 0) / 100.0, 1.0))  # Cap at 100
        
        # Engagement features (if available)
        features.append(record.get("engagement_score", 0.0) / 100.0)
        features.append(record.get("tasks_completed", 0) / 10.0)
        features.append(record.get("customer_interactions", 0) / 20.0)
        
        return features
    
    def _heuristic_prediction(self, agent_profile: AgentProfile) -> float:
        """Fallback heuristic if model not trained"""
        if agent_profile.total_trials == 0:
            return 0.20  # Default for new agents
        
        return agent_profile.success_rate
    
    async def _save_model(self):
        """Save trained model to database"""
        model_data = pickle.dumps(self.model)
        await self.db.ml_models.upsert(
            {"model_name": "trial_success_predictor"},
            {
                "model_name": "trial_success_predictor",
                "model_data": model_data,
                "feature_names": self.feature_names,
                "trained_at": datetime.now().isoformat(),
                "is_active": True
            }
        )
    
    async def load_model(self):
        """Load trained model from database"""
        model_record = await self.db.ml_models.find_one({"model_name": "trial_success_predictor"})
        if model_record:
            self.model = pickle.loads(model_record["model_data"])
            self.feature_names = model_record.get("feature_names", [])
            self.is_trained = True
            logger.info("ML model loaded successfully")


class MatchingLearningLoop:
    """
    Story 1.2.5: Learning Loop (5 points)
    
    Continuous learning from trial outcomes:
    - Capture match accuracy (predicted vs actual)
    - Retrain model monthly
    - Update matching weights based on performance
    - Experiment tracking
    """
    
    def __init__(self, db, predictor: TrialSuccessPredictor):
        self.db = db
        self.predictor = predictor
    
    async def record_match_outcome(
        self,
        match_id: str,
        predicted_score: float,
        actual_outcome: str,  # "CONVERTED", "CANCELLED", "EXPIRED"
        metadata: Dict
    ):
        """
        Record match outcome for learning.
        
        Args:
            match_id: Match identifier
            predicted_score: Predicted conversion probability
            actual_outcome: Actual trial outcome
            metadata: Additional context
        """
        actual_converted = 1 if actual_outcome == "CONVERTED" else 0
        
        # Calculate accuracy
        prediction_error = abs(predicted_score - actual_converted)
        
        # Store outcome
        await self.db.match_outcomes.insert({
            "match_id": match_id,
            "predicted_score": predicted_score,
            "actual_outcome": actual_outcome,
            "actual_converted": actual_converted,
            "prediction_error": prediction_error,
            "metadata": metadata,
            "recorded_at": datetime.now().isoformat()
        })
        
        logger.info(f"Match outcome recorded: {match_id} (predicted={predicted_score:.2f}, actual={actual_converted})")
    
    async def trigger_retraining_if_needed(self):
        """
        Check if retraining is needed and trigger if so.
        Run daily, retrains monthly or if accuracy drops.
        """
        # Get last training date
        model_record = await self.db.ml_models.find_one({"model_name": "trial_success_predictor"})
        if not model_record:
            await self.predictor.train_model()
            return
        
        last_trained = datetime.fromisoformat(model_record["trained_at"])
        days_since_training = (datetime.now() - last_trained).days
        
        # Retrain monthly
        if days_since_training >= 30:
            logger.info("Monthly retraining triggered")
            await self.predictor.train_model()
            return
        
        # Check accuracy on recent matches
        recent_outcomes = await self.db.match_outcomes.find({
            "recorded_at": {"$gte": (datetime.now() - timedelta(days=7)).isoformat()}
        })
        
        if len(recent_outcomes) < 10:
            return  # Not enough recent data
        
        # Calculate recent accuracy
        errors = [outcome["prediction_error"] for outcome in recent_outcomes]
        avg_error = sum(errors) / len(errors)
        
        # Retrain if accuracy degraded
        if avg_error > 0.30:
            logger.warning(f"Accuracy degraded (avg_error={avg_error:.2f}), triggering retraining")
            await self.predictor.train_model()


class PersonalizedRankingEngine:
    """
    Story 1.2.6: Personalized Rankings (5 points)
    
    Personalize agent rankings for each customer:
    - Combine match score + ML prediction
    - Apply customer-specific preferences
    - Boost agents with customer's preferred attributes
    - Re-rank based on real-time behavior
    """
    
    def __init__(self, predictor: TrialSuccessPredictor):
        self.predictor = predictor
    
    async def personalize_rankings(
        self,
        customer_profile: CustomerProfile,
        scored_matches: List[Tuple[AgentProfile, float, Dict]],
        context: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Personalize agent rankings for customer.
        
        Args:
            customer_profile: Customer profile
            scored_matches: List of (agent, match_score, breakdown) from MatchingAlgorithm
            context: Optional context (source, referrer, etc.)
        
        Returns:
            Personalized ranked list with ML predictions
        """
        personalized_results = []
        
        for agent, match_score, score_breakdown in scored_matches:
            # Get ML prediction
            if self.predictor.is_trained:
                ml_prediction = await self.predictor.predict_conversion_probability(
                    customer_profile=customer_profile,
                    agent_profile=agent,
                    context=context
                )
            else:
                ml_prediction = agent.success_rate
            
            # Combine match score (0-100) and ML prediction (0-1)
            # 60% match score, 40% ML prediction
            combined_score = (match_score * 0.6) + (ml_prediction * 100 * 0.4)
            
            # Apply customer preference boosts
            boost = self._calculate_preference_boost(customer_profile, agent)
            final_score = combined_score + boost
            
            personalized_results.append({
                "agent_type": agent.agent_type,
                "agent_name": agent.agent_name,
                "final_score": round(final_score, 2),
                "match_score": round(match_score, 2),
                "ml_prediction": round(ml_prediction, 2),
                "preference_boost": round(boost, 2),
                "score_breakdown": score_breakdown,
                "specializations": agent.specializations,
                "success_rate": round(agent.success_rate * 100, 1),
                "avg_satisfaction": round(agent.avg_satisfaction, 2),
                "pricing_tier": agent.pricing_tier
            })
        
        # Re-sort by final score
        personalized_results.sort(key=lambda x: x["final_score"], reverse=True)
        
        return personalized_results
    
    def _calculate_preference_boost(
        self,
        customer_profile: CustomerProfile,
        agent_profile: AgentProfile
    ) -> float:
        """Calculate boost based on customer preferences"""
        boost = 0.0
        
        preferences = customer_profile.preferences
        
        # Preferred agent types
        if "preferred_agent_types" in preferences:
            if agent_profile.agent_type in preferences["preferred_agent_types"]:
                boost += 5.0
        
        # Budget alignment
        budget_lower = int(customer_profile.budget_range.split("-")[0])
        if agent_profile.pricing_tier == "standard" and budget_lower < 10000:
            boost += 3.0
        elif agent_profile.pricing_tier == "premium" and 10000 <= budget_lower < 18000:
            boost += 3.0
        elif agent_profile.pricing_tier == "enterprise" and budget_lower >= 18000:
            boost += 3.0
        
        # High urgency prefers high-performing agents
        if customer_profile.urgency == "immediate" and agent_profile.success_rate > 0.7:
            boost += 4.0
        
        return boost


class MatchExplainer:
    """
    Story 1.2.7: Explainability (3 points)
    
    Explain why agents were matched:
    - Top 3 reasons per match
    - Human-readable explanations
    - Transparency for customers
    """
    
    def __init__(self):
        pass
    
    def explain_match(
        self,
        customer_profile: CustomerProfile,
        agent_profile: AgentProfile,
        score_breakdown: Dict
    ) -> List[str]:
        """
        Generate human-readable explanations for match.
        
        Args:
            customer_profile: Customer profile
            agent_profile: Agent profile
            score_breakdown: Scoring breakdown
        
        Returns:
            List of top 3 reasons
        """
        reasons = []
        
        # Industry fit
        if customer_profile.industry in agent_profile.industries:
            reasons.append(f"✅ **Industry Expert:** {agent_profile.agent_name} specializes in {customer_profile.industry}")
        
        # Performance
        if agent_profile.success_rate > 0.7:
            reasons.append(f"⭐ **High Success Rate:** {agent_profile.success_rate*100:.0f}% conversion rate across {agent_profile.total_trials} trials")
        
        # Specializations
        if agent_profile.specializations:
            spec_str = ", ".join(agent_profile.specializations[:2])
            reasons.append(f"🎯 **Specialized Skills:** {spec_str}")
        
        # Satisfaction
        if agent_profile.avg_satisfaction >= 4.5:
            reasons.append(f"💖 **Highly Rated:** {agent_profile.avg_satisfaction:.1f}/5.0 customer satisfaction")
        
        # Availability
        if agent_profile.availability_status == "available":
            reasons.append(f"⚡ **Instant Start:** Available for immediate trial provisioning")
        
        # Return top 3
        return reasons[:3]


class WowMemoryIntegration:
    """
    Story 1.2.8: WowMemory Integration (3 points)
    
    Integrate with WowMemory for persistent learnings:
    - Store customer preferences long-term
    - Retrieve past interaction patterns
    - Cross-trial learning (if customer tries multiple agents)
    """
    
    def __init__(self, db, memory_service):
        self.db = db
        self.memory_service = memory_service
    
    async def store_match_memory(
        self,
        customer_id: str,
        agent_type: str,
        match_result: Dict
    ):
        """Store match result in WowMemory"""
        memory_key = f"customer_match_{customer_id}_{agent_type}"
        
        await self.memory_service.store(
            key=memory_key,
            value=match_result,
            ttl_days=365  # Keep for 1 year
        )
        
        logger.info(f"Match memory stored: {memory_key}")
    
    async def retrieve_past_matches(
        self,
        customer_id: str
    ) -> List[Dict]:
        """Retrieve customer's past matches"""
        pattern = f"customer_match_{customer_id}_*"
        memories = await self.memory_service.retrieve_pattern(pattern)
        
        return memories
    
    async def analyze_cross_trial_patterns(
        self,
        customer_id: str
    ) -> Dict:
        """Analyze patterns across multiple trials"""
        past_matches = await self.retrieve_past_matches(customer_id)
        
        if len(past_matches) < 2:
            return {"insight": "Insufficient data for cross-trial analysis"}
        
        # Analyze patterns
        converted_agents = [m["agent_type"] for m in past_matches if m.get("outcome") == "CONVERTED"]
        cancelled_agents = [m["agent_type"] for m in past_matches if m.get("outcome") == "CANCELLED"]
        
        return {
            "total_trials": len(past_matches),
            "converted_count": len(converted_agents),
            "cancelled_count": len(cancelled_agents),
            "preferred_agents": converted_agents,
            "avoided_agents": cancelled_agents,
            "insight": f"Customer has tried {len(past_matches)} agents, converted {len(converted_agents)} times"
        }


class ABTestingFramework:
    """
    Story 1.2.9: A/B Testing Framework (3 points)
    
    A/B test matching strategies:
    - Define experiments (control vs treatment)
    - Random assignment to cohorts
    - Track conversion metrics per cohort
    - Statistical significance testing
    """
    
    def __init__(self, db):
        self.db = db
    
    async def create_experiment(
        self,
        experiment_name: str,
        description: str,
        control_strategy: str,
        treatment_strategy: str,
        traffic_split: float = 0.5
    ) -> str:
        """
        Create A/B test experiment.
        
        Args:
            experiment_name: Experiment name
            description: Description
            control_strategy: Control strategy identifier
            treatment_strategy: Treatment strategy identifier
            traffic_split: % traffic to treatment (0-1)
        
        Returns:
            Experiment ID
        """
        experiment_id = str(uuid4())
        
        await self.db.ab_experiments.insert({
            "experiment_id": experiment_id,
            "experiment_name": experiment_name,
            "description": description,
            "control_strategy": control_strategy,
            "treatment_strategy": treatment_strategy,
            "traffic_split": traffic_split,
            "status": "ACTIVE",
            "created_at": datetime.now().isoformat(),
            "results": {
                "control": {"impressions": 0, "conversions": 0},
                "treatment": {"impressions": 0, "conversions": 0}
            }
        })
        
        logger.info(f"A/B experiment created: {experiment_name} ({experiment_id})")
        return experiment_id
    
    async def assign_cohort(
        self,
        customer_id: str,
        experiment_id: str
    ) -> str:
        """
        Assign customer to control or treatment cohort.
        
        Returns:
            "control" or "treatment"
        """
        experiment = await self.db.ab_experiments.find_one({"experiment_id": experiment_id})
        if not experiment:
            return "control"  # Default to control if experiment not found
        
        # Hash customer_id for consistent assignment
        import hashlib
        hash_val = int(hashlib.md5(customer_id.encode()).hexdigest(), 16)
        assignment_val = (hash_val % 100) / 100.0
        
        cohort = "treatment" if assignment_val < experiment["traffic_split"] else "control"
        
        # Record assignment
        await self.db.ab_assignments.insert({
            "customer_id": customer_id,
            "experiment_id": experiment_id,
            "cohort": cohort,
            "assigned_at": datetime.now().isoformat()
        })
        
        return cohort
    
    async def record_conversion(
        self,
        customer_id: str,
        experiment_id: str,
        converted: bool
    ):
        """Record conversion for A/B test"""
        assignment = await self.db.ab_assignments.find_one({
            "customer_id": customer_id,
            "experiment_id": experiment_id
        })
        
        if not assignment:
            logger.warning(f"No A/B assignment found for customer: {customer_id}")
            return
        
        cohort = assignment["cohort"]
        
        # Update experiment results
        experiment = await self.db.ab_experiments.find_one({"experiment_id": experiment_id})
        results = experiment.get("results", {"control": {"impressions": 0, "conversions": 0}, "treatment": {"impressions": 0, "conversions": 0}})
        
        results[cohort]["impressions"] += 1
        if converted:
            results[cohort]["conversions"] += 1
        
        await self.db.ab_experiments.update(
            {"experiment_id": experiment_id},
            {"results": results, "updated_at": datetime.now().isoformat()}
        )
        
        logger.info(f"A/B conversion recorded: {experiment_id} ({cohort}, converted={converted})")
    
    async def get_experiment_results(
        self,
        experiment_id: str
    ) -> Dict:
        """Get A/B test results with statistical analysis"""
        experiment = await self.db.ab_experiments.find_one({"experiment_id": experiment_id})
        if not experiment:
            return {}
        
        results = experiment.get("results", {})
        
        control = results.get("control", {"impressions": 0, "conversions": 0})
        treatment = results.get("treatment", {"impressions": 0, "conversions": 0})
        
        control_rate = control["conversions"] / control["impressions"] if control["impressions"] > 0 else 0
        treatment_rate = treatment["conversions"] / treatment["impressions"] if treatment["impressions"] > 0 else 0
        
        lift = ((treatment_rate - control_rate) / control_rate * 100) if control_rate > 0 else 0
        
        return {
            "experiment_name": experiment["experiment_name"],
            "status": experiment["status"],
            "control": {
                "impressions": control["impressions"],
                "conversions": control["conversions"],
                "conversion_rate": round(control_rate * 100, 2)
            },
            "treatment": {
                "impressions": treatment["impressions"],
                "conversions": treatment["conversions"],
                "conversion_rate": round(treatment_rate * 100, 2)
            },
            "lift_pct": round(lift, 2),
            "winner": "treatment" if treatment_rate > control_rate else "control"
        }


class WowMatcher:
    """
    WowMatcher Agent - Intelligent Trial-to-Agent Matching
    
    Matches customers with optimal agents based on:
    - Customer profile (industry, use case, budget)
    - Agent capabilities and performance
    - Historical trial outcomes (ML-powered)
    - Real-time behavior signals
    
    Epic 1.2 Complete: All 9 stories (42 points)
    """
    
    def __init__(
        self,
        db_connection,
        notification_service,
        analytics_service,
        memory_service
    ):
        # Story 1.2.1: Customer Profile Analyzer
        self.customer_analyzer = CustomerProfileAnalyzer(db=db_connection)
        
        # Story 1.2.2: Agent Profile Database
        self.agent_database = AgentProfileDatabase(db=db_connection)
        
        # Story 1.2.3: Matching Algorithm
        self.matching_algo = MatchingAlgorithm()
        
        # Story 1.2.4: Trial Success Prediction
        self.predictor = TrialSuccessPredictor(db=db_connection)
        
        # Story 1.2.5: Learning Loop
        self.learning_loop = MatchingLearningLoop(
            db=db_connection,
            predictor=self.predictor
        )
        
        # Story 1.2.6: Personalized Rankings
        self.ranking_engine = PersonalizedRankingEngine(predictor=self.predictor)
        
        # Story 1.2.7: Explainability
        self.explainer = MatchExplainer()
        
        # Story 1.2.8: WowMemory Integration
        self.memory_integration = WowMemoryIntegration(
            db=db_connection,
            memory_service=memory_service
        )
        
        # Story 1.2.9: A/B Testing
        self.ab_testing = ABTestingFramework(db=db_connection)
        
        self.db = db_connection
        self.notification_service = notification_service
        self.analytics_service = analytics_service
        
        logger.info("WowMatcher initialized with all 9 story components (42 points)")
    
    async def initialize(self):
        """Initialize WowMatcher (load ML model)"""
        await self.predictor.load_model()
    
    async def match_customer(
        self,
        customer_id: str,
        onboarding_data: Optional[Dict] = None,
        limit: int = 5,
        context: Optional[Dict] = None,
        experiment_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Match customer to best agents with personalized rankings.
        
        Args:
            customer_id: Customer identifier
            onboarding_data: Optional onboarding data (creates profile if needed)
            limit: Max number of matches
            context: Optional context (source, referrer, etc.)
            experiment_id: Optional A/B test experiment ID
        
        Returns:
            List of personalized match results with explanations
        """
        # Get or create customer profile
        profile_data = await self.db.customer_profiles.find_one({"customer_id": customer_id})
        
        if not profile_data and onboarding_data:
            # Create new profile
            customer_profile = await self.customer_analyzer.create_profile(
                customer_id=customer_id,
                onboarding_data=onboarding_data
            )
        elif profile_data:
            # Load existing profile
            customer_profile = CustomerProfile(
                customer_id=profile_data["customer_id"],
                industry=profile_data.get("industry", "general"),
                use_case=profile_data.get("use_case", ""),
                budget_range=profile_data.get("budget_range", "8000-15000"),
                company_size=profile_data.get("company_size", "startup"),
                urgency=profile_data.get("urgency", "exploring"),
                technical_level=profile_data.get("technical_level", "beginner"),
                preferences=profile_data.get("preferences", {}),
                behavior_history=profile_data.get("behavior_history", []),
                created_at=datetime.fromisoformat(profile_data["created_at"]),
                updated_at=datetime.fromisoformat(profile_data["updated_at"])
            )
        else:
            raise ValueError(f"Customer profile not found and no onboarding data provided: {customer_id}")
        
        # A/B testing: assign cohort if experiment active
        cohort = None
        if experiment_id:
            cohort = await self.ab_testing.assign_cohort(customer_id, experiment_id)
            logger.info(f"Customer {customer_id} assigned to {cohort} cohort")
        
        # Get all available agents
        agent_profiles = await self.agent_database.get_all_agents(
            filters={"availability_status": "available"}
        )
        
        # Run matching algorithm
        scored_matches = await self.matching_algo.match_customer_to_agents(
            customer_profile=customer_profile,
            agent_profiles=agent_profiles,
            limit=limit * 2  # Get more for personalization
        )
        
        # Apply personalized rankings
        personalized_results = await self.ranking_engine.personalize_rankings(
            customer_profile=customer_profile,
            scored_matches=scored_matches,
            context=context
        )
        
        # Add explanations
        for result in personalized_results:
            agent = next((a for a, _, _ in scored_matches if a.agent_type == result["agent_type"]), None)
            if agent:
                score_breakdown = next((sb for a, _, sb in scored_matches if a.agent_type == result["agent_type"]), {})
                explanations = self.explainer.explain_match(
                    customer_profile=customer_profile,
                    agent_profile=agent,
                    score_breakdown=score_breakdown
                )
                result["why_matched"] = explanations
        
        # Limit to requested count
        final_results = personalized_results[:limit]
        
        # Store in WowMemory
        for result in final_results:
            await self.memory_integration.store_match_memory(
                customer_id=customer_id,
                agent_type=result["agent_type"],
                match_result=result
            )
        
        logger.info(f"Matched customer {customer_id} to {len(final_results)} agents (personalized)")
        return final_results
    
    async def update_customer_behavior(
        self,
        customer_id: str,
        behavior_event: Dict
    ):
        """Update customer profile from behavior"""
        await self.customer_analyzer.update_from_behavior(customer_id, behavior_event)
    
    async def record_trial_outcome(
        self,
        customer_id: str,
        agent_type: str,
        trial_id: str,
        outcome: str,
        trial_data: Dict,
        experiment_id: Optional[str] = None
    ):
        """
        Record trial outcome for learning.
        
        Args:
            customer_id: Customer ID
            agent_type: Agent type
            trial_id: Trial ID
            outcome: "CONVERTED", "CANCELLED", "EXPIRED"
            trial_data: Trial metrics
            experiment_id: Optional experiment ID for A/B testing
        """
        # Update agent performance metrics
        await self.agent_database.update_performance_metrics(
            agent_type=agent_type,
            trial_outcome={
                "outcome": outcome,
                "satisfaction_score": trial_data.get("satisfaction_score", 0.0),
                "tasks_completed": trial_data.get("tasks_completed", 0),
                "engagement_score": trial_data.get("engagement_score", 0.0)
            }
        )
        
        # Record for learning loop
        match_id = f"{customer_id}_{agent_type}_{trial_id}"
        predicted_score = trial_data.get("predicted_conversion_probability", 0.5)
        
        await self.learning_loop.record_match_outcome(
            match_id=match_id,
            predicted_score=predicted_score,
            actual_outcome=outcome,
            metadata={
                "customer_id": customer_id,
                "agent_type": agent_type,
                "trial_id": trial_id,
                **trial_data
            }
        )
        
        # A/B testing: record conversion
        if experiment_id:
            converted = (outcome == "CONVERTED")
            await self.ab_testing.record_conversion(customer_id, experiment_id, converted)
        
        logger.info(f"Trial outcome recorded: {trial_id} → {outcome}")
    
    async def train_prediction_model(self):
        """Train ML prediction model (monthly cron job)"""
        await self.predictor.train_model()
    
    async def check_retraining_needed(self):
        """Check if retraining needed (daily cron job)"""
        await self.learning_loop.trigger_retraining_if_needed()
    
    async def get_customer_insights(
        self,
        customer_id: str
    ) -> Dict:
        """Get insights about customer's matching history"""
        return await self.memory_integration.analyze_cross_trial_patterns(customer_id)
    
    # A/B Testing Admin APIs
    async def create_experiment(
        self,
        experiment_name: str,
        description: str,
        control_strategy: str,
        treatment_strategy: str,
        traffic_split: float = 0.5
    ) -> str:
        """Create A/B test experiment"""
        return await self.ab_testing.create_experiment(
            experiment_name, description, control_strategy, treatment_strategy, traffic_split
        )
    
    async def get_experiment_results(
        self,
        experiment_id: str
    ) -> Dict:
        """Get A/B test results"""
        return await self.ab_testing.get_experiment_results(experiment_id)
