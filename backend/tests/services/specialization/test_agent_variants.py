"""
Tests for agent variants and task classification
"""

import pytest
from datetime import datetime

from app.services.specialization.agent_variants import (
    TaskCategory,
    AgentConfiguration,
    TaskClassification,
    AgentPerformance,
    TaskClassifier,
    AgentVariantRegistry,
)


class TestAgentConfiguration:
    """Tests for AgentConfiguration"""
    
    def test_create_configuration(self):
        """Test creating agent configuration"""
        config = AgentConfiguration(
            variant_id="test_agent",
            name="Test Agent",
            task_category=TaskCategory.CONTENT_CREATION,
            domain="marketing",
            system_prompt="You are a test agent",
            temperature=0.7,
            capabilities=["writing", "editing"],
            specializations=["blog_posts"]
        )
        
        assert config.variant_id == "test_agent"
        assert config.name == "Test Agent"
        assert config.task_category == TaskCategory.CONTENT_CREATION
        assert config.domain == "marketing"
        assert config.temperature == 0.7
        assert "writing" in config.capabilities
        assert "blog_posts" in config.specializations
    
    def test_default_values(self):
        """Test default configuration values"""
        config = AgentConfiguration(
            variant_id="test_agent",
            name="Test Agent",
            task_category=TaskCategory.CONTENT_CREATION,
            domain="marketing",
            system_prompt="You are a test agent"
        )
        
        assert config.temperature == 0.7
        assert config.max_tokens == 2000
        assert config.expected_success_rate == 0.85
        assert isinstance(config.created_at, datetime)
        assert config.version == "1.0"


class TestAgentPerformance:
    """Tests for AgentPerformance"""
    
    def test_create_performance(self):
        """Test creating performance tracker"""
        perf = AgentPerformance(variant_id="test_agent")
        
        assert perf.variant_id == "test_agent"
        assert perf.total_tasks == 0
        assert perf.successful_tasks == 0
        assert perf.failed_tasks == 0
        assert perf.success_rate == 0.0
    
    def test_record_success(self):
        """Test recording successful task"""
        perf = AgentPerformance(variant_id="test_agent")
        
        perf.record_success(rating=4.5, response_time_ms=1200)
        
        assert perf.total_tasks == 1
        assert perf.successful_tasks == 1
        assert perf.failed_tasks == 0
        assert perf.success_rate == 1.0
        assert perf.avg_rating == 4.5
        assert perf.avg_response_time_ms == 1200
    
    def test_record_failure(self):
        """Test recording failed task"""
        perf = AgentPerformance(variant_id="test_agent")
        
        perf.record_failure(response_time_ms=800)
        
        assert perf.total_tasks == 1
        assert perf.successful_tasks == 0
        assert perf.failed_tasks == 1
        assert perf.success_rate == 0.0
        assert perf.avg_response_time_ms == 800
    
    def test_success_rate_calculation(self):
        """Test success rate calculation with multiple tasks"""
        perf = AgentPerformance(variant_id="test_agent")
        
        # Record 7 successes and 3 failures
        for _ in range(7):
            perf.record_success(rating=4.0)
        for _ in range(3):
            perf.record_failure()
        
        assert perf.total_tasks == 10
        assert perf.successful_tasks == 7
        assert perf.failed_tasks == 3
        assert perf.success_rate == 0.7
    
    def test_average_rating(self):
        """Test average rating calculation"""
        perf = AgentPerformance(variant_id="test_agent")
        
        perf.record_success(rating=5.0)
        perf.record_success(rating=4.0)
        perf.record_success(rating=3.0)
        
        assert perf.rating_count == 3
        assert perf.avg_rating == 4.0
    
    def test_average_response_time(self):
        """Test average response time calculation"""
        perf = AgentPerformance(variant_id="test_agent")
        
        perf.record_success(response_time_ms=1000)
        perf.record_success(response_time_ms=2000)
        perf.record_failure(response_time_ms=1500)
        
        assert perf.total_tasks == 3
        # (1000 + 2000 + 1500) / 3 = 1500
        assert perf.avg_response_time_ms == 1500


