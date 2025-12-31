"""
Tests for multi-agent orchestration
"""

import pytest
from datetime import datetime

from app.services.specialization.orchestration import (
    TaskStatus,
    AgentRole,
    SubTask,
    WorkflowExecution,
    TaskDecomposer,
    ResultAggregator,
    AgentOrchestrator,
)
from app.services.specialization.agent_variants import AgentVariantRegistry


class TestSubTask:
    """Tests for SubTask"""
    
    def test_create_subtask(self):
        """Test creating subtask"""
        task = SubTask(
            id="task-1",
            description="Create blog post",
            agent_variant_id="content_creation_agent",
            dependencies=["task-0"]
        )
        
        assert task.id == "task-1"
        assert task.description == "Create blog post"
        assert task.agent_variant_id == "content_creation_agent"
        assert task.dependencies == ["task-0"]
        assert task.status == TaskStatus.PENDING
        assert task.result is None
    
    def test_subtask_to_dict(self):
        """Test subtask serialization"""
        task = SubTask(
            id="task-1",
            description="Test task",
            agent_variant_id="test_agent"
        )
        
        data = task.to_dict()
        
        assert data["id"] == "task-1"
        assert data["description"] == "Test task"
        assert data["agent_variant_id"] == "test_agent"
        assert data["status"] == "pending"


class TestWorkflowExecution:
    """Tests for WorkflowExecution"""
    
    def test_create_workflow(self):
        """Test creating workflow execution"""
        subtasks = [
            SubTask(id="1", description="Task 1", agent_variant_id="agent1"),
            SubTask(id="2", description="Task 2", agent_variant_id="agent2", dependencies=["1"])
        ]
        
        workflow = WorkflowExecution(
            id="workflow-1",
            original_task="Complete project",
            subtasks=subtasks,
            status=TaskStatus.PENDING
        )
        
        assert workflow.id == "workflow-1"
        assert workflow.original_task == "Complete project"
        assert len(workflow.subtasks) == 2
        assert workflow.status == TaskStatus.PENDING
    
    def test_get_ready_tasks_no_dependencies(self):
        """Test getting ready tasks with no dependencies"""
        subtasks = [
            SubTask(id="1", description="Task 1", agent_variant_id="agent1"),
            SubTask(id="2", description="Task 2", agent_variant_id="agent2")
        ]
        
        workflow = WorkflowExecution(
            id="workflow-1",
            original_task="Test",
            subtasks=subtasks,
            status=TaskStatus.PENDING
        )
        
        ready = workflow.get_ready_tasks()
        
        assert len(ready) == 2
        assert ready[0].id == "1"
        assert ready[1].id == "2"
    
    def test_get_ready_tasks_with_dependencies(self):
        """Test getting ready tasks with dependencies"""
        subtasks = [
            SubTask(id="1", description="Task 1", agent_variant_id="agent1"),
            SubTask(id="2", description="Task 2", agent_variant_id="agent2", dependencies=["1"]),
            SubTask(id="3", description="Task 3", agent_variant_id="agent3", dependencies=["1", "2"])
        ]
        
        workflow = WorkflowExecution(
            id="workflow-1",
            original_task="Test",
            subtasks=subtasks,
            status=TaskStatus.PENDING
        )
        
        # Initially only task 1 is ready
        ready = workflow.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].id == "1"
        
        # Complete task 1
        subtasks[0].status = TaskStatus.COMPLETED
        
        # Now task 2 is ready
        ready = workflow.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].id == "2"
        
        # Complete task 2
        subtasks[1].status = TaskStatus.COMPLETED
        
        # Now task 3 is ready
        ready = workflow.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].id == "3"
    
    def test_is_complete(self):
        """Test workflow completion check"""
        subtasks = [
            SubTask(id="1", description="Task 1", agent_variant_id="agent1"),
            SubTask(id="2", description="Task 2", agent_variant_id="agent2")
        ]
        
        workflow = WorkflowExecution(
            id="workflow-1",
            original_task="Test",
            subtasks=subtasks,
            status=TaskStatus.PENDING
        )
        
        assert not workflow.is_complete()
        
        subtasks[0].status = TaskStatus.COMPLETED
        assert not workflow.is_complete()
        
        subtasks[1].status = TaskStatus.COMPLETED
        assert workflow.is_complete()
    
    def test_has_failures(self):
        """Test failure detection"""
        subtasks = [
            SubTask(id="1", description="Task 1", agent_variant_id="agent1"),
            SubTask(id="2", description="Task 2", agent_variant_id="agent2")
        ]
        
        workflow = WorkflowExecution(
            id="workflow-1",
            original_task="Test",
            subtasks=subtasks,
            status=TaskStatus.PENDING
        )
        
        assert not workflow.has_failures()
        
        subtasks[0].status = TaskStatus.FAILED
        assert workflow.has_failures()


