"""
Multi-Agent Orchestration

Coordinates multiple specialized agents for complex tasks.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid

from .agent_variants import AgentVariantRegistry, TaskClassifier


class TaskStatus(str, Enum):
    """Status of a task in workflow"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class AgentRole(str, Enum):
    """Role of agent in orchestration"""
    PRIMARY = "primary"  # Main agent for the task
    SUPPORTING = "supporting"  # Provides additional context/validation
    VALIDATOR = "validator"  # Reviews and validates results
    AGGREGATOR = "aggregator"  # Combines results from multiple agents


@dataclass
class SubTask:
    """Individual subtask in decomposed workflow"""
    id: str
    description: str
    agent_variant_id: str
    dependencies: List[str] = field(default_factory=list)  # IDs of tasks that must complete first
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "description": self.description,
            "agent_variant_id": self.agent_variant_id,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class WorkflowExecution:
    """Execution state of a workflow"""
    id: str
    original_task: str
    subtasks: List[SubTask]
    status: TaskStatus
    final_result: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    def get_ready_tasks(self) -> List[SubTask]:
        """Get tasks that are ready to execute (dependencies met)"""
        ready = []
        completed_ids = {t.id for t in self.subtasks if t.status == TaskStatus.COMPLETED}
        
        for task in self.subtasks:
            if task.status == TaskStatus.PENDING:
                # Check if all dependencies are completed
                if all(dep_id in completed_ids for dep_id in task.dependencies):
                    ready.append(task)
        
        return ready
    
    def is_complete(self) -> bool:
        """Check if all tasks are completed"""
        return all(
            t.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]
            for t in self.subtasks
        )
    
    def has_failures(self) -> bool:
        """Check if any tasks failed"""
        return any(t.status == TaskStatus.FAILED for t in self.subtasks)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "original_task": self.original_task,
            "subtasks": [t.to_dict() for t in self.subtasks],
            "status": self.status.value,
            "final_result": self.final_result,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class TaskDecomposer:
    """
    Decomposes complex tasks into subtasks.
    
    Analyzes task complexity and creates workflow with appropriate agents.
    """
    
    def __init__(self, variant_registry: AgentVariantRegistry):
        """Initialize task decomposer"""
        self._registry = variant_registry
        self._classifier = TaskClassifier()
    
    def decompose(self, task_description: str, context: Optional[Dict[str, Any]] = None) -> List[SubTask]:
        """
        Decompose task into subtasks.
        
        Args:
            task_description: Description of complex task
            context: Additional context
            
        Returns:
            List of subtasks with dependencies
        """
        # Detect if task requires multiple agents
        subtasks = []
        
        # Check for multi-domain patterns
        if self._is_campaign_creation_task(task_description):
            subtasks = self._decompose_campaign_creation(task_description)
        elif self._is_learning_project_task(task_description):
            subtasks = self._decompose_learning_project(task_description)
        elif self._is_sales_sequence_task(task_description):
            subtasks = self._decompose_sales_sequence(task_description)
        else:
            # Single agent task
            classification = self._classifier.classify(task_description, context)
            variant = self._registry.select_variant(task_description, context)
            
            subtasks = [SubTask(
                id=str(uuid.uuid4()),
                description=task_description,
                agent_variant_id=variant.variant_id,
                dependencies=[]
            )]
        
        return subtasks
    
    def _is_campaign_creation_task(self, task: str) -> bool:
        """Check if task requires campaign creation workflow"""
        keywords = ["campaign", "launch", "marketing plan", "content strategy", "multi-channel"]
        return any(kw in task.lower() for kw in keywords)
    
    def _is_learning_project_task(self, task: str) -> bool:
        """Check if task requires learning project workflow"""
        keywords = ["learn", "master", "study plan", "curriculum", "course"]
        return any(kw in task.lower() for kw in keywords)
    
    def _is_sales_sequence_task(self, task: str) -> bool:
        """Check if task requires sales sequence workflow"""
        keywords = ["sales sequence", "outreach campaign", "lead nurture", "sales funnel"]
        return any(kw in task.lower() for kw in keywords)
    
    def _decompose_campaign_creation(self, task: str) -> List[SubTask]:
        """Decompose campaign creation into subtasks"""
        subtasks = []
        
        # Task 1: Campaign strategy (uses MarketingExpert knowledge graph)
        strategy_id = str(uuid.uuid4())
        subtasks.append(SubTask(
            id=strategy_id,
            description=f"Develop campaign strategy for: {task}",
            agent_variant_id="content_creation_agent",
            dependencies=[]
        ))
        
        # Task 2: SEO optimization (depends on strategy)
        seo_id = str(uuid.uuid4())
        subtasks.append(SubTask(
            id=seo_id,
            description=f"Create SEO strategy for campaign: {task}",
            agent_variant_id="seo_optimization_agent",
            dependencies=[strategy_id]
        ))
        
        # Task 3: Content creation (depends on both)
        content_id = str(uuid.uuid4())
        subtasks.append(SubTask(
            id=content_id,
            description=f"Create campaign content based on strategy and SEO",
            agent_variant_id="content_creation_agent",
            dependencies=[strategy_id, seo_id]
        ))
        
        return subtasks
    
    def _decompose_learning_project(self, task: str) -> List[SubTask]:
        """Decompose learning project into subtasks"""
        subtasks = []
        
        # Task 1: Learning plan creation
        plan_id = str(uuid.uuid4())
        subtasks.append(SubTask(
            id=plan_id,
            description=f"Create learning plan for: {task}",
            agent_variant_id="concept_teaching_agent",
            dependencies=[]
        ))
        
        # Task 2: Resource curation (depends on plan)
        resource_id = str(uuid.uuid4())
        subtasks.append(SubTask(
            id=resource_id,
            description=f"Curate learning resources based on plan",
            agent_variant_id="concept_teaching_agent",
            dependencies=[plan_id]
        ))
        
        # Task 3: Assessment strategy (depends on plan)
        assessment_id = str(uuid.uuid4())
        subtasks.append(SubTask(
            id=assessment_id,
            description=f"Design assessment strategy for learning goals",
            agent_variant_id="test_preparation_agent",
            dependencies=[plan_id]
        ))
        
        return subtasks
    
    def _decompose_sales_sequence(self, task: str) -> List[SubTask]:
        """Decompose sales sequence into subtasks"""
        subtasks = []
        
        # Task 1: Lead qualification
        qual_id = str(uuid.uuid4())
        subtasks.append(SubTask(
            id=qual_id,
            description=f"Qualify leads for: {task}",
            agent_variant_id="lead_qualification_agent",
            dependencies=[]
        ))
        
        # Task 2: Outreach sequence (depends on qualification)
        outreach_id = str(uuid.uuid4())
        subtasks.append(SubTask(
            id=outreach_id,
            description=f"Create personalized outreach sequence based on qualification",
            agent_variant_id="outreach_writing_agent",
            dependencies=[qual_id]
        ))
        
        return subtasks


