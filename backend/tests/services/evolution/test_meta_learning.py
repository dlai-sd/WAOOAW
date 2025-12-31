"""
Tests for Meta-Learning & Transfer Learning Engine - Story 5.6.4
"""

import pytest
from datetime import datetime

from app.services.evolution.meta_learning import (
    MetaLearningEngine,
    LearningExperience,
    TransferPath,
    SkillComposition,
    MetaLearningInsight,
    LearningStrategy,
    DomainType,
)


def test_create_engine():
    """Test engine initialization"""
    engine = MetaLearningEngine()
    
    stats = engine.get_statistics()
    assert stats["total_learning_experiences"] == 0
    assert stats["total_transfer_paths"] == 0
    assert stats["total_skill_compositions"] == 0


def test_record_learning_experience():
    """Test recording a learning experience"""
    engine = MetaLearningEngine()
    
    experience = engine.record_learning_experience(
        agent_variant_id="agent_1",
        task_type="content_writing",
        domain=DomainType.CONTENT_CREATION,
        skill_acquired="Blog Writing",
        strategy_used=LearningStrategy.EXPERIENTIAL,
        attempts_to_competence=5,
        time_to_competence_hours=10.0,
        prior_knowledge=["Writing Basics", "Grammar"]
    )
    
    assert experience.experience_id.startswith("exp_agent_1")
    assert experience.skill_acquired == "Blog Writing"
    assert experience.attempts_to_competence == 5
    assert experience.time_to_competence_hours == 10.0
    assert 0.0 <= experience.final_proficiency <= 1.0


def test_proficiency_calculation():
    """Test that proficiency is calculated correctly"""
    engine = MetaLearningEngine()
    
    # Quick learner (few attempts, less time) should have higher proficiency
    fast_exp = engine.record_learning_experience(
        agent_variant_id="agent_1",
        task_type="test",
        domain=DomainType.MARKETING,
        skill_acquired="Fast Skill",
        strategy_used=LearningStrategy.EXPERIENTIAL,
        attempts_to_competence=3,
        time_to_competence_hours=5.0,
        prior_knowledge=[]
    )
    
    # Slow learner (many attempts, more time) should have lower proficiency
    slow_exp = engine.record_learning_experience(
        agent_variant_id="agent_2",
        task_type="test",
        domain=DomainType.MARKETING,
        skill_acquired="Slow Skill",
        strategy_used=LearningStrategy.EXPERIENTIAL,
        attempts_to_competence=15,
        time_to_competence_hours=30.0,
        prior_knowledge=[]
    )
    
    assert fast_exp.final_proficiency > slow_exp.final_proficiency


def test_analyze_learning_efficiency():
    """Test learning efficiency analysis"""
    engine = MetaLearningEngine()
    
    # Record multiple learning experiences
    for i in range(5):
        engine.record_learning_experience(
            agent_variant_id="agent_1",
            task_type=f"task_{i}",
            domain=DomainType.MARKETING,
            skill_acquired=f"Skill {i}",
            strategy_used=LearningStrategy.EXPERIENTIAL,
            attempts_to_competence=4 + i,
            time_to_competence_hours=8.0 + i * 2,
            prior_knowledge=[]
        )
    
    efficiency = engine.analyze_learning_efficiency("agent_1")
    
    assert efficiency["has_data"] is True
    assert efficiency["total_skills_learned"] == 5
    assert efficiency["avg_attempts_to_competence"] > 0
    assert efficiency["avg_time_to_competence_hours"] > 0
    assert efficiency["avg_final_proficiency"] > 0
    assert efficiency["most_effective_strategy"] is not None


def test_learning_efficiency_no_data():
    """Test learning efficiency with no data"""
    engine = MetaLearningEngine()
    
    efficiency = engine.analyze_learning_efficiency("agent_unknown")
    
    assert efficiency["has_data"] is False


def test_identify_most_effective_strategy():
    """Test identification of most effective learning strategy"""
    engine = MetaLearningEngine()
    
    # Record experiences with different strategies
    engine.record_learning_experience(
        agent_variant_id="agent_1",
        task_type="task_1",
        domain=DomainType.MARKETING,
        skill_acquired="Skill 1",
        strategy_used=LearningStrategy.EXPERIENTIAL,
        attempts_to_competence=3,
        time_to_competence_hours=5.0,
        prior_knowledge=[]
    )
    
    engine.record_learning_experience(
        agent_variant_id="agent_1",
        task_type="task_2",
        domain=DomainType.MARKETING,
        skill_acquired="Skill 2",
        strategy_used=LearningStrategy.OBSERVATIONAL,
        attempts_to_competence=10,
        time_to_competence_hours=20.0,
        prior_knowledge=[]
    )
    
    efficiency = engine.analyze_learning_efficiency("agent_1")
    
    # Experiential should be more effective (better proficiency)
    assert efficiency["most_effective_strategy"] == "experiential"


