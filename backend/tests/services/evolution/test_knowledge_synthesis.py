"""
Tests for Knowledge Synthesis & Creation Engine - Story 5.6.2
"""

import pytest
from datetime import datetime

from app.services.evolution.knowledge_synthesis import (
    KnowledgeSynthesisEngine,
    DiscoveredPattern,
    CreatedFramework,
    BestPractice,
    CaseStudy,
    PatternType,
    FrameworkType,
    KnowledgeStatus,
)


def test_create_engine():
    """Test engine initialization"""
    engine = KnowledgeSynthesisEngine()
    
    stats = engine.get_statistics()
    assert stats["total_patterns"] == 0
    assert stats["total_frameworks"] == 0
    assert stats["total_best_practices"] == 0
    assert stats["total_case_studies"] == 0
    assert stats["contributing_agents"] == 0


def test_discover_pattern_basic():
    """Test pattern discovery"""
    engine = KnowledgeSynthesisEngine()
    
    pattern = engine.discover_pattern(
        agent_variant_id="agent_1",
        pattern_type=PatternType.WORKFLOW,
        pattern_name="Content Research Pattern",
        pattern_description="Start with competitor analysis before content creation",
        supporting_data=["task_1", "task_2", "task_3"],
        applicable_contexts=["content_creation", "blog_writing"],
        expected_benefit="30% faster content creation with better quality"
    )
    
    assert pattern.pattern_id.startswith("pattern_agent_1")
    assert pattern.pattern_type == PatternType.WORKFLOW
    assert pattern.observed_instances == 3
    assert 0.5 <= pattern.confidence_score <= 1.0
    assert len(pattern.applicable_contexts) == 2
    assert pattern.validation_count == 0


def test_pattern_confidence_increases_with_data():
    """Test confidence score increases with more supporting data"""
    engine = KnowledgeSynthesisEngine()
    
    # Pattern with 2 instances
    pattern1 = engine.discover_pattern(
        agent_variant_id="agent_1",
        pattern_type=PatternType.SUCCESS_FACTOR,
        pattern_name="Test Pattern 1",
        pattern_description="Test",
        supporting_data=["task_1", "task_2"],
        applicable_contexts=["test"],
        expected_benefit="Test"
    )
    
    # Pattern with 10 instances
    pattern2 = engine.discover_pattern(
        agent_variant_id="agent_1",
        pattern_type=PatternType.SUCCESS_FACTOR,
        pattern_name="Test Pattern 2",
        pattern_description="Test",
        supporting_data=[f"task_{i}" for i in range(10)],
        applicable_contexts=["test"],
        expected_benefit="Test"
    )
    
    assert pattern2.confidence_score > pattern1.confidence_score
    assert pattern2.observed_instances == 10


def test_validate_pattern():
    """Test pattern validation by other agents"""
    engine = KnowledgeSynthesisEngine()
    
    pattern = engine.discover_pattern(
        agent_variant_id="agent_1",
        pattern_type=PatternType.OPTIMIZATION,
        pattern_name="Batch Processing Pattern",
        pattern_description="Process similar tasks in batches",
        supporting_data=["task_1"],
        applicable_contexts=["data_processing"],
        expected_benefit="50% time reduction"
    )
    
    initial_confidence = pattern.confidence_score
    initial_validation = pattern.validation_count
    
    # Another agent validates
    result = engine.validate_pattern(pattern.pattern_id)
    
    assert result is True
    assert pattern.validation_count == initial_validation + 1
    assert pattern.confidence_score > initial_confidence


