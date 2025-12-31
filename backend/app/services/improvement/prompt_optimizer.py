"""
Prompt optimization service for self-improving agents
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set
import uuid
import statistics


class OptimizationStrategy(Enum):
    """Prompt optimization strategies"""
    SIMPLIFY = "simplify"  # Reduce complexity
    EXPAND = "expand"  # Add more detail
    RESTRUCTURE = "restructure"  # Change organization
    CLARIFY = "clarify"  # Improve clarity
    SPECIALIZE = "specialize"  # Add domain-specific context


class PromptVersion(Enum):
    """Prompt version status"""
    DRAFT = "draft"
    TESTING = "testing"
    ACTIVE = "active"
    ARCHIVED = "archived"


@dataclass
class PromptVariant:
    """A variant of a prompt for A/B testing"""
    variant_id: str
    prompt_id: str
    content: str
    strategy: OptimizationStrategy
    version: int
    status: PromptVersion = PromptVersion.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)
    
    # Performance tracking
    test_count: int = 0
    success_count: int = 0
    avg_response_time: float = 0.0
    user_rating: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "variant_id": self.variant_id,
            "prompt_id": self.prompt_id,
            "content": self.content,
            "strategy": self.strategy.value,
            "version": self.version,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
            "test_count": self.test_count,
            "success_count": self.success_count,
            "success_rate": self.success_count / self.test_count if self.test_count > 0 else 0.0,
            "avg_response_time": self.avg_response_time,
            "user_rating": self.user_rating,
        }


@dataclass
class ABTest:
    """A/B test configuration"""
    test_id: str
    prompt_id: str
    variants: List[str]  # variant_ids
    traffic_split: Dict[str, float]  # variant_id -> percentage (0-1)
    start_date: datetime
    end_date: Optional[datetime] = None
    min_sample_size: int = 100
    confidence_level: float = 0.95
    winner: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class PromptTemplate:
    """Base prompt template"""
    prompt_id: str
    name: str
    category: str
    base_content: str
    variables: List[str] = field(default_factory=list)
    active_variant_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)


class PromptOptimizer:
    """
    Prompt optimization system for self-improving agents.
    
    Features:
    - Automatic prompt variation generation
    - A/B testing framework
    - Performance-based optimization
    - Version control and rollback
    """
    
    def __init__(self):
        self._prompts: Dict[str, PromptTemplate] = {}
        self._variants: Dict[str, PromptVariant] = {}
        self._tests: Dict[str, ABTest] = {}
        self._variant_by_prompt: Dict[str, List[str]] = {}  # prompt_id -> [variant_ids]
    
    def register_prompt(
        self,
        name: str,
        category: str,
        base_content: str,
        variables: Optional[List[str]] = None
    ) -> str:
        """Register a new prompt template"""
        prompt_id = str(uuid.uuid4())
        
        prompt = PromptTemplate(
            prompt_id=prompt_id,
            name=name,
            category=category,
            base_content=base_content,
            variables=variables or [],
        )
        
        self._prompts[prompt_id] = prompt
        self._variant_by_prompt[prompt_id] = []
        
        # Create initial variant from base content
        variant_id = self.create_variant(
            prompt_id=prompt_id,
            content=base_content,
            strategy=OptimizationStrategy.CLARIFY,
            metadata={"is_baseline": True}
        )
        
        prompt.active_variant_id = variant_id
        
        return prompt_id
    
    def create_variant(
        self,
        prompt_id: str,
        content: str,
        strategy: OptimizationStrategy,
        metadata: Optional[Dict] = None
    ) -> str:
        """Create a new prompt variant"""
        if prompt_id not in self._prompts:
            raise ValueError(f"Prompt {prompt_id} not found")
        
        prompt = self._prompts[prompt_id]
        version = len(self._variant_by_prompt[prompt_id]) + 1
        
        variant_id = str(uuid.uuid4())
        variant = PromptVariant(
            variant_id=variant_id,
            prompt_id=prompt_id,
            content=content,
            strategy=strategy,
            version=version,
            metadata=metadata or {},
        )
        
        self._variants[variant_id] = variant
        self._variant_by_prompt[prompt_id].append(variant_id)
        
        return variant_id
    
    def generate_variants(
        self,
        prompt_id: str,
        strategies: Optional[List[OptimizationStrategy]] = None
    ) -> List[str]:
        """
        Generate prompt variants using different optimization strategies.
        
        Returns list of variant IDs.
        """
        if prompt_id not in self._prompts:
            raise ValueError(f"Prompt {prompt_id} not found")
        
        prompt = self._prompts[prompt_id]
        base_content = prompt.base_content
        
        if strategies is None:
            strategies = list(OptimizationStrategy)
        
        variant_ids = []
        
        for strategy in strategies:
            # Generate variant based on strategy
            if strategy == OptimizationStrategy.SIMPLIFY:
                content = self._simplify_prompt(base_content)
            elif strategy == OptimizationStrategy.EXPAND:
                content = self._expand_prompt(base_content)
            elif strategy == OptimizationStrategy.RESTRUCTURE:
                content = self._restructure_prompt(base_content)
            elif strategy == OptimizationStrategy.CLARIFY:
                content = self._clarify_prompt(base_content)
            elif strategy == OptimizationStrategy.SPECIALIZE:
                content = self._specialize_prompt(base_content, prompt.category)
            else:
                continue
            
            variant_id = self.create_variant(
                prompt_id=prompt_id,
                content=content,
                strategy=strategy,
                metadata={"generated": True}
            )
            variant_ids.append(variant_id)
        
        return variant_ids
    
    def _simplify_prompt(self, content: str) -> str:
        """Simplify prompt by reducing complexity"""
        # Remove redundant phrases
        simplifications = {
            "please make sure to": "ensure",
            "it is important that you": "you must",
            "try to": "",
            "make sure": "ensure",
            "in order to": "to",
        }
        
        simplified = content
        for old, new in simplifications.items():
            simplified = simplified.replace(old, new)
        
        # Split into sentences and keep concise ones
        sentences = [s.strip() for s in simplified.split(".") if s.strip()]
        concise_sentences = [s for s in sentences if len(s.split()) <= 20]
        
        return ". ".join(concise_sentences) + "."
    
    def _expand_prompt(self, content: str) -> str:
        """Expand prompt with more detail and examples"""
        expansions = {
            "Be accurate": "Be accurate by verifying facts and providing precise information",
            "Be clear": "Be clear by using simple language and well-structured explanations",
            "Be helpful": "Be helpful by anticipating user needs and providing comprehensive solutions",
        }
        
        expanded = content
        for pattern, replacement in expansions.items():
            expanded = expanded.replace(pattern, replacement)
        
        # Add examples section if not present
        if "example" not in expanded.lower():
            expanded += "\n\nProvide specific examples to illustrate your points."
        
        return expanded
    
    def _restructure_prompt(self, content: str) -> str:
        """Restructure prompt organization"""
        # Convert to bullet points if paragraphs
        if "\n\n" in content:
            sections = content.split("\n\n")
            bullets = [f"- {s.strip()}" for s in sections if s.strip()]
            return "\n".join(bullets)
        
        # Convert bullets to numbered list
        if content.startswith("-"):
            lines = content.split("\n")
            numbered = [f"{i+1}. {line.lstrip('- ')}" for i, line in enumerate(lines) if line.strip()]
            return "\n".join(numbered)
        
        return content
    
    def _clarify_prompt(self, content: str) -> str:
        """Clarify prompt by improving readability"""
        clarifications = {
            "use": "utilize",
            "get": "obtain",
            "do": "perform",
            "make": "create",
        }
        
        clarified = content
        for vague, clear in clarifications.items():
            # Only replace whole words
            clarified = clarified.replace(f" {vague} ", f" {clear} ")
        
        return clarified
    
    def _specialize_prompt(self, content: str, category: str) -> str:
        """Add domain-specific context"""
        specializations = {
            "content_creation": "Focus on creativity, engaging language, and audience appeal.",
            "data_analysis": "Prioritize accuracy, statistical rigor, and clear data visualization.",
            "customer_support": "Emphasize empathy, problem-solving, and clear communication.",
            "code_generation": "Ensure code quality, best practices, and comprehensive documentation.",
        }
        
        if category in specializations:
            specialized = f"{content}\n\n{specializations[category]}"
            return specialized
        
        return content
    
    def start_ab_test(
        self,
        prompt_id: str,
        variant_ids: List[str],
        traffic_split: Optional[Dict[str, float]] = None,
        min_sample_size: int = 100
    ) -> str:
        """Start A/B test for prompt variants"""
        if prompt_id not in self._prompts:
            raise ValueError(f"Prompt {prompt_id} not found")
        
        # Validate variants
        for vid in variant_ids:
            if vid not in self._variants:
                raise ValueError(f"Variant {vid} not found")
            if self._variants[vid].prompt_id != prompt_id:
                raise ValueError(f"Variant {vid} does not belong to prompt {prompt_id}")
        
        # Default equal traffic split
        if traffic_split is None:
            split_pct = 1.0 / len(variant_ids)
            traffic_split = {vid: split_pct for vid in variant_ids}
        
        # Validate traffic split
        total = sum(traffic_split.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Traffic split must sum to 1.0, got {total}")
        
        test_id = str(uuid.uuid4())
        test = ABTest(
            test_id=test_id,
            prompt_id=prompt_id,
            variants=variant_ids,
            traffic_split=traffic_split,
            start_date=datetime.now(),
            min_sample_size=min_sample_size,
        )
        
        self._tests[test_id] = test
        
        # Update variant status
        for vid in variant_ids:
            self._variants[vid].status = PromptVersion.TESTING
        
        return test_id
    
    def record_test_result(
        self,
        variant_id: str,
        success: bool,
        response_time_ms: float,
        user_rating: Optional[float] = None
    ):
        """Record A/B test result for a variant"""
        if variant_id not in self._variants:
            raise ValueError(f"Variant {variant_id} not found")
        
        variant = self._variants[variant_id]
        
        # Update counts
        variant.test_count += 1
        if success:
            variant.success_count += 1
        
        # Update average response time
        if variant.test_count == 1:
            variant.avg_response_time = response_time_ms
        else:
            variant.avg_response_time = (
                (variant.avg_response_time * (variant.test_count - 1) + response_time_ms)
                / variant.test_count
            )
        
        # Update user rating
        if user_rating is not None:
            if variant.test_count == 1:
                variant.user_rating = user_rating
            else:
                variant.user_rating = (
                    (variant.user_rating * (variant.test_count - 1) + user_rating)
                    / variant.test_count
                )
    
    def evaluate_ab_test(self, test_id: str) -> Optional[str]:
        """
        Evaluate A/B test and determine winner.
        
        Returns variant_id of winner if test is conclusive, None otherwise.
        """
        if test_id not in self._tests:
            raise ValueError(f"Test {test_id} not found")
        
        test = self._tests[test_id]
        
        # Check if all variants have minimum sample size
        variants = [self._variants[vid] for vid in test.variants]
        if any(v.test_count < test.min_sample_size for v in variants):
            return None
        
        # Calculate composite score for each variant
        scores = {}
        for variant in variants:
            success_rate = variant.success_count / variant.test_count if variant.test_count > 0 else 0
            
            # Normalize response time (lower is better)
            all_times = [v.avg_response_time for v in variants if v.avg_response_time > 0]
            if all_times:
                min_time = min(all_times)
                max_time = max(all_times)
                time_range = max_time - min_time
                time_score = 1.0 - (variant.avg_response_time - min_time) / time_range if time_range > 0 else 1.0
            else:
                time_score = 1.0
            
            # Composite score (weighted)
            composite = (
                success_rate * 0.6 +  # 60% weight on success
                time_score * 0.2 +    # 20% weight on speed
                variant.user_rating / 5.0 * 0.2  # 20% weight on user rating
            )
            
            scores[variant.variant_id] = composite
        
        # Find winner (highest score with statistical significance)
        sorted_variants = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        if len(sorted_variants) < 2:
            return sorted_variants[0][0] if sorted_variants else None
        
        winner_id, winner_score = sorted_variants[0]
        runner_up_id, runner_up_score = sorted_variants[1]
        
        # Check for statistical significance (simple threshold check)
        # In production, use proper statistical tests (t-test, chi-square)
        if winner_score > runner_up_score * 1.05:  # 5% improvement threshold
            test.winner = winner_id
            test.end_date = datetime.now()
            
            # Update winner status
            self._variants[winner_id].status = PromptVersion.ACTIVE
            
            # Archive losers
            for vid in test.variants:
                if vid != winner_id:
                    self._variants[vid].status = PromptVersion.ARCHIVED
            
            # Update prompt active variant
            prompt = self._prompts[test.prompt_id]
            prompt.active_variant_id = winner_id
            prompt.updated_at = datetime.now()
            
            return winner_id
        
        return None
    
    def get_active_prompt(self, prompt_id: str) -> Optional[str]:
        """Get active prompt content"""
        if prompt_id not in self._prompts:
            return None
        
        prompt = self._prompts[prompt_id]
        if prompt.active_variant_id:
            variant = self._variants[prompt.active_variant_id]
            return variant.content
        
        return prompt.base_content
    
    def get_variant_performance(self, variant_id: str) -> Dict:
        """Get performance metrics for a variant"""
        if variant_id not in self._variants:
            raise ValueError(f"Variant {variant_id} not found")
        
        variant = self._variants[variant_id]
        
        success_rate = variant.success_count / variant.test_count if variant.test_count > 0 else 0.0
        
        return {
            "variant_id": variant_id,
            "test_count": variant.test_count,
            "success_count": variant.success_count,
            "success_rate": success_rate,
            "avg_response_time": variant.avg_response_time,
            "user_rating": variant.user_rating,
            "status": variant.status.value,
            "strategy": variant.strategy.value,
        }
    
    def get_prompt_history(self, prompt_id: str) -> List[Dict]:
        """Get version history for a prompt"""
        if prompt_id not in self._prompts:
            raise ValueError(f"Prompt {prompt_id} not found")
        
        variant_ids = self._variant_by_prompt[prompt_id]
        variants = [self._variants[vid] for vid in variant_ids]
        
        # Sort by version
        variants.sort(key=lambda v: v.version)
        
        return [v.to_dict() for v in variants]
    
    def rollback_prompt(self, prompt_id: str, version: int) -> bool:
        """Rollback prompt to a previous version"""
        if prompt_id not in self._prompts:
            raise ValueError(f"Prompt {prompt_id} not found")
        
        # Find variant with specified version
        variant_ids = self._variant_by_prompt[prompt_id]
        target_variant = None
        
        for vid in variant_ids:
            if self._variants[vid].version == version:
                target_variant = self._variants[vid]
                break
        
        if target_variant is None:
            return False
        
        # Set as active
        prompt = self._prompts[prompt_id]
        prompt.active_variant_id = target_variant.variant_id
        prompt.updated_at = datetime.now()
        
        target_variant.status = PromptVersion.ACTIVE
        
        return True
    
    def get_statistics(self) -> Dict:
        """Get optimizer statistics"""
        total_variants = len(self._variants)
        total_tests = len(self._tests)
        
        active_tests = sum(1 for t in self._tests.values() if t.end_date is None)
        completed_tests = total_tests - active_tests
        
        variants_by_status = {}
        for variant in self._variants.values():
            status = variant.status.value
            variants_by_status[status] = variants_by_status.get(status, 0) + 1
        
        avg_success_rates = []
        for variant in self._variants.values():
            if variant.test_count > 0:
                avg_success_rates.append(variant.success_count / variant.test_count)
        
        return {
            "total_prompts": len(self._prompts),
            "total_variants": total_variants,
            "total_tests": total_tests,
            "active_tests": active_tests,
            "completed_tests": completed_tests,
            "variants_by_status": variants_by_status,
            "avg_success_rate": statistics.mean(avg_success_rates) if avg_success_rates else 0.0,
        }
