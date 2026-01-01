"""
Workflow State

Manages workflow orchestration monitoring state.
"""

import reflex as rx
from datetime import datetime
from typing import List, Optional


class WorkflowTask(rx.Base):
    """Individual task within a workflow"""
    task_id: str
    task_name: str
    agent_id: str
    agent_name: str
    status: str  # pending, running, completed, failed
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_sec: int = 0
    dependencies: List[str] = []
    error_message: Optional[str] = None
    retry_count: int = 0


class Workflow(rx.Base):
    """Workflow definition"""
    workflow_id: str
    workflow_name: str
    customer_id: str
    customer_name: str
    status: str  # pending, running, completed, failed, paused
    progress: int  # 0-100
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    tasks: List[WorkflowTask]


class WorkflowState(rx.State):
    """State management for workflow monitoring"""
    
    workflows: List[Workflow] = []
    selected_workflow: Optional[Workflow] = None
    show_task_inspector: bool = False
    selected_task: Optional[WorkflowTask] = None
    
    # Filters
    status_filter: str = "all"  # all, running, completed, failed
    
    def load_workflows(self):
        """Load workflows from backend"""
        # Mock data for development
        self.workflows = [
            Workflow(
                workflow_id="wf-001",
                workflow_name="Customer Onboarding Pipeline",
                customer_id="cust-001",
                customer_name="Acme Corp",
                status="running",
                progress=60,
                created_at="2025-01-15T10:00:00",
                started_at="2025-01-15T10:05:00",
                total_tasks=10,
                completed_tasks=6,
                failed_tasks=0,
                tasks=[
                    WorkflowTask(
                        task_id="task-001",
                        task_name="Verify Customer Data",
                        agent_id="agent-1",
                        agent_name="Data Validator",
                        status="completed",
                        start_time="2025-01-15T10:05:00",
                        end_time="2025-01-15T10:08:00",
                        duration_sec=180,
                        dependencies=[],
                    ),
                    WorkflowTask(
                        task_id="task-002",
                        task_name="Create Account",
                        agent_id="agent-2",
                        agent_name="Account Manager",
                        status="completed",
                        start_time="2025-01-15T10:08:00",
                        end_time="2025-01-15T10:12:00",
                        duration_sec=240,
                        dependencies=["task-001"],
                    ),
                    WorkflowTask(
                        task_id="task-003",
                        task_name="Setup Billing",
                        agent_id="agent-3",
                        agent_name="Billing Agent",
                        status="running",
                        start_time="2025-01-15T10:12:00",
                        duration_sec=300,
                        dependencies=["task-002"],
                    ),
                    WorkflowTask(
                        task_id="task-004",
                        task_name="Configure Services",
                        agent_id="agent-4",
                        agent_name="Service Configurator",
                        status="pending",
                        dependencies=["task-003"],
                    ),
                ],
            ),
            Workflow(
                workflow_id="wf-002",
                workflow_name="Content Generation Campaign",
                customer_id="cust-002",
                customer_name="TechStart Inc",
                status="completed",
                progress=100,
                created_at="2025-01-14T14:00:00",
                started_at="2025-01-14T14:05:00",
                completed_at="2025-01-14T16:30:00",
                total_tasks=8,
                completed_tasks=8,
                failed_tasks=0,
                tasks=[],
            ),
            Workflow(
                workflow_id="wf-003",
                workflow_name="Lead Qualification Process",
                customer_id="cust-003",
                customer_name="Sales Pro LLC",
                status="failed",
                progress=25,
                created_at="2025-01-15T09:00:00",
                started_at="2025-01-15T09:05:00",
                total_tasks=12,
                completed_tasks=3,
                failed_tasks=1,
                tasks=[
                    WorkflowTask(
                        task_id="task-101",
                        task_name="Fetch Lead Data",
                        agent_id="agent-5",
                        agent_name="Lead Fetcher",
                        status="failed",
                        start_time="2025-01-15T09:15:00",
                        end_time="2025-01-15T09:16:00",
                        duration_sec=60,
                        dependencies=["task-100"],
                        error_message="API rate limit exceeded",
                        retry_count=2,
                    ),
                ],
            ),
        ]
    
    def select_workflow(self, workflow_id: str):
        """Select a workflow for detailed view"""
        self.selected_workflow = next(
            (wf for wf in self.workflows if wf.workflow_id == workflow_id),
            None
        )
    
    def close_workflow_detail(self):
        """Close workflow detail view"""
        self.selected_workflow = None
        self.show_task_inspector = False
        self.selected_task = None
    
    def select_task(self, task_id: str):
        """Select a task for inspection"""
        if self.selected_workflow:
            self.selected_task = next(
                (task for task in self.selected_workflow.tasks if task.task_id == task_id),
                None
            )
            self.show_task_inspector = True
    
    def close_task_inspector(self):
        """Close task inspector"""
        self.show_task_inspector = False
        self.selected_task = None
    
    def retry_workflow(self, workflow_id: str):
        """Retry a failed workflow"""
        # TODO: Call backend API
        workflow = next((wf for wf in self.workflows if wf.workflow_id == workflow_id), None)
        if workflow:
            workflow.status = "running"
            workflow.failed_tasks = 0
    
    def pause_workflow(self, workflow_id: str):
        """Pause a running workflow"""
        # TODO: Call backend API
        workflow = next((wf for wf in self.workflows if wf.workflow_id == workflow_id), None)
        if workflow:
            workflow.status = "paused"
    
    def resume_workflow(self, workflow_id: str):
        """Resume a paused workflow"""
        # TODO: Call backend API
        workflow = next((wf for wf in self.workflows if wf.workflow_id == workflow_id), None)
        if workflow:
            workflow.status = "running"
    
    def cancel_workflow(self, workflow_id: str):
        """Cancel a workflow"""
        # TODO: Call backend API
        workflow = next((wf for wf in self.workflows if wf.workflow_id == workflow_id), None)
        if workflow:
            workflow.status = "failed"
    
    def set_status_filter(self, status: str):
        """Set status filter"""
        self.status_filter = status
    
    @rx.var
    def filtered_workflows(self) -> List[Workflow]:
        """Get filtered workflows"""
        if self.status_filter == "all":
            return self.workflows
        return [wf for wf in self.workflows if wf.status == self.status_filter]
    
    @rx.var
    def workflow_count(self) -> int:
        """Total workflow count"""
        return len(self.workflows)
    
    @rx.var
    def running_count(self) -> int:
        """Running workflow count"""
        return len([wf for wf in self.workflows if wf.status == "running"])
    
    @rx.var
    def completed_count(self) -> int:
        """Completed workflow count"""
        return len([wf for wf in self.workflows if wf.status == "completed"])
    
    @rx.var
    def failed_count(self) -> int:
        """Failed workflow count"""
        return len([wf for wf in self.workflows if wf.status == "failed"])