def test_identify_transfer_opportunity():
    """Test identifying transfer opportunities"""
    engine = MetaLearningEngine()
    
    transfer_path = engine.identify_transfer_opportunity(
        agent_variant_id="agent_1",
        source_domain=DomainType.MARKETING,
        target_domain=DomainType.SALES,
        skill="Persuasive Communication"
    )
    
    assert transfer_path.transfer_id.startswith("transfer_agent_1")
    assert transfer_path.source_domain == DomainType.MARKETING
    assert transfer_path.target_domain == DomainType.SALES
    assert transfer_path.transferable_skill == "Persuasive Communication"
    assert 0.0 <= transfer_path.transfer_efficiency <= 1.0
    assert transfer_path.adaptation_required
    assert transfer_path.success_count == 0


def test_domain_similarity():
    """Test domain similarity calculation"""
    engine = MetaLearningEngine()
    
    # Similar domains should have high transfer efficiency
    similar_transfer = engine.identify_transfer_opportunity(
        agent_variant_id="agent_1",
        source_domain=DomainType.MARKETING,
        target_domain=DomainType.SALES,
        skill="Test Skill"
    )
    
    # Dissimilar domains should have lower transfer efficiency
    dissimilar_transfer = engine.identify_transfer_opportunity(
        agent_variant_id="agent_1",
        source_domain=DomainType.TECHNICAL,
        target_domain=DomainType.CREATIVE,
        skill="Test Skill"
    )
    
    assert similar_transfer.transfer_efficiency > dissimilar_transfer.transfer_efficiency


def test_execute_transfer_success():
    """Test executing a successful transfer"""
    engine = MetaLearningEngine()
    
    transfer_path = engine.identify_transfer_opportunity(
        agent_variant_id="agent_1",
        source_domain=DomainType.MARKETING,
        target_domain=DomainType.SALES,
        skill="Test Skill"
    )
    
    initial_efficiency = transfer_path.transfer_efficiency
    initial_success_count = transfer_path.success_count
    
    # Execute successful transfer
    result = engine.execute_transfer(transfer_path.transfer_id, success=True)
    
    assert result is True
    assert transfer_path.success_count == initial_success_count + 1
    assert transfer_path.transfer_efficiency >= initial_efficiency


def test_execute_transfer_failure():
    """Test executing a failed transfer"""
    engine = MetaLearningEngine()
    
    transfer_path = engine.identify_transfer_opportunity(
        agent_variant_id="agent_1",
        source_domain=DomainType.MARKETING,
        target_domain=DomainType.SALES,
        skill="Test Skill"
    )
    
    initial_efficiency = transfer_path.transfer_efficiency
    
    # Execute failed transfer
    result = engine.execute_transfer(transfer_path.transfer_id, success=False)
    
    assert result is True
    assert transfer_path.transfer_efficiency < initial_efficiency


def test_compose_skills():
    """Test skill composition"""
    engine = MetaLearningEngine()
    
    composition = engine.compose_skills(
        agent_variant_id="agent_1",
        complex_task="Create Marketing Campaign",
        component_skills=["Content Writing", "Design", "Analytics"],
        composition_strategy="Sequential: Research -> Create -> Analyze"
    )
    
    assert composition.composition_id.startswith("comp_agent_1")
    assert composition.complex_task == "Create Marketing Campaign"
    assert len(composition.component_skills) == 3
    assert composition.composition_strategy
    assert composition.success_rate == 0.0
    assert composition.times_applied == 0


def test_record_composition_result():
    """Test recording composition results"""
    engine = MetaLearningEngine()
    
    composition = engine.compose_skills(
        agent_variant_id="agent_1",
        complex_task="Test Task",
        component_skills=["Skill 1", "Skill 2"],
        composition_strategy="Parallel"
    )
    
    # Record multiple results
    engine.record_composition_result(composition.composition_id, success=True)
    engine.record_composition_result(composition.composition_id, success=True)
    engine.record_composition_result(composition.composition_id, success=False)
    
    assert composition.times_applied == 3
    assert 0.6 <= composition.success_rate <= 0.7  # 2/3 ≈ 0.67


