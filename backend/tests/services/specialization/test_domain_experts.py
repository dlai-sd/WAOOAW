"""
Tests for Domain Experts
"""

import pytest
from backend.app.services.specialization.domain_experts import (
    MarketingExpert,
    EducationExpert,
    SalesExpert,
    DomainExpertRegistry,
    ExpertiseLevel
)
from backend.app.services.specialization.knowledge_graph import EntityType


class TestMarketingExpert:
    """Test MarketingExpert"""
    
    @pytest.fixture
    def expert(self):
        """Create marketing expert for testing"""
        return MarketingExpert()
    
    def test_create_expert(self, expert):
        """Test creating marketing expert"""
        assert expert.domain == "marketing"
        assert len(expert.specializations) > 0
        assert expert.expertise_level == ExpertiseLevel.EXPERT
        assert expert.knowledge_graph is not None
    
    def test_knowledge_graph_initialized(self, expert):
        """Test that knowledge graph is initialized with marketing data"""
        # Check entities exist
        channels = expert.knowledge_graph.get_entities_by_type(EntityType.CHANNEL)
        assert len(channels) > 0
        
        content_types = expert.knowledge_graph.get_entities_by_type(EntityType.CONTENT_TYPE)
        assert len(content_types) > 0
        
        audiences = expert.knowledge_graph.get_entities_by_type(EntityType.AUDIENCE)
        assert len(audiences) > 0
    
    def test_analyze_campaign_awareness(self, expert):
        """Test analyzing awareness campaign"""
        campaign = {
            "goal": "awareness",
            "audience": "b2b",
            "budget": "medium"
        }
        
        analysis = expert.analyze_campaign(campaign)
        
        assert "campaign_type" in analysis
        assert "awareness" in analysis["campaign_type"].lower()
        assert "channels" in analysis
        assert len(analysis["channels"]) > 0
        assert "metrics" in analysis
        assert "Impressions" in analysis["metrics"]
    
    def test_analyze_campaign_leads(self, expert):
        """Test analyzing lead generation campaign"""
        campaign = {
            "goal": "leads",
            "audience": "smb",
            "budget": "high"
        }
        
        analysis = expert.analyze_campaign(campaign)
        
        assert "lead" in analysis["campaign_type"].lower()
        assert "Lead generation" in analysis["metrics"]
        assert "Conversion rate" in analysis["metrics"]
    
    def test_recommend_channels(self, expert):
        """Test channel recommendations"""
        analysis = expert.analyze_campaign({
            "goal": "awareness",
            "audience": "b2b",
            "budget": "medium"
        })
        
        channels = analysis["channels"]
        
        assert len(channels) > 0
        assert all("channel" in ch for ch in channels)
        assert all("score" in ch for ch in channels)
        assert all("reason" in ch for ch in channels)
        
        # Channels should be sorted by score
        scores = [ch["score"] for ch in channels]
        assert scores == sorted(scores, reverse=True)
    
    def test_recommend_content(self, expert):
        """Test content recommendations"""
        analysis = expert.analyze_campaign({
            "goal": "engagement",
            "audience": "b2c",
            "budget": "medium"
        })
        
        content = analysis["content_strategy"]
        
        assert len(content) > 0
        assert any("content" in c.lower() for c in content)
    
    def test_recommend_metrics(self, expert):
        """Test KPI recommendations"""
        analysis = expert.analyze_campaign({
            "goal": "sales",
            "audience": "b2b",
            "budget": "high"
        })
        
        metrics = analysis["metrics"]
        
        assert len(metrics) > 0
        assert any("revenue" in m.lower() or "roi" in m.lower() for m in metrics)
    
    def test_get_expertise(self, expert):
        """Test getting expertise configuration"""
        expertise = expert.get_expertise()
        
        assert expertise.domain == "marketing"
        assert len(expertise.specializations) > 0
        assert expertise.expertise_level == ExpertiseLevel.EXPERT
        assert len(expertise.reasoning_patterns) > 0