class TestTaskDecomposer:
    """Tests for TaskDecomposer"""
    
    def test_create_decomposer(self):
        """Test creating task decomposer"""
        registry = AgentVariantRegistry()
        decomposer = TaskDecomposer(registry)
        
        assert decomposer is not None
    
    def test_decompose_simple_task(self):
        """Test decomposing simple task (single agent)"""
        registry = AgentVariantRegistry()
        decomposer = TaskDecomposer(registry)
        
        subtasks = decomposer.decompose("Write a blog post about AI")
        
        assert len(subtasks) == 1
        assert subtasks[0].agent_variant_id == "content_creation_agent"
        assert len(subtasks[0].dependencies) == 0
    
    def test_decompose_campaign_creation(self):
        """Test decomposing campaign creation task"""
        registry = AgentVariantRegistry()
        decomposer = TaskDecomposer(registry)
        
        subtasks = decomposer.decompose("Launch a marketing campaign for our new product")
        
        assert len(subtasks) == 3
        # Should have strategy, SEO, and content creation subtasks
        assert any("strategy" in t.description.lower() for t in subtasks)
        assert any("seo" in t.description.lower() for t in subtasks)
        assert any("content" in t.description.lower() for t in subtasks)
    
    def test_decompose_learning_project(self):
        """Test decomposing learning project task"""
        registry = AgentVariantRegistry()
        decomposer = TaskDecomposer(registry)
        
        subtasks = decomposer.decompose("Learn advanced mathematics for data science")
        
        assert len(subtasks) == 3
        # Should have learning plan, resources, and assessment
        assert any("plan" in t.description.lower() for t in subtasks)
        assert any("resource" in t.description.lower() for t in subtasks)
        assert any("assessment" in t.description.lower() for t in subtasks)
    
    def test_decompose_sales_sequence(self):
        """Test decomposing sales sequence task"""
        registry = AgentVariantRegistry()
        decomposer = TaskDecomposer(registry)
        
        subtasks = decomposer.decompose("Create a sales sequence for enterprise leads")
        
        assert len(subtasks) == 2
        # Should have qualification and outreach
        assert any("qualif" in t.description.lower() for t in subtasks)
        assert any("outreach" in t.description.lower() for t in subtasks)
    
    def test_subtask_dependencies(self):
        """Test that subtasks have correct dependencies"""
        registry = AgentVariantRegistry()
        decomposer = TaskDecomposer(registry)
        
        subtasks = decomposer.decompose("Launch a marketing campaign")
        
        # First task should have no dependencies
        assert len(subtasks[0].dependencies) == 0
        
        # Later tasks should depend on earlier ones
        for task in subtasks[1:]:
            assert len(task.dependencies) > 0