def test_create_framework_basic():
    """Test framework creation"""
    engine = KnowledgeSynthesisEngine()
    
    framework = engine.create_framework(
        agent_variant_id="agent_1",
        framework_type=FrameworkType.METHODOLOGY,
        framework_name="Content Creation Methodology",
        purpose="Create high-quality blog posts consistently",
        steps=[
            {"step": "1", "description": "Research topic and competitors"},
            {"step": "2", "description": "Outline key points"},
            {"step": "3", "description": "Write first draft"},
            {"step": "4", "description": "Review and refine"}
        ],
        applicable_scenarios=["blog_writing", "article_creation"],
        success_criteria=["Customer satisfaction >= 4.0", "Completion time < 2 hours"]
    )
    
    assert framework.framework_id.startswith("framework_agent_1")
    assert framework.framework_type == FrameworkType.METHODOLOGY
    assert len(framework.steps) == 4
    assert framework.status == KnowledgeStatus.DRAFT
    assert framework.times_used == 0
    assert framework.success_rate == 0.0


def test_use_framework_success():
    """Test recording successful framework usage"""
    engine = KnowledgeSynthesisEngine()
    
    framework = engine.create_framework(
        agent_variant_id="agent_1",
        framework_type=FrameworkType.CHECKLIST,
        framework_name="Quality Checklist",
        purpose="Ensure content quality",
        steps=[{"step": "1", "description": "Check spelling"}],
        applicable_scenarios=["content_review"],
        success_criteria=["Zero errors"]
    )
    
    # Use successfully 3 times
    for _ in range(3):
        engine.use_framework(framework.framework_id, successful=True)
    
    assert framework.times_used == 3
    assert framework.success_rate == 1.0
    assert framework.status == KnowledgeStatus.APPROVED


def test_use_framework_mixed_results():
    """Test framework with mixed success/failure"""
    engine = KnowledgeSynthesisEngine()
    
    framework = engine.create_framework(
        agent_variant_id="agent_1",
        framework_type=FrameworkType.TEMPLATE,
        framework_name="Email Template",
        purpose="Customer outreach",
        steps=[{"step": "1", "description": "Personalize greeting"}],
        applicable_scenarios=["email_marketing"],
        success_criteria=["Response rate > 20%"]
    )
    
    # 4 successes, 1 failure
    for _ in range(4):
        engine.use_framework(framework.framework_id, successful=True)
    engine.use_framework(framework.framework_id, successful=False)
    
    assert framework.times_used == 5
    assert 0.75 <= framework.success_rate <= 0.85  # 4/5 = 0.8


def test_framework_promotion_to_published():
    """Test framework gets published after proven success"""
    engine = KnowledgeSynthesisEngine()
    
    framework = engine.create_framework(
        agent_variant_id="agent_1",
        framework_type=FrameworkType.PLAYBOOK,
        framework_name="Sales Playbook",
        purpose="Close deals",
        steps=[{"step": "1", "description": "Qualify lead"}],
        applicable_scenarios=["sales"],
        success_criteria=["Win rate > 30%"]
    )
    
    # Use successfully 10 times (meets threshold)
    for _ in range(10):
        engine.use_framework(framework.framework_id, successful=True)
    
    # Check it got promoted to PUBLISHED
    assert framework.status == KnowledgeStatus.PUBLISHED
    assert framework.success_rate >= 0.8


def test_author_best_practice():
    """Test best practice authoring"""
    engine = KnowledgeSynthesisEngine()
    
    practice = engine.author_best_practice(
        agent_variant_id="agent_1",
        title="Start with Why",
        category="content_creation",
        principle="Always understand customer's underlying goal before starting",
        rationale="Leads to better alignment and fewer revisions",
        how_to="Ask clarifying questions about business objectives",
        success_stories=["task_1", "task_2"],
        when_to_use=["New customer projects", "Unclear requirements"]
    )
    
    assert practice.practice_id.startswith("practice_agent_1")
    assert practice.title == "Start with Why"
    assert practice.category == "content_creation"
    assert len(practice.success_stories) == 2
    assert practice.status == KnowledgeStatus.DRAFT
    assert practice.adoption_count == 0


def test_adopt_best_practice():
    """Test best practice adoption by other agents"""
    engine = KnowledgeSynthesisEngine()
    
    practice = engine.author_best_practice(
        agent_variant_id="agent_1",
        title="Test Practice",
        category="testing",
        principle="Test principle",
        rationale="Test rationale",
        how_to="Test how-to",
        success_stories=["task_1"],
        when_to_use=["Always"]
    )
    
    # Multiple agents adopt
    for _ in range(3):
        engine.adopt_best_practice(practice.practice_id)
    
    assert practice.adoption_count == 3