def test_discover_meta_insight():
    """Test discovering meta-learning insights"""
    engine = MetaLearningEngine()
    
    # Record some experiences first
    exp1 = engine.record_learning_experience(
        agent_variant_id="agent_1",
        task_type="task_1",
        domain=DomainType.MARKETING,
        skill_acquired="Skill 1",
        strategy_used=LearningStrategy.EXPERIENTIAL,
        attempts_to_competence=3,
        time_to_competence_hours=5.0,
        prior_knowledge=[]
    )
    
    insight = engine.discover_meta_insight(
        agent_variant_id="agent_1",
        insight_type="optimal_strategy",
        description="Hands-on practice is most effective for marketing skills",
        evidence_experience_ids=[exp1.experience_id],
        applicable_contexts=["marketing", "content_creation"],
        recommended_action="Use experiential learning for marketing tasks",
        impact_multiplier=1.5
    )
    
    assert insight.insight_id.startswith("insight_agent_1")
    assert insight.insight_type == "optimal_strategy"
    assert len(insight.evidence) > 0
    assert insight.impact_on_learning_speed == 1.5


def test_get_optimal_learning_strategy_no_history():
    """Test getting strategy recommendation with no history"""
    engine = MetaLearningEngine()
    
    recommendation = engine.get_optimal_learning_strategy(
        agent_variant_id="agent_unknown",
        target_domain=DomainType.MARKETING
    )
    
    assert recommendation["recommended_strategy"] is not None
    assert recommendation["reason"]
    assert recommendation["expected_efficiency"] > 0


def test_get_optimal_learning_strategy_with_domain_history():
    """Test strategy recommendation with domain history"""
    engine = MetaLearningEngine()
    
    # Record successful experiences with experiential learning
    for i in range(3):
        engine.record_learning_experience(
            agent_variant_id="agent_1",
            task_type=f"task_{i}",
            domain=DomainType.MARKETING,
            skill_acquired=f"Skill {i}",
            strategy_used=LearningStrategy.EXPERIENTIAL,
            attempts_to_competence=3,
            time_to_competence_hours=5.0,
            prior_knowledge=[]
        )
    
    recommendation = engine.get_optimal_learning_strategy(
        agent_variant_id="agent_1",
        target_domain=DomainType.MARKETING
    )
    
    assert recommendation["recommended_strategy"] == "experiential"
    assert "marketing" in recommendation["reason"].lower()


def test_get_optimal_learning_strategy_with_similar_domain():
    """Test strategy recommendation using similar domain experience"""
    engine = MetaLearningEngine()
    
    # Record experiences in similar domain (Marketing)
    engine.record_learning_experience(
        agent_variant_id="agent_1",
        task_type="task_1",
        domain=DomainType.MARKETING,
        skill_acquired="Skill 1",
        strategy_used=LearningStrategy.OBSERVATIONAL,
        attempts_to_competence=3,
        time_to_competence_hours=5.0,
        prior_knowledge=[]
    )
    
    # Ask for recommendation in related domain (Sales)
    recommendation = engine.get_optimal_learning_strategy(
        agent_variant_id="agent_1",
        target_domain=DomainType.SALES
    )
    
    # Should recommend based on similar domain experience
    assert recommendation["recommended_strategy"] is not None
    assert recommendation["expected_efficiency"] > 0


def test_get_transfer_recommendations():
    """Test getting transfer recommendations"""
    engine = MetaLearningEngine()
    
    # Record skills in source domains
    engine.record_learning_experience(
        agent_variant_id="agent_1",
        task_type="task_1",
        domain=DomainType.MARKETING,
        skill_acquired="Campaign Planning",
        strategy_used=LearningStrategy.EXPERIENTIAL,
        attempts_to_competence=3,
        time_to_competence_hours=5.0,
        prior_knowledge=[]
    )
    
    engine.record_learning_experience(
        agent_variant_id="agent_1",
        task_type="task_2",
        domain=DomainType.CONTENT_CREATION,
        skill_acquired="Storytelling",
        strategy_used=LearningStrategy.EXPERIENTIAL,
        attempts_to_competence=4,
        time_to_competence_hours=8.0,
        prior_knowledge=[]
    )
    
    # Get recommendations for target domain
    recommendations = engine.get_transfer_recommendations(
        agent_variant_id="agent_1",
        target_domain=DomainType.SALES
    )
    
    assert len(recommendations) > 0
    for rec in recommendations:
        assert "skill" in rec
        assert "from_domain" in rec
        assert "transfer_efficiency" in rec
        assert rec["transfer_efficiency"] > 0.5  # Should be transferable


