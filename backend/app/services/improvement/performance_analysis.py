"""
Performance Analysis System

Analyzes agent performance metrics to identify bottlenecks.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from collections import defaultdict
import statistics


class MetricType(str, Enum):
    """Type of performance metric"""
    RESPONSE_TIME = "response_time"
    SUCCESS_RATE = "success_rate"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    RESOURCE_USAGE = "resource_usage"


@dataclass
class PerformanceMetric:
    """Performance metric data point"""
    metric_type: MetricType
    agent_variant_id: str
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Bottleneck:
    """Identified performance bottleneck"""
    bottleneck_id: str
    description: str
    severity: str  # low, medium, high, critical
    affected_agents: List[str]
    metric_type: MetricType
    current_value: float
    expected_value: float
    impact: str
    recommendations: List[str] = field(default_factory=list)
    detected_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PerformanceReport:
    """Comprehensive performance report"""
    report_id: str
    generated_at: datetime
    summary: Dict[str, Any]
    metrics_by_agent: Dict[str, Dict[str, float]]
    bottlenecks: List[Bottleneck]
    recommendations: List[str]


class PerformanceAnalyzer:
    """
    Analyzes agent performance metrics.
    
    Identifies bottlenecks, efficiency issues, and optimization opportunities.
    """
    
    def __init__(self):
        """Initialize performance analyzer"""
        self._metrics: List[PerformanceMetric] = []
        self._bottlenecks: List[Bottleneck] = []
    
    def record_metric(self, metric: PerformanceMetric):
        """Record performance metric"""
        self._metrics.append(metric)
    
    def analyze_performance(self) -> PerformanceReport:
        """
        Analyze performance metrics.
        
        Returns:
            Comprehensive performance report
        """
        # Detect bottlenecks
        bottlenecks = self._detect_bottlenecks()
        
        # Calculate metrics by agent
        metrics_by_agent = self._calculate_agent_metrics()
        
        # Generate summary
        summary = self._generate_summary()
        
        # Generate recommendations
        recommendations = self._generate_recommendations(bottlenecks)
        
        report = PerformanceReport(
            report_id=f"perf_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            generated_at=datetime.utcnow(),
            summary=summary,
            metrics_by_agent=metrics_by_agent,
            bottlenecks=bottlenecks,
            recommendations=recommendations
        )
        
        return report
    
    def _detect_bottlenecks(self) -> List[Bottleneck]:
        """Detect performance bottlenecks"""
        bottlenecks = []
        
        # Analyze response times
        response_time_bottlenecks = self._detect_slow_agents()
        bottlenecks.extend(response_time_bottlenecks)
        
        # Analyze success rates
        success_rate_bottlenecks = self._detect_low_success_agents()
        bottlenecks.extend(success_rate_bottlenecks)
        
        # Analyze error rates
        error_rate_bottlenecks = self._detect_high_error_agents()
        bottlenecks.extend(error_rate_bottlenecks)
        
        self._bottlenecks = bottlenecks
        return bottlenecks
    
    def _detect_slow_agents(self) -> List[Bottleneck]:
        """Detect agents with slow response times"""
        bottlenecks = []
        
        # Get response time metrics
        response_times = [
            m for m in self._metrics 
            if m.metric_type == MetricType.RESPONSE_TIME
        ]
        
        if len(response_times) < 10:
            return bottlenecks
        
        # Calculate baseline (median)
        all_times = [m.value for m in response_times]
        baseline = statistics.median(all_times)
        threshold = baseline * 1.5  # 50% slower than median
        
        # Group by agent
        agent_times = defaultdict(list)
        for metric in response_times:
            agent_times[metric.agent_variant_id].append(metric.value)
        
        # Find slow agents
        for agent, times in agent_times.items():
            if len(times) >= 5:
                avg_time = sum(times) / len(times)
                
                if avg_time > threshold:
                    bottlenecks.append(Bottleneck(
                        bottleneck_id=f"slow_response_{agent}",
                        description=f"Agent '{agent}' has slow response time: {int(avg_time)}ms (baseline: {int(baseline)}ms)",
                        severity="high" if avg_time > baseline * 2 else "medium",
                        affected_agents=[agent],
                        metric_type=MetricType.RESPONSE_TIME,
                        current_value=avg_time,
                        expected_value=baseline,
                        impact=f"{int((avg_time - baseline) / baseline * 100)}% slower than baseline",
                        recommendations=[
                            "Profile agent execution to identify slow operations",
                            "Optimize prompt length and complexity",
                            "Consider caching frequently used responses",
                            "Review and optimize API calls"
                        ]
                    ))
        
        return bottlenecks
    
    def _detect_low_success_agents(self) -> List[Bottleneck]:
        """Detect agents with low success rates"""
        bottlenecks = []
        
        # Get success rate metrics
        success_rates = [
            m for m in self._metrics
            if m.metric_type == MetricType.SUCCESS_RATE
        ]
        
        if len(success_rates) < 5:
            return bottlenecks
        
        # Calculate baseline (average)
        all_rates = [m.value for m in success_rates]
        baseline = sum(all_rates) / len(all_rates)
        threshold = 0.80  # 80% minimum acceptable
        
        # Group by agent
        agent_rates = defaultdict(list)
        for metric in success_rates:
            agent_rates[metric.agent_variant_id].append(metric.value)
        
        # Find low-success agents
        for agent, rates in agent_rates.items():
            if len(rates) >= 3:
                avg_rate = sum(rates) / len(rates)
                
                if avg_rate < threshold:
                    bottlenecks.append(Bottleneck(
                        bottleneck_id=f"low_success_{agent}",
                        description=f"Agent '{agent}' has low success rate: {avg_rate:.1%} (target: {threshold:.1%})",
                        severity="critical" if avg_rate < 0.7 else "high",
                        affected_agents=[agent],
                        metric_type=MetricType.SUCCESS_RATE,
                        current_value=avg_rate,
                        expected_value=threshold,
                        impact=f"{int((threshold - avg_rate) * 100)}% below target",
                        recommendations=[
                            "Review failed interactions for common patterns",
                            "Improve prompt engineering and instructions",
                            "Add validation and error handling",
                            "Consider task-specific fine-tuning"
                        ]
                    ))
        
        return bottlenecks
    
    def _detect_high_error_agents(self) -> List[Bottleneck]:
        """Detect agents with high error rates"""
        bottlenecks = []
        
        # Get error rate metrics
        error_rates = [
            m for m in self._metrics
            if m.metric_type == MetricType.ERROR_RATE
        ]
        
        if len(error_rates) < 5:
            return bottlenecks
        
        threshold = 0.10  # 10% maximum acceptable
        
        # Group by agent
        agent_errors = defaultdict(list)
        for metric in error_rates:
            agent_errors[metric.agent_variant_id].append(metric.value)
        
        # Find high-error agents
        for agent, errors in agent_errors.items():
            if len(errors) >= 3:
                avg_error = sum(errors) / len(errors)
                
                if avg_error > threshold:
                    bottlenecks.append(Bottleneck(
                        bottleneck_id=f"high_errors_{agent}",
                        description=f"Agent '{agent}' has high error rate: {avg_error:.1%} (max: {threshold:.1%})",
                        severity="critical" if avg_error > 0.20 else "high",
                        affected_agents=[agent],
                        metric_type=MetricType.ERROR_RATE,
                        current_value=avg_error,
                        expected_value=threshold,
                        impact=f"{int((avg_error - threshold) * 100)}% above threshold",
                        recommendations=[
                            "Investigate error types and root causes",
                            "Add comprehensive error handling",
                            "Implement retry logic for transient failures",
                            "Review input validation"
                        ]
                    ))
        
        return bottlenecks
    
    def _calculate_agent_metrics(self) -> Dict[str, Dict[str, float]]:
        """Calculate aggregated metrics per agent"""
        metrics_by_agent = defaultdict(lambda: {})
        
        # Group metrics by agent and type
        for metric in self._metrics:
            agent = metric.agent_variant_id
            metric_type = metric.metric_type.value
            
            if metric_type not in metrics_by_agent[agent]:
                metrics_by_agent[agent][metric_type] = []
            
            metrics_by_agent[agent][metric_type].append(metric.value)
        
        # Calculate averages
        result = {}
        for agent, metrics in metrics_by_agent.items():
            result[agent] = {
                metric_type: sum(values) / len(values)
                for metric_type, values in metrics.items()
            }
        
        return dict(result)
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate performance summary"""
        if not self._metrics:
            return {"total_metrics": 0}
        
        # Calculate overall metrics
        response_times = [m.value for m in self._metrics if m.metric_type == MetricType.RESPONSE_TIME]
        success_rates = [m.value for m in self._metrics if m.metric_type == MetricType.SUCCESS_RATE]
        error_rates = [m.value for m in self._metrics if m.metric_type == MetricType.ERROR_RATE]
        
        summary = {
            "total_metrics": len(self._metrics),
            "unique_agents": len(set(m.agent_variant_id for m in self._metrics)),
        }
        
        if response_times:
            summary["avg_response_time_ms"] = sum(response_times) / len(response_times)
            summary["min_response_time_ms"] = min(response_times)
            summary["max_response_time_ms"] = max(response_times)
        
        if success_rates:
            summary["avg_success_rate"] = sum(success_rates) / len(success_rates)
        
        if error_rates:
            summary["avg_error_rate"] = sum(error_rates) / len(error_rates)
        
        return summary
    
    def _generate_recommendations(self, bottlenecks: List[Bottleneck]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Priority: Critical and High severity bottlenecks
        critical_bottlenecks = [b for b in bottlenecks if b.severity in ["critical", "high"]]
        
        if critical_bottlenecks:
            recommendations.append(
                f"Address {len(critical_bottlenecks)} critical/high-severity bottlenecks immediately"
            )
            
            # Specific recommendations from bottlenecks
            for bottleneck in critical_bottlenecks[:3]:  # Top 3
                recommendations.append(
                    f"{bottleneck.affected_agents[0]}: {bottleneck.recommendations[0]}"
                )
        else:
            recommendations.append("No critical bottlenecks detected - focus on optimization")
        
        # General recommendations
        if len(self._metrics) >= 50:
            recommendations.append("Sufficient data collected - consider implementing automated optimizations")
        else:
            recommendations.append(f"Continue data collection (current: {len(self._metrics)} metrics)")
        
        return recommendations
    
    def get_agent_performance_score(self, agent_variant_id: str) -> Optional[float]:
        """
        Calculate overall performance score for agent.
        
        Args:
            agent_variant_id: Agent to analyze
            
        Returns:
            Performance score (0-100) or None if insufficient data
        """
        agent_metrics = [m for m in self._metrics if m.agent_variant_id == agent_variant_id]
        
        if len(agent_metrics) < 5:
            return None
        
        scores = []
        
        # Success rate component (60% weight)
        success_metrics = [m for m in agent_metrics if m.metric_type == MetricType.SUCCESS_RATE]
        if success_metrics:
            avg_success = sum(m.value for m in success_metrics) / len(success_metrics)
            scores.append(("success", avg_success * 100, 0.6))
        
        # Response time component (20% weight) - inverse scoring
        response_metrics = [m for m in agent_metrics if m.metric_type == MetricType.RESPONSE_TIME]
        if response_metrics:
            avg_time = sum(m.value for m in response_metrics) / len(response_metrics)
            # Score: 100 for <1000ms, 50 for 2000ms, 0 for >4000ms
            time_score = max(0, min(100, 100 - (avg_time - 1000) / 30))
            scores.append(("response_time", time_score, 0.2))
        
        # Error rate component (20% weight) - inverse scoring
        error_metrics = [m for m in agent_metrics if m.metric_type == MetricType.ERROR_RATE]
        if error_metrics:
            avg_error = sum(m.value for m in error_metrics) / len(error_metrics)
            # Score: 100 for 0%, 0 for 20%+
            error_score = max(0, 100 - (avg_error * 500))
            scores.append(("error_rate", error_score, 0.2))
        
        if not scores:
            return None
        
        # Calculate weighted score
        weighted_score = sum(score * weight for _, score, weight in scores)
        total_weight = sum(weight for _, _, weight in scores)
        
        return weighted_score / total_weight if total_weight > 0 else None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get performance statistics"""
        metrics_by_agent = self._calculate_agent_metrics()
        
        return {
            "total_metrics": len(self._metrics),
            "unique_agents": len(set(m.agent_variant_id for m in self._metrics)),
            "bottlenecks_detected": len(self._bottlenecks),
            "metrics_by_type": {
                mt.value: len([m for m in self._metrics if m.metric_type == mt])
                for mt in MetricType
            },
            "agents_analyzed": list(metrics_by_agent.keys())
        }
