"""
Complex Problem Decomposition & Planning Engine - Story 5.6.3

Epic 5.6: Self-Evolving Agent System

Agents break down multi-month complex projects into 50+ manageable tasks with
dependencies, resource estimates, milestones, risk assessment, and dynamic replanning.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Set
from collections import defaultdict


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = "critical"     # Blocking, must complete ASAP
    HIGH = "high"             # Important, near-term
    MEDIUM = "medium"         # Standard priority
    LOW = "low"               # Nice to have, can defer


class TaskStatus(Enum):
    """Task execution status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RiskLevel(Enum):
    """Risk severity levels"""
    LOW = "low"               # Minor impact if occurs
    MEDIUM = "medium"         # Moderate impact
    HIGH = "high"             # Significant impact
    CRITICAL = "critical"     # Project-threatening


class MilestoneType(Enum):
    """Types of project milestones"""
    PHASE_START = "phase_start"
    PHASE_END = "phase_end"
    DELIVERABLE = "deliverable"
    DECISION_GATE = "decision_gate"
    REVIEW = "review"


@dataclass
class ProjectTask:
    """A single task in the project breakdown"""
    task_id: str
    task_name: str
    description: str
    estimated_hours: float
    
    # Hierarchy
    parent_task_id: Optional[str] = None  # For subtasks
    subtask_ids: List[str] = field(default_factory=list)
    
    # Scheduling
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    actual_hours: float = 0.0
    
    # Dependencies
    depends_on: List[str] = field(default_factory=list)  # Task IDs that must complete first
    blocks: List[str] = field(default_factory=list)      # Tasks that wait for this
    
    # Execution
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.NOT_STARTED
    assigned_to: Optional[str] = None  # Agent variant ID
    progress_percentage: float = 0.0   # 0-100
    
    # Resources
    required_skills: List[str] = field(default_factory=list)
    required_resources: List[str] = field(default_factory=list)
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "description": self.description,
            "parent_task_id": self.parent_task_id,
            "subtask_ids": self.subtask_ids,
            "estimated_hours": self.estimated_hours,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "actual_hours": self.actual_hours,
            "depends_on": self.depends_on,
            "blocks": self.blocks,
            "priority": self.priority.value,
            "status": self.status.value,
            "assigned_to": self.assigned_to,
            "progress_percentage": self.progress_percentage,
            "required_skills": self.required_skills,
            "required_resources": self.required_resources,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class ProjectMilestone:
    """A key milestone in the project"""
    milestone_id: str
    milestone_name: str
    milestone_type: MilestoneType
    description: str
    
    # Timing
    target_date: datetime
    actual_date: Optional[datetime] = None
    
    # Dependencies
    required_tasks: List[str] = field(default_factory=list)  # Tasks that must complete
    deliverables: List[str] = field(default_factory=list)    # What gets delivered
    
    # Status
    is_achieved: bool = False
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "milestone_id": self.milestone_id,
            "milestone_name": self.milestone_name,
            "milestone_type": self.milestone_type.value,
            "description": self.description,
            "target_date": self.target_date.isoformat(),
            "actual_date": self.actual_date.isoformat() if self.actual_date else None,
            "required_tasks": self.required_tasks,
            "deliverables": self.deliverables,
            "is_achieved": self.is_achieved,
            "notes": self.notes,
        }


@dataclass
class ProjectRisk:
    """A risk that could impact the project"""
    risk_id: str
    risk_description: str
    risk_level: RiskLevel
    
    # Assessment
    probability: float  # 0.0 to 1.0
    impact_hours: float  # Estimated delay if occurs
    
    # Mitigation
    mitigation_strategy: str
    contingency_plan: str
    
    # Tracking
    is_materialized: bool = False
    affected_tasks: List[str] = field(default_factory=list)
    
    identified_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "risk_id": self.risk_id,
            "risk_description": self.risk_description,
            "risk_level": self.risk_level.value,
            "probability": self.probability,
            "impact_hours": self.impact_hours,
            "mitigation_strategy": self.mitigation_strategy,
            "contingency_plan": self.contingency_plan,
            "is_materialized": self.is_materialized,
            "affected_tasks": self.affected_tasks,
            "identified_at": self.identified_at.isoformat(),
        }


