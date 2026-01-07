"""
Tests for Dependency Resolution

Validates DAG construction, cycle detection, topological sort,
and execution plan generation.
"""

import pytest

from waooaw.orchestration import (
    DependencyGraph,
    TaskNode,
    ExecutionPlan,
    CyclicDependencyError,
    InvalidDependencyError,
    DependencyNotSatisfiedError,
)


class TestTaskNode:
    """Test TaskNode dataclass"""

    def test_create_node(self):
        """Should create node with dependencies"""
        node = TaskNode(
            task_id="task-1", dependencies={"task-0"}, dependents={"task-2"}
        )

        assert node.task_id == "task-1"
        assert node.dependencies == {"task-0"}
        assert node.dependents == {"task-2"}
        assert node.completed is False
        assert node.in_degree == 0  # Set manually after creation

    def test_node_equality(self):
        """Should check equality by task_id"""
        node1 = TaskNode(task_id="task-1")
        node2 = TaskNode(task_id="task-1")
        node3 = TaskNode(task_id="task-2")

        assert node1 == node2
        assert node1 != node3

    def test_node_hash(self):
        """Should hash by task_id"""
        node = TaskNode(task_id="task-1")
        assert hash(node) == hash("task-1")


class TestExecutionPlan:
    """Test ExecutionPlan dataclass"""

    def test_create_plan(self):
        """Should create execution plan"""
        plan = ExecutionPlan(
            execution_order=["task-1", "task-2", "task-3"],
            levels=[{"task-1"}, {"task-2", "task-3"}],
            total_tasks=3,
            max_parallel_tasks=2,
        )

        assert plan.execution_order == ["task-1", "task-2", "task-3"]
        assert plan.levels == [{"task-1"}, {"task-2", "task-3"}]
        assert plan.total_tasks == 3
        assert plan.max_parallel_tasks == 2

    def test_get_next_batch_first_level(self):
        """Should return first level when no tasks completed"""
        plan = ExecutionPlan(
            execution_order=["task-1", "task-2", "task-3"],
            levels=[{"task-1"}, {"task-2", "task-3"}],
            total_tasks=3,
            max_parallel_tasks=2,
        )

        next_batch = plan.get_next_batch(completed_tasks=set())
        assert next_batch == {"task-1"}

    def test_get_next_batch_second_level(self):
        """Should return second level after first completed"""
        plan = ExecutionPlan(
            execution_order=["task-1", "task-2", "task-3"],
            levels=[{"task-1"}, {"task-2", "task-3"}],
            total_tasks=3,
            max_parallel_tasks=2,
        )

        next_batch = plan.get_next_batch(completed_tasks={"task-1"})
        assert next_batch == {"task-2", "task-3"}

    def test_get_next_batch_partial_completion(self):
        """Should return remaining tasks in level"""
        plan = ExecutionPlan(
            execution_order=["task-1", "task-2", "task-3"],
            levels=[{"task-1"}, {"task-2", "task-3"}],
            total_tasks=3,
            max_parallel_tasks=2,
        )

        next_batch = plan.get_next_batch(completed_tasks={"task-1", "task-2"})
        assert next_batch == {"task-3"}

    def test_get_next_batch_all_complete(self):
        """Should return empty set when all complete"""
        plan = ExecutionPlan(
            execution_order=["task-1", "task-2"],
            levels=[{"task-1"}, {"task-2"}],
            total_tasks=2,
            max_parallel_tasks=1,
        )

        next_batch = plan.get_next_batch(completed_tasks={"task-1", "task-2"})
        assert next_batch == set()