def test_get_transfer_recommendations_no_history():
    """Test transfer recommendations with no history"""
    engine = MetaLearningEngine()
    
    recommendations = engine.get_transfer_recommendations(
        agent_variant_id="agent_unknown",
        target_domain=DomainType.SALES
    )
    
    assert recommendations == []


def test_get_agent_meta_profile():
    """Test getting comprehensive meta-learning profile"""
    engine = MetaLearningEngine()
    
    # Record various learning activities
    engine.record_learning_experience(
        agent_variant_id="agent_1",
        task_type="task_1",
        domain=DomainType.MARKETING,
        skill_acquired="Skill 1",
        strategy_used=LearningStrategy.EXPERIENTIAL,
        attempts_to_competence=3,
        time_to_competence_hours=5.0,
        prior_knowledge=[]
    )
    
    transfer = engine.identify_transfer_opportunity(
        agent_variant_id="agent_1",
        source_domain=DomainType.MARKETING,
        target_domain=DomainType.SALES,
        skill="Test Skill"
    )
    
    composition = engine.compose_skills(
        agent_variant_id="agent_1",
        complex_task="Complex Task",
        component_skills=["Skill 1", "Skill 2"],
        composition_strategy="Sequential"
    )
    
    profile = engine.get_agent_meta_profile("agent_1")
    
    assert profile["agent_variant_id"] == "agent_1"
    assert profile["total_learning_experiences"] == 1
    assert profile["transfer_paths_discovered"] == 1
    assert profile["skill_compositions_created"] == 1
    assert profile["meta_learning_maturity"] in ["Novice", "Developing", "Proficient", "Advanced", "Expert"]


def test_meta_learning_maturity_progression():
    """Test that maturity level increases with experience"""
    engine = MetaLearningEngine()
    
    # Novice (few experiences)
    engine.record_learning_experience(
        agent_variant_id="agent_1",
        task_type="task_1",
        domain=DomainType.MARKETING,
        skill_acquired="Skill 1",
        strategy_used=LearningStrategy.EXPERIENTIAL,
        attempts_to_competence=5,
        time_to_competence_hours=10.0,
        prior_knowledge=[]
    )
    
    profile1 = engine.get_agent_meta_profile("agent_1")
    maturity1 = profile1["meta_learning_maturity"]
    
    # Add more experiences, transfers, compositions, insights
    for i in range(20):
        engine.record_learning_experience(
            agent_variant_id="agent_1",
            task_type=f"task_{i}",
            domain=DomainType.MARKETING,
            skill_acquired=f"Skill {i}",
            strategy_used=LearningStrategy.EXPERIENTIAL,
            attempts_to_competence=4,
            time_to_competence_hours=8.0,
            prior_knowledge=[]
        )
    
    for i in range(5):
        engine.identify_transfer_opportunity(
            agent_variant_id="agent_1",
            source_domain=DomainType.MARKETING,
            target_domain=DomainType.SALES,
            skill=f"Transfer Skill {i}"
        )
    
    for i in range(3):
        engine.compose_skills(
            agent_variant_id="agent_1",
            complex_task=f"Complex Task {i}",
            component_skills=["Skill 1", "Skill 2"],
            composition_strategy="Parallel"
        )
    
    profile2 = engine.get_agent_meta_profile("agent_1")
    maturity2 = profile2["meta_learning_maturity"]
    
    # Maturity should progress
    maturity_order = ["Novice", "Developing", "Proficient", "Advanced", "Expert"]
    assert maturity_order.index(maturity2) >= maturity_order.index(maturity1)


