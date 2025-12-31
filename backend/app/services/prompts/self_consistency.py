"""
Self-Consistency Voting

Generates multiple responses and selects the best one through voting/consensus.
Improves accuracy for complex reasoning tasks.
"""

from typing import List, Dict, Optional, Callable
from collections import Counter
from dataclasses import dataclass
import asyncio


@dataclass
class Response:
    """Single model response"""
    text: str
    reasoning: Optional[str] = None
    confidence: float = 0.0
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class VotingResult:
    """Result of self-consistency voting"""
    winner: Response
    all_responses: List[Response]
    vote_counts: Dict[str, int]
    consensus_score: float  # 0-1, how much agreement
    reasoning_quality: Optional[float] = None


class SelfConsistencyVoter:
    """
    Implements self-consistency voting for improved accuracy.
    
    Process:
    1. Generate N responses to the same prompt (with sampling)
    2. Compare responses for consistency
    3. Select the most common/best answer
    4. Return winner with confidence score
    """
    
    def __init__(
        self,
        num_samples: int = 3,
        temperature: float = 0.7
    ):
        """
        Initialize self-consistency voter.
        
        Args:
            num_samples: Number of responses to generate (default: 3)
            temperature: Sampling temperature for diversity (default: 0.7)
        """
        self.num_samples = num_samples
        self.temperature = temperature
    
    async def vote(
        self,
        prompt: str,
        generator_func: Callable,
        similarity_threshold: float = 0.8
    ) -> VotingResult:
        """
        Generate multiple responses and vote on the best one.
        
        Args:
            prompt: Input prompt
            generator_func: Async function that generates responses
            similarity_threshold: Threshold for considering responses "same" (0-1)
            
        Returns:
            VotingResult with winner and voting details
        """
        # Generate N responses
        responses = await self._generate_multiple(prompt, generator_func)
        
        # Group similar responses
        clusters = self._cluster_responses(responses, similarity_threshold)
        
        # Vote: largest cluster wins
        winner_cluster = max(clusters, key=lambda c: len(c))
        
        # Select best response from winner cluster
        winner = self._select_best_from_cluster(winner_cluster)
        
        # Calculate consensus score
        consensus_score = len(winner_cluster) / len(responses)
        
        # Count votes
        vote_counts = {
            f"cluster_{i}": len(cluster)
            for i, cluster in enumerate(clusters)
        }
        
        return VotingResult(
            winner=winner,
            all_responses=responses,
            vote_counts=vote_counts,
            consensus_score=consensus_score
        )
    
    async def _generate_multiple(
        self,
        prompt: str,
        generator_func: Callable
    ) -> List[Response]:
        """Generate multiple responses in parallel"""
        tasks = [
            generator_func(prompt, temperature=self.temperature)
            for _ in range(self.num_samples)
        ]
        
        results = await asyncio.gather(*tasks)
        
        return [
            Response(text=result) if isinstance(result, str) else result
            for result in results
        ]
    
    def _cluster_responses(
        self,
        responses: List[Response],
        threshold: float
    ) -> List[List[Response]]:
        """
        Group similar responses into clusters.
        
        Uses simple similarity: exact match or high overlap.
        Future: Use embedding similarity for semantic clustering.
        """
        clusters = []
        
        for response in responses:
            # Find matching cluster
            matched = False
            for cluster in clusters:
                if self._are_similar(response, cluster[0], threshold):
                    cluster.append(response)
                    matched = True
                    break
            
            # Create new cluster if no match
            if not matched:
                clusters.append([response])
        
        return clusters
    
    def _are_similar(
        self,
        response1: Response,
        response2: Response,
        threshold: float
    ) -> bool:
        """
        Check if two responses are similar.
        
        Current: Simple word overlap
        Future: Use embeddings for semantic similarity
        """
        # Normalize text
        text1 = response1.text.lower().strip()
        text2 = response2.text.lower().strip()
        
        # Exact match
        if text1 == text2:
            return True
        
        # Word-level similarity
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return False
        
        overlap = len(words1 & words2)
        union = len(words1 | words2)
        
        jaccard_sim = overlap / union if union > 0 else 0
        
        return jaccard_sim >= threshold
    
    def _select_best_from_cluster(
        self,
        cluster: List[Response]
    ) -> Response:
        """
        Select the best response from a cluster.
        
        Criteria:
        1. Longest response (more detailed)
        2. Highest confidence (if available)
        3. Best reasoning quality (if available)
        """
        if len(cluster) == 1:
            return cluster[0]
        
        # Score each response
        scored = []
        for response in cluster:
            score = 0
            
            # Length (normalized 0-1)
            max_length = max(len(r.text) for r in cluster)
            score += (len(response.text) / max_length) * 0.4 if max_length > 0 else 0
            
            # Confidence
            score += response.confidence * 0.3
            
            # Reasoning quality
            if response.reasoning:
                reasoning_score = min(len(response.reasoning) / 100, 1.0)
                score += reasoning_score * 0.3
            
            scored.append((score, response))
        
        # Return highest-scored
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1]
    
    def explain_voting(self, result: VotingResult) -> str:
        """
        Generate human-readable explanation of voting results.
        
        Args:
            result: VotingResult to explain
            
        Returns:
            Explanation text
        """
        explanation_parts = []
        
        explanation_parts.append(f"Generated {len(result.all_responses)} responses")
        explanation_parts.append(f"Consensus score: {result.consensus_score:.0%}")
        
        if result.consensus_score >= 0.8:
            explanation_parts.append("✓ High agreement (80%+)")
        elif result.consensus_score >= 0.6:
            explanation_parts.append("⚠ Moderate agreement (60-80%)")
        else:
            explanation_parts.append("⚠ Low agreement (<60%) - results may vary")
        
        explanation_parts.append(f"\nWinner selected from {result.vote_counts.get('cluster_0', 0)} similar responses")
        
        return "\n".join(explanation_parts)


# Specialized voting strategies

class MajorityVoter(SelfConsistencyVoter):
    """Simple majority voting (most common answer wins)"""
    
    def __init__(self, num_samples: int = 5):
        super().__init__(num_samples=num_samples, temperature=0.8)


class WeightedVoter(SelfConsistencyVoter):
    """Weighted voting based on confidence/quality"""
    
    def __init__(self, num_samples: int = 3):
        super().__init__(num_samples=num_samples, temperature=0.7)
    
    def _select_best_from_cluster(self, cluster: List[Response]) -> Response:
        """Override to use weighted selection"""
        if len(cluster) == 1:
            return cluster[0]
        
        # Weight by confidence and length
        scored = [
            (
                (r.confidence * 0.6) + (min(len(r.text) / 500, 1.0) * 0.4),
                r
            )
            for r in cluster
        ]
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1]


class ConservativeVoter(SelfConsistencyVoter):
    """Conservative voting (requires high consensus)"""
    
    def __init__(self, num_samples: int = 5, min_consensus: float = 0.8):
        super().__init__(num_samples=num_samples, temperature=0.5)
        self.min_consensus = min_consensus
    
    async def vote(
        self,
        prompt: str,
        generator_func: Callable,
        similarity_threshold: float = 0.9
    ) -> VotingResult:
        """Override to check minimum consensus"""
        result = await super().vote(prompt, generator_func, similarity_threshold)
        
        if result.consensus_score < self.min_consensus:
            result.winner.metadata["warning"] = (
                f"Low consensus ({result.consensus_score:.0%}). "
                f"Consider regenerating or manual review."
            )
        
        return result
