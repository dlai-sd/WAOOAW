"""
Continuous learning pipeline for automated agent improvement
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Callable
import uuid

from .pattern_detection import PatternDetector
from .feedback_analysis import FeedbackAnalyzer
from .performance_analysis import PerformanceAnalyzer
from .prompt_optimizer import PromptOptimizer


class AnalysisFrequency(Enum):
    """Analysis frequency options"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ImprovementAction(Enum):
    """Types of improvement actions"""
    OPTIMIZE_PROMPT = "optimize_prompt"
    UPDATE_CONFIGURATION = "update_configuration"
    SCALE_RESOURCES = "scale_resources"
    RETRAIN_MODEL = "retrain_model"
    NOTIFY_ADMIN = "notify_admin"


@dataclass
class ImprovementEvent:
    """Record of an improvement action"""
    event_id: str
    action_type: ImprovementAction
    trigger_reason: str
    agent_variant_id: Optional[str]
    prompt_id: Optional[str]
    details: Dict
    executed_at: datetime
    success: bool
    metadata: Dict = field(default_factory=dict)


@dataclass
class AnalysisSchedule:
    """Schedule configuration for periodic analysis"""
    schedule_id: str
    frequency: AnalysisFrequency
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0


class ContinuousLearningPipeline:
    """
    Continuous learning pipeline that orchestrates automated improvements.
    
    Features:
    - Periodic analysis scheduling
    - Automatic improvement triggers
    - Improvement history tracking
    - Integration with all improvement services
    """
    
    def __init__(
        self,
        pattern_detector: Optional[PatternDetector] = None,
        feedback_analyzer: Optional[FeedbackAnalyzer] = None,
        performance_analyzer: Optional[PerformanceAnalyzer] = None,
        prompt_optimizer: Optional[PromptOptimizer] = None,
    ):
        self._pattern_detector = pattern_detector or PatternDetector()
        self._feedback_analyzer = feedback_analyzer or FeedbackAnalyzer()
        self._performance_analyzer = performance_analyzer or PerformanceAnalyzer()
        self._prompt_optimizer = prompt_optimizer or PromptOptimizer()
        
        self._schedules: Dict[str, AnalysisSchedule] = {}
        self._improvement_history: List[ImprovementEvent] = []
        self._callbacks: Dict[ImprovementAction, List[Callable]] = {}
        
        # Improvement thresholds
        self._thresholds = {
            "low_success_rate": 0.75,  # Trigger if success rate < 75%
            "high_error_rate": 0.15,   # Trigger if error rate > 15%
            "slow_response": 3000,     # Trigger if avg response > 3000ms
            "low_satisfaction": 3.0,   # Trigger if rating < 3.0
            "min_feedback_count": 10,  # Minimum feedback for analysis
        }
    
    def configure_schedule(
        self,
        frequency: AnalysisFrequency,
        enabled: bool = True
    ) -> str:
        """Configure analysis schedule"""
        schedule_id = str(uuid.uuid4())
        
        schedule = AnalysisSchedule(
            schedule_id=schedule_id,
            frequency=frequency,
            enabled=enabled,
            next_run=self._calculate_next_run(frequency)
        )
        
        self._schedules[schedule_id] = schedule
        
        return schedule_id
    
    def _calculate_next_run(
        self,
        frequency: AnalysisFrequency,
        from_time: Optional[datetime] = None
    ) -> datetime:
        """Calculate next run time based on frequency"""
        base_time = from_time or datetime.now()
        
        if frequency == AnalysisFrequency.HOURLY:
            return base_time + timedelta(hours=1)
        elif frequency == AnalysisFrequency.DAILY:
            return base_time + timedelta(days=1)
        elif frequency == AnalysisFrequency.WEEKLY:
            return base_time + timedelta(weeks=1)
        elif frequency == AnalysisFrequency.MONTHLY:
            return base_time + timedelta(days=30)
        
        return base_time + timedelta(days=1)
    
    def register_callback(
        self,
        action_type: ImprovementAction,
        callback: Callable
    ):
        """Register callback for improvement actions"""
        if action_type not in self._callbacks:
            self._callbacks[action_type] = []
        
        self._callbacks[action_type].append(callback)
    
    def run_scheduled_analysis(self, schedule_id: str) -> Dict:
        """Run scheduled analysis"""
        if schedule_id not in self._schedules:
            raise ValueError(f"Schedule {schedule_id} not found")
        
        schedule = self._schedules[schedule_id]
        
        if not schedule.enabled:
            return {"status": "skipped", "reason": "schedule_disabled"}
        
        # Check if it's time to run
        now = datetime.now()
        if schedule.next_run and now < schedule.next_run:
            return {"status": "skipped", "reason": "not_time_yet"}
        
        # Run analysis
        results = self.analyze_and_improve()
        
        # Update schedule
        schedule.last_run = now
        schedule.next_run = self._calculate_next_run(schedule.frequency, now)
        schedule.run_count += 1
        
        return {
            "status": "completed",
            "schedule_id": schedule_id,
            "run_count": schedule.run_count,
            "next_run": schedule.next_run.isoformat(),
            "improvements": results
        }
    
    def analyze_and_improve(self) -> List[ImprovementEvent]:
        """
        Run comprehensive analysis and trigger improvements.
        
        Returns list of improvement events.
        """
        improvements = []
        
        # 1. Analyze patterns
        patterns = self._pattern_detector.detect_patterns()
        opportunities = self._pattern_detector.get_improvement_opportunities()
        
        for opp in opportunities:
            if opp["type"] == "fix_failure":
                improvement = self._trigger_failure_fix(opp)
                if improvement:
                    improvements.append(improvement)
            
            elif opp["type"] == "optimize_slow":
                improvement = self._trigger_performance_optimization(opp)
                if improvement:
                    improvements.append(improvement)
        
        # 2. Analyze feedback
        feedback_insights = self._feedback_analyzer.analyze_feedback()
        
        for insight in feedback_insights:
            if insight.severity in ["critical", "high"]:
                improvement = self._trigger_feedback_response(insight)
                if improvement:
                    improvements.append(improvement)
        
        # 3. Analyze performance
        performance_report = self._performance_analyzer.analyze_performance()
        
        for bottleneck in performance_report.bottlenecks:
            if bottleneck.severity in ["critical", "high"]:
                improvement = self._trigger_bottleneck_fix(bottleneck)
                if improvement:
                    improvements.append(improvement)
        
        # 4. Optimize prompts for underperforming agents
        stats = self._performance_analyzer.get_statistics()
        if stats["total_metrics"] >= self._thresholds["min_feedback_count"]:
            improvements.extend(self._optimize_underperforming_prompts())
        
        # Store improvement history
        self._improvement_history.extend(improvements)
        
        return improvements
    
    def _trigger_failure_fix(self, opportunity: Dict) -> Optional[ImprovementEvent]:
        """Trigger improvement for failure patterns"""
        event = ImprovementEvent(
            event_id=str(uuid.uuid4()),
            action_type=ImprovementAction.NOTIFY_ADMIN,
            trigger_reason=opportunity["description"],
            agent_variant_id=None,
            prompt_id=None,
            details=opportunity,
            executed_at=datetime.now(),
            success=True,
            metadata={"priority": "high"}
        )
        
        # Execute callbacks
        self._execute_callbacks(ImprovementAction.NOTIFY_ADMIN, event)
        
        return event
    
    def _trigger_performance_optimization(self, opportunity: Dict) -> Optional[ImprovementEvent]:
        """Trigger performance optimization"""
        event = ImprovementEvent(
            event_id=str(uuid.uuid4()),
            action_type=ImprovementAction.UPDATE_CONFIGURATION,
            trigger_reason=opportunity["description"],
            agent_variant_id=None,
            prompt_id=None,
            details=opportunity,
            executed_at=datetime.now(),
            success=True,
            metadata={"optimization_target": "response_time"}
        )
        
        self._execute_callbacks(ImprovementAction.UPDATE_CONFIGURATION, event)
        
        return event
    
    def _trigger_feedback_response(self, insight) -> Optional[ImprovementEvent]:
        """Trigger response to feedback insight"""
        action_type = ImprovementAction.NOTIFY_ADMIN
        
        if insight.category == "quality_issue":
            if "bug" in insight.description.lower():
                action_type = ImprovementAction.NOTIFY_ADMIN
            else:
                action_type = ImprovementAction.OPTIMIZE_PROMPT
        
        event = ImprovementEvent(
            event_id=str(uuid.uuid4()),
            action_type=action_type,
            trigger_reason=insight.description,
            agent_variant_id=insight.affected_agents[0] if insight.affected_agents else None,
            prompt_id=None,
            details={
                "category": insight.category,
                "severity": insight.severity,
                "recommendation": insight.recommendation
            },
            executed_at=datetime.now(),
            success=True
        )
        
        self._execute_callbacks(action_type, event)
        
        return event
    
    def _trigger_bottleneck_fix(self, bottleneck) -> Optional[ImprovementEvent]:
        """Trigger bottleneck fix"""
        action_type = ImprovementAction.UPDATE_CONFIGURATION
        
        if bottleneck.severity == "critical":
            action_type = ImprovementAction.SCALE_RESOURCES
        
        event = ImprovementEvent(
            event_id=str(uuid.uuid4()),
            action_type=action_type,
            trigger_reason=bottleneck.description,
            agent_variant_id=bottleneck.affected_agents[0] if bottleneck.affected_agents else None,
            prompt_id=None,
            details={
                "metric_type": str(bottleneck.metric_type.value) if hasattr(bottleneck.metric_type, 'value') else str(bottleneck.metric_type),
                "severity": bottleneck.severity,
                "current_value": bottleneck.current_value,
                "expected_value": bottleneck.expected_value,
                "recommendations": bottleneck.recommendations
            },
            executed_at=datetime.now(),
            success=True
        )
        
        self._execute_callbacks(action_type, event)
        
        return event
    
    def _optimize_underperforming_prompts(self) -> List[ImprovementEvent]:
        """Optimize prompts for underperforming agents"""
        improvements = []
        
        # Get all registered prompts
        # In production, this would query actual agent prompts
        # For now, return empty list as demonstration
        
        return improvements
    
    def _execute_callbacks(self, action_type: ImprovementAction, event: ImprovementEvent):
        """Execute registered callbacks for action type"""
        if action_type in self._callbacks:
            for callback in self._callbacks[action_type]:
                try:
                    callback(event)
                except Exception as e:
                    event.metadata["callback_error"] = str(e)
    
    def get_improvement_history(
        self,
        limit: Optional[int] = None,
        action_type: Optional[ImprovementAction] = None
    ) -> List[ImprovementEvent]:
        """Get improvement history"""
        history = self._improvement_history
        
        # Filter by action type
        if action_type:
            history = [e for e in history if e.action_type == action_type]
        
        # Sort by timestamp (most recent first)
        history = sorted(history, key=lambda e: e.executed_at, reverse=True)
        
        # Limit results
        if limit:
            history = history[:limit]
        
        return history
    
    def get_schedule_status(self, schedule_id: str) -> Dict:
        """Get schedule status"""
        if schedule_id not in self._schedules:
            raise ValueError(f"Schedule {schedule_id} not found")
        
        schedule = self._schedules[schedule_id]
        
        return {
            "schedule_id": schedule_id,
            "frequency": schedule.frequency.value,
            "enabled": schedule.enabled,
            "last_run": schedule.last_run.isoformat() if schedule.last_run else None,
            "next_run": schedule.next_run.isoformat() if schedule.next_run else None,
            "run_count": schedule.run_count
        }
    
    def enable_schedule(self, schedule_id: str):
        """Enable schedule"""
        if schedule_id not in self._schedules:
            raise ValueError(f"Schedule {schedule_id} not found")
        
        schedule = self._schedules[schedule_id]
        schedule.enabled = True
        
        if schedule.next_run is None:
            schedule.next_run = self._calculate_next_run(schedule.frequency)
    
    def disable_schedule(self, schedule_id: str):
        """Disable schedule"""
        if schedule_id not in self._schedules:
            raise ValueError(f"Schedule {schedule_id} not found")
        
        self._schedules[schedule_id].enabled = False
    
    def set_threshold(self, key: str, value: float):
        """Set improvement threshold"""
        if key not in self._thresholds:
            raise ValueError(f"Unknown threshold key: {key}")
        
        self._thresholds[key] = value
    
    def get_statistics(self) -> Dict:
        """Get pipeline statistics"""
        total_improvements = len(self._improvement_history)
        
        improvements_by_type = {}
        for event in self._improvement_history:
            action = event.action_type.value
            improvements_by_type[action] = improvements_by_type.get(action, 0) + 1
        
        successful_improvements = sum(1 for e in self._improvement_history if e.success)
        
        # Recent improvements (last 24 hours)
        now = datetime.now()
        recent_cutoff = now - timedelta(hours=24)
        recent_improvements = sum(
            1 for e in self._improvement_history
            if e.executed_at >= recent_cutoff
        )
        
        return {
            "total_improvements": total_improvements,
            "successful_improvements": successful_improvements,
            "success_rate": successful_improvements / total_improvements if total_improvements > 0 else 0.0,
            "improvements_by_type": improvements_by_type,
            "recent_improvements_24h": recent_improvements,
            "active_schedules": sum(1 for s in self._schedules.values() if s.enabled),
            "total_schedules": len(self._schedules),
            "registered_callbacks": sum(len(cbs) for cbs in self._callbacks.values()),
            "thresholds": self._thresholds.copy()
        }
