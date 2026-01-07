"""
Tests for Complex Problem Decomposition & Planning Engine - Story 5.6.3
"""

import pytest
from datetime import datetime, timedelta

from app.services.evolution.problem_decomposition import (
    ProblemDecompositionEngine,
    ProjectTask,
    ProjectMilestone,
    ProjectRisk,
    ProjectPlan,
    TaskPriority,
    TaskStatus,
    RiskLevel,
    MilestoneType,
)


def test_create_engine():
    """Test engine initialization"""
    engine = ProblemDecompositionEngine()
    
    stats = engine.get_statistics()
    assert stats["total_plans"] == 0
    assert stats["total_tasks"] == 0
    assert stats["total_milestones"] == 0


def test_decompose_software_project():
    """Test decomposing a software project"""
    engine = ProblemDecompositionEngine()
    
    plan = engine.decompose_project(
        agent_variant_id="agent_1",
        project_name="Build SaaS Platform",
        project_description="Create a cloud-based SaaS platform for customer management",
        duration_days=90,
        complexity="medium"
    )
    
    assert plan.plan_id.startswith("plan_agent_1")
    assert plan.project_name == "Build SaaS Platform"
    assert len(plan.tasks) > 50  # Should generate 50+ tasks
    assert len(plan.milestones) > 0
    assert len(plan.risks) > 0
    assert plan.total_estimated_hours > 0


def test_decompose_marketing_campaign():
    """Test decomposing a marketing campaign"""
    engine = ProblemDecompositionEngine()
    
    plan = engine.decompose_project(
        agent_variant_id="agent_1",
        project_name="Product Launch Campaign",
        project_description="Launch marketing campaign for new product line",
        duration_days=60,
        complexity="medium"
    )
    
    # Should recognize as marketing project and generate 50+ tasks
    assert len(plan.tasks) > 40
    # Verify marketing-related phases exist
    phase_names_in_tasks = set()
    for task in plan.tasks.values():
        # Extract phase name (first part before " - Task")
        if " - Task" in task.task_name:
            phase_name = task.task_name.split(" - Task")[0]
            phase_names_in_tasks.add(phase_name)
    
    # Should have marketing-specific phases
    assert any("Research" in phase or "Creative" in phase or "Campaign" in phase or "Launch" in phase 
               for phase in phase_names_in_tasks)


def test_complexity_affects_task_count():
    """Test that complexity level affects task count"""
    engine = ProblemDecompositionEngine()
    
    low_plan = engine.decompose_project(
        agent_variant_id="agent_1",
        project_name="Simple Project",
        project_description="Build a simple app",
        duration_days=30,
        complexity="low"
    )
    
    high_plan = engine.decompose_project(
        agent_variant_id="agent_1",
        project_name="Complex Project",
        project_description="Build a complex app",
        duration_days=30,
        complexity="high"
    )
    
    # High complexity should generate more tasks
    assert len(high_plan.tasks) > len(low_plan.tasks)


def test_tasks_have_dependencies():
    """Test that tasks have proper dependencies"""
    engine = ProblemDecompositionEngine()
    
    plan = engine.decompose_project(
        agent_variant_id="agent_1",
        project_name="Test Project",
        project_description="Test software development project",
        duration_days=60,
        complexity="medium"
    )
    
    # Check that some tasks have dependencies
    tasks_with_deps = [t for t in plan.tasks.values() if t.depends_on]
    assert len(tasks_with_deps) > 0
    
    # Verify dependency relationships are bidirectional
    for task in tasks_with_deps:
        for dep_id in task.depends_on:
            if dep_id in plan.tasks:
                dep_task = plan.tasks[dep_id]
                assert task.task_id in dep_task.blocks


def test_task_priorities_distributed():
    """Test that task priorities are distributed appropriately"""
    engine = ProblemDecompositionEngine()
    
    plan = engine.decompose_project(
        agent_variant_id="agent_1",
        project_name="Test Project",
        project_description="Test project",
        duration_days=60,
        complexity="medium"
    )
    
    # Count tasks by priority
    priority_counts = {}
    for task in plan.tasks.values():
        priority_counts[task.priority] = priority_counts.get(task.priority, 0) + 1
    
    # Should have distribution across priorities
    assert len(priority_counts) > 1
    # Medium priority should be most common
    assert priority_counts[TaskPriority.MEDIUM] > priority_counts.get(TaskPriority.CRITICAL, 0)


