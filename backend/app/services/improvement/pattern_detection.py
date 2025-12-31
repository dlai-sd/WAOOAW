"""
Pattern Detection System

Analyzes agent interactions to detect success and failure patterns.
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from collections import Counter, defaultdict
import re


class PatternType(str, Enum):
    """Type of detected pattern"""
    SUCCESS = "success"
    FAILURE = "failure"
    EFFICIENCY = "efficiency"
    BOTTLENECK = "bottleneck"
    USER_SATISFACTION = "user_satisfaction"


@dataclass
class InteractionPattern:
    """Detected pattern in agent interactions"""
    pattern_id: str
    pattern_type: PatternType
    description: str
    frequency: int
    confidence: float  # 0-1
    examples: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    detected_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type.value,
            "description": self.description,
            "frequency": self.frequency,
            "confidence": self.confidence,
            "examples": self.examples[:3],  # Limit examples
            "metadata": self.metadata,
            "detected_at": self.detected_at.isoformat(),
        }


@dataclass
class SuccessPattern:
    """Pattern associated with successful outcomes"""
    pattern: str
    success_rate: float
    occurrence_count: int
    agent_variants: Set[str] = field(default_factory=set)
    task_categories: Set[str] = field(default_factory=set)
    common_features: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FailurePattern:
    """Pattern associated with failures"""
    pattern: str
    failure_rate: float
    occurrence_count: int
    error_types: List[str] = field(default_factory=list)
    agent_variants: Set[str] = field(default_factory=set)
    root_causes: List[str] = field(default_factory=list)


class PatternDetector:
    """
    Detects patterns in agent interactions.
    
    Analyzes execution logs, success/failure cases, and user feedback
    to identify improvement opportunities.
    """
    
    def __init__(self):
        """Initialize pattern detector"""
        self._patterns: List[InteractionPattern] = []
        self._interaction_history: List[Dict[str, Any]] = []
    
    def record_interaction(
        self,
        interaction: Dict[str, Any]
    ):
        """
        Record agent interaction for analysis.
        
        Args:
            interaction: Interaction data (task, agent, result, success, etc.)
        """
        self._interaction_history.append({
            **interaction,
            "recorded_at": datetime.utcnow()
        })
    
    def detect_patterns(
        self,
        min_frequency: int = 3,
        min_confidence: float = 0.6
    ) -> List[InteractionPattern]:
        """
        Detect patterns in recorded interactions.
        
        Args:
            min_frequency: Minimum occurrences to consider a pattern
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of detected patterns
        """
        patterns = []
        
        # Detect success patterns
        success_patterns = self._detect_success_patterns(min_frequency)
        patterns.extend(success_patterns)
        
        # Detect failure patterns
        failure_patterns = self._detect_failure_patterns(min_frequency)
        patterns.extend(failure_patterns)
        
        # Detect efficiency patterns
        efficiency_patterns = self._detect_efficiency_patterns(min_frequency)
        patterns.extend(efficiency_patterns)
        
        # Filter by confidence
        patterns = [p for p in patterns if p.confidence >= min_confidence]
        
        self._patterns = patterns
        return patterns
    
    def _detect_success_patterns(self, min_frequency: int) -> List[InteractionPattern]:
        """Detect patterns in successful interactions"""
        patterns = []
        
        # Get successful interactions
        successful = [i for i in self._interaction_history if i.get("success", False)]
        
        if len(successful) < min_frequency:
            return patterns
        
        # Analyze by agent variant
        variant_success = defaultdict(list)
        for interaction in successful:
            variant = interaction.get("agent_variant_id", "unknown")
            variant_success[variant].append(interaction)
        
        for variant, interactions in variant_success.items():
            if len(interactions) >= min_frequency:
                # Calculate confidence based on success rate
                total_variant = len([i for i in self._interaction_history 
                                    if i.get("agent_variant_id") == variant])
                confidence = len(interactions) / total_variant if total_variant > 0 else 0
                
                if confidence >= 0.6:
                    patterns.append(InteractionPattern(
                        pattern_id=f"success_{variant}_{len(patterns)}",
                        pattern_type=PatternType.SUCCESS,
                        description=f"Agent variant '{variant}' shows consistent success",
                        frequency=len(interactions),
                        confidence=confidence,
                        examples=interactions[:3],
                        metadata={"agent_variant": variant}
                    ))
        
        # Analyze by task category
        category_success = defaultdict(list)
        for interaction in successful:
            category = interaction.get("task_category", "unknown")
            category_success[category].append(interaction)
        
        for category, interactions in category_success.items():
            if len(interactions) >= min_frequency:
                total_category = len([i for i in self._interaction_history 
                                     if i.get("task_category") == category])
                confidence = len(interactions) / total_category if total_category > 0 else 0
                
                if confidence >= 0.6:
                    patterns.append(InteractionPattern(
                        pattern_id=f"success_{category}_{len(patterns)}",
                        pattern_type=PatternType.SUCCESS,
                        description=f"Task category '{category}' has high success rate",
                        frequency=len(interactions),
                        confidence=confidence,
                        examples=interactions[:3],
                        metadata={"task_category": category}
                    ))
        
        # Analyze keyword patterns
        keyword_patterns = self._detect_keyword_success_patterns(successful, min_frequency)
        patterns.extend(keyword_patterns)
        
        return patterns
    
    def _detect_keyword_success_patterns(
        self,
        successful: List[Dict[str, Any]],
        min_frequency: int
    ) -> List[InteractionPattern]:
        """Detect success patterns based on task keywords"""
        patterns = []
        
        # Extract keywords from task descriptions
        keyword_occurrences = defaultdict(int)
        keyword_examples = defaultdict(list)
        
        for interaction in successful:
            task_desc = interaction.get("task_description", "")
            keywords = self._extract_keywords(task_desc)
            
            for keyword in keywords:
                keyword_occurrences[keyword] += 1
                if len(keyword_examples[keyword]) < 3:
                    keyword_examples[keyword].append(interaction)
        
        # Find high-frequency keywords
        for keyword, count in keyword_occurrences.items():
            if count >= min_frequency:
                # Calculate confidence
                total_with_keyword = sum(
                    1 for i in self._interaction_history
                    if keyword.lower() in i.get("task_description", "").lower()
                )
                confidence = count / total_with_keyword if total_with_keyword > 0 else 0
                
                if confidence >= 0.6:
                    patterns.append(InteractionPattern(
                        pattern_id=f"keyword_success_{keyword}_{len(patterns)}",
                        pattern_type=PatternType.SUCCESS,
                        description=f"Tasks containing '{keyword}' tend to succeed",
                        frequency=count,
                        confidence=confidence,
                        examples=keyword_examples[keyword],
                        metadata={"keyword": keyword}
                    ))
        
        return patterns
    
    def _detect_failure_patterns(self, min_frequency: int) -> List[InteractionPattern]:
        """Detect patterns in failed interactions"""
        patterns = []
        
        # Get failed interactions
        failed = [i for i in self._interaction_history if not i.get("success", False)]
        
        if len(failed) < min_frequency:
            return patterns
        
        # Analyze by error type
        error_counts = Counter(i.get("error_type", "unknown") for i in failed)
        
        for error_type, count in error_counts.items():
            if count >= min_frequency:
                error_examples = [i for i in failed if i.get("error_type") == error_type]
                confidence = count / len(failed) if failed else 0
                
                patterns.append(InteractionPattern(
                    pattern_id=f"failure_{error_type}_{len(patterns)}",
                    pattern_type=PatternType.FAILURE,
                    description=f"Common failure: {error_type}",
                    frequency=count,
                    confidence=min(confidence * 2, 1.0),  # Boost confidence for failure patterns
                    examples=error_examples[:3],
                    metadata={"error_type": error_type}
                ))
        
        # Analyze by agent variant
        variant_failures = defaultdict(list)
        for interaction in failed:
            variant = interaction.get("agent_variant_id", "unknown")
            variant_failures[variant].append(interaction)
        
        for variant, interactions in variant_failures.items():
            if len(interactions) >= min_frequency:
                total_variant = len([i for i in self._interaction_history 
                                    if i.get("agent_variant_id") == variant])
                failure_rate = len(interactions) / total_variant if total_variant > 0 else 0
                
                if failure_rate >= 0.2:  # 20% failure rate is concerning
                    patterns.append(InteractionPattern(
                        pattern_id=f"failure_{variant}_{len(patterns)}",
                        pattern_type=PatternType.FAILURE,
                        description=f"Agent variant '{variant}' has elevated failure rate",
                        frequency=len(interactions),
                        confidence=failure_rate,
                        examples=interactions[:3],
                        metadata={"agent_variant": variant, "failure_rate": failure_rate}
                    ))
        
        return patterns
    
    def _detect_efficiency_patterns(self, min_frequency: int) -> List[InteractionPattern]:
        """Detect efficiency patterns (response time, resource usage)"""
        patterns = []
        
        # Analyze response times
        interactions_with_time = [
            i for i in self._interaction_history 
            if i.get("response_time_ms") is not None
        ]
        
        if len(interactions_with_time) < min_frequency:
            return patterns
        
        # Calculate average response time
        avg_time = sum(i["response_time_ms"] for i in interactions_with_time) / len(interactions_with_time)
        
        # Find fast performers
        fast_interactions = [i for i in interactions_with_time if i["response_time_ms"] < avg_time * 0.7]
        
        if len(fast_interactions) >= min_frequency:
            # Group by agent variant
            variant_fast = defaultdict(list)
            for interaction in fast_interactions:
                variant = interaction.get("agent_variant_id", "unknown")
                variant_fast[variant].append(interaction)
            
            for variant, interactions in variant_fast.items():
                if len(interactions) >= min_frequency:
                    avg_fast_time = sum(i["response_time_ms"] for i in interactions) / len(interactions)
                    
                    patterns.append(InteractionPattern(
                        pattern_id=f"efficiency_{variant}_{len(patterns)}",
                        pattern_type=PatternType.EFFICIENCY,
                        description=f"Agent variant '{variant}' responds efficiently (avg {int(avg_fast_time)}ms)",
                        frequency=len(interactions),
                        confidence=0.8,
                        examples=interactions[:3],
                        metadata={
                            "agent_variant": variant,
                            "avg_response_time_ms": avg_fast_time,
                            "baseline_time_ms": avg_time
                        }
                    ))
        
        return patterns
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """Extract meaningful keywords from text"""
        # Simple keyword extraction (in production, use NLP)
        text = text.lower()
        
        # Remove common words
        stop_words = {
            "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "about", "as", "is", "was", "are", "were",
            "be", "been", "being", "have", "has", "had", "do", "does", "did",
            "will", "would", "could", "should", "may", "might", "can", "i", "you",
            "he", "she", "it", "we", "they", "me", "him", "her", "us", "them",
            "this", "that", "these", "those", "my", "your", "his", "her", "its",
            "our", "their"
        }
        
        # Extract words (alphanumeric, 3+ characters)
        words = re.findall(r'\b[a-z]{3,}\b', text)
        keywords = {w for w in words if w not in stop_words}
        
        return keywords
    
    def get_success_patterns(self) -> List[SuccessPattern]:
        """Get detailed success patterns"""
        success_patterns = []
        
        successful = [i for i in self._interaction_history if i.get("success", False)]
        
        # Group by common features
        feature_groups = defaultdict(list)
        
        for interaction in successful:
            # Group by agent + category combination
            variant = interaction.get("agent_variant_id", "unknown")
            category = interaction.get("task_category", "unknown")
            key = f"{variant}_{category}"
            feature_groups[key].append(interaction)
        
        for key, interactions in feature_groups.items():
            if len(interactions) >= 3:
                variant, category = key.rsplit("_", 1)
                
                # Calculate success rate for this combination
                total_similar = len([
                    i for i in self._interaction_history
                    if i.get("agent_variant_id") == variant 
                    and i.get("task_category") == category
                ])
                
                success_rate = len(interactions) / total_similar if total_similar > 0 else 0
                
                success_patterns.append(SuccessPattern(
                    pattern=f"{variant} + {category}",
                    success_rate=success_rate,
                    occurrence_count=len(interactions),
                    agent_variants={variant},
                    task_categories={category},
                    common_features={
                        "agent_variant": variant,
                        "task_category": category,
                        "avg_response_time": sum(i.get("response_time_ms", 0) for i in interactions) / len(interactions)
                    }
                ))
        
        # Sort by success rate
        success_patterns.sort(key=lambda x: x.success_rate, reverse=True)
        
        return success_patterns
    
    def get_failure_patterns(self) -> List[FailurePattern]:
        """Get detailed failure patterns"""
        failure_patterns = []
        
        failed = [i for i in self._interaction_history if not i.get("success", False)]
        
        # Group by error type
        error_groups = defaultdict(list)
        
        for interaction in failed:
            error_type = interaction.get("error_type", "unknown")
            error_groups[error_type].append(interaction)
        
        for error_type, interactions in error_groups.items():
            if len(interactions) >= 2:
                # Get affected variants
                variants = {i.get("agent_variant_id", "unknown") for i in interactions}
                
                # Calculate failure rate
                total_interactions = len(self._interaction_history)
                failure_rate = len(interactions) / total_interactions if total_interactions > 0 else 0
                
                # Identify root causes (simple heuristic)
                root_causes = []
                if "timeout" in error_type.lower():
                    root_causes.append("Response time exceeded limit")
                elif "validation" in error_type.lower():
                    root_causes.append("Input validation failed")
                elif "not found" in error_type.lower():
                    root_causes.append("Resource not available")
                else:
                    root_causes.append("Unknown cause - requires investigation")
                
                failure_patterns.append(FailurePattern(
                    pattern=error_type,
                    failure_rate=failure_rate,
                    occurrence_count=len(interactions),
                    error_types=[error_type],
                    agent_variants=variants,
                    root_causes=root_causes
                ))
        
        # Sort by occurrence count
        failure_patterns.sort(key=lambda x: x.occurrence_count, reverse=True)
        
        return failure_patterns
    
    def get_improvement_opportunities(self) -> List[Dict[str, Any]]:
        """
        Identify specific improvement opportunities.
        
        Returns:
            List of actionable improvements
        """
        opportunities = []
        
        # Get patterns
        success_patterns = self.get_success_patterns()
        failure_patterns = self.get_failure_patterns()
        
        # Opportunity 1: Replicate successful patterns
        for pattern in success_patterns[:3]:  # Top 3
            if pattern.success_rate >= 0.85:
                opportunities.append({
                    "type": "replicate_success",
                    "priority": "high",
                    "description": f"Replicate success pattern: {pattern.pattern}",
                    "success_rate": pattern.success_rate,
                    "actionable_steps": [
                        f"Analyze what makes {pattern.pattern} successful",
                        "Apply learnings to similar task types",
                        "Consider using this agent variant as default for this category"
                    ],
                    "expected_impact": "+2-5% success rate"
                })
        
        # Opportunity 2: Address failure patterns
        for pattern in failure_patterns[:3]:  # Top 3
            if pattern.occurrence_count >= 5:
                opportunities.append({
                    "type": "fix_failure",
                    "priority": "high" if pattern.occurrence_count >= 10 else "medium",
                    "description": f"Address failure pattern: {pattern.pattern}",
                    "failure_rate": pattern.failure_rate,
                    "affected_variants": list(pattern.agent_variants),
                    "root_causes": pattern.root_causes,
                    "actionable_steps": [
                        f"Investigate root cause: {pattern.root_causes[0]}",
                        "Implement error handling or retry logic",
                        "Update agent prompts or configuration"
                    ],
                    "expected_impact": "+1-3% success rate"
                })
        
        # Opportunity 3: Optimize slow performers
        slow_interactions = [
            i for i in self._interaction_history
            if i.get("response_time_ms", 0) > 3000  # >3s
        ]
        
        if len(slow_interactions) >= 5:
            variant_slow = Counter(i.get("agent_variant_id") for i in slow_interactions)
            for variant, count in variant_slow.most_common(2):
                opportunities.append({
                    "type": "optimize_performance",
                    "priority": "medium",
                    "description": f"Optimize slow agent variant: {variant}",
                    "slow_interaction_count": count,
                    "actionable_steps": [
                        "Profile agent execution to find bottlenecks",
                        "Reduce prompt complexity or token count",
                        "Consider caching or preprocessing"
                    ],
                    "expected_impact": "20-40% faster response time"
                })
        
        return opportunities
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get pattern detection statistics"""
        total = len(self._interaction_history)
        successful = len([i for i in self._interaction_history if i.get("success", False)])
        failed = total - successful
        
        return {
            "total_interactions": total,
            "successful_interactions": successful,
            "failed_interactions": failed,
            "success_rate": successful / total if total > 0 else 0,
            "patterns_detected": len(self._patterns),
            "patterns_by_type": {
                pt.value: len([p for p in self._patterns if p.pattern_type == pt])
                for pt in PatternType
            }
        }