class TestDependencyGraph:
    """Test DependencyGraph operations"""

    def test_create_graph(self):
        """Should create empty graph"""
        graph = DependencyGraph()
        stats = graph.get_stats()

        assert stats["total_tasks"] == 0
        assert stats["completed_tasks"] == 0

    def test_add_task_no_dependencies(self):
        """Should add task without dependencies"""
        graph = DependencyGraph()
        graph.add_task("task-1")

        stats = graph.get_stats()
        assert stats["total_tasks"] == 1
        assert stats["ready_tasks"] == 1

    def test_add_task_with_dependencies(self):
        """Should add task with dependencies"""
        graph = DependencyGraph()
        graph.add_task("task-1")
        graph.add_task("task-2", dependencies={"task-1"})

        stats = graph.get_stats()
        assert stats["total_tasks"] == 2
        assert stats["ready_tasks"] == 1  # Only task-1 ready
        assert stats["pending_tasks"] == 1  # task-2 pending

    def test_add_task_updates_dependents(self):
        """Should update dependents when adding task with dependencies"""
        graph = DependencyGraph()
        graph.add_task("task-1")
        graph.add_task("task-2", dependencies={"task-1"})

        dependents = graph.get_task_dependents("task-1")
        assert dependents == {"task-2"}

    def test_add_duplicate_task(self):
        """Should raise error for duplicate task"""
        graph = DependencyGraph()
        graph.add_task("task-1")

        with pytest.raises(ValueError, match="already exists"):
            graph.add_task("task-1")

    def test_remove_task(self):
        """Should remove task from graph"""
        graph = DependencyGraph()
        graph.add_task("task-1")
        graph.add_task("task-2", dependencies={"task-1"})

        graph.remove_task("task-2")

        stats = graph.get_stats()
        assert stats["total_tasks"] == 1
        assert graph.get_task_dependents("task-1") == set()

    def test_remove_task_updates_dependents(self):
        """Should update dependent in_degree when removing dependency"""
        graph = DependencyGraph()
        graph.add_task("task-1")
        graph.add_task("task-2")
        graph.add_task("task-3", dependencies={"task-1", "task-2"})

        # Remove task-1 (dependency of task-3)
        graph.remove_task("task-1")

        # task-3 should now only depend on task-2
        deps = graph.get_task_dependencies("task-3")
        assert deps == {"task-2"}

    def test_remove_nonexistent_task(self):
        """Should raise error for non-existent task"""
        graph = DependencyGraph()

        with pytest.raises(KeyError, match="not found"):
            graph.remove_task("task-1")

    def test_validate_success(self):
        """Should validate valid graph"""
        graph = DependencyGraph()
        graph.add_task("task-1")
        graph.add_task("task-2", dependencies={"task-1"})
        graph.add_task("task-3", dependencies={"task-2"})

        # Should not raise
        graph.validate()

    def test_validate_invalid_dependency(self):
        """Should raise error for non-existent dependency"""
        graph = DependencyGraph()
        graph.add_task("task-1", dependencies={"non-existent"})

        with pytest.raises(InvalidDependencyError, match="non-existent task"):
            graph.validate()

    def test_validate_cycle_detection(self):
        """Should detect circular dependencies"""
        graph = DependencyGraph()
        graph.add_task("task-1")
        graph.add_task("task-2")
        graph.add_task("task-3")

        # Create cycle: task-1 -> task-2 -> task-3 -> task-1
        graph._nodes["task-1"].dependents.add("task-2")
        graph._nodes["task-2"].dependents.add("task-3")
        graph._nodes["task-3"].dependents.add("task-1")

        with pytest.raises(CyclicDependencyError, match="Cyclic dependency"):
            graph.validate()

    def test_topological_sort_linear(self):
        """Should sort linear dependency chain"""
        graph = DependencyGraph()
        graph.add_task("task-1")
        graph.add_task("task-2", dependencies={"task-1"})
        graph.add_task("task-3", dependencies={"task-2"})

        order = graph.topological_sort()
        assert order == ["task-1", "task-2", "task-3"]

    def test_topological_sort_parallel(self):
        """Should sort graph with parallel tasks"""
        graph = DependencyGraph()
        graph.add_task("task-1")
        graph.add_task("task-2")
        graph.add_task("task-3", dependencies={"task-1", "task-2"})

        order = graph.topological_sort()
        # task-1 and task-2 can be in any order, but both before task-3
        assert len(order) == 3
        assert order[-1] == "task-3"
        assert set(order[:2]) == {"task-1", "task-2"}

    def test_topological_sort_diamond(self):
        """Should sort diamond-shaped dependency graph"""
        graph = DependencyGraph()
        graph.add_task("task-1")
        graph.add_task("task-2", dependencies={"task-1"})
        graph.add_task("task-3", dependencies={"task-1"})
        graph.add_task("task-4", dependencies={"task-2", "task-3"})

        order = graph.topological_sort()
        assert order[0] == "task-1"
        assert order[-1] == "task-4"
        assert set(order[1:3]) == {"task-2", "task-3"}

    def test_topological_sort_cycle(self):
        """Should raise error for cyclic graph"""
        graph = DependencyGraph()
        graph.add_task("task-1")
        graph.add_task("task-2", dependencies={"task-1"})

        # Create cycle
        graph._nodes["task-1"].dependencies.add("task-2")
        graph._nodes["task-1"].in_degree = 1
        graph._nodes["task-2"].dependents.add("task-1")

        with pytest.raises(CyclicDependencyError):
            graph.topological_sort()

    def test_get_execution_plan_linear(self):
        """Should create execution plan for linear graph"""
        graph = DependencyGraph()
        graph.add_task("task-1")
        graph.add_task("task-2", dependencies={"task-1"})
        graph.add_task("task-3", dependencies={"task-2"})

        plan = graph.get_execution_plan()
        assert plan.total_tasks == 3
        assert plan.max_parallel_tasks == 1
        assert len(plan.levels) == 3
        assert plan.levels[0] == {"task-1"}
        assert plan.levels[1] == {"task-2"}
        assert plan.levels[2] == {"task-3"}

    def test_get_execution_plan_parallel(self):
        """Should identify parallel tasks in execution plan"""
        graph = DependencyGraph()
        graph.add_task("task-1")
        graph.add_task("task-2")
        graph.add_task("task-3")
        graph.add_task("task-4", dependencies={"task-1", "task-2", "task-3"})

        plan = graph.get_execution_plan()
        assert plan.total_tasks == 4
        assert plan.max_parallel_tasks == 3
        assert len(plan.levels) == 2
        assert plan.levels[0] == {"task-1", "task-2", "task-3"}
        assert plan.levels[1] == {"task-4"}

    def test_get_execution_plan_diamond(self):
        """Should handle diamond dependency in execution plan"""
        graph = DependencyGraph()
        graph.add_task("task-1")
        graph.add_task("task-2", dependencies={"task-1"})
        graph.add_task("task-3", dependencies={"task-1"})
        graph.add_task("task-4", dependencies={"task-2", "task-3"})

        plan = graph.get_execution_plan()
        assert plan.total_tasks == 4
        assert plan.max_parallel_tasks == 2
        assert len(plan.levels) == 3
        assert plan.levels[0] == {"task-1"}
        assert plan.levels[1] == {"task-2", "task-3"}
        assert plan.levels[2] == {"task-4"}

    def test_mark_completed_success(self):
        """Should mark task completed and return ready tasks"""
        graph = DependencyGraph()
        graph.add_task("task-1")
        graph.add_task("task-2", dependencies={"task-1"})
        graph.add_task("task-3", dependencies={"task-1"})

        ready = graph.mark_completed("task-1")
        assert ready == {"task-2", "task-3"}
        assert graph.is_completed("task-1") is True

    def test_mark_completed_partial_dependencies(self):
        """Should not return tasks with unsatisfied dependencies"""
        graph = DependencyGraph()
        graph.add_task("task-1")
        graph.add_task("task-2")
        graph.add_task("task-3", dependencies={"task-1", "task-2"})

        # Complete task-1
        ready = graph.mark_completed("task-1")
        # task-3 still depends on task-2
        assert ready == set()

        # Complete task-2
        ready = graph.mark_completed("task-2")
        # Now task-3 is ready
        assert ready == {"task-3"}

    def test_mark_completed_with_unsatisfied_dependencies(self):
        """Should raise error if dependencies not satisfied"""
        graph = DependencyGraph()
        graph.add_task("task-1")
        graph.add_task("task-2", dependencies={"task-1"})

        with pytest.raises(DependencyNotSatisfiedError, match="unsatisfied dependencies"):
            graph.mark_completed("task-2")

    def test_mark_completed_nonexistent_task(self):
        """Should raise error for non-existent task"""
        graph = DependencyGraph()

        with pytest.raises(KeyError, match="not found"):
            graph.mark_completed("task-1")

    def test_get_ready_tasks(self):
        """Should return all tasks ready to execute"""
        graph = DependencyGraph()
        graph.add_task("task-1")
        graph.add_task("task-2")
        graph.add_task("task-3", dependencies={"task-1"})

        ready = graph.get_ready_tasks()
        assert ready == {"task-1", "task-2"}

    def test_get_ready_tasks_after_completion(self):
        """Should update ready tasks after completion"""
        graph = DependencyGraph()
        graph.add_task("task-1")
        graph.add_task("task-2", dependencies={"task-1"})

        # Initially only task-1 ready
        assert graph.get_ready_tasks() == {"task-1"}

        # After completing task-1, task-2 ready
        graph.mark_completed("task-1")
        assert graph.get_ready_tasks() == {"task-2"}

    def test_get_task_dependencies(self):
        """Should return task dependencies"""
        graph = DependencyGraph()
        graph.add_task("task-1")
        graph.add_task("task-2")
        graph.add_task("task-3", dependencies={"task-1", "task-2"})

        deps = graph.get_task_dependencies("task-3")
        assert deps == {"task-1", "task-2"}

    def test_get_task_dependents(self):
        """Should return task dependents"""
        graph = DependencyGraph()
        graph.add_task("task-1")
        graph.add_task("task-2", dependencies={"task-1"})
        graph.add_task("task-3", dependencies={"task-1"})

        dependents = graph.get_task_dependents("task-1")
        assert dependents == {"task-2", "task-3"}

    def test_is_completed(self):
        """Should check task completion status"""
        graph = DependencyGraph()
        graph.add_task("task-1")

        assert graph.is_completed("task-1") is False

        graph.mark_completed("task-1")
        assert graph.is_completed("task-1") is True

    def test_get_stats(self):
        """Should return graph statistics"""
        graph = DependencyGraph()
        graph.add_task("task-1")
        graph.add_task("task-2", dependencies={"task-1"})
        graph.add_task("task-3", dependencies={"task-1"})

        stats = graph.get_stats()
        assert stats["total_tasks"] == 3
        assert stats["completed_tasks"] == 0
        assert stats["ready_tasks"] == 1  # task-1
        assert stats["pending_tasks"] == 2  # task-2, task-3

        # Complete task-1
        graph.mark_completed("task-1")
        stats = graph.get_stats()
        assert stats["completed_tasks"] == 1
        assert stats["ready_tasks"] == 2  # task-2, task-3
        assert stats["pending_tasks"] == 0

    def test_reset(self):
        """Should reset completion states"""
        graph = DependencyGraph()
        graph.add_task("task-1")
        graph.add_task("task-2", dependencies={"task-1"})

        graph.mark_completed("task-1")
        assert graph.is_completed("task-1") is True

        graph.reset()
        assert graph.is_completed("task-1") is False
        assert graph.get_stats()["completed_tasks"] == 0
        # Should restore original dependencies
        assert graph.get_ready_tasks() == {"task-1"}

    def test_clear(self):
        """Should remove all tasks"""
        graph = DependencyGraph()
        graph.add_task("task-1")
        graph.add_task("task-2")

        graph.clear()
        stats = graph.get_stats()
        assert stats["total_tasks"] == 0

    def test_complex_workflow(self):
        """Should handle complex multi-level workflow"""
        graph = DependencyGraph()

        # Level 0: No dependencies
        graph.add_task("init")

        # Level 1: Depend on init
        graph.add_task("fetch-data", dependencies={"init"})
        graph.add_task("setup-env", dependencies={"init"})

        # Level 2: Depend on level 1
        graph.add_task("process-data", dependencies={"fetch-data", "setup-env"})
        graph.add_task("validate-env", dependencies={"setup-env"})

        # Level 3: Depend on level 2
        graph.add_task("analyze", dependencies={"process-data"})
        graph.add_task("report", dependencies={"process-data", "validate-env"})

        # Level 4: Final task
        graph.add_task("cleanup", dependencies={"analyze", "report"})

        # Validate
        graph.validate()

        # Get execution plan
        plan = graph.get_execution_plan()
        assert plan.total_tasks == 8
        assert len(plan.levels) == 5

        # Verify level structure
        assert plan.levels[0] == {"init"}
        assert plan.levels[1] == {"fetch-data", "setup-env"}
        assert plan.levels[2] == {"process-data", "validate-env"}
        assert plan.levels[3] == {"analyze", "report"}
        assert plan.levels[4] == {"cleanup"}

        # Maximum parallel tasks
        assert plan.max_parallel_tasks == 2
