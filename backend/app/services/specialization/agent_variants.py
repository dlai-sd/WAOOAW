"""
Task-Specific Agent Variants

Specialized agent configurations optimized for specific tasks.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from .domain_experts import BaseDomainExpert, MarketingExpert, EducationExpert, SalesExpert


class TaskCategory(str, Enum):
    """High-level task categories"""
    # Marketing tasks
    CONTENT_CREATION = "content_creation"
    SOCIAL_MEDIA_MANAGEMENT = "social_media_management"
    SEO_OPTIMIZATION = "seo_optimization"
    CAMPAIGN_PLANNING = "campaign_planning"
    BRAND_STRATEGY = "brand_strategy"
    
    # Education tasks
    CONCEPT_TEACHING = "concept_teaching"
    HOMEWORK_HELP = "homework_help"
    TEST_PREPARATION = "test_preparation"
    STUDY_PLANNING = "study_planning"
    CAREER_GUIDANCE = "career_guidance"
    
    # Sales tasks
    LEAD_QUALIFICATION = "lead_qualification"
    OUTREACH_WRITING = "outreach_writing"
    PROPOSAL_CREATION = "proposal_creation"
    OBJECTION_HANDLING = "objection_handling"
    RELATIONSHIP_BUILDING = "relationship_building"


@dataclass
class AgentConfiguration:
    """Configuration for specialized agent variant"""
    variant_id: str
    name: str
    task_category: TaskCategory
    domain: str
    
    # Prompt configuration
    system_prompt: str
    temperature: float = 0.7
    max_tokens: int = 2000
    
    # Capabilities
    capabilities: List[str] = field(default_factory=list)
    specializations: List[str] = field(default_factory=list)
    
    # Performance parameters
    expected_success_rate: float = 0.85
    avg_response_time_ms: int = 1500
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    version: str = "1.0"


@dataclass
class TaskClassification:
    """Result of task classification"""
    task_category: TaskCategory
    confidence: float
    domain: str
    suggested_variant: str
    reasoning: str
    alternative_variants: List[str] = field(default_factory=list)


@dataclass
class AgentPerformance:
    """Performance metrics for agent variant"""
    variant_id: str
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    avg_rating: float = 0.0
    avg_response_time_ms: int = 0
    
    # Detailed metrics
    rating_count: int = 0
    total_rating: float = 0.0
    total_response_time_ms: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_tasks == 0:
            return 0.0
        return self.successful_tasks / self.total_tasks
    
    def record_success(self, rating: Optional[float] = None, response_time_ms: Optional[int] = None):
        """Record successful task"""
        self.total_tasks += 1
        self.successful_tasks += 1
        
        if rating is not None:
            self.total_rating += rating
            self.rating_count += 1
            self.avg_rating = self.total_rating / self.rating_count
        
        if response_time_ms is not None:
            self.total_response_time_ms += response_time_ms
            self.avg_response_time_ms = self.total_response_time_ms // self.total_tasks
    
    def record_failure(self, response_time_ms: Optional[int] = None):
        """Record failed task"""
        self.total_tasks += 1
        self.failed_tasks += 1
        
        if response_time_ms is not None:
            self.total_response_time_ms += response_time_ms
            self.avg_response_time_ms = self.total_response_time_ms // self.total_tasks


class TaskClassifier:
    """
    Classifies tasks to select appropriate agent variant.
    
    Uses keyword matching, pattern recognition, and ML-ready structure.
    """
    
    def __init__(self):
        """Initialize task classifier"""
        self._category_keywords = self._build_keyword_map()
    
    def _build_keyword_map(self) -> Dict[TaskCategory, List[str]]:
        """Build keyword map for task classification"""
        return {
            # Marketing keywords
            TaskCategory.CONTENT_CREATION: [
                "blog", "article", "content", "write", "copy", "post",
                "newsletter", "ebook", "whitepaper", "case study"
            ],
            TaskCategory.SOCIAL_MEDIA_MANAGEMENT: [
                "social media", "twitter", "linkedin", "facebook", "instagram",
                "tiktok", "post", "tweet", "engagement", "followers"
            ],
            TaskCategory.SEO_OPTIMIZATION: [
                "seo", "search engine", "keywords", "ranking", "google",
                "organic", "backlinks", "meta", "optimization"
            ],
            TaskCategory.CAMPAIGN_PLANNING: [
                "campaign", "strategy", "launch", "promotion", "advertising",
                "marketing plan", "budget", "timeline", "goals"
            ],
            TaskCategory.BRAND_STRATEGY: [
                "brand", "positioning", "identity", "messaging", "voice",
                "differentiation", "competitive", "value proposition"
            ],
            
            # Education keywords
            TaskCategory.CONCEPT_TEACHING: [
                "explain", "teach", "understand", "learn", "concept",
                "theory", "how does", "what is", "definition"
            ],
            TaskCategory.HOMEWORK_HELP: [
                "homework", "assignment", "question",
                "exercise", "help me with"
            ],
            TaskCategory.TEST_PREPARATION: [
                "test", "exam", "quiz", "preparation", "prepare for", "study for",
                "jee", "neet", "sat", "review", "practice test", "practice problems"
            ],
            TaskCategory.STUDY_PLANNING: [
                "study plan", "schedule", "organize", "time management",
                "learning path", "curriculum", "roadmap"
            ],
            TaskCategory.CAREER_GUIDANCE: [
                "career", "college", "university", "major", "job",
                "profession", "future", "guidance", "counseling"
            ],
            
            # Sales keywords
            TaskCategory.LEAD_QUALIFICATION: [
                "qualify", "lead", "prospect", "bant", "fit",
                "evaluate", "assess", "score", "priority"
            ],
            TaskCategory.OUTREACH_WRITING: [
                "outreach", "cold email", "cold", "email to", "message", "introduction",
                "reach out", "connect", "pitch", "first contact", "potential customers"
            ],
            TaskCategory.PROPOSAL_CREATION: [
                "proposal", "quote", "pricing", "sow", "statement of work",
                "contract", "agreement", "terms"
            ],
            TaskCategory.OBJECTION_HANDLING: [
                "objection", "concern", "hesitation", "pushback",
                "too expensive", "not sure", "competitor", "risk"
            ],
            TaskCategory.RELATIONSHIP_BUILDING: [
                "relationship", "follow up", "nurture", "trust",
                "rapport", "check in", "stay in touch"
            ]
        }
    
    def classify(self, task_description: str, context: Optional[Dict[str, Any]] = None) -> TaskClassification:
        """
        Classify task to determine appropriate agent variant.
        
        Args:
            task_description: Description of task
            context: Additional context (domain hint, user history, etc.)
            
        Returns:
            TaskClassification with suggested variant
        """
        task_lower = task_description.lower()
        
        # Score each category based on keyword matches
        scores: Dict[TaskCategory, float] = {}
        
        for category, keywords in self._category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in task_lower)
            if score > 0:
                scores[category] = score
        
        # If no matches, try context-based classification
        if not scores and context:
            domain_hint = context.get("domain")
            if domain_hint == "marketing":
                scores[TaskCategory.CONTENT_CREATION] = 0.5
            elif domain_hint == "education":
                scores[TaskCategory.CONCEPT_TEACHING] = 0.5
            elif domain_hint == "sales":
                scores[TaskCategory.LEAD_QUALIFICATION] = 0.5
        
        # Default if still no matches
        if not scores:
            return TaskClassification(
                task_category=TaskCategory.CONTENT_CREATION,
                confidence=0.3,
                domain="marketing",
                suggested_variant="general_marketing_agent",
                reasoning="No clear task indicators, defaulting to general content creation",
                alternative_variants=[]
            )
        
        # Get top category
        top_category = max(scores.items(), key=lambda x: x[1])
        category, raw_score = top_category
        
        # Calculate confidence (normalize score)
        max_possible_score = len(self._category_keywords[category])
        confidence = min(1.0, raw_score / max(3, max_possible_score * 0.3))
        
        # Determine domain from category
        domain = self._category_to_domain(category)
        
        # Get variant ID
        variant_id = self._category_to_variant_id(category)
        
        # Get alternatives (other categories with scores)
        alternatives = [
            self._category_to_variant_id(cat)
            for cat, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)[1:3]
        ]
        
        return TaskClassification(
            task_category=category,
            confidence=confidence,
            domain=domain,
            suggested_variant=variant_id,
            reasoning=f"Matched {int(raw_score)} keywords for {category.value}",
            alternative_variants=alternatives
        )
    
    def _category_to_domain(self, category: TaskCategory) -> str:
        """Map task category to domain"""
        if category in [
            TaskCategory.CONTENT_CREATION,
            TaskCategory.SOCIAL_MEDIA_MANAGEMENT,
            TaskCategory.SEO_OPTIMIZATION,
            TaskCategory.CAMPAIGN_PLANNING,
            TaskCategory.BRAND_STRATEGY
        ]:
            return "marketing"
        elif category in [
            TaskCategory.CONCEPT_TEACHING,
            TaskCategory.HOMEWORK_HELP,
            TaskCategory.TEST_PREPARATION,
            TaskCategory.STUDY_PLANNING,
            TaskCategory.CAREER_GUIDANCE
        ]:
            return "education"
        elif category in [
            TaskCategory.LEAD_QUALIFICATION,
            TaskCategory.OUTREACH_WRITING,
            TaskCategory.PROPOSAL_CREATION,
            TaskCategory.OBJECTION_HANDLING,
            TaskCategory.RELATIONSHIP_BUILDING
        ]:
            return "sales"
        return "marketing"
    
    def _category_to_variant_id(self, category: TaskCategory) -> str:
        """Map task category to variant ID"""
        return f"{category.value}_agent"


class AgentVariantRegistry:
    """
    Registry of agent variants with performance tracking.
    
    Manages variant configurations, selection, and performance metrics.
    """
    
    def __init__(self):
        """Initialize variant registry"""
        self._variants: Dict[str, AgentConfiguration] = {}
        self._performance: Dict[str, AgentPerformance] = {}
        self._classifier = TaskClassifier()
        
        # Register default variants
        self._register_default_variants()
    
    def _register_default_variants(self):
        """Register default agent variants"""
        # Marketing variants
        self.register_variant(AgentConfiguration(
            variant_id="content_creation_agent",
            name="Content Creator",
            task_category=TaskCategory.CONTENT_CREATION,
            domain="marketing",
            system_prompt="""You are a skilled content creator specializing in engaging, 