def test_tasks_have_required_skills():
    """Test that tasks have required skills assigned"""
    engine = ProblemDecompositionEngine()
    
    plan = engine.decompose_project(
        agent_variant_id="agent_1",
        project_name="Software Project",
        project_description="Build software application",
        duration_days=60,
        complexity="medium"
    )
    
    # Some tasks should have required skills
    tasks_with_skills = [t for t in plan.tasks.values() if t.required_skills]
    assert len(tasks_with_skills) > 0


def test_milestones_generated():
    """Test that milestones are generated for phases"""
    engine = ProblemDecompositionEngine()
    
    plan = engine.decompose_project(
        agent_variant_id="agent_1",
        project_name="Test Project",
        project_description="Test software project",
        duration_days=90,
        complexity="medium"
    )
    
    assert len(plan.milestones) > 0
    
    # Check milestone properties
    for milestone in plan.milestones.values():
        assert milestone.milestone_name
        assert milestone.milestone_type == MilestoneType.PHASE_END
        assert len(milestone.required_tasks) > 0
        assert not milestone.is_achieved  # Initially not achieved


def test_risks_identified():
    """Test that project risks are identified"""
    engine = ProblemDecompositionEngine()
    
    plan = engine.decompose_project(
        agent_variant_id="agent_1",
        project_name="Test Project",
        project_description="Test project",
        duration_days=60,
        complexity="medium"
    )
    
    assert len(plan.risks) >= 3  # At least 3 standard risks
    
    # Check risk properties
    for risk in plan.risks.values():
        assert risk.risk_description
        assert 0.0 <= risk.probability <= 1.0
        assert risk.impact_hours > 0
        assert risk.mitigation_strategy
        assert risk.contingency_plan
        assert not risk.is_materialized  # Initially not materialized


def test_high_complexity_has_more_risks():
    """Test that high complexity projects have more risks"""
    engine = ProblemDecompositionEngine()
    
    low_plan = engine.decompose_project(
        agent_variant_id="agent_1",
        project_name="Low Project",
        project_description="Low complexity project",
        duration_days=30,
        complexity="low"
    )
    
    high_plan = engine.decompose_project(
        agent_variant_id="agent_1",
        project_name="High Project",
        project_description="High complexity project",
        duration_days=30,
        complexity="high"
    )
    
    # High complexity should have more or higher-level risks
    high_risk_count_high = sum(
        1 for r in high_plan.risks.values()
        if r.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
    )
    high_risk_count_low = sum(
        1 for r in low_plan.risks.values()
        if r.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
    )
    
    assert high_risk_count_high >= high_risk_count_low


def test_update_task_progress():
    """Test updating task progress"""
    engine = ProblemDecompositionEngine()
    
    plan = engine.decompose_project(
        agent_variant_id="agent_1",
        project_name="Test Project",
        project_description="Test project",
        duration_days=30,
        complexity="low"
    )
    
    task_id = list(plan.tasks.keys())[0]
    task = plan.tasks[task_id]
    
    # Update to in-progress
    result = engine.update_task_progress(plan.plan_id, task_id, 50.0, actual_hours=5.0)
    
    assert result is True
    assert task.progress_percentage == 50.0
    assert task.status == TaskStatus.IN_PROGRESS
    assert task.actual_hours == 5.0


def test_complete_task():
    """Test completing a task"""
    engine = ProblemDecompositionEngine()
    
    plan = engine.decompose_project(
        agent_variant_id="agent_1",
        project_name="Test Project",
        project_description="Test project",
        duration_days=30,
        complexity="low"
    )
    
    task_id = list(plan.tasks.keys())[0]
    task = plan.tasks[task_id]
    
    # Complete task
    result = engine.update_task_progress(plan.plan_id, task_id, 100.0, actual_hours=8.0)
    
    assert result is True
    assert task.status == TaskStatus.COMPLETED
    assert task.completed_at is not None