class TestTaskClassifier:
    """Tests for TaskClassifier"""
    
    def test_create_classifier(self):
        """Test creating task classifier"""
        classifier = TaskClassifier()
        assert classifier is not None
    
    def test_classify_content_creation(self):
        """Test classifying content creation task"""
        classifier = TaskClassifier()
        
        result = classifier.classify("Write a blog post about AI agents")
        
        assert result.task_category == TaskCategory.CONTENT_CREATION
        assert result.domain == "marketing"
        assert result.confidence > 0.5
        assert "content_creation_agent" in result.suggested_variant
    
    def test_classify_seo_task(self):
        """Test classifying SEO task"""
        classifier = TaskClassifier()
        
        result = classifier.classify("Optimize my website for search engines and improve Google ranking")
        
        assert result.task_category == TaskCategory.SEO_OPTIMIZATION
        assert result.domain == "marketing"
        assert "seo" in result.suggested_variant
    
    def test_classify_teaching_task(self):
        """Test classifying teaching task"""
        classifier = TaskClassifier()
        
        result = classifier.classify("Explain the concept of photosynthesis to a 10th grade student")
        
        assert result.task_category == TaskCategory.CONCEPT_TEACHING
        assert result.domain == "education"
        assert "concept_teaching" in result.suggested_variant
    
    def test_classify_test_prep_task(self):
        """Test classifying test preparation task"""
        classifier = TaskClassifier()
        
        result = classifier.classify("Help me prepare for JEE exam with practice problems")
        
        assert result.task_category == TaskCategory.TEST_PREPARATION
        assert result.domain == "education"
        assert "test_preparation" in result.suggested_variant
    
    def test_classify_lead_qualification(self):
        """Test classifying lead qualification task"""
        classifier = TaskClassifier()
        
        result = classifier.classify("Qualify this lead using BANT framework and assess fit")
        
        assert result.task_category == TaskCategory.LEAD_QUALIFICATION
        assert result.domain == "sales"
        assert "lead_qualification" in result.suggested_variant
    
    def test_classify_outreach_task(self):
        """Test classifying outreach task"""
        classifier = TaskClassifier()
        
        result = classifier.classify("Write a cold email to reach out to potential customers")
        
        assert result.task_category == TaskCategory.OUTREACH_WRITING
        assert result.domain == "sales"
        assert "outreach_writing" in result.suggested_variant
    
    def test_classify_with_context(self):
        """Test classification with context hint"""
        classifier = TaskClassifier()
        
        # Ambiguous task with domain hint
        result = classifier.classify(
            "Help me with this problem",
            context={"domain": "education"}
        )
        
        assert result.domain == "education"
    
    def test_classify_ambiguous_task(self):
        """Test classification of ambiguous task"""
        classifier = TaskClassifier()
        
        result = classifier.classify("Help me")
        
        # Should have low confidence and provide default
        assert result.confidence < 0.5
        assert result.domain in ["marketing", "education", "sales"]
    
    def test_alternative_variants(self):
        """Test that alternative variants are suggested"""
        classifier = TaskClassifier()
        
        result = classifier.classify("Write social media posts and blog articles")
        
        # Should match multiple categories
        assert len(result.alternative_variants) > 0