class ResultAggregator:
    """
    Aggregates results from multiple agents.
    
    Handles merging, conflict resolution, and consensus building.
    """
    
    def aggregate(
        self,
        subtask_results: List[Dict[str, Any]],
        aggregation_strategy: str = "merge"
    ) -> Dict[str, Any]:
        """
        Aggregate results from multiple subtasks.
        
        Args:
            subtask_results: Results from completed subtasks
            aggregation_strategy: Strategy for aggregation (merge, vote, priority)
            
        Returns:
            Aggregated result
        """
        if not subtask_results:
            return {}
        
        if aggregation_strategy == "merge":
            return self._merge_results(subtask_results)
        elif aggregation_strategy == "vote":
            return self._vote_on_results(subtask_results)
        elif aggregation_strategy == "priority":
            return self._priority_results(subtask_results)
        else:
            return subtask_results[-1]  # Return last result
    
    def _merge_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge results by combining unique keys"""
        merged = {}
        
        for result in results:
            for key, value in result.items():
                if key not in merged:
                    merged[key] = value
                elif isinstance(value, list) and isinstance(merged[key], list):
                    # Merge lists
                    merged[key].extend(value)
                elif isinstance(value, dict) and isinstance(merged[key], dict):
                    # Merge dicts
                    merged[key].update(value)
                else:
                    # Keep as list of values
                    if not isinstance(merged[key], list):
                        merged[key] = [merged[key]]
                    merged[key].append(value)
        
        return merged
    
    def _vote_on_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Vote on results - pick most common values"""
        if len(results) == 1:
            return results[0]
        
        # For now, use simple majority voting on string values
        voted = {}
        
        # Get all keys
        all_keys = set()
        for result in results:
            all_keys.update(result.keys())
        
        for key in all_keys:
            values = [r.get(key) for r in results if key in r]
            if not values:
                continue
            
            # Count occurrences
            if all(isinstance(v, str) for v in values):
                # Vote on strings
                from collections import Counter
                counter = Counter(values)
                voted[key] = counter.most_common(1)[0][0]
            elif all(isinstance(v, (int, float)) for v in values):
                # Average numbers
                voted[key] = sum(values) / len(values)
            else:
                # Take first value
                voted[key] = values[0]
        
        return voted
    
    def _priority_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Priority-based aggregation - first result takes precedence"""
        if not results:
            return {}
        
        # Start with first result
        aggregated = dict(results[0])
        
        # Add keys from other results that don't conflict
        for result in results[1:]:
            for key, value in result.items():
                if key not in aggregated:
                    aggregated[key] = value
        
        return aggregated


class AgentOrchestrator:
    """
    Orchestrates multiple agents for complex tasks.
    
    Manages workflow execution, agent coordination, and result aggregation.
    """
    
    def __init__(self, variant_registry: Optional[AgentVariantRegistry] = None):
        """Initialize orchestrator"""
        self._registry = variant_registry or AgentVariantRegistry()
        self._decomposer = TaskDecomposer(self._registry)
        self._aggregator = ResultAggregator()
        self._executions: Dict[str, WorkflowExecution] = {}
    
    def create_workflow(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> WorkflowExecution:
        """
        Create workflow for task.
        
        Args:
            task_description: Description of complex task
            context: Additional context
            
        Returns:
            WorkflowExecution with subtasks
        """
        # Decompose task
        subtasks = self._decomposer.decompose(task_description, context)
        
        # Create workflow execution
        execution = WorkflowExecution(
            id=str(uuid.uuid4()),
            original_task=task_description,
            subtasks=subtasks,
            status=TaskStatus.PENDING,
            metadata=context or {}
        )
        
        self._executions[execution.id] = execution
        
        return execution
    
    def execute_workflow(
        self,
        execution_id: str,
        task_executor: Optional[Callable[[SubTask], Dict[str, Any]]] = None
    ) -> WorkflowExecution:
        """
        Execute workflow.
        
        Args:
            execution_id: ID of workflow execution
            task_executor: Optional function to execute tasks (for testing)
            
        Returns:
            Updated workflow execution
        """
        execution = self._executions.get(execution_id)
        if not execution:
            raise ValueError(f"Workflow {execution_id} not found")
        
        execution.status = TaskStatus.IN_PROGRESS
        
        # Execute tasks in dependency order
        while not execution.is_complete():
            ready_tasks = execution.get_ready_tasks()
            
            if not ready_tasks:
                # Check if blocked
                if not execution.is_complete():
                    execution.status = TaskStatus.BLOCKED
                break
            
            # Execute ready tasks
            for task in ready_tasks:
                task.status = TaskStatus.IN_PROGRESS
                task.started_at = datetime.utcnow()
                
                try:
                    # Execute task (mock for now, would call actual agent)
                    if task_executor:
                        result = task_executor(task)
                    else:
                        result = self._mock_execute_task(task)
                    
                    task.result = result
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = datetime.utcnow()
                except Exception as e:
                    task.error = str(e)
                    task.status = TaskStatus.FAILED
                    task.completed_at = datetime.utcnow()
        
        # Aggregate results
        if execution.is_complete() and not execution.has_failures():
            completed_results = [
                t.result for t in execution.subtasks
                if t.status == TaskStatus.COMPLETED and t.result
            ]
            execution.final_result = self._aggregator.aggregate(completed_results)
            execution.status = TaskStatus.COMPLETED
        elif execution.has_failures():
            execution.status = TaskStatus.FAILED
        
        execution.completed_at = datetime.utcnow()
        
        return execution
    
    def _mock_execute_task(self, task: SubTask) -> Dict[str, Any]:
        """Mock task execution (placeholder for actual agent execution)"""
        return {
            "task_id": task.id,
            "description": task.description,
            "agent": task.agent_variant_id,
            "result": f"Completed: {task.description}",
            "mock": True
        }
    
    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get workflow execution by ID"""
        return self._executions.get(execution_id)
    
    def list_executions(
        self,
        status: Optional[TaskStatus] = None
    ) -> List[WorkflowExecution]:
        """List workflow executions with optional status filter"""
        executions = list(self._executions.values())
        
        if status:
            executions = [e for e in executions if e.status == status]
        
        # Sort by created_at descending
        executions.sort(key=lambda e: e.created_at, reverse=True)
        
        return executions
    
    def get_execution_summary(self, execution_id: str) -> Dict[str, Any]:
        """Get summary of workflow execution"""
        execution = self._executions.get(execution_id)
        if not execution:
            return {}
        
        return {
            "id": execution.id,
            "original_task": execution.original_task,
            "status": execution.status.value,
            "total_subtasks": len(execution.subtasks),
            "completed_subtasks": sum(1 for t in execution.subtasks if t.status == TaskStatus.COMPLETED),
            "failed_subtasks": sum(1 for t in execution.subtasks if t.status == TaskStatus.FAILED),
            "pending_subtasks": sum(1 for t in execution.subtasks if t.status == TaskStatus.PENDING),
            "agents_involved": list(set(t.agent_variant_id for t in execution.subtasks)),
            "has_result": execution.final_result is not None,
            "created_at": execution.created_at.isoformat(),
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
        }