def test_get_statistics():
    """Test engine-wide statistics"""
    engine = MetaLearningEngine()
    
    # Create data for multiple agents
    for agent_id in ["agent_1", "agent_2"]:
        for i in range(3):
            engine.record_learning_experience(
                agent_variant_id=agent_id,
                task_type=f"task_{i}",
                domain=DomainType.MARKETING,
                skill_acquired=f"Skill {i}",
                strategy_used=LearningStrategy.EXPERIENTIAL,
                attempts_to_competence=5,
                time_to_competence_hours=10.0,
                prior_knowledge=[]
            )
        
        engine.identify_transfer_opportunity(
            agent_variant_id=agent_id,
            source_domain=DomainType.MARKETING,
            target_domain=DomainType.SALES,
            skill="Test Skill"
        )
    
    stats = engine.get_statistics()
    
    assert stats["total_learning_experiences"] == 6
    assert stats["total_transfer_paths"] == 2
    assert stats["avg_attempts_to_competence"] > 0
    assert stats["avg_final_proficiency"] > 0
    assert stats["contributing_agents"] == 2


def test_learning_experience_serialization():
    """Test LearningExperience to_dict serialization"""
    engine = MetaLearningEngine()
    
    experience = engine.record_learning_experience(
        agent_variant_id="agent_1",
        task_type="test_task",
        domain=DomainType.MARKETING,
        skill_acquired="Test Skill",
        strategy_used=LearningStrategy.EXPERIENTIAL,
        attempts_to_competence=5,
        time_to_competence_hours=10.0,
        prior_knowledge=["Prior Skill"]
    )
    
    data = experience.to_dict()
    
    assert data["experience_id"] == experience.experience_id
    assert data["domain"] == "marketing"
    assert data["strategy_used"] == "experiential"
    assert data["attempts_to_competence"] == 5


def test_transfer_path_serialization():
    """Test TransferPath to_dict serialization"""
    engine = MetaLearningEngine()
    
    transfer = engine.identify_transfer_opportunity(
        agent_variant_id="agent_1",
        source_domain=DomainType.MARKETING,
        target_domain=DomainType.SALES,
        skill="Test Skill"
    )
    
    data = transfer.to_dict()
    
    assert data["transfer_id"] == transfer.transfer_id
    assert data["source_domain"] == "marketing"
    assert data["target_domain"] == "sales"
    assert "transfer_efficiency" in data


def test_skill_composition_serialization():
    """Test SkillComposition to_dict serialization"""
    engine = MetaLearningEngine()
    
    composition = engine.compose_skills(
        agent_variant_id="agent_1",
        complex_task="Complex Task",
        component_skills=["Skill 1", "Skill 2"],
        composition_strategy="Sequential"
    )
    
    data = composition.to_dict()
    
    assert data["composition_id"] == composition.composition_id
    assert data["complex_task"] == "Complex Task"
    assert len(data["component_skills"]) == 2


def test_meta_insight_serialization():
    """Test MetaLearningInsight to_dict serialization"""
    engine = MetaLearningEngine()
    
    insight = engine.discover_meta_insight(
        agent_variant_id="agent_1",
        insight_type="optimal_strategy",
        description="Test insight",
        evidence_experience_ids=["exp_1"],
        applicable_contexts=["context_1"],
        recommended_action="Test action",
        impact_multiplier=1.5
    )
    
    data = insight.to_dict()
    
    assert data["insight_id"] == insight.insight_id
    assert data["insight_type"] == "optimal_strategy"
    assert data["impact_on_learning_speed"] == 1.5


def test_fast_learning_domains_identified():
    """Test that fast learning domains are identified"""
    engine = MetaLearningEngine()
    
    # Fast in Marketing
    for i in range(3):
        engine.record_learning_experience(
            agent_variant_id="agent_1",
            task_type=f"marketing_task_{i}",
            domain=DomainType.MARKETING,
            skill_acquired=f"Marketing Skill {i}",
            strategy_used=LearningStrategy.EXPERIENTIAL,
            attempts_to_competence=3,
            time_to_competence_hours=5.0,
            prior_knowledge=[]
        )
    
    # Slow in Technical
    for i in range(3):
        engine.record_learning_experience(
            agent_variant_id="agent_1",
            task_type=f"technical_task_{i}",
            domain=DomainType.TECHNICAL,
            skill_acquired=f"Technical Skill {i}",
            strategy_used=LearningStrategy.EXPERIENTIAL,
            attempts_to_competence=10,
            time_to_competence_hours=20.0,
            prior_knowledge=[]
        )
    
    efficiency = engine.analyze_learning_efficiency("agent_1")
    
    # Marketing should be in fast learning domains
    assert "marketing" in efficiency["fast_learning_domains"]