class TestAgentVariantRegistry:
    """Tests for AgentVariantRegistry"""
    
    def test_create_registry(self):
        """Test creating variant registry"""
        registry = AgentVariantRegistry()
        
        # Should have default variants registered
        variants = registry.list_variants()
        assert len(variants) >= 6  # At least 6 default variants
    
    def test_register_custom_variant(self):
        """Test registering custom variant"""
        registry = AgentVariantRegistry()
        
        custom_config = AgentConfiguration(
            variant_id="custom_agent",
            name="Custom Agent",
            task_category=TaskCategory.CONTENT_CREATION,
            domain="marketing",
            system_prompt="Custom prompt"
        )
        
        registry.register_variant(custom_config)
        
        variant = registry.get_variant("custom_agent")
        assert variant is not None
        assert variant.variant_id == "custom_agent"
        assert variant.name == "Custom Agent"
    
    def test_get_variant(self):
        """Test getting variant by ID"""
        registry = AgentVariantRegistry()
        
        variant = registry.get_variant("content_creation_agent")
        
        assert variant is not None
        assert variant.name == "Content Creator"
        assert variant.task_category == TaskCategory.CONTENT_CREATION
        assert variant.domain == "marketing"
    
    def test_get_nonexistent_variant(self):
        """Test getting non-existent variant"""
        registry = AgentVariantRegistry()
        
        variant = registry.get_variant("nonexistent_agent")
        
        assert variant is None
    
    def test_list_variants_by_domain(self):
        """Test listing variants by domain"""
        registry = AgentVariantRegistry()
        
        marketing_variants = registry.list_variants(domain="marketing")
        education_variants = registry.list_variants(domain="education")
        sales_variants = registry.list_variants(domain="sales")
        
        assert len(marketing_variants) >= 2
        assert len(education_variants) >= 2
        assert len(sales_variants) >= 2
        
        # Verify domains
        for variant in marketing_variants:
            assert variant.domain == "marketing"
        for variant in education_variants:
            assert variant.domain == "education"
        for variant in sales_variants:
            assert variant.domain == "sales"
    
    def test_list_variants_by_category(self):
        """Test listing variants by task category"""
        registry = AgentVariantRegistry()
        
        content_variants = registry.list_variants(
            task_category=TaskCategory.CONTENT_CREATION
        )
        
        assert len(content_variants) >= 1
        for variant in content_variants:
            assert variant.task_category == TaskCategory.CONTENT_CREATION
    
    def test_select_variant_content_creation(self):
        """Test selecting variant for content creation"""
        registry = AgentVariantRegistry()
        
        variant = registry.select_variant("Write a blog post about machine learning")
        
        assert variant is not None
        assert variant.task_category == TaskCategory.CONTENT_CREATION
        assert variant.domain == "marketing"
    
    def test_select_variant_seo(self):
        """Test selecting variant for SEO"""
        registry = AgentVariantRegistry()
        
        variant = registry.select_variant("Optimize my website for search engines")
        
        assert variant is not None
        assert variant.task_category == TaskCategory.SEO_OPTIMIZATION
        assert variant.domain == "marketing"
    
    def test_select_variant_teaching(self):
        """Test selecting variant for teaching"""
        registry = AgentVariantRegistry()
        
        variant = registry.select_variant("Explain quantum mechanics in simple terms")
        
        assert variant is not None
        assert variant.task_category == TaskCategory.CONCEPT_TEACHING
        assert variant.domain == "education"
    
    def test_select_variant_test_prep(self):
        """Test selecting variant for test prep"""
        registry = AgentVariantRegistry()
        
        variant = registry.select_variant("Help me study for NEET exam")
        
        assert variant is not None
        assert variant.task_category == TaskCategory.TEST_PREPARATION
        assert variant.domain == "education"
    
    def test_select_variant_sales_outreach(self):
        """Test selecting variant for sales outreach"""
        registry = AgentVariantRegistry()
        
        variant = registry.select_variant("Write a cold email to potential customers")
        
        assert variant is not None
        assert variant.task_category == TaskCategory.OUTREACH_WRITING
        assert variant.domain == "sales"
    
    def test_record_task_success(self):
        """Test recording successful task"""
        registry = AgentVariantRegistry()
        
        variant_id = "content_creation_agent"
        registry.record_task_result(
            variant_id=variant_id,
            success=True,
            rating=4.5,
            response_time_ms=1200
        )
        
        performance = registry.get_performance(variant_id)
        assert performance.total_tasks == 1
        assert performance.successful_tasks == 1
        assert performance.success_rate == 1.0
        assert performance.avg_rating == 4.5
    
    def test_record_task_failure(self):
        """Test recording failed task"""
        registry = AgentVariantRegistry()
        
        variant_id = "content_creation_agent"
        registry.record_task_result(
            variant_id=variant_id,
            success=False,
            response_time_ms=800
        )
        
        performance = registry.get_performance(variant_id)
        assert performance.total_tasks == 1
        assert performance.failed_tasks == 1
        assert performance.success_rate == 0.0
    
    def test_get_leaderboard(self):
        """Test getting performance leaderboard"""
        registry = AgentVariantRegistry()
        
        # Record some results
        registry.record_task_result("content_creation_agent", success=True, rating=4.5)
        registry.record_task_result("content_creation_agent", success=True, rating=4.0)
        registry.record_task_result("seo_optimization_agent", success=True, rating=5.0)
        registry.record_task_result("concept_teaching_agent", success=True, rating=4.8)
        registry.record_task_result("concept_teaching_agent", success=False)
        
        leaderboard = registry.get_leaderboard()
        
        assert len(leaderboard) >= 3
        # Should be sorted by success rate
        for i in range(len(leaderboard) - 1):
            assert leaderboard[i]["success_rate"] >= leaderboard[i + 1]["success_rate"]
    
    def test_get_leaderboard_by_domain(self):
        """Test getting domain-specific leaderboard"""
        registry = AgentVariantRegistry()
        
        # Record results for marketing variants
        registry.record_task_result("content_creation_agent", success=True, rating=4.5)
        registry.record_task_result("seo_optimization_agent", success=True, rating=5.0)
        # Record results for education variants
        registry.record_task_result("concept_teaching_agent", success=True, rating=4.8)
        
        marketing_leaderboard = registry.get_leaderboard(domain="marketing")
        education_leaderboard = registry.get_leaderboard(domain="education")
        
        # Verify domains
        for entry in marketing_leaderboard:
            assert entry["domain"] == "marketing"
        for entry in education_leaderboard:
            assert entry["domain"] == "education"
    
    def test_get_variant_recommendations(self):
        """Test getting variant recommendations"""
        registry = AgentVariantRegistry()
        
        recommendations = registry.get_variant_recommendations(
            "Write engaging blog content about AI",
            top_k=3
        )
        
        assert len(recommendations) <= 3
        assert len(recommendations) > 0
        
        # Should be sorted by score
        for i in range(len(recommendations) - 1):
            assert recommendations[i]["score"] >= recommendations[i + 1]["score"]
        
        # Top recommendation should match task
        top_rec = recommendations[0]
        assert "variant_id" in top_rec
        assert "name" in top_rec
        assert "score" in top_rec
        assert "capabilities" in top_rec
        assert "specializations" in top_rec
    
    def test_recommendations_with_performance_history(self):
        """Test recommendations factor in performance history"""
        registry = AgentVariantRegistry()
        
        # Give one variant better performance
        for _ in range(10):
            registry.record_task_result("content_creation_agent", success=True, rating=5.0)
        
        recommendations = registry.get_variant_recommendations(
            "Write a blog post",
            top_k=3
        )
        
        # Content creation agent should be highly ranked due to good performance
        top_rec = recommendations[0]
        assert top_rec["success_rate"] >= 0.85
    
    def test_variant_capabilities(self):
        """Test that variants have appropriate capabilities"""
        registry = AgentVariantRegistry()
        
        content_agent = registry.get_variant("content_creation_agent")
        seo_agent = registry.get_variant("seo_optimization_agent")
        teaching_agent = registry.get_variant("concept_teaching_agent")
        
        assert "writing" in content_agent.capabilities
        assert "keyword_research" in seo_agent.capabilities or "technical_seo" in seo_agent.capabilities
        assert "explanation" in teaching_agent.capabilities or "step_by_step" in teaching_agent.capabilities
    
    def test_variant_specializations(self):
        """Test that variants have appropriate specializations"""
        registry = AgentVariantRegistry()
        
        content_agent = registry.get_variant("content_creation_agent")
        test_prep_agent = registry.get_variant("test_preparation_agent")
        outreach_agent = registry.get_variant("outreach_writing_agent")
        
        assert len(content_agent.specializations) > 0
        assert len(test_prep_agent.specializations) > 0
        assert len(outreach_agent.specializations) > 0