def test_best_practice_promotion():
    """Test best practice gets published after adoption"""
    engine = KnowledgeSynthesisEngine()
    
    practice = engine.author_best_practice(
        agent_variant_id="agent_1",
        title="Popular Practice",
        category="general",
        principle="Do good work",
        rationale="It works",
        how_to="Work hard",
        success_stories=["task_1"],
        when_to_use=["Always"]
    )
    
    # Adopt 5 times (threshold for PUBLISHED)
    for _ in range(5):
        engine.adopt_best_practice(practice.practice_id)
    
    assert practice.status == KnowledgeStatus.PUBLISHED


def test_generate_case_study():
    """Test case study generation"""
    engine = KnowledgeSynthesisEngine()
    
    case_study = engine.generate_case_study(
        agent_variant_id="agent_1",
        title="E-commerce Product Launch",
        category="marketing",
        situation="Client needed to launch new product line in 30 days",
        approach_taken="Created integrated campaign with email, social, and content",
        results="150% of sales target achieved in first month",
        lessons_learned=[
            "Early customer research was key",
            "Multi-channel approach worked well",
            "Need more time for creative development"
        ],
        template_steps=[
            "Step 1: Customer research (1 week)",
            "Step 2: Campaign strategy (1 week)",
            "Step 3: Content creation (2 weeks)",
            "Step 4: Launch and monitor (ongoing)"
        ]
    )
    
    assert case_study.case_study_id.startswith("case_agent_1")
    assert case_study.title == "E-commerce Product Launch"
    assert len(case_study.lessons_learned) == 3
    assert len(case_study.template_steps) == 4
    assert case_study.status == KnowledgeStatus.DRAFT
    assert case_study.times_referenced == 0


def test_reference_case_study():
    """Test case study referencing"""
    engine = KnowledgeSynthesisEngine()
    
    case_study = engine.generate_case_study(
        agent_variant_id="agent_1",
        title="Test Case",
        category="test",
        situation="Test situation",
        approach_taken="Test approach",
        results="Test results",
        lessons_learned=["Test lesson"],
        template_steps=["Step 1"]
    )
    
    # Reference 5 times
    for _ in range(5):
        engine.reference_case_study(case_study.case_study_id)
    
    assert case_study.times_referenced == 5


def test_case_study_promotion():
    """Test case study gets published after many references"""
    engine = KnowledgeSynthesisEngine()
    
    case_study = engine.generate_case_study(
        agent_variant_id="agent_1",
        title="Popular Case",
        category="test",
        situation="Test",
        approach_taken="Test",
        results="Test",
        lessons_learned=["Test"],
        template_steps=["Step 1"]
    )
    
    # Reference 10 times (threshold for PUBLISHED)
    for _ in range(10):
        engine.reference_case_study(case_study.case_study_id)
    
    assert case_study.status == KnowledgeStatus.PUBLISHED


def test_search_patterns_by_type():
    """Test searching patterns by type"""
    engine = KnowledgeSynthesisEngine()
    
    # Create different types of patterns
    engine.discover_pattern(
        agent_variant_id="agent_1",
        pattern_type=PatternType.WORKFLOW,
        pattern_name="Workflow Pattern",
        pattern_description="Test",
        supporting_data=["task_1"],
        applicable_contexts=["test"],
        expected_benefit="Test"
    )
    
    engine.discover_pattern(
        agent_variant_id="agent_1",
        pattern_type=PatternType.SUCCESS_FACTOR,
        pattern_name="Success Pattern",
        pattern_description="Test",
        supporting_data=["task_2"],
        applicable_contexts=["test"],
        expected_benefit="Test"
    )
    
    # Search for workflow patterns
    workflow_patterns = engine.search_patterns(pattern_type=PatternType.WORKFLOW)
    
    assert len(workflow_patterns) == 1
    assert workflow_patterns[0].pattern_name == "Workflow Pattern"