high-quality content across formats (blogs, social media, emails). Focus on clarity, 
storytelling, and audience engagement. Use SEO best practices when relevant.""",
            temperature=0.8,
            capabilities=["writing", "storytelling", "seo", "research"],
            specializations=["blog_posts", "social_content", "email_campaigns"],
            expected_success_rate=0.88
        ))
        
        self.register_variant(AgentConfiguration(
            variant_id="seo_optimization_agent",
            name="SEO Specialist",
            task_category=TaskCategory.SEO_OPTIMIZATION,
            domain="marketing",
            system_prompt="""You are an SEO expert focused on improving search rankings and 
organic traffic. Provide keyword research, on-page optimization, technical SEO advice, 
and content strategies that balance user value with search engine requirements.""",
            temperature=0.6,
            capabilities=["keyword_research", "technical_seo", "content_optimization"],
            specializations=["on_page_seo", "keyword_strategy", "seo_audits"],
            expected_success_rate=0.86
        ))
        
        # Education variants
        self.register_variant(AgentConfiguration(
            variant_id="concept_teaching_agent",
            name="Concept Teacher",
            task_category=TaskCategory.CONCEPT_TEACHING,
            domain="education",
            system_prompt="""You are an expert tutor who excels at explaining complex concepts 
clearly. Use analogies, examples, and step-by-step reasoning. Check understanding frequently 
and adapt explanations to the student's level. Build on prerequisites before introducing 
new concepts.""",
            temperature=0.7,
            capabilities=["explanation", "analogies", "step_by_step", "assessment"],
            specializations=["math", "science", "concept_breakdown"],
            expected_success_rate=0.90
        ))
        
        self.register_variant(AgentConfiguration(
            variant_id="test_preparation_agent",
            name="Test Prep Coach",
            task_category=TaskCategory.TEST_PREPARATION,
            domain="education",
            system_prompt="""You are a test preparation coach specializing in exam strategies, 
