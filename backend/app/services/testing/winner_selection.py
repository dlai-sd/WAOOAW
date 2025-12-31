"""
Winner Selection

Automated winner selection using statistical tests.
"""

from typing import Optional, Dict, Any, Tuple, List
from dataclasses import dataclass
from enum import Enum
import math

from .ab_testing import ABTest, TestMetrics


class StatisticalTest(str, Enum):
    """Statistical test types"""
    FISHERS_EXACT = "fishers_exact"  # For success/failure (categorical)
    CHI_SQUARED = "chi_squared"  # For success/failure (large samples)
    T_TEST = "t_test"  # For continuous metrics (rating)
    BAYESIAN = "bayesian"  # Bayesian A/B test


@dataclass
class WinnerResult:
    """Result of winner selection"""
    winner: str  # "A" or "B"
    confidence: float  # Confidence level (0-1)
    p_value: float  # Statistical p-value
    effect_size: float  # Magnitude of improvement
    reason: str  # Human-readable explanation
    metrics_comparison: Dict[str, Any]
    recommendation: str  # Action recommendation


class WinnerSelector:
    """
    Selects winner from A/B test using statistical analysis.
    
    Supports multiple metrics:
    - Success rate (primary)
    - Average rating (secondary)
    - Duration (tertiary)
    """
    
    def __init__(
        self,
        confidence_level: float = 0.95,
        min_effect_size: float = 0.05,  # 5% minimum improvement
        test_type: StatisticalTest = StatisticalTest.CHI_SQUARED
    ):
        """
        Initialize winner selector.
        
        Args:
            confidence_level: Required confidence (default 95%)
            min_effect_size: Minimum improvement to declare winner
            test_type: Statistical test to use
        """
        self.confidence_level = confidence_level
        self.min_effect_size = min_effect_size
        self.test_type = test_type
    
    def select_winner(self, test: ABTest) -> WinnerResult:
        """
        Select winner from completed test.
        
        Args:
            test: Completed A/B test
            
        Returns:
            WinnerResult with analysis
        """
        metrics_a = test.metrics_a
        metrics_b = test.metrics_b
        
        # Calculate improvements
        success_rate_improvement = (
            metrics_b.success_rate - metrics_a.success_rate
        )
        rating_improvement = (
            metrics_b.avg_rating - metrics_a.avg_rating
        )
        duration_improvement = (
            metrics_a.avg_duration_ms - metrics_b.avg_duration_ms
        ) / max(metrics_a.avg_duration_ms, 1)  # Negative if B is slower
        
        # Primary metric: success rate
        p_value = self._calculate_p_value(metrics_a, metrics_b)
        is_significant = p_value < (1 - self.confidence_level)
        
        # Calculate effect size (relative improvement)
        effect_size = abs(success_rate_improvement)
        
        # Determine winner
        if not is_significant or effect_size < self.min_effect_size:
            # No clear winner
            return WinnerResult(
                winner="A",  # Keep control by default
                confidence=0.0,
                p_value=p_value,
                effect_size=effect_size,
                reason="No statistically significant difference detected",
                metrics_comparison=self._compare_metrics(metrics_a, metrics_b),
                recommendation="Keep current version (A). Consider longer test or larger sample."
            )
        
        # B is significantly better
        if success_rate_improvement > 0:
            confidence = 1 - p_value
            return WinnerResult(
                winner="B",
                confidence=confidence,
                p_value=p_value,
                effect_size=effect_size,
                reason=self._build_reason(
                    "B",
                    success_rate_improvement,
                    rating_improvement,
                    duration_improvement
                ),
                metrics_comparison=self._compare_metrics(metrics_a, metrics_b),
                recommendation=f"Deploy variant B. Expected {effect_size*100:.1f}% improvement."
            )
        
        # A is significantly better (B performed worse)
        confidence = 1 - p_value
        return WinnerResult(
            winner="A",
            confidence=confidence,
            p_value=p_value,
            effect_size=effect_size,
            reason=self._build_reason(
                "A",
                -success_rate_improvement,
                -rating_improvement,
                -duration_improvement
            ),
            metrics_comparison=self._compare_metrics(metrics_a, metrics_b),
            recommendation="Keep current version (A). Variant B underperformed."
        )
    
    def _calculate_p_value(
        self,
        metrics_a: TestMetrics,
        metrics_b: TestMetrics
    ) -> float:
        """
        Calculate p-value using chi-squared test.
        
        Simplified implementation for educational purposes.
        Production should use scipy.stats.chi2_contingency or similar.
        """
        # Observed values
        success_a = metrics_a.successful_requests
        failure_a = metrics_a.failed_requests
        success_b = metrics_b.successful_requests
        failure_b = metrics_b.failed_requests
        
        total_a = success_a + failure_a
        total_b = success_b + failure_b
        total_success = success_a + success_b
        total_failure = failure_a + failure_b
        total = total_a + total_b
        
        if total == 0:
            return 1.0
        
        # Expected values
        expected_success_a = (total_a * total_success) / total
        expected_failure_a = (total_a * total_failure) / total
        expected_success_b = (total_b * total_success) / total
        expected_failure_b = (total_b * total_failure) / total
        
        # Chi-squared statistic
        chi_squared = 0.0
        
        if expected_success_a > 0:
            chi_squared += ((success_a - expected_success_a) ** 2) / expected_success_a
        if expected_failure_a > 0:
            chi_squared += ((failure_a - expected_failure_a) ** 2) / expected_failure_a
        if expected_success_b > 0:
            chi_squared += ((success_b - expected_success_b) ** 2) / expected_success_b
        if expected_failure_b > 0:
            chi_squared += ((failure_b - expected_failure_b) ** 2) / expected_failure_b
        
        # Convert chi-squared to p-value (simplified)
        # For df=1, p-value ≈ erfc(sqrt(chi_squared/2)) / 2
        # Approximation: p-value ≈ exp(-chi_squared/2)
        p_value = math.exp(-chi_squared / 2)
        
        return min(1.0, p_value)
    
    def _compare_metrics(
        self,
        metrics_a: TestMetrics,
        metrics_b: TestMetrics
    ) -> Dict[str, Any]:
        """Compare metrics between variants"""
        return {
            "variant_a": {
                "success_rate": round(metrics_a.success_rate * 100, 2),
                "avg_rating": round(metrics_a.avg_rating, 2),
                "avg_duration_ms": metrics_a.avg_duration_ms,
                "total_requests": metrics_a.total_requests
            },
            "variant_b": {
                "success_rate": round(metrics_b.success_rate * 100, 2),
                "avg_rating": round(metrics_b.avg_rating, 2),
                "avg_duration_ms": metrics_b.avg_duration_ms,
                "total_requests": metrics_b.total_requests
            },
            "deltas": {
                "success_rate": round(
                    (metrics_b.success_rate - metrics_a.success_rate) * 100,
                    2
                ),
                "avg_rating": round(
                    metrics_b.avg_rating - metrics_a.avg_rating,
                    2
                ),
                "avg_duration_ms": metrics_b.avg_duration_ms - metrics_a.avg_duration_ms
            }
        }
    
    def _build_reason(
        self,
        winner: str,
        success_improvement: float,
        rating_improvement: float,
        duration_improvement: float
    ) -> str:
        """Build human-readable reason"""
        reasons = []
        
        # Success rate
        if abs(success_improvement) > 0.01:
            reasons.append(
                f"{abs(success_improvement)*100:.1f}% {'higher' if success_improvement > 0 else 'lower'} success rate"
            )
        
        # Rating
        if abs(rating_improvement) > 0.1:
            reasons.append(
                f"{abs(rating_improvement):.2f} {'higher' if rating_improvement > 0 else 'lower'} rating"
            )
        
        # Duration
        if abs(duration_improvement) > 0.1:
            reasons.append(
                f"{abs(duration_improvement)*100:.1f}% {'faster' if duration_improvement > 0 else 'slower'}"
            )
        
        if not reasons:
            return f"Variant {winner} performed better overall"
        
        return f"Variant {winner} showed: " + ", ".join(reasons)
    
    def analyze_test(self, test: ABTest) -> Dict[str, Any]:
        """
        Analyze test without selecting winner.
        Useful for monitoring during test execution.
        
        Args:
            test: Running or completed test
            
        Returns:
            Analysis dict with current state
        """
        if not test.is_ready_for_analysis():
            return {
                "ready": False,
                "reason": "Insufficient data for analysis",
                "samples_needed": {
                    "variant_a": max(
                        0,
                        test.min_sample_size - test.metrics_a.total_requests
                    ),
                    "variant_b": max(
                        0,
                        test.min_sample_size - test.metrics_b.total_requests
                    )
                }
            }
        
        # Calculate preliminary metrics
        p_value = self._calculate_p_value(test.metrics_a, test.metrics_b)
        is_significant = p_value < (1 - self.confidence_level)
        
        success_improvement = (
            test.metrics_b.success_rate - test.metrics_a.success_rate
        )
        
        return {
            "ready": True,
            "is_significant": is_significant,
            "p_value": p_value,
            "confidence_level": self.confidence_level,
            "success_rate_delta": round(success_improvement * 100, 2),
            "rating_delta": round(
                test.metrics_b.avg_rating - test.metrics_a.avg_rating,
                2
            ),
            "leading_variant": "B" if success_improvement > 0 else "A",
            "metrics": self._compare_metrics(test.metrics_a, test.metrics_b),
            "recommendation": (
                "Continue test" if not is_significant
                else "Ready to complete test"
            )
        }