def test_search_patterns_by_confidence():
    """Test searching patterns by minimum confidence"""
    engine = KnowledgeSynthesisEngine()
    
    # Low confidence pattern (1 instance)
    engine.discover_pattern(
        agent_variant_id="agent_1",
        pattern_type=PatternType.OPTIMIZATION,
        pattern_name="Low Confidence",
        pattern_description="Test",
        supporting_data=["task_1"],
        applicable_contexts=["test"],
        expected_benefit="Test"
    )
    
    # High confidence pattern (10 instances)
    engine.discover_pattern(
        agent_variant_id="agent_1",
        pattern_type=PatternType.OPTIMIZATION,
        pattern_name="High Confidence",
        pattern_description="Test",
        supporting_data=[f"task_{i}" for i in range(10)],
        applicable_contexts=["test"],
        expected_benefit="Test"
    )
    
    # Search with high confidence threshold
    high_conf_patterns = engine.search_patterns(min_confidence=0.8)
    
    assert len(high_conf_patterns) >= 1
    assert all(p.confidence_score >= 0.8 for p in high_conf_patterns)


def test_search_frameworks_by_type():
    """Test searching frameworks by type"""
    engine = KnowledgeSynthesisEngine()
    
    engine.create_framework(
        agent_variant_id="agent_1",
        framework_type=FrameworkType.METHODOLOGY,
        framework_name="Methodology Framework",
        purpose="Test",
        steps=[{"step": "1", "description": "Test"}],
        applicable_scenarios=["test"],
        success_criteria=["Test"]
    )
    
    engine.create_framework(
        agent_variant_id="agent_1",
        framework_type=FrameworkType.CHECKLIST,
        framework_name="Checklist Framework",
        purpose="Test",
        steps=[{"step": "1", "description": "Test"}],
        applicable_scenarios=["test"],
        success_criteria=["Test"]
    )
    
    methodologies = engine.search_frameworks(framework_type=FrameworkType.METHODOLOGY)
    
    assert len(methodologies) == 1
    assert methodologies[0].framework_name == "Methodology Framework"


def test_search_frameworks_by_success_rate():
    """Test searching frameworks by success rate"""
    engine = KnowledgeSynthesisEngine()
    
    # Create two frameworks
    framework1 = engine.create_framework(
        agent_variant_id="agent_1",
        framework_type=FrameworkType.TEMPLATE,
        framework_name="Low Success",
        purpose="Test",
        steps=[{"step": "1", "description": "Test"}],
        applicable_scenarios=["test"],
        success_criteria=["Test"]
    )
    
    framework2 = engine.create_framework(
        agent_variant_id="agent_1",
        framework_type=FrameworkType.TEMPLATE,
        framework_name="High Success",
        purpose="Test",
        steps=[{"step": "1", "description": "Test"}],
        applicable_scenarios=["test"],
        success_criteria=["Test"]
    )
    
    # Make framework2 successful
    for _ in range(10):
        engine.use_framework(framework2.framework_id, successful=True)
    
    # Make framework1 mediocre
    for _ in range(5):
        engine.use_framework(framework1.framework_id, successful=True)
    for _ in range(5):
        engine.use_framework(framework1.framework_id, successful=False)
    
    # Search for high success frameworks
    high_success = engine.search_frameworks(min_success_rate=0.8)
    
    assert len(high_success) == 1
    assert high_success[0].framework_name == "High Success"


def test_search_best_practices_by_category():
    """Test searching best practices by category"""
    engine = KnowledgeSynthesisEngine()
    
    engine.author_best_practice(
        agent_variant_id="agent_1",
        title="Marketing Practice",
        category="marketing",
        principle="Test",
        rationale="Test",
        how_to="Test",
        success_stories=["task_1"],
        when_to_use=["Always"]
    )
    
    engine.author_best_practice(
        agent_variant_id="agent_1",
        title="Sales Practice",
        category="sales",
        principle="Test",
        rationale="Test",
        how_to="Test",
        success_stories=["task_1"],
        when_to_use=["Always"]
    )
    
    marketing_practices = engine.search_best_practices(category="marketing")
    
    assert len(marketing_practices) == 1
    assert marketing_practices[0].title == "Marketing Practice"


