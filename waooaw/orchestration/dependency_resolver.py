"""
Dependency Resolution

DAG-based dependency resolution with topological sorting for determining
task execution order in multi-agent workflows.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional
from collections import deque

from waooaw.common.logging_framework import StructuredLogger


class CyclicDependencyError(Exception):
    """Raised when circular dependency detected in task graph"""

    def __init__(self, cycle: List[str]):
        self.cycle = cycle
        super().__init__(f"Cyclic dependency detected: {' -> '.join(cycle)}")


class InvalidDependencyError(Exception):
    """Raised when dependency references non-existent task"""

    pass


class DependencyNotSatisfiedError(Exception):
    """Raised when attempting to execute task with unmet dependencies"""

    pass


@dataclass
class TaskNode:
    """
    Node in the dependency graph representing a task
    
    Tracks dependencies (tasks that must complete before this one)
    and dependents (tasks that depend on this one).
    """

    task_id: str
    dependencies: Set[str] = field(default_factory=set)  # Tasks this depends on
    dependents: Set[str] = field(default_factory=set)  # Tasks that depend on this
    completed: bool = False
    in_degree: int = 0  # Number of unsatisfied dependencies

    def __hash__(self) -> int:
        return hash(self.task_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TaskNode):
            return False
        return self.task_id == other.task_id


@dataclass
class ExecutionPlan:
    """
    Execution plan with topologically sorted task order
    
    Provides sequential execution order and identifies tasks that
    can be executed in parallel (same level in the DAG).
    """

    execution_order: List[str]  # Topologically sorted task IDs
    levels: List[Set[str]]  # Tasks grouped by parallelization level
    total_tasks: int
    max_parallel_tasks: int  # Maximum tasks in any single level

    def get_next_batch(self, completed_tasks: Set[str]) -> Set[str]:
        """
        Get next batch of tasks ready to execute
        
        Args:
            completed_tasks: Set of already completed task IDs
            
        Returns:
            Set of task IDs ready to execute (dependencies satisfied)
        """
        for level in self.levels:
            # Check if all tasks in this level are completed
            if level.issubset(completed_tasks):
                continue

            # Return tasks in this level not yet completed
            return level - completed_tasks

        return set()  # All tasks completed


class DependencyGraph:
    """
    Directed Acyclic Graph (DAG) for task dependencies
    
    Features:
    - Add tasks with dependencies
    - Validate graph (no cycles, valid dependencies)
    - Topological sort for execution order
    - Identify parallel execution opportunities
    - Track completion and resolve next tasks
    """

    def __init__(self):
        """Initialize empty dependency graph"""
        self._nodes: Dict[str, TaskNode] = {}
        self._logger = StructuredLogger(name="dependency-resolver", level="INFO")

    def add_task(
        self, task_id: str, dependencies: Optional[Set[str]] = None
    ) -> None:
        """
        Add task to dependency graph
        
        Args:
            task_id: Unique task identifier
            dependencies: Set of task IDs this task depends on
            
        Raises:
            ValueError: If task already exists
        """
        if task_id in self._nodes:
            raise ValueError(f"Task {task_id} already exists in graph")

        deps = dependencies or set()
        node = TaskNode(
            task_id=task_id, dependencies=deps.copy(), in_degree=len(deps)
        )
        self._nodes[task_id] = node

        # Update dependents for dependency nodes
        for dep_id in deps:
            if dep_id in self._nodes:
                self._nodes[dep_id].dependents.add(task_id)

        self._logger.info(
            "task_added_to_graph",
            extra={
                "task_id": task_id,
                "dependencies": list(deps),
                "total_tasks": len(self._nodes),
            },
        )

    def remove_task(self, task_id: str) -> None:
        """
        Remove task from dependency graph
        
        Args:
            task_id: Task identifier to remove
            
        Raises:
            KeyError: If task doesn't exist
        """
        if task_id not in self._nodes:
            raise KeyError(f"Task {task_id} not found in graph")

        node = self._nodes[task_id]

        # Remove from dependents of dependencies
        for dep_id in node.dependencies:
            if dep_id in self._nodes:
                self._nodes[dep_id].dependents.discard(task_id)

        # Update in_degree for tasks that depended on this one
        for dependent_id in node.dependents:
            if dependent_id in self._nodes:
                self._nodes[dependent_id].in_degree -= 1
                self._nodes[dependent_id].dependencies.discard(task_id)

        del self._nodes[task_id]

        self._logger.info(
            "task_removed_from_graph",
            extra={"task_id": task_id, "remaining_tasks": len(self._nodes)},
        )

    def validate(self) -> None:
        """
        Validate dependency graph
        
        Checks:
        1. All dependencies reference existing tasks
        2. No circular dependencies (DAG property)
        
        Raises:
            InvalidDependencyError: If dependency references non-existent task
            CyclicDependencyError: If circular dependency detected
        """
        # Check all dependencies exist
        for task_id, node in self._nodes.items():
            for dep_id in node.dependencies:
                if dep_id not in self._nodes:
                    raise InvalidDependencyError(
                        f"Task {task_id} depends on non-existent task {dep_id}"
                    )

        # Check for cycles using DFS
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        path: List[str] = []

        def dfs(task_id: str) -> bool:
            """DFS to detect cycles"""
            visited.add(task_id)
            rec_stack.add(task_id)
            path.append(task_id)

            # Check all dependents (outgoing edges)
            node = self._nodes[task_id]
            for dependent_id in node.dependents:
                if dependent_id not in visited:
                    if dfs(dependent_id):
                        return True
                elif dependent_id in rec_stack:
                    # Cycle detected - build cycle path
                    cycle_start = path.index(dependent_id)
                    cycle = path[cycle_start:] + [dependent_id]
                    raise CyclicDependencyError(cycle)

            path.pop()
            rec_stack.remove(task_id)
            return False

        # Run DFS from each unvisited node
        for task_id in self._nodes:
            if task_id not in visited:
                dfs(task_id)

        self._logger.info(
            "graph_validated",
            extra={"total_tasks": len(self._nodes), "is_dag": True},
        )

    def topological_sort(self) -> List[str]:
        """
        Perform topological sort using Kahn's algorithm
        
        Returns:
            List of task IDs in topologically sorted order
            
        Raises:
            CyclicDependencyError: If graph contains cycle
        """
        # Create working copy of in-degrees
        in_degree = {tid: node.in_degree for tid, node in self._nodes.items()}

        # Queue of tasks with no dependencies
        queue = deque([tid for tid, deg in in_degree.items() if deg == 0])
        result: List[str] = []

        while queue:
            # Process task with no remaining dependencies
            task_id = queue.popleft()
            result.append(task_id)

            # Reduce in-degree for all dependents
            node = self._nodes[task_id]
            for dependent_id in node.dependents:
                in_degree[dependent_id] -= 1
                if in_degree[dependent_id] == 0:
                    queue.append(dependent_id)

        # If not all tasks processed, there's a cycle
        if len(result) != len(self._nodes):
            unprocessed = set(self._nodes.keys()) - set(result)
            raise CyclicDependencyError(
                ["<cycle>"] + list(unprocessed)[:5] + ["..."]
            )

        self._logger.info(
            "topological_sort_complete",
            extra={"total_tasks": len(result), "order": result[:10]},
        )

        return result

    def get_execution_plan(self) -> ExecutionPlan:
        """
        Generate execution plan with parallelization levels
        
        Groups tasks by "level" where all tasks in a level can execute
        in parallel (their dependencies are in earlier levels).
        
        Returns:
            ExecutionPlan with execution order and parallel levels
        """
        # Create working copy of in-degrees
        in_degree = {tid: node.in_degree for tid, node in self._nodes.items()}

        levels: List[Set[str]] = []
        execution_order: List[str] = []
        processed = 0

        while processed < len(self._nodes):
            # Find all tasks with no remaining dependencies
            current_level = {
                tid for tid, deg in in_degree.items() if deg == 0 and tid not in execution_order
            }

            if not current_level:
                # No tasks ready - cycle exists
                raise CyclicDependencyError(["<cycle>"])

            levels.append(current_level)
            execution_order.extend(sorted(current_level))  # Sort for determinism

            # Reduce in-degree for dependents
            for task_id in current_level:
                node = self._nodes[task_id]
                for dependent_id in node.dependents:
                    in_degree[dependent_id] -= 1

            processed += len(current_level)

        max_parallel = max(len(level) for level in levels) if levels else 0

        plan = ExecutionPlan(
            execution_order=execution_order,
            levels=levels,
            total_tasks=len(self._nodes),
            max_parallel_tasks=max_parallel,
        )

        self._logger.info(
            "execution_plan_created",
            extra={
                "total_tasks": plan.total_tasks,
                "total_levels": len(levels),
                "max_parallel_tasks": max_parallel,
            },
        )

        return plan

    def mark_completed(self, task_id: str) -> Set[str]:
        """
        Mark task as completed and return newly ready tasks
        
        Args:
            task_id: Task identifier to mark as complete
            
        Returns:
            Set of task IDs now ready to execute (dependencies satisfied)
            
        Raises:
            KeyError: If task doesn't exist
            DependencyNotSatisfiedError: If task dependencies not met
        """
        if task_id not in self._nodes:
            raise KeyError(f"Task {task_id} not found in graph")

        node = self._nodes[task_id]

        # Check dependencies satisfied
        if node.in_degree > 0:
            unsatisfied = {
                dep for dep in node.dependencies if not self._nodes[dep].completed
            }
            raise DependencyNotSatisfiedError(
                f"Task {task_id} has unsatisfied dependencies: {unsatisfied}"
            )

        # Mark complete
        node.completed = True

        # Find newly ready dependents
        ready_tasks: Set[str] = set()
        for dependent_id in node.dependents:
            dependent = self._nodes[dependent_id]
            dependent.in_degree -= 1

            # Check if all dependencies now satisfied
            if dependent.in_degree == 0 and not dependent.completed:
                ready_tasks.add(dependent_id)

        self._logger.info(
            "task_completed",
            extra={
                "task_id": task_id,
                "newly_ready_tasks": list(ready_tasks),
            },
        )

        return ready_tasks

    def get_ready_tasks(self) -> Set[str]:
        """
        Get all tasks currently ready to execute
        
        Returns:
            Set of task IDs with no unsatisfied dependencies
        """
        return {
            tid
            for tid, node in self._nodes.items()
            if node.in_degree == 0 and not node.completed
        }

    def get_task_dependencies(self, task_id: str) -> Set[str]:
        """
        Get direct dependencies for a task
        
        Args:
            task_id: Task identifier
            
        Returns:
            Set of task IDs this task depends on
            
        Raises:
            KeyError: If task doesn't exist
        """
        if task_id not in self._nodes:
            raise KeyError(f"Task {task_id} not found in graph")

        return self._nodes[task_id].dependencies.copy()

    def get_task_dependents(self, task_id: str) -> Set[str]:
        """
        Get direct dependents for a task
        
        Args:
            task_id: Task identifier
            
        Returns:
            Set of task IDs that depend on this task
            
        Raises:
            KeyError: If task doesn't exist
        """
        if task_id not in self._nodes:
            raise KeyError(f"Task {task_id} not found in graph")

        return self._nodes[task_id].dependents.copy()

    def is_completed(self, task_id: str) -> bool:
        """
        Check if task is completed
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if task is marked as completed
            
        Raises:
            KeyError: If task doesn't exist
        """
        if task_id not in self._nodes:
            raise KeyError(f"Task {task_id} not found in graph")

        return self._nodes[task_id].completed

    def get_stats(self) -> Dict[str, int]:
        """
        Get graph statistics
        
        Returns:
            Dictionary with graph metrics
        """
        completed_count = sum(1 for node in self._nodes.values() if node.completed)
        ready_count = len(self.get_ready_tasks())

        return {
            "total_tasks": len(self._nodes),
            "completed_tasks": completed_count,
            "ready_tasks": ready_count,
            "pending_tasks": len(self._nodes) - completed_count - ready_count,
        }

    def reset(self) -> None:
        """Reset all completion states without removing tasks"""
        for node in self._nodes.values():
            node.completed = False
            node.in_degree = len(node.dependencies)

        self._logger.info("graph_reset", extra={"total_tasks": len(self._nodes)})

    def clear(self) -> None:
        """Remove all tasks from graph"""
        self._nodes.clear()
        self._logger.info("graph_cleared")