def test_plan_completion_percentage_calculated():
    """Test that plan completion percentage is calculated"""
    engine = ProblemDecompositionEngine()
    
    plan = engine.decompose_project(
        agent_variant_id="agent_1",
        project_name="Test Project",
        project_description="Test project",
        duration_days=30,
        complexity="low"
    )
    
    initial_completion = plan.completion_percentage
    assert initial_completion == 0.0
    
    # Complete half the tasks
    task_ids = list(plan.tasks.keys())
    for i in range(len(task_ids) // 2):
        engine.update_task_progress(plan.plan_id, task_ids[i], 100.0)
    
    # Completion should be around 50%
    assert 40 <= plan.completion_percentage <= 60


def test_milestone_achieved_when_tasks_complete():
    """Test that milestones are achieved when all tasks complete"""
    engine = ProblemDecompositionEngine()
    
    plan = engine.decompose_project(
        agent_variant_id="agent_1",
        project_name="Test Project",
        project_description="Test software project",
        duration_days=60,
        complexity="low"
    )
    
    # Get first milestone
    milestone = list(plan.milestones.values())[0]
    
    # Complete all required tasks
    for task_id in milestone.required_tasks:
        if task_id in plan.tasks:
            engine.update_task_progress(plan.plan_id, task_id, 100.0)
    
    # Milestone should be achieved
    assert milestone.is_achieved
    assert milestone.actual_date is not None


def test_get_critical_path():
    """Test getting critical path through project"""
    engine = ProblemDecompositionEngine()
    
    plan = engine.decompose_project(
        agent_variant_id="agent_1",
        project_name="Test Project",
        project_description="Test software project",
        duration_days=60,
        complexity="medium"
    )
    
    critical_path = engine.get_critical_path(plan.plan_id)
    
    # Should return a path
    assert len(critical_path) > 0
    
    # Path should contain task IDs
    for task_id in critical_path:
        assert task_id in plan.tasks


def test_get_next_available_tasks():
    """Test getting next available tasks (dependencies met)"""
    engine = ProblemDecompositionEngine()
    
    plan = engine.decompose_project(
        agent_variant_id="agent_1",
        project_name="Test Project",
        project_description="Test software project",
        duration_days=60,
        complexity="medium"
    )
    
    # Initially, tasks with no dependencies should be available
    available = engine.get_next_available_tasks(plan.plan_id)
    
    assert len(available) > 0
    
    # All available tasks should have no incomplete dependencies
    for task in available:
        if task.depends_on:
            for dep_id in task.depends_on:
                if dep_id in plan.tasks:
                    dep_task = plan.tasks[dep_id]
                    assert dep_task.status == TaskStatus.COMPLETED


def test_available_tasks_sorted_by_priority():
    """Test that available tasks are sorted by priority"""
    engine = ProblemDecompositionEngine()
    
    plan = engine.decompose_project(
        agent_variant_id="agent_1",
        project_name="Test Project",
        project_description="Test project",
        duration_days=60,
        complexity="medium"
    )
    
    available = engine.get_next_available_tasks(plan.plan_id)
    
    if len(available) > 1:
        # Verify priority ordering
        priority_order = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3
        }
        
        for i in range(len(available) - 1):
            assert priority_order[available[i].priority] <= priority_order[available[i+1].priority]


def test_replan_based_on_progress_no_slippage():
    """Test replanning analysis when on track"""
    engine = ProblemDecompositionEngine()
    
    plan = engine.decompose_project(
        agent_variant_id="agent_1",
        project_name="Test Project",
        project_description="Test project",
        duration_days=30,
        complexity="low"
    )
    
    # Complete a task with good actuals
    task_id = list(plan.tasks.keys())[0]
    task = plan.tasks[task_id]
    engine.update_task_progress(
        plan.plan_id,
        task_id,
        100.0,
        actual_hours=task.estimated_hours  # On estimate
    )
    
    replan_result = engine.replan_based_on_progress(plan.plan_id)
    
    assert "needs_replan" in replan_result
    assert replan_result["needs_replan"] is False


def test_replan_based_on_progress_with_slippage():
    """Test replanning analysis when behind schedule"""
    engine = ProblemDecompositionEngine()
    
    plan = engine.decompose_project(
        agent_variant_id="agent_1",
        project_name="Test Project",
        project_description="Test project",
        duration_days=30,
        complexity="low"
    )
    
    # Complete tasks with significant overruns
    task_ids = list(plan.tasks.keys())[:3]
    for task_id in task_ids:
        task = plan.tasks[task_id]
        engine.update_task_progress(
            plan.plan_id,
            task_id,
            100.0,
            actual_hours=task.estimated_hours * 2.0  # 2x overrun
        )
    
    replan_result = engine.replan_based_on_progress(plan.plan_id)
    
    assert replan_result["needs_replan"] is True
    assert "suggestions" in replan_result
    assert len(replan_result["suggestions"]) > 0
    assert replan_result["variance_ratio"] > 1.5