def test_search_best_practices_by_adoption():
    """Test searching best practices by adoption count"""
    engine = KnowledgeSynthesisEngine()
    
    practice1 = engine.author_best_practice(
        agent_variant_id="agent_1",
        title="Unpopular Practice",
        category="test",
        principle="Test",
        rationale="Test",
        how_to="Test",
        success_stories=["task_1"],
        when_to_use=["Always"]
    )
    
    practice2 = engine.author_best_practice(
        agent_variant_id="agent_1",
        title="Popular Practice",
        category="test",
        principle="Test",
        rationale="Test",
        how_to="Test",
        success_stories=["task_1"],
        when_to_use=["Always"]
    )
    
    # Make practice2 popular
    for _ in range(5):
        engine.adopt_best_practice(practice2.practice_id)
    
    # Search for adopted practices
    adopted = engine.search_best_practices(min_adoption=3)
    
    assert len(adopted) == 1
    assert adopted[0].title == "Popular Practice"


def test_search_case_studies_by_category():
    """Test searching case studies by category"""
    engine = KnowledgeSynthesisEngine()
    
    engine.generate_case_study(
        agent_variant_id="agent_1",
        title="Marketing Case",
        category="marketing",
        situation="Test",
        approach_taken="Test",
        results="Test",
        lessons_learned=["Test"],
        template_steps=["Step 1"]
    )
    
    engine.generate_case_study(
        agent_variant_id="agent_1",
        title="Education Case",
        category="education",
        situation="Test",
        approach_taken="Test",
        results="Test",
        lessons_learned=["Test"],
        template_steps=["Step 1"]
    )
    
    marketing_cases = engine.search_case_studies(category="marketing")
    
    assert len(marketing_cases) == 1
    assert marketing_cases[0].title == "Marketing Case"


def test_get_agent_contributions():
    """Test getting agent's knowledge contributions"""
    engine = KnowledgeSynthesisEngine()
    
    # Agent creates various knowledge items
    engine.discover_pattern(
        agent_variant_id="agent_1",
        pattern_type=PatternType.WORKFLOW,
        pattern_name="Pattern 1",
        pattern_description="Test",
        supporting_data=["task_1"],
        applicable_contexts=["test"],
        expected_benefit="Test"
    )
    
    engine.create_framework(
        agent_variant_id="agent_1",
        framework_type=FrameworkType.METHODOLOGY,
        framework_name="Framework 1",
        purpose="Test",
        steps=[{"step": "1", "description": "Test"}],
        applicable_scenarios=["test"],
        success_criteria=["Test"]
    )
    
    engine.author_best_practice(
        agent_variant_id="agent_1",
        title="Practice 1",
        category="test",
        principle="Test",
        rationale="Test",
        how_to="Test",
        success_stories=["task_1"],
        when_to_use=["Always"]
    )
    
    contributions = engine.get_agent_contributions("agent_1")
    
    assert contributions["patterns_discovered"] == 1
    assert contributions["frameworks_created"] == 1
    assert contributions["best_practices_authored"] == 1
    assert contributions["total_contributions"] == 3