practice problems, and confidence building. Focus on identifying knowledge gaps, providing 
targeted practice, and teaching test-taking techniques. Help students manage time and anxiety.""",
            temperature=0.6,
            capabilities=["practice_problems", "exam_strategies", "gap_analysis"],
            specializations=["jee", "neet", "sat", "competitive_exams"],
            expected_success_rate=0.87
        ))
        
        # Sales variants
        self.register_variant(AgentConfiguration(
            variant_id="outreach_writing_agent",
            name="Outreach Writer",
            task_category=TaskCategory.OUTREACH_WRITING,
            domain="sales",
            system_prompt="""You are a sales outreach expert who crafts personalized, compelling 
messages. Focus on value proposition, pain point addressing, and clear calls-to-action. 
Keep messages concise, professional, and human. Use social proof when available.""",
            temperature=0.75,
            capabilities=["personalization", "value_proposition", "call_to_action"],
            specializations=["cold_email", "linkedin_messages", "follow_ups"],
            expected_success_rate=0.85
        ))
        
        self.register_variant(AgentConfiguration(
            variant_id="lead_qualification_agent",
            name="Lead Qualifier",
            task_category=TaskCategory.LEAD_QUALIFICATION,
            domain="sales",
            system_prompt="""You are a lead qualification specialist using BANT framework 
