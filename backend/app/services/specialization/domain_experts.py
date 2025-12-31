"""
Domain Expert Agents

Specialized agents with domain-specific knowledge and reasoning.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from .knowledge_graph import (
    KnowledgeGraph,
    Entity,
    Relationship,
    EntityType,
    RelationshipType,
    GraphQueryEngine
)


class ExpertiseLevel(str, Enum):
    """Level of expertise"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class DomainExpertise:
    """Domain expertise configuration"""
    domain: str
    specializations: List[str]
    expertise_level: ExpertiseLevel
    knowledge_graph: KnowledgeGraph
    reasoning_patterns: List[str]


class BaseDomainExpert:
    """
    Base class for domain expert agents.
    
    Provides domain-specific knowledge and reasoning capabilities.
    """
    
    def __init__(
        self,
        domain: str,
        specializations: List[str],
        expertise_level: ExpertiseLevel = ExpertiseLevel.EXPERT
    ):
        """
        Initialize domain expert.
        
        Args:
            domain: Domain name
            specializations: List of specializations
            expertise_level: Level of expertise
        """
        self.domain = domain
        self.specializations = specializations
        self.expertise_level = expertise_level
        
        # Initialize knowledge graph
        self.knowledge_graph = KnowledgeGraph(domain)
        self.query_engine = GraphQueryEngine(self.knowledge_graph)
        
        # Load domain knowledge
        self._initialize_knowledge()
    
    def _initialize_knowledge(self):
        """Initialize domain-specific knowledge (override in subclasses)"""
        pass
    
    def get_expertise(self) -> DomainExpertise:
        """Get expertise configuration"""
        return DomainExpertise(
            domain=self.domain,
            specializations=self.specializations,
            expertise_level=self.expertise_level,
            knowledge_graph=self.knowledge_graph,
            reasoning_patterns=self.knowledge_graph.ontology.get_reasoning_patterns()
        )
    
    def analyze_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze task using domain knowledge.
        
        Args:
            task: Task description
            
        Returns:
            Analysis with insights and recommendations
        """
        # Extract entities from task
        entities = self._extract_entities(task)
        
        # Find relevant knowledge
        relevant_knowledge = self._find_relevant_knowledge(entities)
        
        # Apply reasoning
        insights = self._apply_reasoning(entities, relevant_knowledge)
        
        return {
            "domain": self.domain,
            "entities": entities,
            "relevant_knowledge": relevant_knowledge,
            "insights": insights,
            "recommendations": self._generate_recommendations(insights)
        }
    
    def _extract_entities(self, task: Dict[str, Any]) -> List[Entity]:
        """Extract entities from task (override in subclasses)"""
        return []
    
    def _find_relevant_knowledge(self, entities: List[Entity]) -> List[Dict[str, Any]]:
        """Find relevant knowledge for entities"""
        knowledge = []
        
        for entity in entities:
            # Get entity context from graph
            context = self.query_engine.get_entity_context(entity.id, depth=2)
            knowledge.append(context)
        
        return knowledge
    
    def _apply_reasoning(
        self,
        entities: List[Entity],
        knowledge: List[Dict[str, Any]]
    ) -> List[str]:
        """Apply domain-specific reasoning"""
        insights = []
        
        for entity in entities:
            # Apply reasoning rules
            entity_insights = self.query_engine.apply_reasoning_rules(entity.id)
            insights.extend(entity_insights)
        
        return insights
    
    def _generate_recommendations(self, insights: List[str]) -> List[str]:
        """Generate recommendations based on insights"""
        # Base implementation - override in subclasses for domain-specific logic
        return [f"Consider: {insight}" for insight in insights[:3]]


class MarketingExpert(BaseDomainExpert):
    """
    Marketing domain expert.
    
    Specializations:
    - Content marketing
    - Social media marketing
    - SEO optimization
    - Campaign management
    - Brand strategy
    """
    
    def __init__(
        self,
        specializations: Optional[List[str]] = None,
        expertise_level: ExpertiseLevel = ExpertiseLevel.EXPERT
    ):
        """Initialize marketing expert"""
        default_specializations = [
            "content_marketing",
            "social_media",
            "seo",
            "campaign_management",
            "brand_strategy"
        ]
        
        super().__init__(
            domain="marketing",
            specializations=specializations or default_specializations,
            expertise_level=expertise_level
        )
    
    def _initialize_knowledge(self):
        """Initialize marketing knowledge graph"""
        # Add marketing channels
        channels = [
            ("linkedin", "LinkedIn", {"category": "social", "format": "professional"}),
            ("twitter", "Twitter", {"category": "social", "format": "microblogging"}),
            ("blog", "Blog", {"category": "content", "format": "long-form"}),
            ("email", "Email", {"category": "direct", "format": "personal"}),
            ("seo", "SEO", {"category": "organic", "format": "search"}),
        ]
        
        for channel_id, name, props in channels:
            entity = Entity(
                id=channel_id,
                type=EntityType.CHANNEL,
                name=name,
                properties=props
            )
            self.knowledge_graph.add_entity(entity)
        
        # Add content types
        content_types = [
            ("blog_post", "Blog Post", {"length": "long", "seo_value": "high"}),
            ("social_post", "Social Media Post", {"length": "short", "engagement": "high"}),
            ("email_campaign", "Email Campaign", {"personalization": "high", "conversion": "medium"}),
            ("video", "Video Content", {"engagement": "very_high", "production": "high"}),
        ]
        
        for content_id, name, props in content_types:
            entity = Entity(
                id=content_id,
                type=EntityType.CONTENT_TYPE,
                name=name,
                properties=props
            )
            self.knowledge_graph.add_entity(entity)
        
        # Add audiences
        audiences = [
            ("b2b", "B2B Decision Makers", {"industry": "business", "size": "enterprise"}),
            ("b2c", "B2C Consumers", {"industry": "consumer", "size": "mass_market"}),
            ("smb", "Small Business Owners", {"industry": "business", "size": "small"}),
        ]
        
        for audience_id, name, props in audiences:
            entity = Entity(
                id=audience_id,
                type=EntityType.AUDIENCE,
                name=name,
                properties=props
            )
            self.knowledge_graph.add_entity(entity)
        
        # Add relationships: content types to channels
        relationships = [
            ("blog_linkedin", RelationshipType.USES_CHANNEL, "blog_post", "linkedin", 0.8),
            ("blog_seo", RelationshipType.USES_CHANNEL, "blog_post", "seo", 0.9),
            ("social_twitter", RelationshipType.USES_CHANNEL, "social_post", "twitter", 0.9),
            ("email_b2b", RelationshipType.TARGETS, "email_campaign", "b2b", 0.85),
        ]
        
        for rel_id, rel_type, source, target, strength in relationships:
            rel = Relationship(
                id=rel_id,
                type=rel_type,
                source_id=source,
                target_id=target,
                strength=strength
            )
            self.knowledge_graph.add_relationship(rel)
    
    def analyze_campaign(self, campaign: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze marketing campaign.
        
        Args:
            campaign: Campaign details (goal, audience, budget, timeline)
            
        Returns:
            Analysis with channel recommendations and strategy
        """
        goal = campaign.get("goal", "awareness")
        audience = campaign.get("audience", "b2b")
        budget = campaign.get("budget", "medium")
        
        # Find relevant channels for audience
        audience_entity = self.knowledge_graph.get_entity(audience)
        
        recommendations = {
            "campaign_type": self._recommend_campaign_type(goal),
            "channels": self._recommend_channels(audience, budget),
            "content_strategy": self._recommend_content(goal, audience),
            "metrics": self._recommend_metrics(goal),
            "timeline": self._recommend_timeline(goal, budget)
        }
        
        return recommendations
    
    def _recommend_campaign_type(self, goal: str) -> str:
        """Recommend campaign type based on goal"""
        campaign_types = {
            "awareness": "Brand awareness campaign with reach focus",
            "leads": "Lead generation campaign with conversion focus",
            "engagement": "Engagement campaign with community building",
            "sales": "Sales campaign with direct response focus"
        }
        return campaign_types.get(goal, "Multi-objective campaign")
    
    def _recommend_channels(self, audience: str, budget: str) -> List[Dict[str, Any]]:
        """Recommend marketing channels"""
        # Query knowledge graph for audience-appropriate channels
        channels = self.knowledge_graph.get_entities_by_type(EntityType.CHANNEL)
        
        recommendations = []
        for channel in channels:
            # Simple scoring based on audience and budget
            score = 0.5
            
            if audience == "b2b" and channel.properties.get("category") == "professional":
                score = 0.9
            elif audience == "b2c" and channel.properties.get("engagement") == "high":
                score = 0.8
            
            recommendations.append({
                "channel": channel.name,
                "score": score,
                "reason": f"Good fit for {audience} audience"
            })
        
        # Sort by score
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:3]
    
    def _recommend_content(self, goal: str, audience: str) -> List[str]:
        """Recommend content types"""
        if goal == "awareness":
            return ["Blog posts for SEO", "Social media content", "Video content"]
        elif goal == "leads":
            return ["Gated content (ebooks, whitepapers)", "Webinars", "Case studies"]
        elif goal == "engagement":
            return ["Interactive content", "User-generated content", "Community posts"]
        else:
            return ["Product demos", "Customer testimonials", "Limited-time offers"]
    
    def _recommend_metrics(self, goal: str) -> List[str]:
        """Recommend KPIs to track"""
        metrics_map = {
            "awareness": ["Impressions", "Reach", "Brand mentions", "Share of voice"],
            "leads": ["Lead generation", "Conversion rate", "Cost per lead", "Lead quality score"],
            "engagement": ["Engagement rate", "Comments", "Shares", "Time on site"],
            "sales": ["Sales revenue", "ROI", "Customer acquisition cost", "Conversion rate"]
        }
        return metrics_map.get(goal, ["Impressions", "Clicks", "Conversions"])
    
    def _recommend_timeline(self, goal: str, budget: str) -> str:
        """Recommend campaign timeline"""
        if goal == "awareness":
            return "3-6 months for sustained brand building"
        elif goal == "leads":
            return "2-3 months with A/B testing phases"
        elif goal == "sales":
            return "1-2 months for immediate results"
        else:
            return "3-4 months for comprehensive campaign"


