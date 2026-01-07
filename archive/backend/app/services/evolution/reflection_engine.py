"""
Reflection & Self-Evaluation Engine - Story 5.6.1

Epic 5.6: Self-Evolving Agent System

Agents critically evaluate their own outputs, identify patterns in performance,
compare to top agents, and create self-improvement plans.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from collections import defaultdict


class PerformanceMetric(Enum):
    """Key performance metrics for evaluation"""
    QUALITY = "quality"           # Output quality score
    SPEED = "speed"               # Task completion time
    ACCURACY = "accuracy"         # Correctness of output
    CREATIVITY = "creativity"     # Novel/creative solutions
    EFFICIENCY = "efficiency"     # Resource usage
    CUSTOMER_SATISFACTION = "customer_satisfaction"  # Customer ratings


class StrengthArea(Enum):
    """Areas where agent excels"""
    TECHNICAL_ACCURACY = "technical_accuracy"
    CREATIVE_PROBLEM_SOLVING = "creative_problem_solving"
    SPEED_EXECUTION = "speed_execution"
    ATTENTION_TO_DETAIL = "attention_to_detail"
    CUSTOMER_EMPATHY = "customer_empathy"
    COMPLEX_REASONING = "complex_reasoning"
    DOMAIN_EXPERTISE = "domain_expertise"
    ADAPTABILITY = "adaptability"


class WeaknessArea(Enum):
    """Areas needing improvement"""
    SLOW_EXECUTION = "slow_execution"
    INCONSISTENT_QUALITY = "inconsistent_quality"
    LIMITED_CREATIVITY = "limited_creativity"
    MISSING_EDGE_CASES = "missing_edge_cases"
    POOR_ERROR_HANDLING = "poor_error_handling"
    UNCLEAR_COMMUNICATION = "unclear_communication"
    NARROW_DOMAIN_KNOWLEDGE = "narrow_domain_knowledge"
    LACK_OF_PROACTIVITY = "lack_of_proactivity"


class ImprovementPriority(Enum):
    """Priority levels for improvement goals"""
    CRITICAL = "critical"     # Must fix immediately
    HIGH = "high"             # Important, address soon
    MEDIUM = "medium"         # Moderate impact
    LOW = "low"              # Nice to have


@dataclass
class TaskReflection:
    """Self-evaluation of a single task execution"""
    task_id: str
    agent_variant_id: str
    task_category: str
    task_description: str
    execution_time_seconds: float
    customer_rating: Optional[float]
    customer_feedback: Optional[str]
    
    # Self-assessment
    self_rating: float  # 0.0 to 5.0, agent's self-assessment
    what_went_well: List[str]
    what_could_improve: List[str]
    lessons_learned: List[str]
    would_do_differently: List[str]
    
    # Metrics
    quality_score: float  # 0.0 to 1.0
    speed_score: float    # 0.0 to 1.0
    accuracy_score: float # 0.0 to 1.0
    
    reflected_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "task_id": self.task_id,
            "agent_variant_id": self.agent_variant_id,
            "task_category": self.task_category,
            "task_description": self.task_description,
            "execution_time_seconds": self.execution_time_seconds,
            "customer_rating": self.customer_rating,
            "customer_feedback": self.customer_feedback,
            "self_rating": self.self_rating,
            "what_went_well": self.what_went_well,
            "what_could_improve": self.what_could_improve,
            "lessons_learned": self.lessons_learned,
            "would_do_differently": self.would_do_differently,
            "quality_score": self.quality_score,
            "speed_score": self.speed_score,
            "accuracy_score": self.accuracy_score,
            "reflected_at": self.reflected_at.isoformat(),
        }


@dataclass
class PerformanceAnalysis:
    """Analysis of performance patterns over time"""
    agent_variant_id: str
    analysis_period_days: int
    total_tasks: int
    
    # Average metrics
    avg_customer_rating: float
    avg_self_rating: float
    avg_quality_score: float
    avg_speed_score: float
    avg_accuracy_score: float
    avg_execution_time: float
    
    # Trends
    rating_trend: str  # "improving", "stable", "declining"
    quality_trend: str
    speed_trend: str
    
    # Task category breakdown
    category_performance: Dict[str, Dict[str, float]]  # category -> metrics
    
    # Identified patterns
    strengths: List[StrengthArea]
    weaknesses: List[WeaknessArea]
    
    # Top performing tasks
    best_tasks: List[str]  # task_ids
    worst_tasks: List[str]
    
    analyzed_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "agent_variant_id": self.agent_variant_id,
            "analysis_period_days": self.analysis_period_days,
            "total_tasks": self.total_tasks,
            "avg_customer_rating": self.avg_customer_rating,
            "avg_self_rating": self.avg_self_rating,
            "avg_quality_score": self.avg_quality_score,
            "avg_speed_score": self.avg_speed_score,
            "avg_accuracy_score": self.avg_accuracy_score,
            "avg_execution_time": self.avg_execution_time,
            "rating_trend": self.rating_trend,
            "quality_trend": self.quality_trend,
            "speed_trend": self.speed_trend,
            "category_performance": self.category_performance,
            "strengths": [s.value for s in self.strengths],
            "weaknesses": [w.value for w in self.weaknesses],
            "best_tasks": self.best_tasks,
            "worst_tasks": self.worst_tasks,
            "analyzed_at": self.analyzed_at.isoformat(),
        }


@dataclass
class GapAnalysis:
    """Comparison to top-performing agents"""
    agent_variant_id: str
    comparison_agents: List[str]  # Top agent IDs compared against
    
    # Performance gaps
    rating_gap: float  # Difference from top agents
    quality_gap: float
    speed_gap: float
    
    # Capability gaps
    missing_skills: List[str]
    underdeveloped_areas: List[WeaknessArea]
    
    # Opportunities
    improvement_opportunities: List[str]
    potential_specializations: List[str]
    
    analyzed_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "agent_variant_id": self.agent_variant_id,
            "comparison_agents": self.comparison_agents,
            "rating_gap": self.rating_gap,
            "quality_gap": self.quality_gap,
            "speed_gap": self.speed_gap,
            "missing_skills": self.missing_skills,
            "underdeveloped_areas": [a.value for a in self.underdeveloped_areas],
            "improvement_opportunities": self.improvement_opportunities,
            "potential_specializations": self.potential_specializations,
            "analyzed_at": self.analyzed_at.isoformat(),
        }


@dataclass
class ImprovementGoal:
    """Specific improvement goal with measurable target"""
    goal_id: str
    agent_variant_id: str
    priority: ImprovementPriority
    target_area: WeaknessArea
    
    current_performance: float  # 0.0 to 1.0
    target_performance: float   # 0.0 to 1.0
    
    goal_description: str
    success_criteria: List[str]
    timeline_days: int
    
    status: str  # "not_started", "in_progress", "achieved", "abandoned"
    progress: float  # 0.0 to 1.0
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "goal_id": self.goal_id,
            "agent_variant_id": self.agent_variant_id,
            "priority": self.priority.value,
            "target_area": self.target_area.value,
            "current_performance": self.current_performance,
            "target_performance": self.target_performance,
            "goal_description": self.goal_description,
            "success_criteria": self.success_criteria,
            "timeline_days": self.timeline_days,
            "status": self.status,
            "progress": self.progress,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class LearningTask:
    """Self-assigned learning task for improvement"""
    learning_task_id: str
    agent_variant_id: str
    goal_id: str  # Related improvement goal
    
    task_type: str  # "practice", "study", "experiment", "review"
    task_description: str
    resources_needed: List[str]
    estimated_time_hours: float
    
    status: str  # "planned", "in_progress", "completed", "skipped"
    completion_notes: Optional[str]
    effectiveness_rating: Optional[float]  # 0.0 to 5.0
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "learning_task_id": self.learning_task_id,
            "agent_variant_id": self.agent_variant_id,
            "goal_id": self.goal_id,
            "task_type": self.task_type,
            "task_description": self.task_description,
            "resources_needed": self.resources_needed,
            "estimated_time_hours": self.estimated_time_hours,
            "status": self.status,
            "completion_notes": self.completion_notes,
            "effectiveness_rating": self.effectiveness_rating,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class ReflectionEngine:
    """
    Agent self-reflection and continuous improvement system.
    
    Enables agents to evaluate their own performance, identify gaps,
    set improvement goals, and create learning plans autonomously.
    """
    
    def __init__(self):
        self._reflections: Dict[str, TaskReflection] = {}  # task_id -> reflection
        self._agent_reflections: Dict[str, List[str]] = defaultdict(list)  # agent -> task_ids
        self._performance_analyses: Dict[str, List[PerformanceAnalysis]] = defaultdict(list)
        self._gap_analyses: Dict[str, List[GapAnalysis]] = defaultdict(list)
        self._improvement_goals: Dict[str, ImprovementGoal] = {}  # goal_id -> goal
        self._agent_goals: Dict[str, List[str]] = defaultdict(list)  # agent -> goal_ids
        self._learning_tasks: Dict[str, LearningTask] = {}  # learning_task_id -> task
        self._goal_tasks: Dict[str, List[str]] = defaultdict(list)  # goal_id -> learning_task_ids
    
    def reflect_on_task(
        self,
        task_id: str,
        agent_variant_id: str,
        task_category: str,
        task_description: str,
        execution_time_seconds: float,
        output: str,
        customer_rating: Optional[float] = None,
        customer_feedback: Optional[str] = None
    ) -> TaskReflection:
        """
        Agent reflects on completed task, evaluating its own performance.
        """
        # Self-assessment based on various factors
        self_rating = self._calculate_self_rating(
            customer_rating, execution_time_seconds, output, customer_feedback
        )
        
        # Identify what went well
        what_went_well = self._identify_positives(
            task_category, output, customer_rating, customer_feedback
        )
        
        # Identify improvements
        what_could_improve = self._identify_improvements(
            task_category, output, execution_time_seconds, customer_feedback
        )
        
        # Extract lessons
        lessons_learned = self._extract_lessons(
            task_category, customer_rating, customer_feedback
        )
        
        # What to do differently
        would_do_differently = self._suggest_alternatives(
            task_category, what_could_improve
        )
        
        # Calculate metric scores
        quality_score = self._calculate_quality_score(output, customer_rating)
        speed_score = self._calculate_speed_score(execution_time_seconds, task_category)
        accuracy_score = self._calculate_accuracy_score(output, customer_feedback)
        
        reflection = TaskReflection(
            task_id=task_id,
            agent_variant_id=agent_variant_id,
            task_category=task_category,
            task_description=task_description,
            execution_time_seconds=execution_time_seconds,
            customer_rating=customer_rating,
            customer_feedback=customer_feedback,
            self_rating=self_rating,
            what_went_well=what_went_well,
            what_could_improve=what_could_improve,
            lessons_learned=lessons_learned,
            would_do_differently=would_do_differently,
            quality_score=quality_score,
            speed_score=speed_score,
            accuracy_score=accuracy_score
        )
        
        self._reflections[task_id] = reflection
        self._agent_reflections[agent_variant_id].append(task_id)
        
        # Keep only last 100 reflections per agent
        if len(self._agent_reflections[agent_variant_id]) > 100:
            oldest_task_id = self._agent_reflections[agent_variant_id].pop(0)
            if oldest_task_id in self._reflections:
                del self._reflections[oldest_task_id]
        
        return reflection
    
    def analyze_performance(
        self,
        agent_variant_id: str,
        period_days: int = 30
    ) -> PerformanceAnalysis:
        """
        Analyze agent's performance patterns over time period.
        """
        task_ids = self._agent_reflections.get(agent_variant_id, [])
        if not task_ids:
            # Return empty analysis
            return PerformanceAnalysis(
                agent_variant_id=agent_variant_id,
                analysis_period_days=period_days,
                total_tasks=0,
                avg_customer_rating=0.0,
                avg_self_rating=0.0,
                avg_quality_score=0.0,
                avg_speed_score=0.0,
                avg_accuracy_score=0.0,
                avg_execution_time=0.0,
                rating_trend="stable",
                quality_trend="stable",
                speed_trend="stable",
                category_performance={},
                strengths=[],
                weaknesses=[],
                best_tasks=[],
                worst_tasks=[]
            )
        
        reflections = [self._reflections[tid] for tid in task_ids if tid in self._reflections]
        
        # Calculate averages
        total_tasks = len(reflections)
        avg_customer_rating = self._calculate_average(
            [r.customer_rating for r in reflections if r.customer_rating is not None]
        )
        avg_self_rating = self._calculate_average([r.self_rating for r in reflections])
        avg_quality_score = self._calculate_average([r.quality_score for r in reflections])
        avg_speed_score = self._calculate_average([r.speed_score for r in reflections])
        avg_accuracy_score = self._calculate_average([r.accuracy_score for r in reflections])
        avg_execution_time = self._calculate_average([r.execution_time_seconds for r in reflections])
        
        # Determine trends
        rating_trend = self._determine_trend([r.customer_rating for r in reflections if r.customer_rating])
        quality_trend = self._determine_trend([r.quality_score for r in reflections])
        speed_trend = self._determine_trend([r.speed_score for r in reflections])
        
        # Category breakdown
        category_performance = self._analyze_by_category(reflections)
        
        # Identify strengths and weaknesses
        strengths = self._identify_strengths(reflections, avg_quality_score, avg_speed_score)
        weaknesses = self._identify_weaknesses(reflections, avg_quality_score, avg_speed_score)
        
        # Best/worst tasks
        best_tasks = self._identify_best_tasks(reflections, top_n=5)
        worst_tasks = self._identify_worst_tasks(reflections, top_n=5)
        
        analysis = PerformanceAnalysis(
            agent_variant_id=agent_variant_id,
            analysis_period_days=period_days,
            total_tasks=total_tasks,
            avg_customer_rating=avg_customer_rating,
            avg_self_rating=avg_self_rating,
            avg_quality_score=avg_quality_score,
            avg_speed_score=avg_speed_score,
            avg_accuracy_score=avg_accuracy_score,
            avg_execution_time=avg_execution_time,
            rating_trend=rating_trend,
            quality_trend=quality_trend,
            speed_trend=speed_trend,
            category_performance=category_performance,
            strengths=strengths,
            weaknesses=weaknesses,
            best_tasks=best_tasks,
            worst_tasks=worst_tasks
        )
        
        self._performance_analyses[agent_variant_id].append(analysis)
        return analysis
    
    def identify_gaps(
        self,
        agent_variant_id: str,
        top_agent_ids: List[str]
    ) -> GapAnalysis:
        """
        Compare agent to top performers and identify capability gaps.
        """
        # Get agent's performance
        agent_analysis = self.analyze_performance(agent_variant_id)
        
        # Get top agents' performance (simulated for now)
        top_avg_rating = 4.5  # Would query actual top agents
        top_avg_quality = 0.9
        top_avg_speed = 0.85
        
        # Calculate gaps
        rating_gap = top_avg_rating - agent_analysis.avg_customer_rating
        quality_gap = top_avg_quality - agent_analysis.avg_quality_score
        speed_gap = top_avg_speed - agent_analysis.avg_speed_score
        
        # Identify missing skills
        missing_skills = self._identify_missing_skills(agent_analysis, top_agent_ids)
        
        # Underdeveloped areas
        underdeveloped = agent_analysis.weaknesses
        
        # Improvement opportunities
        opportunities = self._identify_opportunities(
            agent_analysis, rating_gap, quality_gap, speed_gap
        )
        
        # Potential specializations
        specializations = self._identify_specializations(agent_analysis)
        
        gap_analysis = GapAnalysis(
            agent_variant_id=agent_variant_id,
            comparison_agents=top_agent_ids,
            rating_gap=rating_gap,
            quality_gap=quality_gap,
            speed_gap=speed_gap,
            missing_skills=missing_skills,
            underdeveloped_areas=underdeveloped,
            improvement_opportunities=opportunities,
            potential_specializations=specializations
        )
        
        self._gap_analyses[agent_variant_id].append(gap_analysis)
        return gap_analysis
    
    def create_improvement_plan(
        self,
        agent_variant_id: str,
        gap_analysis: GapAnalysis
    ) -> List[ImprovementGoal]:
        """
        Create improvement plan with prioritized goals.
        """
        goals = []
        
        # Goal 1: Address largest rating gap if significant
        if gap_analysis.rating_gap > 0.5:
            goal_id = f"goal_{agent_variant_id}_{datetime.utcnow().timestamp()}_quality"
            goal = ImprovementGoal(
                goal_id=goal_id,
                agent_variant_id=agent_variant_id,
                priority=ImprovementPriority.HIGH,
                target_area=WeaknessArea.INCONSISTENT_QUALITY,
                current_performance=max(0.0, 1.0 - gap_analysis.quality_gap),
                target_performance=0.9,
                goal_description="Improve output quality to match top agents",
                success_criteria=[
                    "Achieve average customer rating >= 4.5",
                    "Quality score consistently >= 0.9",
                    "Reduce low-rating tasks by 50%"
                ],
                timeline_days=30,
                status="not_started",
                progress=0.0
            )
            goals.append(goal)
            self._improvement_goals[goal_id] = goal
            self._agent_goals[agent_variant_id].append(goal_id)
        
        # Goal 2: Address speed if needed
        if gap_analysis.speed_gap > 0.2:
            goal_id = f"goal_{agent_variant_id}_{datetime.utcnow().timestamp()}_speed"
            goal = ImprovementGoal(
                goal_id=goal_id,
                agent_variant_id=agent_variant_id,
                priority=ImprovementPriority.MEDIUM,
                target_area=WeaknessArea.SLOW_EXECUTION,
                current_performance=max(0.0, 1.0 - gap_analysis.speed_gap),
                target_performance=0.85,
                goal_description="Improve task execution speed",
                success_criteria=[
                    "Reduce average execution time by 25%",
                    "Complete 90% of tasks within time budget"
                ],
                timeline_days=45,
                status="not_started",
                progress=0.0
            )
            goals.append(goal)
            self._improvement_goals[goal_id] = goal
            self._agent_goals[agent_variant_id].append(goal_id)
        
        # Goal 3: Develop underdeveloped areas
        for weakness in gap_analysis.underdeveloped_areas[:2]:  # Top 2 weaknesses
            goal_id = f"goal_{agent_variant_id}_{datetime.utcnow().timestamp()}_{weakness.value}"
            goal = ImprovementGoal(
                goal_id=goal_id,
                agent_variant_id=agent_variant_id,
                priority=ImprovementPriority.MEDIUM,
                target_area=weakness,
                current_performance=0.6,  # Assumed current
                target_performance=0.8,
                goal_description=f"Improve {weakness.value.replace('_', ' ')}",
                success_criteria=[
                    f"Demonstrate improvement in {weakness.value}",
                    "Apply learned techniques in 10+ tasks"
                ],
                timeline_days=60,
                status="not_started",
                progress=0.0
            )
            goals.append(goal)
            self._improvement_goals[goal_id] = goal
            self._agent_goals[agent_variant_id].append(goal_id)
        
        return goals
    
    def assign_learning_tasks(
        self,
        goal_id: str
    ) -> List[LearningTask]:
        """
        Generate learning tasks for an improvement goal.
        """
        if goal_id not in self._improvement_goals:
            return []
        
        goal = self._improvement_goals[goal_id]
        tasks = []
        
        # Task 1: Study best practices
        task_id = f"learning_{goal_id}_study_{datetime.utcnow().timestamp()}"
        study_task = LearningTask(
            learning_task_id=task_id,
            agent_variant_id=goal.agent_variant_id,
            goal_id=goal_id,
            task_type="study",
            task_description=f"Study top agent approaches for {goal.target_area.value}",
            resources_needed=["Best practice documentation", "Example tasks"],
            estimated_time_hours=4.0,
            status="planned",
            completion_notes=None,
            effectiveness_rating=None
        )
        tasks.append(study_task)
        self._learning_tasks[task_id] = study_task
        self._goal_tasks[goal_id].append(task_id)
        
        # Task 2: Practice exercises
        task_id = f"learning_{goal_id}_practice_{datetime.utcnow().timestamp()}"
        practice_task = LearningTask(
            learning_task_id=task_id,
            agent_variant_id=goal.agent_variant_id,
            goal_id=goal_id,
            task_type="practice",
            task_description=f"Complete 20 practice tasks focused on {goal.target_area.value}",
            resources_needed=["Practice dataset", "Feedback mechanism"],
            estimated_time_hours=10.0,
            status="planned",
            completion_notes=None,
            effectiveness_rating=None
        )
        tasks.append(practice_task)
        self._learning_tasks[task_id] = practice_task
        self._goal_tasks[goal_id].append(task_id)
        
        # Task 3: Experimentation
        task_id = f"learning_{goal_id}_experiment_{datetime.utcnow().timestamp()}"
        experiment_task = LearningTask(
            learning_task_id=task_id,
            agent_variant_id=goal.agent_variant_id,
            goal_id=goal_id,
            task_type="experiment",
            task_description=f"Try 3 different approaches and compare results",
            resources_needed=["Test environment", "Evaluation metrics"],
            estimated_time_hours=6.0,
            status="planned",
            completion_notes=None,
            effectiveness_rating=None
        )
        tasks.append(experiment_task)
        self._learning_tasks[task_id] = experiment_task
        self._goal_tasks[goal_id].append(task_id)
        
        return tasks
    
    def get_agent_reflection_summary(self, agent_variant_id: str) -> Dict[str, Any]:
        """Get comprehensive reflection summary for agent"""
        task_ids = self._agent_reflections.get(agent_variant_id, [])
        reflections = [self._reflections[tid] for tid in task_ids if tid in self._reflections]
        
        # Recent performance
        recent_10 = reflections[-10:] if len(reflections) >= 10 else reflections
        
        # Active goals
        goal_ids = self._agent_goals.get(agent_variant_id, [])
        active_goals = [
            self._improvement_goals[gid] for gid in goal_ids 
            if gid in self._improvement_goals and self._improvement_goals[gid].status != "achieved"
        ]
        
        return {
            "agent_variant_id": agent_variant_id,
            "total_reflections": len(reflections),
            "recent_average_rating": self._calculate_average([r.customer_rating for r in recent_10 if r.customer_rating]),
            "recent_lessons": [lesson for r in recent_10 for lesson in r.lessons_learned],
            "active_goals_count": len(active_goals),
            "active_goals": [g.goal_description for g in active_goals],
            "reflection_frequency": "after_each_task"
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get reflection engine statistics"""
        total_reflections = len(self._reflections)
        total_agents = len(self._agent_reflections)
        total_goals = len(self._improvement_goals)
        total_learning_tasks = len(self._learning_tasks)
        
        # Goal status breakdown
        achieved_goals = sum(1 for g in self._improvement_goals.values() if g.status == "achieved")
        in_progress_goals = sum(1 for g in self._improvement_goals.values() if g.status == "in_progress")
        
        # Learning task completion
        completed_tasks = sum(1 for t in self._learning_tasks.values() if t.status == "completed")
        
        return {
            "total_reflections": total_reflections,
            "agents_with_reflections": total_agents,
            "total_improvement_goals": total_goals,
            "achieved_goals": achieved_goals,
            "in_progress_goals": in_progress_goals,
            "total_learning_tasks": total_learning_tasks,
            "completed_learning_tasks": completed_tasks,
            "average_reflections_per_agent": total_reflections / total_agents if total_agents > 0 else 0
        }
    
    # Private helper methods
    
    def _calculate_self_rating(
        self,
        customer_rating: Optional[float],
        execution_time: float,
        output: str,
        feedback: Optional[str]
    ) -> float:
        """Calculate agent's self-rating"""
        if customer_rating is not None:
            return customer_rating  # Align with customer initially
        
        # Heuristic based on execution time and output length
        base_rating = 3.5
        if execution_time < 60:  # Fast execution
            base_rating += 0.5
        if len(output) > 500:  # Comprehensive output
            base_rating += 0.5
        
        return min(base_rating, 5.0)
    
    def _identify_positives(
        self,
        task_category: str,
        output: str,
        rating: Optional[float],
        feedback: Optional[str]
    ) -> List[str]:
        """Identify what went well"""
        positives = []
        
        if rating and rating >= 4.0:
            positives.append("High customer satisfaction achieved")
        
        if output and len(output) > 300:
            positives.append("Comprehensive and detailed output")
        
        if feedback and any(word in feedback.lower() for word in ["excellent", "great", "perfect"]):
            positives.append("Positive customer feedback received")
        
        positives.append(f"Successfully completed {task_category} task")
        
        return positives
    
    def _identify_improvements(
        self,
        task_category: str,
        output: str,
        execution_time: float,
        feedback: Optional[str]
    ) -> List[str]:
        """Identify areas for improvement"""
        improvements = []
        
        if execution_time > 300:  # Over 5 minutes
            improvements.append("Execution time could be faster")
        
        if output and len(output) < 100:
            improvements.append("Output could be more detailed")
        
        if feedback and any(word in feedback.lower() for word in ["missing", "incomplete", "more"]):
            improvements.append("Could provide more comprehensive coverage")
        
        return improvements
    
    def _extract_lessons(
        self,
        task_category: str,
        rating: Optional[float],
        feedback: Optional[str]
    ) -> List[str]:
        """Extract lessons learned"""
        lessons = []
        
        if rating and rating < 3.0:
            lessons.append(f"Customer expectations for {task_category} may differ from approach used")
        
        if feedback:
            lessons.append(f"Customer feedback provides valuable insights for {task_category}")
        
        lessons.append(f"Each {task_category} task provides learning opportunity")
        
        return lessons
    
    def _suggest_alternatives(
        self,
        task_category: str,
        improvements: List[str]
    ) -> List[str]:
        """Suggest alternative approaches"""
        alternatives = []
        
        if any("faster" in imp.lower() for imp in improvements):
            alternatives.append("Could optimize approach for speed")
        
        if any("detailed" in imp.lower() for imp in improvements):
            alternatives.append("Could expand on key points")
        
        if any("comprehensive" in imp.lower() for imp in improvements):
            alternatives.append("Could break task into smaller steps")
        
        return alternatives
    
    def _calculate_quality_score(self, output: str, rating: Optional[float]) -> float:
        """Calculate quality score"""
        if rating is not None:
            return rating / 5.0
        return 0.7  # Default
    
    def _calculate_speed_score(self, execution_time: float, task_category: str) -> float:
        """Calculate speed score"""
        # Inverse relationship with time
        if execution_time < 60:
            return 1.0
        elif execution_time < 180:
            return 0.8
        elif execution_time < 300:
            return 0.6
        else:
            return 0.4
    
    def _calculate_accuracy_score(self, output: str, feedback: Optional[str]) -> float:
        """Calculate accuracy score"""
        if feedback and any(word in feedback.lower() for word in ["accurate", "correct", "right"]):
            return 0.95
        if feedback and any(word in feedback.lower() for word in ["wrong", "incorrect", "error"]):
            return 0.4
        return 0.8  # Default
    
    def _calculate_average(self, values: List[float]) -> float:
        """Calculate average of values"""
        if not values:
            return 0.0
        return sum(values) / len(values)
    
    def _determine_trend(self, values: List[float]) -> str:
        """Determine trend from time series"""
        if len(values) < 5:
            return "stable"
        
        recent_5 = values[-5:]
        previous_5 = values[-10:-5] if len(values) >= 10 else values[:-5]
        
        if not previous_5:
            return "stable"
        
        recent_avg = sum(recent_5) / len(recent_5)
        previous_avg = sum(previous_5) / len(previous_5)
        
        diff = recent_avg - previous_avg
        
        if diff > 0.2:
            return "improving"
        elif diff < -0.2:
            return "declining"
        else:
            return "stable"
    
    def _analyze_by_category(self, reflections: List[TaskReflection]) -> Dict[str, Dict[str, float]]:
        """Analyze performance by task category"""
        category_data = defaultdict(list)
        
        for r in reflections:
            category_data[r.task_category].append({
                "rating": r.customer_rating if r.customer_rating else 0,
                "quality": r.quality_score,
                "speed": r.speed_score
            })
        
        result = {}
        for category, data in category_data.items():
            result[category] = {
                "avg_rating": self._calculate_average([d["rating"] for d in data if d["rating"] > 0]),
                "avg_quality": self._calculate_average([d["quality"] for d in data]),
                "avg_speed": self._calculate_average([d["speed"] for d in data]),
                "count": len(data)
            }
        
        return result
    
    def _identify_strengths(
        self,
        reflections: List[TaskReflection],
        avg_quality: float,
        avg_speed: float
    ) -> List[StrengthArea]:
        """Identify agent strengths"""
        strengths = []
        
        if avg_quality >= 0.85:
            strengths.append(StrengthArea.TECHNICAL_ACCURACY)
        
        if avg_speed >= 0.8:
            strengths.append(StrengthArea.SPEED_EXECUTION)
        
        # Check for consistent high ratings
        high_ratings = sum(1 for r in reflections if r.customer_rating and r.customer_rating >= 4.5)
        if high_ratings / len(reflections) > 0.7:
            strengths.append(StrengthArea.CUSTOMER_EMPATHY)
        
        return strengths
    
    def _identify_weaknesses(
        self,
        reflections: List[TaskReflection],
        avg_quality: float,
        avg_speed: float
    ) -> List[WeaknessArea]:
        """Identify agent weaknesses"""
        weaknesses = []
        
        if avg_quality < 0.7:
            weaknesses.append(WeaknessArea.INCONSISTENT_QUALITY)
        
        if avg_speed < 0.6:
            weaknesses.append(WeaknessArea.SLOW_EXECUTION)
        
        # Check for error patterns in feedback
        error_mentions = sum(
            1 for r in reflections 
            if r.customer_feedback and "error" in r.customer_feedback.lower()
        )
        if error_mentions > len(reflections) * 0.1:
            weaknesses.append(WeaknessArea.POOR_ERROR_HANDLING)
        
        return weaknesses
    
    def _identify_best_tasks(self, reflections: List[TaskReflection], top_n: int = 5) -> List[str]:
        """Identify best performing tasks"""
        sorted_reflections = sorted(
            reflections,
            key=lambda r: (r.customer_rating if r.customer_rating else 0, r.quality_score),
            reverse=True
        )
        return [r.task_id for r in sorted_reflections[:top_n]]
    
    def _identify_worst_tasks(self, reflections: List[TaskReflection], top_n: int = 5) -> List[str]:
        """Identify worst performing tasks"""
        sorted_reflections = sorted(
            reflections,
            key=lambda r: (r.customer_rating if r.customer_rating else 5, r.quality_score)
        )
        return [r.task_id for r in sorted_reflections[:top_n]]
    
    def _identify_missing_skills(self, analysis: PerformanceAnalysis, top_agents: List[str]) -> List[str]:
        """Identify skills missing compared to top agents"""
        # Would query actual top agents in production
        potential_missing = []
        
        if analysis.avg_quality_score < 0.85:
            potential_missing.append("Advanced quality control techniques")
        
        if analysis.avg_speed_score < 0.75:
            potential_missing.append("Efficient workflow optimization")
        
        return potential_missing
    
    def _identify_opportunities(
        self,
        analysis: PerformanceAnalysis,
        rating_gap: float,
        quality_gap: float,
        speed_gap: float
    ) -> List[str]:
        """Identify improvement opportunities"""
        opportunities = []
        
        if quality_gap > 0.1:
            opportunities.append("Implement quality improvement processes")
        
        if speed_gap > 0.1:
            opportunities.append("Optimize task execution workflow")
        
        if rating_gap > 0.3:
            opportunities.append("Study top-rated agent approaches")
        
        return opportunities
    
    def _identify_specializations(self, analysis: PerformanceAnalysis) -> List[str]:
        """Identify potential specialization areas"""
        specializations = []
        
        # Find categories where agent performs best
        sorted_categories = sorted(
            analysis.category_performance.items(),
            key=lambda x: x[1].get("avg_quality", 0),
            reverse=True
        )
        
        for category, metrics in sorted_categories[:3]:
            if metrics.get("avg_quality", 0) >= 0.85:
                specializations.append(f"{category.replace('_', ' ').title()} specialist")
        
        return specializations
