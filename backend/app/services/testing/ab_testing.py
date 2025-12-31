"""
A/B Testing Framework

Manages prompt A/B tests with traffic splitting and metrics collection.
"""

from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import random


class TestStatus(str, Enum):
    """Status of A/B test"""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class TestMetrics:
    """Metrics collected during A/B test"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_rating: float = 0.0
    rating_count: int = 0
    total_duration_ms: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    @property
    def avg_rating(self) -> float:
        """Calculate average rating"""
        if self.rating_count == 0:
            return 0.0
        return self.total_rating / self.rating_count
    
    @property
    def avg_duration_ms(self) -> int:
        """Calculate average duration"""
        if self.total_requests == 0:
            return 0
        return self.total_duration_ms // self.total_requests
    
    def record_success(
        self,
        rating: Optional[float] = None,
        duration_ms: Optional[int] = None
    ):
        """Record successful request"""
        self.total_requests += 1
        self.successful_requests += 1
        
        if rating is not None:
            self.total_rating += rating
            self.rating_count += 1
        
        if duration_ms is not None:
            self.total_duration_ms += duration_ms
    
    def record_failure(self, duration_ms: Optional[int] = None):
        """Record failed request"""
        self.total_requests += 1
        self.failed_requests += 1
        
        if duration_ms is not None:
            self.total_duration_ms += duration_ms
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": self.success_rate,
            "avg_rating": self.avg_rating,
            "rating_count": self.rating_count,
            "avg_duration_ms": self.avg_duration_ms
        }


@dataclass
class TestResult:
    """Result of single test execution"""
    variant_id: str
    success: bool
    rating: Optional[float] = None
    duration_ms: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ABTest:
    """A/B test configuration and state"""
    id: str
    name: str
    description: str
    prompt_name: str  # Name of prompt being tested
    variant_a: str  # Version ID for variant A (control)
    variant_b: str  # Version ID for variant B (treatment)
    
    # Configuration
    traffic_split: float = 0.5  # % to variant B (0.5 = 50/50 split)
    min_sample_size: int = 100  # Minimum requests per variant
    confidence_level: float = 0.95  # Statistical confidence (95%)
    max_duration_hours: Optional[int] = 168  # 1 week default
    
    # State
    status: TestStatus = TestStatus.DRAFT
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Metrics
    metrics_a: TestMetrics = field(default_factory=TestMetrics)
    metrics_b: TestMetrics = field(default_factory=TestMetrics)
    
    # Winner (determined after test completion)
    winner: Optional[str] = None  # "A" or "B"
    winner_reason: Optional[str] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = f"test_{self.prompt_name}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    def start(self):
        """Start the test"""
        self.status = TestStatus.RUNNING
        self.started_at = datetime.utcnow()
    
    def pause(self):
        """Pause the test"""
        self.status = TestStatus.PAUSED
    
    def resume(self):
        """Resume paused test"""
        if self.status == TestStatus.PAUSED:
            self.status = TestStatus.RUNNING
    
    def complete(self, winner: str, reason: str):
        """Complete the test with winner"""
        self.status = TestStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.winner = winner
        self.winner_reason = reason
    
    def cancel(self):
        """Cancel the test"""
        self.status = TestStatus.CANCELLED
        self.completed_at = datetime.utcnow()
    
    def select_variant(self) -> str:
        """
        Select variant for next request based on traffic split.
        
        Returns:
            "A" or "B"
        """
        if random.random() < self.traffic_split:
            return "B"
        return "A"
    
    def record_result(self, result: TestResult):
        """Record result for a variant"""
        metrics = self.metrics_b if result.variant_id == "B" else self.metrics_a
        
        if result.success:
            metrics.record_success(
                rating=result.rating,
                duration_ms=result.duration_ms
            )
        else:
            metrics.record_failure(duration_ms=result.duration_ms)
    
    def is_ready_for_analysis(self) -> bool:
        """Check if test has enough data for statistical analysis"""
        return (
            self.metrics_a.total_requests >= self.min_sample_size and
            self.metrics_b.total_requests >= self.min_sample_size
        )
    
    def should_stop(self) -> bool:
        """Check if test should stop (max duration reached)"""
        if not self.started_at or not self.max_duration_hours:
            return False
        
        elapsed = datetime.utcnow() - self.started_at
        max_duration = timedelta(hours=self.max_duration_hours)
        
        return elapsed >= max_duration
    
    def get_progress(self) -> Dict[str, Any]:
        """Get test progress information"""
        total_a = self.metrics_a.total_requests
        total_b = self.metrics_b.total_requests
        min_needed = self.min_sample_size
        
        return {
            "status": self.status.value,
            "variant_a": {
                "requests": total_a,
                "progress": min(100, (total_a / min_needed) * 100),
                "metrics": self.metrics_a.to_dict()
            },
            "variant_b": {
                "requests": total_b,
                "progress": min(100, (total_b / min_needed) * 100),
                "metrics": self.metrics_b.to_dict()
            },
            "ready_for_analysis": self.is_ready_for_analysis(),
            "should_stop": self.should_stop(),
            "winner": self.winner
        }
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "prompt_name": self.prompt_name,
            "variant_a": self.variant_a,
            "variant_b": self.variant_b,
            "traffic_split": self.traffic_split,
            "min_sample_size": self.min_sample_size,
            "confidence_level": self.confidence_level,
            "max_duration_hours": self.max_duration_hours,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metrics_a": self.metrics_a.to_dict(),
            "metrics_b": self.metrics_b.to_dict(),
            "winner": self.winner,
            "winner_reason": self.winner_reason,
            "progress": self.get_progress()
        }


class ABTestManager:
    """
    Manages multiple A/B tests.
    
    Features:
    - Create and configure tests
    - Route traffic to variants
    - Collect metrics
    - Monitor test progress
    """
    
    def __init__(self, storage: Optional[Dict] = None):
        """
        Initialize test manager.
        
        Args:
            storage: Storage backend (dict for testing, database in prod)
        """
        self.storage = storage if storage is not None else {}
    
    def create_test(
        self,
        name: str,
        description: str,
        prompt_name: str,
        variant_a: str,
        variant_b: str,
        traffic_split: float = 0.5,
        min_sample_size: int = 100,
        confidence_level: float = 0.95,
        max_duration_hours: Optional[int] = 168
    ) -> ABTest:
        """
        Create new A/B test.
        
        Args:
            name: Test name
            description: Test description
            prompt_name: Name of prompt being tested
            variant_a: Version ID for control
            variant_b: Version ID for treatment
            traffic_split: % traffic to variant B
            min_sample_size: Minimum samples per variant
            confidence_level: Statistical confidence level
            max_duration_hours: Maximum test duration
            
        Returns:
            Created ABTest
        """
        test = ABTest(
            id="",  # Auto-generated
            name=name,
            description=description,
            prompt_name=prompt_name,
            variant_a=variant_a,
            variant_b=variant_b,
            traffic_split=traffic_split,
            min_sample_size=min_sample_size,
            confidence_level=confidence_level,
            max_duration_hours=max_duration_hours
        )
        
        self.storage[test.id] = test
        return test
    
    def get_test(self, test_id: str) -> Optional[ABTest]:
        """Get test by ID"""
        return self.storage.get(test_id)
    
    def list_tests(
        self,
        prompt_name: Optional[str] = None,
        status: Optional[TestStatus] = None
    ) -> List[ABTest]:
        """
        List all tests with optional filters.
        
        Args:
            prompt_name: Filter by prompt name
            status: Filter by status
            
        Returns:
            List of tests
        """
        tests = list(self.storage.values())
        
        if prompt_name:
            tests = [t for t in tests if t.prompt_name == prompt_name]
        if status:
            tests = [t for t in tests if t.status == status]
        
        return tests
    
    def start_test(self, test_id: str) -> bool:
        """Start a test"""
        test = self.get_test(test_id)
        if not test:
            return False
        
        test.start()
        return True
    
    def record_result(self, test_id: str, result: TestResult) -> bool:
        """
        Record test result.
        
        Args:
            test_id: Test ID
            result: Test result
            
        Returns:
            True if recorded successfully
        """
        test = self.get_test(test_id)
        if not test or test.status != TestStatus.RUNNING:
            return False
        
        test.record_result(result)
        return True
    
    def get_active_test(self, prompt_name: str) -> Optional[ABTest]:
        """Get active test for prompt (if any)"""
        running_tests = self.list_tests(
            prompt_name=prompt_name,
            status=TestStatus.RUNNING
        )
        return running_tests[0] if running_tests else None
    
    def route_request(self, prompt_name: str) -> Optional[str]:
        """
        Route request to appropriate variant.
        
        Args:
            prompt_name: Name of prompt
            
        Returns:
            Version ID to use, or None if no active test
        """
        test = self.get_active_test(prompt_name)
        if not test:
            return None
        
        variant = test.select_variant()
        return test.variant_b if variant == "B" else test.variant_a
    
    def get_running_tests(self) -> List[ABTest]:
        """Get all currently running tests"""
        return self.list_tests(status=TestStatus.RUNNING)
    
    def check_test_completion(self, test_id: str) -> Dict[str, Any]:
        """
        Check if test should be completed.
        
        Args:
            test_id: Test ID
            
        Returns:
            Dict with completion status and reason
        """
        test = self.get_test(test_id)
        if not test:
            return {"should_complete": False, "reason": "Test not found"}
        
        if test.status != TestStatus.RUNNING:
            return {"should_complete": False, "reason": "Test not running"}
        
        # Check if max duration reached
        if test.should_stop():
            return {
                "should_complete": True,
                "reason": "Maximum duration reached"
            }
        
        # Check if minimum sample size reached
        if not test.is_ready_for_analysis():
            return {
                "should_complete": False,
                "reason": f"Need {test.min_sample_size} samples per variant"
            }
        
        return {
            "should_complete": True,
            "reason": "Minimum sample size reached"
        }