class TestResultAggregator:
    """Tests for ResultAggregator"""
    
    def test_create_aggregator(self):
        """Test creating result aggregator"""
        aggregator = ResultAggregator()
        assert aggregator is not None
    
    def test_aggregate_empty_results(self):
        """Test aggregating empty results"""
        aggregator = ResultAggregator()
        
        result = aggregator.aggregate([])
        
        assert result == {}
    
    def test_merge_results(self):
        """Test merging results"""
        aggregator = ResultAggregator()
        
        results = [
            {"strategy": "content marketing", "budget": 10000},
            {"channels": ["linkedin", "twitter"], "timeline": "3 months"},
            {"metrics": ["reach", "engagement"]}
        ]
        
        merged = aggregator.aggregate(results, aggregation_strategy="merge")
        
        assert "strategy" in merged
        assert "channels" in merged
        assert "metrics" in merged
        assert "budget" in merged
        assert "timeline" in merged
    
    def test_merge_conflicting_results(self):
        """Test merging results with conflicts"""
        aggregator = ResultAggregator()
        
        results = [
            {"priority": "high", "score": 0.9},
            {"priority": "medium", "score": 0.7}
        ]
        
        merged = aggregator.aggregate(results, aggregation_strategy="merge")
        
        # Conflicting values should be kept as list
        assert "priority" in merged
        assert "score" in merged
    
    def test_vote_on_results(self):
        """Test voting on results"""
        aggregator = ResultAggregator()
        
        results = [
            {"category": "marketing", "priority": "high"},
            {"category": "marketing", "priority": "medium"},
            {"category": "marketing", "priority": "high"}
        ]
        
        voted = aggregator.aggregate(results, aggregation_strategy="vote")
        
        # "high" appears twice, "medium" once
        assert voted["priority"] == "high"
        assert voted["category"] == "marketing"
    
    def test_priority_results(self):
        """Test priority-based aggregation"""
        aggregator = ResultAggregator()
        
        results = [
            {"strategy": "content", "budget": 10000, "primary": True},
            {"channels": ["linkedin"], "budget": 5000},
            {"metrics": ["reach"]}
        ]
        
        prioritized = aggregator.aggregate(results, aggregation_strategy="priority")
        
        # First result takes precedence for conflicts
        assert prioritized["strategy"] == "content"
        assert prioritized["budget"] == 10000
        assert prioritized["primary"] == True
        # Non-conflicting keys are included
        assert "channels" in prioritized
        assert "metrics" in prioritized