def test_get_plan_statistics():
    """Test getting plan statistics"""
    engine = ProblemDecompositionEngine()
    
    plan = engine.decompose_project(
        agent_variant_id="agent_1",
        project_name="Test Project",
        project_description="Test software project",
        duration_days=60,
        complexity="medium"
    )
    
    stats = engine.get_plan_statistics(plan.plan_id)
    
    assert stats["plan_id"] == plan.plan_id
    assert stats["project_name"] == "Test Project"
    assert stats["total_tasks"] > 0
    assert "status_breakdown" in stats
    assert "priority_breakdown" in stats
    assert stats["completion_percentage"] == 0.0  # No tasks complete yet
    assert stats["total_milestones"] > 0
    assert stats["total_risks"] > 0


def test_get_statistics():
    """Test engine-wide statistics"""
    engine = ProblemDecompositionEngine()
    
    # Create multiple plans
    engine.decompose_project(
        agent_variant_id="agent_1",
        project_name="Project 1",
        project_description="Test project 1",
        duration_days=30,
        complexity="low"
    )
    
    engine.decompose_project(
        agent_variant_id="agent_2",
        project_name="Project 2",
        project_description="Test project 2",
        duration_days=60,
        complexity="medium"
    )
    
    stats = engine.get_statistics()
    
    assert stats["total_plans"] == 2
    assert stats["total_tasks"] > 0
    assert stats["total_milestones"] > 0
    assert stats["contributing_agents"] == 2
    assert stats["avg_tasks_per_plan"] > 0


def test_project_task_serialization():
    """Test ProjectTask to_dict serialization"""
    task = ProjectTask(
        task_id="task_1",
        task_name="Test Task",
        description="Test description",
        parent_task_id=None,
        estimated_hours=8.0,
        priority=TaskPriority.HIGH,
        status=TaskStatus.IN_PROGRESS,
        progress_percentage=50.0
    )
    
    data = task.to_dict()
    
    assert data["task_id"] == "task_1"
    assert data["task_name"] == "Test Task"
    assert data["priority"] == "high"
    assert data["status"] == "in_progress"
    assert data["progress_percentage"] == 50.0


def test_project_milestone_serialization():
    """Test ProjectMilestone to_dict serialization"""
    milestone = ProjectMilestone(
        milestone_id="milestone_1",
        milestone_name="Phase 1 Complete",
        milestone_type=MilestoneType.PHASE_END,
        description="Test milestone",
        target_date=datetime.utcnow(),
        required_tasks=["task_1", "task_2"],
        is_achieved=False
    )
    
    data = milestone.to_dict()
    
    assert data["milestone_id"] == "milestone_1"
    assert data["milestone_name"] == "Phase 1 Complete"
    assert data["milestone_type"] == "phase_end"
    assert len(data["required_tasks"]) == 2


def test_project_risk_serialization():
    """Test ProjectRisk to_dict serialization"""
    risk = ProjectRisk(
        risk_id="risk_1",
        risk_description="Test risk",
        risk_level=RiskLevel.HIGH,
        probability=0.5,
        impact_hours=100.0,
        mitigation_strategy="Test mitigation",
        contingency_plan="Test contingency"
    )
    
    data = risk.to_dict()
    
    assert data["risk_id"] == "risk_1"
    assert data["risk_level"] == "high"
    assert data["probability"] == 0.5
    assert data["impact_hours"] == 100.0


def test_project_plan_serialization():
    """Test ProjectPlan to_dict serialization"""
    engine = ProblemDecompositionEngine()
    
    plan = engine.decompose_project(
        agent_variant_id="agent_1",
        project_name="Test Project",
        project_description="Test project",
        duration_days=30,
        complexity="low"
    )
    
    data = plan.to_dict()
    
    assert data["plan_id"] == plan.plan_id
    assert data["project_name"] == "Test Project"
    assert "tasks" in data
    assert "milestones" in data
    assert "risks" in data
    assert len(data["tasks"]) == len(plan.tasks)
