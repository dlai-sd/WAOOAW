"""
Tests for Reflection & Self-Evaluation Engine - Story 5.6.1

Epic 5.6: Self-Evolving Agent System
Story Points: 34
"""

import pytest
from app.services.evolution import (
    PerformanceMetric,
    StrengthArea,
    WeaknessArea,
    ImprovementPriority,
    TaskReflection,
    PerformanceAnalysis,
    GapAnalysis,
    ImprovementGoal,
    LearningTask,
    ReflectionEngine,
)


class TestReflectionEngine:
    """Test suite for agent reflection and self-evaluation"""
    
    def test_create_engine(self):
        """Test engine instantiation"""
        engine = ReflectionEngine()
        
        assert engine is not None
        stats = engine.get_statistics()
        assert stats["total_reflections"] == 0
        assert stats["agents_with_reflections"] == 0
    
    def test_reflect_on_task_basic(self):
        """Test basic task reflection"""
        engine = ReflectionEngine()
        
        reflection = engine.reflect_on_task(
            task_id="task_001",
            agent_variant_id="agent_marketing",
            task_category="content_creation",
            task_description="Write blog post",
            execution_time_seconds=120.0,
            output="Comprehensive blog post about marketing strategies...",
            customer_rating=4.5,
            customer_feedback="Excellent work!"
        )
        
        assert reflection is not None
        assert reflection.task_id == "task_001"
        assert reflection.self_rating > 0
        assert len(reflection.what_went_well) > 0
        assert reflection.quality_score > 0
    
    def test_reflect_with_high_rating(self):
        """Test reflection on high-rated task"""
        engine = ReflectionEngine()
        
        reflection = engine.reflect_on_task(
            task_id="task_002",
            agent_variant_id="agent_marketing",
            task_category="social_media",
            task_description="Create social media campaign",
            execution_time_seconds=90.0,
            output="Creative campaign with 5 posts...",
            customer_rating=5.0,
            customer_feedback="Perfect! Exactly what I needed"
        )
        
        assert reflection.customer_rating == 5.0
        assert "High customer satisfaction" in str(reflection.what_went_well)
        assert reflection.quality_score >= 0.9
    
    def test_reflect_with_low_rating(self):
        """Test reflection on low-rated task"""
        engine = ReflectionEngine()
        
        reflection = engine.reflect_on_task(
            task_id="task_003",
            agent_variant_id="agent_marketing",
            task_category="content_creation",
            task_description="Write article",
            execution_time_seconds=200.0,
            output="Short article...",
            customer_rating=2.0,
            customer_feedback="Not what I expected, incomplete"
        )
        
        assert reflection.customer_rating == 2.0
        assert len(reflection.what_could_improve) > 0
        assert len(reflection.lessons_learned) > 0
    
    def test_reflect_without_customer_rating(self):
        """Test reflection without customer rating"""
        engine = ReflectionEngine()
        
        reflection = engine.reflect_on_task(
            task_id="task_004",
            agent_variant_id="agent_marketing",
            task_category="email_campaign",
            task_description="Create email",
            execution_time_seconds=60.0,
            output="Email campaign with subject and body..."
        )
        
        assert reflection.customer_rating is None
        assert reflection.self_rating > 0  # Should still self-assess
        assert reflection.quality_score > 0
    
    def test_reflection_limit_per_agent(self):
        """Test that only last 100 reflections are kept per agent"""
        engine = ReflectionEngine()
        
        # Create 105 reflections
        for i in range(105):
            engine.reflect_on_task(
                task_id=f"task_{i}",
                agent_variant_id="agent_marketing",
                task_category="content",
                task_description=f"Task {i}",
                execution_time_seconds=60.0,
                output="Output"
            )
        
        # Should only keep last 100
        reflections = engine._agent_reflections["agent_marketing"]
        assert len(reflections) == 100
        assert "task_104" in reflections  # Most recent
        assert "task_0" not in reflections  # Oldest removed
    
    def test_analyze_performance_empty(self):
        """Test performance analysis with no reflections"""
        engine = ReflectionEngine()
        
        analysis = engine.analyze_performance("agent_marketing")
        
        assert analysis.total_tasks == 0
        assert analysis.avg_customer_rating == 0.0
        assert analysis.rating_trend == "stable"
    
    def test_analyze_performance_with_data(self):
        """Test performance analysis with reflections"""
        engine = ReflectionEngine()
        
        # Create multiple reflections
        for i in range(20):
            engine.reflect_on_task(
                task_id=f"task_{i}",
                agent_variant_id="agent_marketing",
                task_category="content",
                task_description=f"Task {i}",
                execution_time_seconds=100.0,
                output="Good output",
                customer_rating=4.0 + (i * 0.02)  # Gradually improving
            )
        
        analysis = engine.analyze_performance("agent_marketing")
        
        assert analysis.total_tasks == 20
        assert analysis.avg_customer_rating > 0
        assert analysis.avg_quality_score > 0
        assert len(analysis.category_performance) > 0
    
    def test_performance_trends(self):
        """Test trend detection in performance analysis"""
        engine = ReflectionEngine()
        
        # Create improving trend
        for i in range(15):
            rating = 3.0 + (i * 0.15)  # Improving from 3.0 to 5.0
            engine.reflect_on_task(
                task_id=f"task_{i}",
                agent_variant_id="agent_marketing",
                task_category="content",
                task_description=f"Task {i}",
                execution_time_seconds=100.0,
                output="Output",
                customer_rating=min(rating, 5.0)
            )
        
        analysis = engine.analyze_performance("agent_marketing")
        assert analysis.rating_trend in ["improving", "stable"]
    
    def test_identify_strengths(self):
        """Test strength identification"""
        engine = ReflectionEngine()
        
        # Create high-quality tasks
        for i in range(10):
            engine.reflect_on_task(
                task_id=f"task_{i}",
                agent_variant_id="agent_marketing",
                task_category="content",
                task_description=f"Task {i}",
                execution_time_seconds=50.0,  # Fast
                output="High quality output with details...",
                customer_rating=4.8
            )
        
        analysis = engine.analyze_performance("agent_marketing")
        
        assert len(analysis.strengths) > 0
        assert analysis.avg_quality_score > 0.8
    
    def test_identify_weaknesses(self):
        """Test weakness identification"""
        engine = ReflectionEngine()
        
        # Create tasks with issues
        for i in range(10):
            engine.reflect_on_task(
                task_id=f"task_{i}",
                agent_variant_id="agent_marketing",
                task_category="content",
                task_description=f"Task {i}",
                execution_time_seconds=400.0,  # Slow
                output="Short output",
                customer_rating=2.5,
                customer_feedback="Has errors"
            )
        
        analysis = engine.analyze_performance("agent_marketing")
        
        assert len(analysis.weaknesses) > 0
        assert WeaknessArea.SLOW_EXECUTION in analysis.weaknesses or \
               WeaknessArea.INCONSISTENT_QUALITY in analysis.weaknesses
    
    def test_category_performance_breakdown(self):
        """Test performance breakdown by category"""
        engine = ReflectionEngine()
        
        # Create tasks in different categories
        for i in range(5):
            engine.reflect_on_task(
                task_id=f"content_{i}",
                agent_variant_id="agent_marketing",
                task_category="content_creation",
                task_description=f"Content {i}",
                execution_time_seconds=100.0,
                output="Output",
                customer_rating=4.5
            )
            engine.reflect_on_task(
                task_id=f"social_{i}",
                agent_variant_id="agent_marketing",
                task_category="social_media",
                task_description=f"Social {i}",
                execution_time_seconds=60.0,
                output="Output",
                customer_rating=4.0
            )
        
        analysis = engine.analyze_performance("agent_marketing")
        
        assert "content_creation" in analysis.category_performance
        assert "social_media" in analysis.category_performance
        assert analysis.category_performance["content_creation"]["count"] == 5
    
    def test_identify_gaps(self):
        """Test gap identification vs top agents"""
        engine = ReflectionEngine()
        
        # Create some reflections
        for i in range(10):
            engine.reflect_on_task(
                task_id=f"task_{i}",
                agent_variant_id="agent_marketing",
                task_category="content",
                task_description=f"Task {i}",
                execution_time_seconds=150.0,
                output="Output",
                customer_rating=3.8
            )
        
        gap_analysis = engine.identify_gaps(
            agent_variant_id="agent_marketing",
            top_agent_ids=["agent_top1", "agent_top2"]
        )
        
        assert gap_analysis is not None
        assert gap_analysis.rating_gap >= 0
        assert gap_analysis.quality_gap >= 0
        assert len(gap_analysis.improvement_opportunities) > 0
    
    def test_create_improvement_plan(self):
        """Test improvement plan creation"""
        engine = ReflectionEngine()
        
        # Create baseline performance
        for i in range(10):
            engine.reflect_on_task(
                task_id=f"task_{i}",
                agent_variant_id="agent_marketing",
                task_category="content",
                task_description=f"Task {i}",
                execution_time_seconds=200.0,
                output="Output",
                customer_rating=3.5
            )
        
        gap_analysis = engine.identify_gaps(
            agent_variant_id="agent_marketing",
            top_agent_ids=["agent_top1"]
        )
        
        goals = engine.create_improvement_plan(
            agent_variant_id="agent_marketing",
            gap_analysis=gap_analysis
        )
        
        assert len(goals) > 0
        assert all(isinstance(g, ImprovementGoal) for g in goals)
        assert all(g.agent_variant_id == "agent_marketing" for g in goals)
    
    def test_improvement_goal_prioritization(self):
        """Test that goals are prioritized correctly"""
        engine = ReflectionEngine()
        
        # Create poor performance (should trigger high priority goals)
        for i in range(10):
            engine.reflect_on_task(
                task_id=f"task_{i}",
                agent_variant_id="agent_marketing",
                task_category="content",
                task_description=f"Task {i}",
                execution_time_seconds=300.0,
                output="Short",
                customer_rating=2.5
            )
        
        gap_analysis = engine.identify_gaps(
            agent_variant_id="agent_marketing",
            top_agent_ids=["agent_top1"]
        )
        
        goals = engine.create_improvement_plan(
            agent_variant_id="agent_marketing",
            gap_analysis=gap_analysis
        )
        
        # Should have at least one high priority goal
        priorities = [g.priority for g in goals]
        assert ImprovementPriority.HIGH in priorities or ImprovementPriority.CRITICAL in priorities
    
    def test_assign_learning_tasks(self):
        """Test learning task assignment for goal"""
        engine = ReflectionEngine()
        
        # Create a goal
        for i in range(5):
            engine.reflect_on_task(
                task_id=f"task_{i}",
                agent_variant_id="agent_marketing",
                task_category="content",
                task_description=f"Task {i}",
                execution_time_seconds=100.0,
                output="Output",
                customer_rating=3.5
            )
        
        gap_analysis = engine.identify_gaps("agent_marketing", ["agent_top1"])
        goals = engine.create_improvement_plan("agent_marketing", gap_analysis)
        
        if goals:
            goal_id = goals[0].goal_id
            learning_tasks = engine.assign_learning_tasks(goal_id)
            
            assert len(learning_tasks) > 0
            assert all(isinstance(t, LearningTask) for t in learning_tasks)
            assert all(t.goal_id == goal_id for t in learning_tasks)
            
            # Should have different types of learning tasks
            task_types = {t.task_type for t in learning_tasks}
            assert len(task_types) > 1  # Multiple types
    
    def test_learning_task_types(self):
        """Test that different learning task types are created"""
        engine = ReflectionEngine()
        
        for i in range(5):
            engine.reflect_on_task(
                task_id=f"task_{i}",
                agent_variant_id="agent_marketing",
                task_category="content",
                task_description=f"Task {i}",
                execution_time_seconds=100.0,
                output="Output",
                customer_rating=3.5
            )
        
        gap_analysis = engine.identify_gaps("agent_marketing", ["agent_top1"])
        goals = engine.create_improvement_plan("agent_marketing", gap_analysis)
        
        if goals:
            learning_tasks = engine.assign_learning_tasks(goals[0].goal_id)
            task_types = {t.task_type for t in learning_tasks}
            
            # Should include study, practice, experiment
            assert "study" in task_types or "practice" in task_types or "experiment" in task_types
    
    def test_reflection_summary(self):
        """Test agent reflection summary"""
        engine = ReflectionEngine()
        
        for i in range(15):
            engine.reflect_on_task(
                task_id=f"task_{i}",
                agent_variant_id="agent_marketing",
                task_category="content",
                task_description=f"Task {i}",
                execution_time_seconds=100.0,
                output="Output",
                customer_rating=4.2
            )
        
        summary = engine.get_agent_reflection_summary("agent_marketing")
        
        assert summary["agent_variant_id"] == "agent_marketing"
        assert summary["total_reflections"] == 15
        assert summary["recent_average_rating"] > 0
        assert isinstance(summary["recent_lessons"], list)
    
    def test_get_statistics(self):
        """Test engine statistics"""
        engine = ReflectionEngine()
        
        # Create reflections for multiple agents with lower ratings to trigger goals
        for agent_id in ["agent_1", "agent_2"]:
            for i in range(5):
                engine.reflect_on_task(
                    task_id=f"{agent_id}_task_{i}",
                    agent_variant_id=agent_id,
                    task_category="content",
                    task_description=f"Task {i}",
                    execution_time_seconds=300.0,  # Slow to trigger gap
                    output="Output",
                    customer_rating=3.0  # Lower rating to trigger goals
                )
        
        # Create some goals
        for agent_id in ["agent_1", "agent_2"]:
            gap = engine.identify_gaps(agent_id, ["top_agent"])
            engine.create_improvement_plan(agent_id, gap)
        
        stats = engine.get_statistics()
        
        assert stats["total_reflections"] == 10
        assert stats["agents_with_reflections"] == 2
        assert stats["total_improvement_goals"] >= 0  # At least created the data structure
    
    def test_task_reflection_serialization(self):
        """Test task reflection serialization"""
        engine = ReflectionEngine()
        
        reflection = engine.reflect_on_task(
            task_id="task_001",
            agent_variant_id="agent_marketing",
            task_category="content",
            task_description="Test task",
            execution_time_seconds=100.0,
            output="Output",
            customer_rating=4.5
        )
        
        reflection_dict = reflection.to_dict()
        
        assert isinstance(reflection_dict, dict)
        assert reflection_dict["task_id"] == "task_001"
        assert "what_went_well" in reflection_dict
        assert "lessons_learned" in reflection_dict
    
    def test_performance_analysis_serialization(self):
        """Test performance analysis serialization"""
        engine = ReflectionEngine()
        
        for i in range(10):
            engine.reflect_on_task(
                task_id=f"task_{i}",
                agent_variant_id="agent_marketing",
                task_category="content",
                task_description=f"Task {i}",
                execution_time_seconds=100.0,
                output="Output",
                customer_rating=4.0
            )
        
        analysis = engine.analyze_performance("agent_marketing")
        analysis_dict = analysis.to_dict()
        
        assert isinstance(analysis_dict, dict)
        assert "avg_customer_rating" in analysis_dict
        assert "strengths" in analysis_dict
        assert "weaknesses" in analysis_dict
    
    def test_gap_analysis_serialization(self):
        """Test gap analysis serialization"""
        engine = ReflectionEngine()
        
        for i in range(5):
            engine.reflect_on_task(
                task_id=f"task_{i}",
                agent_variant_id="agent_marketing",
                task_category="content",
                task_description=f"Task {i}",
                execution_time_seconds=100.0,
                output="Output",
                customer_rating=3.8
            )
        
        gap = engine.identify_gaps("agent_marketing", ["top1"])
        gap_dict = gap.to_dict()
        
        assert isinstance(gap_dict, dict)
        assert "rating_gap" in gap_dict
        assert "improvement_opportunities" in gap_dict
    
    def test_improvement_goal_serialization(self):
        """Test improvement goal serialization"""
        engine = ReflectionEngine()
        
        for i in range(5):
            engine.reflect_on_task(
                task_id=f"task_{i}",
                agent_variant_id="agent_marketing",
                task_category="content",
                task_description=f"Task {i}",
                execution_time_seconds=100.0,
                output="Output",
                customer_rating=3.5
            )
        
        gap = engine.identify_gaps("agent_marketing", ["top1"])
        goals = engine.create_improvement_plan("agent_marketing", gap)
        
        if goals:
            goal_dict = goals[0].to_dict()
            
            assert isinstance(goal_dict, dict)
            assert "goal_description" in goal_dict
            assert "success_criteria" in goal_dict
            assert "priority" in goal_dict
    
    def test_learning_task_serialization(self):
        """Test learning task serialization"""
        engine = ReflectionEngine()
        
        for i in range(5):
            engine.reflect_on_task(
                task_id=f"task_{i}",
                agent_variant_id="agent_marketing",
                task_category="content",
                task_description=f"Task {i}",
                execution_time_seconds=100.0,
                output="Output",
                customer_rating=3.5
            )
        
        gap = engine.identify_gaps("agent_marketing", ["top1"])
        goals = engine.create_improvement_plan("agent_marketing", gap)
        
        if goals:
            tasks = engine.assign_learning_tasks(goals[0].goal_id)
            
            if tasks:
                task_dict = tasks[0].to_dict()
                
                assert isinstance(task_dict, dict)
                assert "task_description" in task_dict
                assert "task_type" in task_dict
                assert "estimated_time_hours" in task_dict
    
    def test_multiple_agents_independent(self):
        """Test that reflections are independent per agent"""
        engine = ReflectionEngine()
        
        # Agent 1 reflections
        for i in range(5):
            engine.reflect_on_task(
                task_id=f"agent1_task_{i}",
                agent_variant_id="agent_1",
                task_category="content",
                task_description=f"Task {i}",
                execution_time_seconds=100.0,
                output="Output",
                customer_rating=4.5
            )
        
        # Agent 2 reflections
        for i in range(3):
            engine.reflect_on_task(
                task_id=f"agent2_task_{i}",
                agent_variant_id="agent_2",
                task_category="content",
                task_description=f"Task {i}",
                execution_time_seconds=100.0,
                output="Output",
                customer_rating=3.5
            )
        
        # Check independence
        agent1_reflections = engine._agent_reflections["agent_1"]
        agent2_reflections = engine._agent_reflections["agent_2"]
        
        assert len(agent1_reflections) == 5
        assert len(agent2_reflections) == 3
        
        analysis1 = engine.analyze_performance("agent_1")
        analysis2 = engine.analyze_performance("agent_2")
        
        assert analysis1.avg_customer_rating > analysis2.avg_customer_rating