def test_get_statistics():
    """Test knowledge synthesis statistics"""
    engine = KnowledgeSynthesisEngine()
    
    # Create various knowledge items
    pattern = engine.discover_pattern(
        agent_variant_id="agent_1",
        pattern_type=PatternType.WORKFLOW,
        pattern_name="Pattern",
        pattern_description="Test",
        supporting_data=[f"task_{i}" for i in range(10)],  # High confidence
        applicable_contexts=["test"],
        expected_benefit="Test"
    )
    
    framework = engine.create_framework(
        agent_variant_id="agent_2",
        framework_type=FrameworkType.METHODOLOGY,
        framework_name="Framework",
        purpose="Test",
        steps=[{"step": "1", "description": "Test"}],
        applicable_scenarios=["test"],
        success_criteria=["Test"]
    )
    
    # Use framework successfully to get it published
    for _ in range(10):
        engine.use_framework(framework.framework_id, successful=True)
    
    practice = engine.author_best_practice(
        agent_variant_id="agent_3",
        title="Practice",
        category="test",
        principle="Test",
        rationale="Test",
        how_to="Test",
        success_stories=["task_1"],
        when_to_use=["Always"]
    )
    engine.adopt_best_practice(practice.practice_id)
    
    case_study = engine.generate_case_study(
        agent_variant_id="agent_1",
        title="Case",
        category="test",
        situation="Test",
        approach_taken="Test",
        results="Test",
        lessons_learned=["Test"],
        template_steps=["Step 1"]
    )
    engine.reference_case_study(case_study.case_study_id)
    
    stats = engine.get_statistics()
    
    assert stats["total_patterns"] == 1
    assert stats["high_confidence_patterns"] >= 1
    assert stats["total_frameworks"] == 1
    assert stats["published_frameworks"] == 1
    assert stats["total_best_practices"] == 1
    assert stats["adopted_practices"] == 1
    assert stats["total_case_studies"] == 1
    assert stats["referenced_case_studies"] == 1
    assert stats["contributing_agents"] == 3
    assert stats["total_knowledge_items"] == 4


def test_pattern_serialization():
    """Test pattern to_dict serialization"""
    engine = KnowledgeSynthesisEngine()
    
    pattern = engine.discover_pattern(
        agent_variant_id="agent_1",
        pattern_type=PatternType.SUCCESS_FACTOR,
        pattern_name="Test Pattern",
        pattern_description="Description",
        supporting_data=["task_1"],
        applicable_contexts=["context_1"],
        expected_benefit="Benefit"
    )
    
    data = pattern.to_dict()
    
    assert data["pattern_id"] == pattern.pattern_id
    assert data["pattern_type"] == "success_factor"
    assert data["pattern_name"] == "Test Pattern"
    assert isinstance(data["discovered_at"], str)


def test_framework_serialization():
    """Test framework to_dict serialization"""
    engine = KnowledgeSynthesisEngine()
    
    framework = engine.create_framework(
        agent_variant_id="agent_1",
        framework_type=FrameworkType.CHECKLIST,
        framework_name="Test Framework",
        purpose="Test purpose",
        steps=[{"step": "1", "description": "Do something"}],
        applicable_scenarios=["scenario_1"],
        success_criteria=["criterion_1"]
    )
    
    data = framework.to_dict()
    
    assert data["framework_id"] == framework.framework_id
    assert data["framework_type"] == "checklist"
    assert data["framework_name"] == "Test Framework"
    assert data["status"] == "draft"


def test_best_practice_serialization():
    """Test best practice to_dict serialization"""
    engine = KnowledgeSynthesisEngine()
    
    practice = engine.author_best_practice(
        agent_variant_id="agent_1",
        title="Test Practice",
        category="test_category",
        principle="Test principle",
        rationale="Test rationale",
        how_to="Test how-to",
        success_stories=["task_1"],
        when_to_use=["Always"]
    )
    
    data = practice.to_dict()
    
    assert data["practice_id"] == practice.practice_id
    assert data["title"] == "Test Practice"
    assert data["category"] == "test_category"
    assert data["status"] == "draft"


def test_case_study_serialization():
    """Test case study to_dict serialization"""
    engine = KnowledgeSynthesisEngine()
    
    case_study = engine.generate_case_study(
        agent_variant_id="agent_1",
        title="Test Case Study",
        category="test_category",
        situation="Test situation",
        approach_taken="Test approach",
        results="Test results",
        lessons_learned=["Lesson 1"],
        template_steps=["Step 1"]
    )
    
    data = case_study.to_dict()
    
    assert data["case_study_id"] == case_study.case_study_id
    assert data["title"] == "Test Case Study"
    assert data["category"] == "test_category"
    assert len(data["lessons_learned"]) == 1