(Budget, Authority, Need, Timeline). Assess lead fit, identify decision makers, understand 
pain points, and provide prioritization. Be thorough but efficient in qualification.""",
            temperature=0.5,
            capabilities=["bant_analysis", "prioritization", "pain_point_identification"],
            specializations=["b2b_qualification", "enterprise_sales", "scoring"],
            expected_success_rate=0.89
        ))
    
    def register_variant(self, config: AgentConfiguration):
        """Register agent variant"""
        self._variants[config.variant_id] = config
        self._performance[config.variant_id] = AgentPerformance(variant_id=config.variant_id)
    
    def get_variant(self, variant_id: str) -> Optional[AgentConfiguration]:
        """Get variant configuration"""
        return self._variants.get(variant_id)
    
    def list_variants(
        self,
        domain: Optional[str] = None,
        task_category: Optional[TaskCategory] = None
    ) -> List[AgentConfiguration]:
        """List variants with optional filters"""
        variants = list(self._variants.values())
        
        if domain:
            variants = [v for v in variants if v.domain == domain]
        if task_category:
            variants = [v for v in variants if v.task_category == task_category]
        
        return variants
    
    def select_variant(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentConfiguration:
        """
        Select best variant for task.
        
        Args:
            task_description: Description of task
            context: Additional context
            
        Returns:
            Selected variant configuration
        """
        # Classify task
        classification = self._classifier.classify(task_description, context)
        
        # Get suggested variant
        variant = self.get_variant(classification.suggested_variant)
        
        # Fallback if variant not found
        if not variant:
            # Try alternatives
            for alt_id in classification.alternative_variants:
                variant = self.get_variant(alt_id)
                if variant:
                    break
            
            # Ultimate fallback: first variant in domain
            if not variant:
                domain_variants = self.list_variants(domain=classification.domain)
                variant = domain_variants[0] if domain_variants else list(self._variants.values())[0]
        
        return variant
    
    def get_performance(self, variant_id: str) -> Optional[AgentPerformance]:
        """Get performance metrics for variant"""
        return self._performance.get(variant_id)
    
    def record_task_result(
        self,
        variant_id: str,
        success: bool,
        rating: Optional[float] = None,
        response_time_ms: Optional[int] = None
    ):
        """Record task execution result"""
        performance = self._performance.get(variant_id)
        if not performance:
            return
        
        if success:
            performance.record_success(rating, response_time_ms)
        else:
            performance.record_failure(response_time_ms)
    
    def get_leaderboard(self, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get variant performance leaderboard.
        
        Args:
            domain: Filter by domain
            
        Returns:
            Sorted list of variants by performance
        """
        variants = self.list_variants(domain=domain)
        
        leaderboard = []
        for variant in variants:
            performance = self._performance.get(variant.variant_id)
            if not performance or performance.total_tasks == 0:
                continue
            
            leaderboard.append({
                "variant_id": variant.variant_id,
                "name": variant.name,
                "domain": variant.domain,
                "task_category": variant.task_category.value,
                "success_rate": performance.success_rate,
                "avg_rating": performance.avg_rating,
                "total_tasks": performance.total_tasks,
                "avg_response_time_ms": performance.avg_response_time_ms
            })
        
        # Sort by success rate, then rating
        leaderboard.sort(
            key=lambda x: (x["success_rate"], x["avg_rating"]),
            reverse=True
        )
        
        return leaderboard
    
    def get_variant_recommendations(
        self,
        task_description: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get top K variant recommendations for task.
        
        Args:
            task_description: Task description
            top_k: Number of recommendations
            
        Returns:
            List of variant recommendations with scores
        """
        classification = self._classifier.classify(task_description)
        
        # Get all variants in classified domain
        domain_variants = self.list_variants(domain=classification.domain)
        
        recommendations = []
        for variant in domain_variants:
            # Calculate recommendation score
            # Factor 1: Task category match
            category_match = 1.0 if variant.task_category == classification.task_category else 0.5
            
            # Factor 2: Historical performance
            performance = self._performance.get(variant.variant_id)
            perf_score = performance.success_rate if performance and performance.total_tasks > 0 else 0.85
            
            # Combined score
            score = (category_match * 0.6) + (perf_score * 0.4)
            
            recommendations.append({
                "variant_id": variant.variant_id,
                "name": variant.name,
                "score": score,
                "category_match": category_match,
                "success_rate": perf_score,
                "capabilities": variant.capabilities,
                "specializations": variant.specializations
            })
        
        # Sort and return top K
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:top_k]
