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


class WowMatcher:
    """
    WowMatcher Agent - Intelligent Trial-to-Agent Matching
    
    Matches customers with optimal agents based on:
    - Customer profile (industry, use case, budget)
    - Agent capabilities and performance
    - Historical trial outcomes (ML-powered)
    - Real-time behavior signals
    """
    
    def __init__(
        self,
        db_connection,
        notification_service,
        analytics_service
    ):
        self.customer_analyzer = CustomerProfileAnalyzer(db=db_connection)
        self.agent_database = AgentProfileDatabase(db=db_connection)
        self.matching_algo = MatchingAlgorithm()
        
        self.db = db_connection
        self.notification_service = notification_service
        self.analytics_service = analytics_service
        
        logger.info("WowMatcher initialized (Stories 1.2.1-1.2.3)")
    
    async def match_customer(
        self,
        customer_id: str,
        onboarding_data: Optional[Dict] = None,
        limit: int = 5
    ) -> List[Dict]:
        """
        Match customer to best agents.
        
        Args:
            customer_id: Customer identifier
            onboarding_data: Optional onboarding data (creates profile if needed)
            limit: Max number of matches
        
        Returns:
            List of match results with agent details and scores
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
        
        # Get all available agents
        agent_profiles = await self.agent_database.get_all_agents(
            filters={"availability_status": "available"}
        )
        
        # Run matching algorithm
        scored_matches = await self.matching_algo.match_customer_to_agents(
            customer_profile=customer_profile,
            agent_profiles=agent_profiles,
            limit=limit
        )
        
        # Format results
        results = []
        for agent, total_score, score_breakdown in scored_matches:
            results.append({
                "agent_type": agent.agent_type,
                "agent_name": agent.agent_name,
                "match_score": round(total_score, 2),
                "score_breakdown": {k: round(v, 2) for k, v in score_breakdown.items()},
                "specializations": agent.specializations,
                "success_rate": round(agent.success_rate * 100, 1),
                "avg_satisfaction": round(agent.avg_satisfaction, 2),
                "pricing_tier": agent.pricing_tier
            })
        
        logger.info(f"Matched customer {customer_id} to {len(results)} agents")
        return results
    
    async def update_customer_behavior(
        self,
        customer_id: str,
        behavior_event: Dict
    ):
        """Update customer profile from behavior"""
        await self.customer_analyzer.update_from_behavior(customer_id, behavior_event)
    
    async def record_trial_outcome(
        self,
        agent_type: str,
        trial_outcome: Dict
    ):
        """Record trial outcome for agent performance tracking"""
        await self.agent_database.update_performance_metrics(agent_type, trial_outcome)