@dataclass
class ProjectPlan:
    """Complete decomposed project plan"""
    plan_id: str
    project_name: str
    project_description: str
    agent_variant_id: str  # Agent who created the plan
    
    # Timeline
    start_date: datetime
    target_end_date: datetime
    actual_end_date: Optional[datetime] = None
    
    # Structure
    tasks: Dict[str, ProjectTask] = field(default_factory=dict)
    milestones: Dict[str, ProjectMilestone] = field(default_factory=dict)
    risks: Dict[str, ProjectRisk] = field(default_factory=dict)
    
    # Metrics
    total_estimated_hours: float = 0.0
    total_actual_hours: float = 0.0
    completion_percentage: float = 0.0
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "plan_id": self.plan_id,
            "project_name": self.project_name,
            "project_description": self.project_description,
            "agent_variant_id": self.agent_variant_id,
            "start_date": self.start_date.isoformat(),
            "target_end_date": self.target_end_date.isoformat(),
            "actual_end_date": self.actual_end_date.isoformat() if self.actual_end_date else None,
            "tasks": {tid: task.to_dict() for tid, task in self.tasks.items()},
            "milestones": {mid: milestone.to_dict() for mid, milestone in self.milestones.items()},
            "risks": {rid: risk.to_dict() for rid, risk in self.risks.items()},
            "total_estimated_hours": self.total_estimated_hours,
            "total_actual_hours": self.total_actual_hours,
            "completion_percentage": self.completion_percentage,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
        }