class TestAgentOrchestrator:
    """Tests for AgentOrchestrator"""
    
    def test_create_orchestrator(self):
        """Test creating orchestrator"""
        orchestrator = AgentOrchestrator()
        assert orchestrator is not None
    
    def test_create_workflow(self):
        """Test creating workflow"""
        orchestrator = AgentOrchestrator()
        
        workflow = orchestrator.create_workflow("Write a blog post about AI")
        
        assert workflow is not None
        assert workflow.id is not None
        assert workflow.original_task == "Write a blog post about AI"
        assert len(workflow.subtasks) > 0
        assert workflow.status == TaskStatus.PENDING
    
    def test_execute_simple_workflow(self):
        """Test executing simple workflow"""
        orchestrator = AgentOrchestrator()
        
        workflow = orchestrator.create_workflow("Write a blog post")
        
        # Execute workflow with mock executor
        def mock_executor(task):
            return {"result": f"Completed {task.description}"}
        
        executed = orchestrator.execute_workflow(workflow.id, mock_executor)
        
        assert executed.status == TaskStatus.COMPLETED
        assert all(t.status == TaskStatus.COMPLETED for t in executed.subtasks)
        assert executed.final_result is not None
    
    def test_execute_complex_workflow(self):
        """Test executing complex workflow with dependencies"""
        orchestrator = AgentOrchestrator()
        
        workflow = orchestrator.create_workflow("Launch a marketing campaign")
        
        # Should have multiple subtasks
        assert len(workflow.subtasks) > 1
        
        # Execute workflow
        def mock_executor(task):
            return {"task": task.description, "completed": True}
        
        executed = orchestrator.execute_workflow(workflow.id, mock_executor)
        
        assert executed.status == TaskStatus.COMPLETED
        assert all(t.status == TaskStatus.COMPLETED for t in executed.subtasks)
        assert executed.final_result is not None
    
    def test_workflow_dependency_order(self):
        """Test that workflow executes in correct dependency order"""
        orchestrator = AgentOrchestrator()
        
        workflow = orchestrator.create_workflow("Launch a marketing campaign")
        
        execution_order = []
        
        def tracking_executor(task):
            execution_order.append(task.id)
            return {"task": task.id}
        
        orchestrator.execute_workflow(workflow.id, tracking_executor)
        
        # Verify dependencies were respected
        for task in workflow.subtasks:
            if task.dependencies:
                task_index = execution_order.index(task.id)
                for dep_id in task.dependencies:
                    dep_index = execution_order.index(dep_id)
                    assert dep_index < task_index, f"Dependency {dep_id} should execute before {task.id}"
    
    def test_get_execution(self):
        """Test getting workflow execution"""
        orchestrator = AgentOrchestrator()
        
        workflow = orchestrator.create_workflow("Test task")
        
        retrieved = orchestrator.get_execution(workflow.id)
        
        assert retrieved is not None
        assert retrieved.id == workflow.id
    
    def test_list_executions(self):
        """Test listing workflow executions"""
        orchestrator = AgentOrchestrator()
        
        workflow1 = orchestrator.create_workflow("Task 1")
        workflow2 = orchestrator.create_workflow("Task 2")
        
        executions = orchestrator.list_executions()
        
        assert len(executions) >= 2
        assert any(e.id == workflow1.id for e in executions)
        assert any(e.id == workflow2.id for e in executions)
    
    def test_list_executions_by_status(self):
        """Test filtering executions by status"""
        orchestrator = AgentOrchestrator()
        
        workflow1 = orchestrator.create_workflow("Task 1")
        workflow2 = orchestrator.create_workflow("Task 2")
        
        # Execute one workflow
        orchestrator.execute_workflow(workflow1.id)
        
        pending = orchestrator.list_executions(status=TaskStatus.PENDING)
        completed = orchestrator.list_executions(status=TaskStatus.COMPLETED)
        
        assert any(e.id == workflow2.id for e in pending)
        assert any(e.id == workflow1.id for e in completed)
    
    def test_get_execution_summary(self):
        """Test getting execution summary"""
        orchestrator = AgentOrchestrator()
        
        workflow = orchestrator.create_workflow("Launch a campaign")
        orchestrator.execute_workflow(workflow.id)
        
        summary = orchestrator.get_execution_summary(workflow.id)
        
        assert summary["id"] == workflow.id
        assert "total_subtasks" in summary
        assert "completed_subtasks" in summary
        assert "agents_involved" in summary
        assert summary["has_result"] == True
    
    def test_workflow_with_failures(self):
        """Test workflow handling failures"""
        orchestrator = AgentOrchestrator()
        
        workflow = orchestrator.create_workflow("Test task")
        
        # Executor that fails
        def failing_executor(task):
            raise Exception("Task failed")
        
        executed = orchestrator.execute_workflow(workflow.id, failing_executor)
        
        assert executed.status == TaskStatus.FAILED
        assert executed.has_failures()
    
    def test_result_aggregation(self):
        """Test that results are properly aggregated"""
        orchestrator = AgentOrchestrator()
        
        workflow = orchestrator.create_workflow("Launch a campaign")
        
        # Executor returns different results per task
        task_results = {}
        
        def mock_executor(task):
            result = {"task_id": task.id, "data": f"data_{task.id}"}
            task_results[task.id] = result
            return result
        
        executed = orchestrator.execute_workflow(workflow.id, mock_executor)
        
        # Final result should aggregate all task results
        assert executed.final_result is not None
        assert len(executed.final_result) > 0