class TestEducationExpert:
    """Test EducationExpert"""
    
    @pytest.fixture
    def expert(self):
        """Create education expert for testing"""
        return EducationExpert()
    
    def test_create_expert(self, expert):
        """Test creating education expert"""
        assert expert.domain == "education"
        assert "math_tutoring" in expert.specializations
        assert expert.knowledge_graph is not None
    
    def test_knowledge_graph_initialized(self, expert):
        """Test that knowledge graph is initialized with education data"""
        subjects = expert.knowledge_graph.get_entities_by_type(EntityType.SUBJECT)
        assert len(subjects) > 0
        
        concepts = expert.knowledge_graph.get_entities_by_type(EntityType.CONCEPT)
        assert len(concepts) > 0
        
        prerequisites = expert.knowledge_graph.get_entities_by_type(EntityType.PREREQUISITE)
        assert len(prerequisites) > 0
    
    def test_create_learning_plan(self, expert):
        """Test creating learning plan"""
        student = {
            "current_level": "beginner",
            "goals": ["algebra", "geometry"],
            "challenges": ["time_management", "motivation"]
        }
        
        plan = expert.create_learning_plan(student)
        
        assert "topics" in plan
        assert len(plan["topics"]) > 0
        assert "resources" in plan
        assert "timeline" in plan
        assert "assessment_schedule" in plan
        assert "support_needed" in plan
    
    def test_sequence_topics(self, expert):
        """Test topic sequencing based on prerequisites"""
        student = {
            "current_level": "beginner",
            "goals": ["advanced_math"]
        }
        
        plan = expert.create_learning_plan(student)
        topics = plan["topics"]
        
        # Topics should be sequenced (simpler first)
        assert len(topics) > 0
        assert all("topic" in t for t in topics)
        assert all("difficulty" in t for t in topics)
        assert all("prerequisites" in t for t in topics)
    
    def test_recommend_resources(self, expert):
        """Test resource recommendations"""
        plan = expert.create_learning_plan({
            "current_level": "intermediate",
            "goals": ["calculus"]
        })
        
        resources = plan["resources"]
        
        assert len(resources) > 0
        assert all("type" in r for r in resources)
        assert all("platform" in r for r in resources)
    
    def test_identify_support(self, expert):
        """Test identifying support needs"""
        plan = expert.create_learning_plan({
            "current_level": "beginner",
            "goals": ["algebra"],
            "challenges": ["comprehension", "motivation"]
        })
        
        support = plan["support_needed"]
        
        assert len(support) > 0
        assert any("chunk" in s.lower() for s in support)  # Break down complex topics
        assert any("milestone" in s.lower() or "reward" in s.lower() for s in support)  # Motivation