class AutomatedWinnerSelector(WinnerSelector):
    """
    Automated winner selection with auto-deployment.
    
    Monitors tests and automatically:
    - Detects when test is ready
    - Selects winner
    - Updates version manager
    - Activates winning variant
    """
    
    def __init__(
        self,
        version_manager,
        test_manager,
        confidence_level: float = 0.95,
        min_effect_size: float = 0.05,
        auto_deploy: bool = False
    ):
        """
        Initialize automated selector.
        
        Args:
            version_manager: PromptVersionManager instance
            test_manager: ABTestManager instance
            confidence_level: Required confidence
            min_effect_size: Minimum improvement
            auto_deploy: Automatically deploy winners
        """
        super().__init__(confidence_level, min_effect_size)
        self.version_manager = version_manager
        self.test_manager = test_manager
        self.auto_deploy = auto_deploy
    
    def process_completed_tests(self) -> List[Dict[str, Any]]:
        """
        Process all completed tests and select winners.
        
        Returns:
            List of processing results
        """
        results = []
        
        running_tests = self.test_manager.get_running_tests()
        
        for test in running_tests:
            if not test.is_ready_for_analysis():
                continue
            
            # Select winner
            winner_result = self.select_winner(test)
            
            # Complete test
            test.complete(
                winner=winner_result.winner,
                reason=winner_result.reason
            )
            
            # Update version metrics
            version_id = (
                test.variant_b if winner_result.winner == "B"
                else test.variant_a
            )
            
            winner_metrics = (
                test.metrics_b if winner_result.winner == "B"
                else test.metrics_a
            )
            
            self.version_manager.update_metrics(
                version_id=version_id,
                success_rate=winner_metrics.success_rate,
                avg_rating=winner_metrics.avg_rating,
                avg_duration_ms=winner_metrics.avg_duration_ms
            )
            
            # Auto-deploy if enabled and B won
            if self.auto_deploy and winner_result.winner == "B":
                self.version_manager.activate_version(test.variant_b)
                deployed = True
            else:
                deployed = False
            
            results.append({
                "test_id": test.id,
                "test_name": test.name,
                "winner": winner_result.winner,
                "confidence": winner_result.confidence,
                "effect_size": winner_result.effect_size,
                "reason": winner_result.reason,
                "deployed": deployed,
                "recommendation": winner_result.recommendation
            })
        
        return results