class ProblemDecompositionEngine:
    """
    Complex problem decomposition and project planning system.
    
    Enables agents to break down multi-month projects into detailed task plans
    with dependencies, resource estimates, milestones, and risk management.
    """
    
    def __init__(self):
        self._plans: Dict[str, ProjectPlan] = {}
        self._plans_by_agent: Dict[str, List[str]] = defaultdict(list)
    
    def decompose_project(
        self,
        agent_variant_id: str,
        project_name: str,
        project_description: str,
        duration_days: int,
        complexity: str = "medium"  # low, medium, high
    ) -> ProjectPlan:
        """
        Decompose a complex project into detailed task plan.
        """
        plan_id = f"plan_{agent_variant_id}_{datetime.utcnow().timestamp()}"
        
        start_date = datetime.utcnow()
        target_end_date = start_date + timedelta(days=duration_days)
        
        plan = ProjectPlan(
            plan_id=plan_id,
            project_name=project_name,
            project_description=project_description,
            agent_variant_id=agent_variant_id,
            start_date=start_date,
            target_end_date=target_end_date
        )
        
        # Generate phases based on project type
        phases = self._generate_phases(project_description, complexity)
        
        # Create tasks for each phase
        task_counter = 1
        for phase_idx, phase in enumerate(phases):
            phase_tasks = self._generate_phase_tasks(
                plan_id,
                phase,
                task_counter,
                start_date,
                duration_days,
                len(phases)
            )
            
            for task in phase_tasks:
                plan.tasks[task.task_id] = task
                task_counter += 1
        
        # Add dependencies between phases
        self._add_phase_dependencies(plan, phases)
        
        # Generate milestones
        milestones = self._generate_milestones(plan, phases, start_date, duration_days)
        for milestone in milestones:
            plan.milestones[milestone.milestone_id] = milestone
        
        # Calculate totals BEFORE identifying risks
        plan.total_estimated_hours = sum(t.estimated_hours for t in plan.tasks.values())
        
        # Identify risks (needs total_estimated_hours)
        risks = self._identify_risks(plan, complexity)
        for risk in risks:
            plan.risks[risk.risk_id] = risk
        
        self._plans[plan_id] = plan
        self._plans_by_agent[agent_variant_id].append(plan_id)
        
        return plan
    
    def _generate_phases(self, project_description: str, complexity: str) -> List[Dict[str, Any]]:
        """Generate project phases based on description"""
        # Simple heuristic: extract key phases from description
        desc_lower = project_description.lower()
        
        phases = []
        
        # Standard software project phases
        if any(word in desc_lower for word in ["software", "app", "platform", "system", "product"]):
            phases = [
                {"name": "Planning & Requirements", "tasks": 8},
                {"name": "Design & Architecture", "tasks": 10},
                {"name": "Implementation", "tasks": 20},
                {"name": "Testing & QA", "tasks": 12},
                {"name": "Deployment & Launch", "tasks": 6},
                {"name": "Post-Launch Support", "tasks": 4}
            ]
        
        # Marketing campaign
        elif any(word in desc_lower for word in ["marketing", "campaign", "launch", "brand"]):
            phases = [
                {"name": "Research & Strategy", "tasks": 10},
                {"name": "Creative Development", "tasks": 15},
                {"name": "Campaign Production", "tasks": 12},
                {"name": "Launch Execution", "tasks": 8},
                {"name": "Performance Monitoring", "tasks": 5}
            ]
        
        # Content creation
        elif any(word in desc_lower for word in ["content", "blog", "article", "writing"]):
            phases = [
                {"name": "Topic Research", "tasks": 8},
                {"name": "Outline Creation", "tasks": 6},
                {"name": "Content Writing", "tasks": 15},
                {"name": "Review & Editing", "tasks": 10},
                {"name": "Publishing & Promotion", "tasks": 6}
            ]
        
        # Default generic phases
        else:
            phases = [
                {"name": "Discovery & Planning", "tasks": 10},
                {"name": "Execution Phase 1", "tasks": 15},
                {"name": "Execution Phase 2", "tasks": 15},
                {"name": "Review & Refinement", "tasks": 8},
                {"name": "Completion & Handoff", "tasks": 5}
            ]
        
        # Adjust task count based on complexity
        if complexity == "high":
            for phase in phases:
                phase["tasks"] = int(phase["tasks"] * 1.5)
        elif complexity == "low":
            for phase in phases:
                phase["tasks"] = max(3, int(phase["tasks"] * 0.7))
        
        return phases
    
    def _generate_phase_tasks(
        self,
        plan_id: str,
        phase: Dict[str, Any],
        start_counter: int,
        project_start: datetime,
        total_days: int,
        num_phases: int
    ) -> List[ProjectTask]:
        """Generate tasks for a phase"""
        tasks = []
        phase_name = phase["name"]
        num_tasks = phase["tasks"]
        
        # Calculate phase duration
        phase_duration_days = total_days // num_phases
        
        for i in range(num_tasks):
            task_id = f"{plan_id}_task_{start_counter + i}"
            
            # Task naming based on phase
            task_name = f"{phase_name} - Task {i+1}"
            description = f"Complete task {i+1} of {num_tasks} in {phase_name} phase"
            
            # Estimate hours (2-16 hours per task)
            estimated_hours = 4.0 + (i % 4) * 3.0
            
            # Priority distribution (critical: 10%, high: 30%, medium: 50%, low: 10%)
            if i < num_tasks * 0.1:
                priority = TaskPriority.CRITICAL
            elif i < num_tasks * 0.4:
                priority = TaskPriority.HIGH
            elif i < num_tasks * 0.9:
                priority = TaskPriority.MEDIUM
            else:
                priority = TaskPriority.LOW
            
            # Required skills based on phase
            required_skills = self._infer_skills(phase_name)
            
            task = ProjectTask(
                task_id=task_id,
                task_name=task_name,
                description=description,
                parent_task_id=None,
                estimated_hours=estimated_hours,
                priority=priority,
                required_skills=required_skills,
                required_resources=[]
            )
            
            tasks.append(task)
        
        return tasks
    
    def _infer_skills(self, phase_name: str) -> List[str]:
        """Infer required skills from phase name"""
        phase_lower = phase_name.lower()
        skills = []
        
        if "planning" in phase_lower or "strategy" in phase_lower:
            skills = ["Strategic Planning", "Project Management"]
        elif "design" in phase_lower or "architecture" in phase_lower:
            skills = ["System Design", "Architecture"]
        elif "implementation" in phase_lower or "development" in phase_lower:
            skills = ["Software Development", "Coding"]
        elif "testing" in phase_lower or "qa" in phase_lower:
            skills = ["Quality Assurance", "Testing"]
        elif "creative" in phase_lower or "content" in phase_lower:
            skills = ["Creative Design", "Content Creation"]
        elif "marketing" in phase_lower or "campaign" in phase_lower:
            skills = ["Digital Marketing", "Campaign Management"]
        else:
            skills = ["Project Execution", "Problem Solving"]
        
        return skills
    
    def _add_phase_dependencies(self, plan: ProjectPlan, phases: List[Dict[str, Any]]) -> None:
        """Add dependencies between phases (sequential execution)"""
        task_list = list(plan.tasks.values())
        
        tasks_per_phase = []
        start_idx = 0
        for phase in phases:
            end_idx = start_idx + phase["tasks"]
            phase_tasks = task_list[start_idx:end_idx]
            tasks_per_phase.append(phase_tasks)
            start_idx = end_idx
        
        # Make first task of each phase depend on last task of previous phase
        for i in range(1, len(tasks_per_phase)):
            if tasks_per_phase[i] and tasks_per_phase[i-1]:
                first_task = tasks_per_phase[i][0]
                last_task = tasks_per_phase[i-1][-1]
                
                first_task.depends_on.append(last_task.task_id)
                last_task.blocks.append(first_task.task_id)
    
    def _generate_milestones(
        self,
        plan: ProjectPlan,
        phases: List[Dict[str, Any]],
        start_date: datetime,
        total_days: int
    ) -> List[ProjectMilestone]:
        """Generate milestones for phases"""
        milestones = []
        task_list = list(plan.tasks.values())
        
        days_per_phase = total_days // len(phases)
        start_idx = 0
        
        for phase_idx, phase in enumerate(phases):
            end_idx = start_idx + phase["tasks"]
            phase_tasks = task_list[start_idx:end_idx]
            
            # Phase end milestone
            milestone_id = f"{plan.plan_id}_milestone_{phase_idx}"
            target_date = start_date + timedelta(days=(phase_idx + 1) * days_per_phase)
            
            milestone = ProjectMilestone(
                milestone_id=milestone_id,
                milestone_name=f"{phase['name']} Complete",
                milestone_type=MilestoneType.PHASE_END,
                description=f"Completion of {phase['name']} phase",
                target_date=target_date,
                required_tasks=[t.task_id for t in phase_tasks],
                deliverables=[f"{phase['name']} deliverables"]
            )
            
            milestones.append(milestone)
            start_idx = end_idx
        
        return milestones
    
    def _identify_risks(self, plan: ProjectPlan, complexity: str) -> List[ProjectRisk]:
        """Identify potential project risks"""
        risks = []
        
        # Risk 1: Schedule slippage
        risk_id = f"{plan.plan_id}_risk_1"
        risks.append(ProjectRisk(
            risk_id=risk_id,
            risk_description="Project schedule slippage due to underestimation",
            risk_level=RiskLevel.MEDIUM,
            probability=0.4,
            impact_hours=plan.total_estimated_hours * 0.2,
            mitigation_strategy="Add 20% buffer to estimates, track actual vs estimated weekly",
            contingency_plan="Reduce scope or extend deadline if slippage detected early"
        ))
        
        # Risk 2: Resource unavailability
        risk_id = f"{plan.plan_id}_risk_2"
        risks.append(ProjectRisk(
            risk_id=risk_id,
            risk_description="Key resources or agents become unavailable",
            risk_level=RiskLevel.HIGH if complexity == "high" else RiskLevel.MEDIUM,
            probability=0.3,
            impact_hours=plan.total_estimated_hours * 0.15,
            mitigation_strategy="Cross-train agents, maintain backup resource pool",
            contingency_plan="Reassign tasks to available agents or extend timeline"
        ))
        
        # Risk 3: Requirement changes
        risk_id = f"{plan.plan_id}_risk_3"
        risks.append(ProjectRisk(
            risk_id=risk_id,
            risk_description="Customer requirements change mid-project",
            risk_level=RiskLevel.MEDIUM,
            probability=0.5,
            impact_hours=plan.total_estimated_hours * 0.25,
            mitigation_strategy="Establish change control process, regular customer check-ins",
            contingency_plan="Assess impact, reprioritize tasks, negotiate timeline adjustment"
        ))
        
        # Risk 4: Technical challenges (for complex projects)
        if complexity in ["medium", "high"]:
            risk_id = f"{plan.plan_id}_risk_4"
            risks.append(ProjectRisk(
                risk_id=risk_id,
                risk_description="Unexpected technical challenges or blockers",
                risk_level=RiskLevel.HIGH if complexity == "high" else RiskLevel.MEDIUM,
                probability=0.4 if complexity == "high" else 0.25,
                impact_hours=plan.total_estimated_hours * 0.3,
                mitigation_strategy="Proof of concept for risky areas, technical spikes early",
                contingency_plan="Seek expert help, consider alternative approaches"
            ))
        
        return risks
    
    def update_task_progress(
        self,
        plan_id: str,
        task_id: str,
        progress_percentage: float,
        actual_hours: Optional[float] = None
    ) -> bool:
        """Update task progress"""
        if plan_id not in self._plans:
            return False
        
        plan = self._plans[plan_id]
        if task_id not in plan.tasks:
            return False
        
        task = plan.tasks[task_id]
        task.progress_percentage = max(0.0, min(100.0, progress_percentage))
        
        if actual_hours is not None:
            task.actual_hours = actual_hours
        
        # Update status based on progress
        if progress_percentage == 0.0:
            task.status = TaskStatus.NOT_STARTED
        elif progress_percentage < 100.0:
            task.status = TaskStatus.IN_PROGRESS
        else:
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
        
        # Recalculate plan metrics
        self._recalculate_plan_metrics(plan)
        plan.last_updated = datetime.utcnow()
        
        return True
    
    def _recalculate_plan_metrics(self, plan: ProjectPlan) -> None:
        """Recalculate plan-level metrics"""
        total_tasks = len(plan.tasks)
        if total_tasks == 0:
            plan.completion_percentage = 0.0
            return
        
        # Calculate completion percentage
        completed_tasks = sum(
            1 for t in plan.tasks.values() if t.status == TaskStatus.COMPLETED
        )
        plan.completion_percentage = (completed_tasks / total_tasks) * 100
        
        # Calculate total actual hours
        plan.total_actual_hours = sum(t.actual_hours for t in plan.tasks.values())
        
        # Check milestones
        for milestone in plan.milestones.values():
            if not milestone.is_achieved:
                # Check if all required tasks are complete
                all_complete = all(
                    plan.tasks[tid].status == TaskStatus.COMPLETED
                    for tid in milestone.required_tasks
                    if tid in plan.tasks
                )
                if all_complete:
                    milestone.is_achieved = True
                    milestone.actual_date = datetime.utcnow()
    
    def get_critical_path(self, plan_id: str) -> List[str]:
        """
        Get critical path (longest path of dependent tasks).
        Simplified version without full CPM algorithm.
        """
        if plan_id not in self._plans:
            return []
        
        plan = self._plans[plan_id]
        
        # Find tasks with no dependencies (starting points)
        start_tasks = [
            tid for tid, task in plan.tasks.items()
            if not task.depends_on
        ]
        
        # Find longest path from each start task
        max_path = []
        max_hours = 0.0
        
        for start_tid in start_tasks:
            path = self._find_longest_path(plan, start_tid)
            path_hours = sum(plan.tasks[tid].estimated_hours for tid in path)
            
            if path_hours > max_hours:
                max_hours = path_hours
                max_path = path
        
        return max_path
    
    def _find_longest_path(self, plan: ProjectPlan, task_id: str) -> List[str]:
        """Recursively find longest path from task"""
        task = plan.tasks.get(task_id)
        if not task:
            return []
        
        if not task.blocks:
            return [task_id]
        
        # Find longest path through blocked tasks
        max_path = []
        max_hours = 0.0
        
        for blocked_id in task.blocks:
            sub_path = self._find_longest_path(plan, blocked_id)
            sub_hours = sum(plan.tasks[tid].estimated_hours for tid in sub_path)
            
            if sub_hours > max_hours:
                max_hours = sub_hours
                max_path = sub_path
        
        return [task_id] + max_path
    
    def get_next_available_tasks(self, plan_id: str) -> List[ProjectTask]:
        """Get tasks that can be started now (all dependencies met)"""
        if plan_id not in self._plans:
            return []
        
        plan = self._plans[plan_id]
        available = []
        
        for task in plan.tasks.values():
            # Skip if already started or completed
            if task.status != TaskStatus.NOT_STARTED:
                continue
            
            # Check if all dependencies are complete
            all_deps_complete = all(
                plan.tasks[dep_id].status == TaskStatus.COMPLETED
                for dep_id in task.depends_on
                if dep_id in plan.tasks
            )
            
            if all_deps_complete:
                available.append(task)
        
        # Sort by priority
        priority_order = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3
        }
        available.sort(key=lambda t: priority_order[t.priority])
        
        return available
    
    def replan_based_on_progress(self, plan_id: str) -> Dict[str, Any]:
        """
        Analyze progress and suggest replanning if needed.
        """
        if plan_id not in self._plans:
            return {}
        
        plan = self._plans[plan_id]
        
        # Calculate schedule variance
        completed_tasks = [t for t in plan.tasks.values() if t.status == TaskStatus.COMPLETED]
        
        if not completed_tasks:
            return {"needs_replan": False, "reason": "No completed tasks yet"}
        
        # Compare estimated vs actual hours
        total_estimated = sum(t.estimated_hours for t in completed_tasks)
        total_actual = sum(t.actual_hours for t in completed_tasks)
        
        variance_ratio = total_actual / total_estimated if total_estimated > 0 else 1.0
        
        # Check if behind schedule
        needs_replan = False
        reason = ""
        suggestions = []
        
        if variance_ratio > 1.3:  # 30% over estimates
            needs_replan = True
            reason = f"Tasks taking {variance_ratio:.1f}x longer than estimated"
            suggestions = [
                "Reduce scope by removing low-priority tasks",
                "Increase resources/agents on remaining tasks",
                "Extend project deadline",
                "Parallelize more tasks if possible"
            ]
        elif plan.completion_percentage < 30 and variance_ratio > 1.15:
            needs_replan = True
            reason = "Early indication of schedule slippage"
            suggestions = [
                "Review estimates for remaining tasks",
                "Identify and address bottlenecks",
                "Consider adjusting task assignments"
            ]
        
        return {
            "needs_replan": needs_replan,
            "reason": reason,
            "suggestions": suggestions,
            "variance_ratio": variance_ratio,
            "completion_percentage": plan.completion_percentage,
            "estimated_hours": plan.total_estimated_hours,
            "actual_hours": plan.total_actual_hours
        }
    
    def get_plan_statistics(self, plan_id: str) -> Dict[str, Any]:
        """Get comprehensive plan statistics"""
        if plan_id not in self._plans:
            return {}
        
        plan = self._plans[plan_id]
        
        # Task status breakdown
        status_counts = {status: 0 for status in TaskStatus}
        for task in plan.tasks.values():
            status_counts[task.status] += 1
        
        # Priority breakdown
        priority_counts = {priority: 0 for priority in TaskPriority}
        for task in plan.tasks.values():
            priority_counts[task.priority] += 1
        
        # Milestone progress
        milestones_achieved = sum(1 for m in plan.milestones.values() if m.is_achieved)
        
        # Risk assessment
        high_risks = sum(
            1 for r in plan.risks.values()
            if r.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL] and not r.is_materialized
        )
        
        return {
            "plan_id": plan_id,
            "project_name": plan.project_name,
            "total_tasks": len(plan.tasks),
            "status_breakdown": {s.value: count for s, count in status_counts.items()},
            "priority_breakdown": {p.value: count for p, count in priority_counts.items()},
            "completion_percentage": plan.completion_percentage,
            "total_estimated_hours": plan.total_estimated_hours,
            "total_actual_hours": plan.total_actual_hours,
            "total_milestones": len(plan.milestones),
            "milestones_achieved": milestones_achieved,
            "total_risks": len(plan.risks),
            "high_risks_active": high_risks,
            "start_date": plan.start_date.isoformat(),
            "target_end_date": plan.target_end_date.isoformat(),
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get engine-wide statistics"""
        total_plans = len(self._plans)
        total_tasks = sum(len(p.tasks) for p in self._plans.values())
        total_milestones = sum(len(p.milestones) for p in self._plans.values())
        total_risks = sum(len(p.risks) for p in self._plans.values())
        
        # Completion stats
        completed_plans = sum(
            1 for p in self._plans.values() if p.completion_percentage == 100.0
        )
        
        # Average metrics
        avg_tasks_per_plan = total_tasks / total_plans if total_plans > 0 else 0
        avg_completion = (
            sum(p.completion_percentage for p in self._plans.values()) / total_plans
            if total_plans > 0 else 0
        )
        
        return {
            "total_plans": total_plans,
            "completed_plans": completed_plans,
            "total_tasks": total_tasks,
            "total_milestones": total_milestones,
            "total_risks": total_risks,
            "avg_tasks_per_plan": avg_tasks_per_plan,
            "avg_completion_percentage": avg_completion,
            "contributing_agents": len(self._plans_by_agent)
        }