class TestSalesExpert:
    """Test SalesExpert"""
    
    @pytest.fixture
    def expert(self):
        """Create sales expert for testing"""
        return SalesExpert()
    
    def test_create_expert(self, expert):
        """Test creating sales expert"""
        assert expert.domain == "sales"
        assert "lead_qualification" in expert.specializations
        assert expert.knowledge_graph is not None
    
    def test_knowledge_graph_initialized(self, expert):
        """Test that knowledge graph is initialized with sales data"""
        pain_points = expert.knowledge_graph.get_entities_by_type(EntityType.PAIN_POINT)
        assert len(pain_points) > 0
        
        products = expert.knowledge_graph.get_entities_by_type(EntityType.PRODUCT)
        assert len(products) > 0
    
    def test_qualify_lead_hot(self, expert):
        """Test qualifying hot lead"""
        lead = {
            "company": "Acme Corp",
            "role": "ceo",
            "pain_points": ["cost", "efficiency", "scalability"],
            "timeline": "immediate",
            "budget": "confirmed"
        }
        
        qualification = expert.qualify_lead(lead)
        
        assert qualification["score"] > 0.7  # High score
        assert qualification["level"] == "Hot Lead"
        assert qualification["priority"] == "high"
        assert "demo" in " ".join(qualification["recommended_actions"]).lower()
    
    def test_qualify_lead_warm(self, expert):
        """Test qualifying warm lead"""
        lead = {
            "role": "director",
            "pain_points": ["efficiency"],
            "timeline": "1_month",
            "budget": "estimated"
        }
        
        qualification = expert.qualify_lead(lead)
        
        assert 0.4 < qualification["score"] < 0.8
        assert qualification["level"] == "Warm Lead"
        assert qualification["priority"] == "medium"
    
    def test_qualify_lead_cold(self, expert):
        """Test qualifying cold lead"""
        lead = {
            "role": "manager",
            "pain_points": [],
            "timeline": "exploring",
            "budget": "unknown"
        }
        
        qualification = expert.qualify_lead(lead)
        
        assert qualification["score"] < 0.5
        assert qualification["priority"] in ["low", "medium"]
        assert "nurture" in " ".join(qualification["recommended_actions"]).lower()
    
    def test_bant_scoring(self, expert):
        """Test BANT framework scoring"""
        lead = {
            "role": "vp",
            "pain_points": ["cost", "efficiency"],
            "timeline": "3_months",
            "budget": "confirmed"
        }
        
        qualification = expert.qualify_lead(lead)
        bant = qualification["bant_breakdown"]
        
        assert "budget" in bant
        assert "authority" in bant
        assert "need" in bant
        assert "timeline" in bant
        
        # All scores should be between 0 and 1
        assert all(0 <= score <= 1 for score in bant.values())
    
    def test_recommended_actions_progression(self, expert):
        """Test that recommended actions match qualification level"""
        hot_lead = {
            "role": "ceo",
            "pain_points": ["cost", "efficiency", "scalability"],
            "timeline": "immediate",
            "budget": "confirmed"
        }
        
        cold_lead = {
            "role": "individual",
            "pain_points": [],
            "timeline": "exploring",
            "budget": "unknown"
        }
        
        hot_qual = expert.qualify_lead(hot_lead)
        cold_qual = expert.qualify_lead(cold_lead)
        
        # Hot leads should get immediate action items
        hot_actions = " ".join(hot_qual["recommended_actions"]).lower()
        assert "demo" in hot_actions or "proposal" in hot_actions
        
        # Cold leads should get nurture actions
        cold_actions = " ".join(cold_qual["recommended_actions"]).lower()
        assert "nurture" in cold_actions or "content" in cold_actions


class TestDomainExpertRegistry:
    """Test DomainExpertRegistry"""
    
    @pytest.fixture
    def registry(self):
        """Create expert registry for testing"""
        return DomainExpertRegistry()
    
    def test_create_registry(self, registry):
        """Test creating registry"""
        assert registry is not None
        
        # Default experts should be registered
        experts = registry.list_experts()
        assert "marketing" in experts
        assert "education" in experts
        assert "sales" in experts
    
    def test_get_expert(self, registry):
        """Test getting expert by domain"""
        marketing_expert = registry.get_expert("marketing")
        
        assert marketing_expert is not None
        assert marketing_expert.domain == "marketing"
        assert isinstance(marketing_expert, MarketingExpert)
    
    def test_get_nonexistent_expert(self, registry):
        """Test getting nonexistent expert"""
        expert = registry.get_expert("nonexistent")
        
        assert expert is None
    
    def test_register_custom_expert(self, registry):
        """Test registering custom expert"""
        custom_expert = MarketingExpert(
            specializations=["custom_specialization"],
            expertise_level=ExpertiseLevel.ADVANCED
        )
        
        registry.register("custom_marketing", custom_expert)
        
        retrieved = registry.get_expert("custom_marketing")
        assert retrieved is not None
        assert "custom_specialization" in retrieved.specializations
    
    def test_list_experts(self, registry):
        """Test listing all experts"""
        experts = registry.list_experts()
        
        assert len(experts) >= 3
        assert isinstance(experts, list)
    
    def test_get_expertise_summary(self, registry):
        """Test getting expertise summary"""
        summary = registry.get_expertise_summary()
        
        assert "marketing" in summary
        assert "education" in summary
        assert "sales" in summary
        
        # Check marketing summary structure
        marketing = summary["marketing"]
        assert "specializations" in marketing
        assert "expertise_level" in marketing
        assert "knowledge_graph_stats" in marketing
        
        # Check knowledge graph stats
        stats = marketing["knowledge_graph_stats"]
        assert "domain" in stats
        assert "total_entities" in stats
        assert stats["total_entities"] > 0