class EducationExpert(BaseDomainExpert):
    """
    Education domain expert.
    
    Specializations:
    - Math tutoring
    - Science tutoring
    - Language arts
    - Test preparation
    - Study planning
    """
    
    def __init__(
        self,
        specializations: Optional[List[str]] = None,
        expertise_level: ExpertiseLevel = ExpertiseLevel.EXPERT
    ):
        """Initialize education expert"""
        default_specializations = [
            "math_tutoring",
            "science_tutoring",
            "language_arts",
            "test_preparation",
            "study_planning"
        ]
        
        super().__init__(
            domain="education",
            specializations=specializations or default_specializations,
            expertise_level=expertise_level
        )
    
    def _initialize_knowledge(self):
        """Initialize education knowledge graph"""
        # Add subjects
        subjects = [
            ("math", "Mathematics", {"category": "stem", "difficulty": "medium"}),
            ("science", "Science", {"category": "stem", "difficulty": "medium"}),
            ("english", "English", {"category": "humanities", "difficulty": "low"}),
        ]
        
        for subject_id, name, props in subjects:
            entity = Entity(
                id=subject_id,
                type=EntityType.SUBJECT,
                name=name,
                properties=props
            )
            self.knowledge_graph.add_entity(entity)
        
        # Add concepts
        concepts = [
            ("algebra", "Algebra", {"subject": "math", "difficulty": "medium"}),
            ("geometry", "Geometry", {"subject": "math", "difficulty": "medium"}),
            ("physics", "Physics", {"subject": "science", "difficulty": "high"}),
            ("chemistry", "Chemistry", {"subject": "science", "difficulty": "high"}),
        ]
        
        for concept_id, name, props in concepts:
            entity = Entity(
                id=concept_id,
                type=EntityType.CONCEPT,
                name=name,
                properties=props
            )
            self.knowledge_graph.add_entity(entity)
        
        # Add prerequisites
        prerequisites = [
            ("basic_math", "Basic Mathematics", {"level": "elementary"}),
            ("arithmetic", "Arithmetic", {"level": "elementary"}),
        ]
        
        for prereq_id, name, props in prerequisites:
            entity = Entity(
                id=prereq_id,
                type=EntityType.PREREQUISITE,
                name=name,
                properties=props
            )
            self.knowledge_graph.add_entity(entity)
        
        # Add relationships: concepts to prerequisites
        relationships = [
            ("algebra_prereq", RelationshipType.REQUIRES, "algebra", "arithmetic", 0.9),
            ("geometry_prereq", RelationshipType.REQUIRES, "geometry", "basic_math", 0.8),
            ("algebra_math", RelationshipType.PART_OF, "algebra", "math", 1.0),
            ("physics_science", RelationshipType.PART_OF, "physics", "science", 1.0),
        ]
        
        for rel_id, rel_type, source, target, strength in relationships:
            rel = Relationship(
                id=rel_id,
                type=rel_type,
                source_id=source,
                target_id=target,
                strength=strength
            )
            self.knowledge_graph.add_relationship(rel)
    
    def create_learning_plan(self, student: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create personalized learning plan.
        
        Args:
            student: Student profile (current_level, goals, challenges)
            
        Returns:
            Learning plan with topics, resources, timeline
        """
        current_level = student.get("current_level", "beginner")
        goals = student.get("goals", [])
        challenges = student.get("challenges", [])
        
        plan = {
            "topics": self._sequence_topics(current_level, goals),
            "resources": self._recommend_resources(current_level),
            "timeline": self._estimate_timeline(current_level, goals),
            "assessment_schedule": self._plan_assessments(goals),
            "support_needed": self._identify_support(challenges)
        }
        
        return plan
    
    def _sequence_topics(self, level: str, goals: List[str]) -> List[Dict[str, Any]]:
        """Sequence topics based on prerequisites"""
        # Get concepts from knowledge graph
        concepts = self.knowledge_graph.get_entities_by_type(EntityType.CONCEPT)
        
        sequenced = []
        for concept in concepts:
            # Check prerequisites
            prereqs = self.knowledge_graph.get_incoming_relationships(
                concept.id,
                RelationshipType.REQUIRES
            )
            
            sequenced.append({
                "topic": concept.name,
                "difficulty": concept.properties.get("difficulty", "medium"),
                "prerequisites": len(prereqs),
                "estimated_hours": 10  # Simplified
            })
        
        # Sort by prerequisites (simpler topics first)
        sequenced.sort(key=lambda x: x["prerequisites"])
        return sequenced
    
    def _recommend_resources(self, level: str) -> List[Dict[str, Any]]:
        """Recommend learning resources"""
        resources = [
            {"type": "video", "platform": "Khan Academy", "difficulty": level},
            {"type": "practice", "platform": "Brilliant", "difficulty": level},
            {"type": "textbook", "platform": "OpenStax", "difficulty": level},
        ]
        return resources
    
    def _estimate_timeline(self, level: str, goals: List[str]) -> str:
        """Estimate learning timeline"""
        weeks = len(goals) * 4  # 4 weeks per goal
        return f"{weeks} weeks with consistent practice"
    
    def _plan_assessments(self, goals: List[str]) -> List[str]:
        """Plan assessment schedule"""
        return [
            "Weekly quizzes for each topic",
            "Midterm assessment after 50% completion",
            "Final comprehensive assessment",
            "Regular progress tracking"
        ]
    
    def _identify_support(self, challenges: List[str]) -> List[str]:
        """Identify support needs"""
        support = []
        
        if "time_management" in challenges:
            support.append("Create structured study schedule")
        if "motivation" in challenges:
            support.append("Set up reward system and milestones")
        if "comprehension" in challenges:
            support.append("Break down complex topics into smaller chunks")
        
        return support


class SalesExpert(BaseDomainExpert):
    """
    Sales domain expert.
    
    Specializations:
    - Lead qualification
    - Outreach strategies
    - Objection handling
    - Deal closing
    - Relationship building
    """
    
    def __init__(
        self,
        specializations: Optional[List[str]] = None,
        expertise_level: ExpertiseLevel = ExpertiseLevel.EXPERT
    ):
        """Initialize sales expert"""
        default_specializations = [
            "lead_qualification",
            "outreach",
            "objection_handling",
            "deal_closing",
            "relationship_building"
        ]
        
        super().__init__(
            domain="sales",
            specializations=specializations or default_specializations,
            expertise_level=expertise_level
        )
    
    def _initialize_knowledge(self):
        """Initialize sales knowledge graph"""
        # Add pain points
        pain_points = [
            ("cost", "High Costs", {"urgency": "high", "impact": "high"}),
            ("efficiency", "Low Efficiency", {"urgency": "medium", "impact": "high"}),
            ("scalability", "Scalability Issues", {"urgency": "medium", "impact": "medium"}),
        ]
        
        for pain_id, name, props in pain_points:
            entity = Entity(
                id=pain_id,
                type=EntityType.PAIN_POINT,
                name=name,
                properties=props
            )
            self.knowledge_graph.add_entity(entity)
        
        # Add products
        products = [
            ("enterprise", "Enterprise Solution", {"price": "high", "complexity": "high"}),
            ("professional", "Professional Plan", {"price": "medium", "complexity": "medium"}),
            ("starter", "Starter Package", {"price": "low", "complexity": "low"}),
        ]
        
        for product_id, name, props in products:
            entity = Entity(
                id=product_id,
                type=EntityType.PRODUCT,
                name=name,
                properties=props
            )
            self.knowledge_graph.add_entity(entity)
    
    def qualify_lead(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """
        Qualify lead using BANT framework.
        
        Args:
            lead: Lead information (company, role, pain_points, timeline, budget)
            
        Returns:
            Qualification score and recommendations
        """
        # BANT: Budget, Authority, Need, Timeline
        budget_score = self._score_budget(lead.get("budget", "unknown"))
        authority_score = self._score_authority(lead.get("role", "unknown"))
        need_score = self._score_need(lead.get("pain_points", []))
        timeline_score = self._score_timeline(lead.get("timeline", "unknown"))
        
        total_score = (budget_score + authority_score + need_score + timeline_score) / 4
        
        qualification = {
            "score": total_score,
            "level": self._qualification_level(total_score),
            "bant_breakdown": {
                "budget": budget_score,
                "authority": authority_score,
                "need": need_score,
                "timeline": timeline_score
            },
            "recommended_actions": self._recommend_actions(total_score, lead),
            "priority": "high" if total_score > 0.7 else "medium" if total_score > 0.4 else "low"
        }
        
        return qualification
    
    def _score_budget(self, budget: str) -> float:
        """Score budget qualification"""
        scores = {"confirmed": 1.0, "estimated": 0.7, "exploring": 0.4, "unknown": 0.2}
        return scores.get(budget, 0.2)
    
    def _score_authority(self, role: str) -> float:
        """Score authority level"""
        roles = {
            "ceo": 1.0, "cto": 1.0, "vp": 0.9,
            "director": 0.7, "manager": 0.5, "individual": 0.3
        }
        return roles.get(role.lower(), 0.5)
    
    def _score_need(self, pain_points: List[str]) -> float:
        """Score need strength"""
        if len(pain_points) >= 3:
            return 1.0
        elif len(pain_points) >= 2:
            return 0.7
        elif len(pain_points) >= 1:
            return 0.5
        return 0.2
    
    def _score_timeline(self, timeline: str) -> float:
        """Score timeline urgency"""
        scores = {"immediate": 1.0, "1_month": 0.8, "3_months": 0.6, "6_months": 0.4, "exploring": 0.2}
        return scores.get(timeline, 0.3)
    
    def _qualification_level(self, score: float) -> str:
        """Determine qualification level"""
        if score >= 0.8:
            return "Hot Lead"
        elif score >= 0.6:
            return "Warm Lead"
        elif score >= 0.4:
            return "Cold Lead"
        else:
            return "Unqualified"
    
    def _recommend_actions(self, score: float, lead: Dict[str, Any]) -> List[str]:
        """Recommend next actions"""
        if score >= 0.8:
            return [
                "Schedule demo immediately",
                "Prepare custom proposal",
                "Involve executive sponsor",
                "Set up trial/POC"
            ]
        elif score >= 0.6:
            return [
                "Schedule discovery call",
                "Share case studies",
                "Identify decision makers",
                "Clarify timeline and budget"
            ]
        elif score >= 0.4:
            return [
                "Nurture with educational content",
                "Build relationship",
                "Understand pain points better",
                "Follow up monthly"
            ]
        else:
            return [
                "Add to nurture sequence",
                "Share general resources",
                "Revisit in 6 months"
            ]


class DomainExpertRegistry:
    """
    Registry of domain experts.
    
    Manages creation and selection of domain-specific experts.
    """
    
    def __init__(self):
        """Initialize expert registry"""
        self._experts: Dict[str, BaseDomainExpert] = {}
        
        # Register default experts
        self.register("marketing", MarketingExpert())
        self.register("education", EducationExpert())
        self.register("sales", SalesExpert())
    
    def register(self, domain: str, expert: BaseDomainExpert):
        """Register domain expert"""
        self._experts[domain] = expert
    
    def get_expert(self, domain: str) -> Optional[BaseDomainExpert]:
        """Get expert for domain"""
        return self._experts.get(domain)
    
    def list_experts(self) -> List[str]:
        """List available expert domains"""
        return list(self._experts.keys())
    
    def get_expertise_summary(self) -> Dict[str, Any]:
        """Get summary of all experts"""
        summary = {}
        
        for domain, expert in self._experts.items():
            expertise = expert.get_expertise()
            summary[domain] = {
                "specializations": expertise.specializations,
                "expertise_level": expertise.expertise_level.value,
                "knowledge_graph_stats": expertise.knowledge_graph.get_statistics()
            }
        
        return summary
