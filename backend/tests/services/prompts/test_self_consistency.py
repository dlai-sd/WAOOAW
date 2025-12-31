"""
Tests for Self-Consistency Voting
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.prompts.self_consistency import (
    SelfConsistencyVoter,
    MajorityVoter,
    WeightedVoter,
    ConservativeVoter,
    Response,
    VotingResult
)


class TestResponse:
    """Test Response dataclass"""
    
    def test_create_response_minimal(self):
        """Test creating response with minimal data"""
        response = Response(text="Test response")
        
        assert response.text == "Test response"
        assert response.reasoning is None
        assert response.confidence == 0.0
        assert response.metadata == {}
    
    def test_create_response_full(self):
        """Test creating response with all fields"""
        response = Response(
            text="Full response",
            reasoning="My reasoning",
            confidence=0.95,
            metadata={"model": "gpt-4", "tokens": 150}
        )
        
        assert response.text == "Full response"
        assert response.confidence == 0.95
        assert response.metadata["model"] == "gpt-4"


class TestSelfConsistencyVoter:
    """Test SelfConsistencyVoter functionality"""
    
    @pytest.mark.asyncio
    async def test_vote_with_consensus(self):
        """Test voting when responses agree"""
        voter = SelfConsistencyVoter(num_samples=3)
        
        # Mock generator that returns same answer
        async def generator(prompt, temperature):
            return Response(text="Paris", confidence=0.9)
        
        result = await voter.vote("What is capital of France?", generator)
        
        assert result.winner.text == "Paris"
        assert result.consensus_score == 1.0  # 100% agreement
        assert len(result.all_responses) == 3
    
    @pytest.mark.asyncio
    async def test_vote_with_split(self):
        """Test voting when responses differ"""
        voter = SelfConsistencyVoter(num_samples=5)
        
        responses_to_return = [
            Response(text="Paris", confidence=0.9),
            Response(text="Paris", confidence=0.85),
            Response(text="Paris", confidence=0.92),
            Response(text="Lyon", confidence=0.7),
            Response(text="Marseille", confidence=0.6)
        ]
        
        call_count = [0]
        
        async def generator(prompt, temperature):
            response = responses_to_return[call_count[0]]
            call_count[0] += 1
            return response
        
        result = await voter.vote("What is capital of France?", generator)
        
        # Paris should win (3/5 = 60%)
        assert result.winner.text == "Paris"
        assert result.consensus_score == 0.6
        assert len(result.all_responses) == 5
    
    @pytest.mark.asyncio
    async def test_vote_selects_best_from_cluster(self):
        """Test that winner is best response from winning cluster"""
        voter = SelfConsistencyVoter(num_samples=3)
        
        responses_to_return = [
            Response(text="Paris is the capital", confidence=0.95),
            Response(text="Paris is the capital", confidence=0.85),
            Response(text="Paris is the capital", confidence=0.99)  # Highest confidence
        ]
        
        call_count = [0]
        
        async def generator(prompt, temperature):
            response = responses_to_return[call_count[0]]
            call_count[0] += 1
            return response
        
        result = await voter.vote("Capital of France?", generator)
        
        # Should select response with highest confidence
        assert result.winner.confidence == 0.99
    
    def test_are_similar_exact_match(self):
        """Test similarity detection with exact match"""
        voter = SelfConsistencyVoter()
        
        r1 = Response(text="Paris")
        r2 = Response(text="Paris")
        
        assert voter._are_similar(r1, r2, threshold=0.8)
    
    def test_are_similar_high_overlap(self):
        """Test similarity with high word overlap"""
        voter = SelfConsistencyVoter()
        
        r1 = Response(text="Paris is the capital of France")
        r2 = Response(text="Paris is the capital")
        
        # High overlap should be similar
        assert voter._are_similar(r1, r2, threshold=0.6)
    
    def test_are_similar_low_overlap(self):
        """Test dissimilarity with low overlap"""
        voter = SelfConsistencyVoter()
        
        r1 = Response(text="Paris is the capital")
        r2 = Response(text="London is nice")
        
        # Low overlap should not be similar
        assert not voter._are_similar(r1, r2, threshold=0.8)
    
    def test_cluster_responses_single_cluster(self):
        """Test clustering when all responses are similar"""
        voter = SelfConsistencyVoter()
        
        responses = [
            Response(text="Answer A"),
            Response(text="Answer A"),
            Response(text="Answer A")
        ]
        
        clusters = voter._cluster_responses(responses, threshold=0.8)
        
        assert len(clusters) == 1
        assert len(clusters[0]) == 3
    
    def test_cluster_responses_multiple_clusters(self):
        """Test clustering when responses differ"""
        voter = SelfConsistencyVoter()
        
        responses = [
            Response(text="Answer A"),
            Response(text="Answer A"),
            Response(text="Answer B"),
            Response(text="Answer C")
        ]
        
        clusters = voter._cluster_responses(responses, threshold=0.9)
        
        # Should have 3 clusters (A, B, C)
        assert len(clusters) >= 2
        # Largest cluster should have 2 responses (Answer A)
        assert max(len(c) for c in clusters) == 2
    
    def test_select_best_prefers_length(self):
        """Test selection prefers longer, more detailed responses"""
        voter = SelfConsistencyVoter()
        
        cluster = [
            Response(text="Short"),
            Response(text="This is a much longer and more detailed response"),
            Response(text="Medium length")
        ]
        
        best = voter._select_best_from_cluster(cluster)
        
        # Should prefer the longest response
        assert "more detailed" in best.text
    
    def test_select_best_prefers_confidence(self):
        """Test selection considers confidence"""
        voter = SelfConsistencyVoter()
        
        cluster = [
            Response(text="Answer with low confidence", confidence=0.5),
            Response(text="Answer with high confidence", confidence=0.95),
            Response(text="Answer with medium confidence", confidence=0.7)
        ]
        
        best = voter._select_best_from_cluster(cluster)
        
        # Should strongly weight confidence
        assert best.confidence == 0.95
    
    def test_explain_voting_high_consensus(self):
        """Test explanation for high consensus"""
        result = VotingResult(
            winner=Response(text="Paris"),
            all_responses=[Response(text="Paris")] * 5,
            vote_counts={"cluster_0": 5},
            consensus_score=1.0
        )
        
        voter = SelfConsistencyVoter()
        explanation = voter.explain_voting(result)
        
        assert "High agreement" in explanation or "80%" in explanation
        assert "5" in explanation  # Number of responses
    
    def test_explain_voting_low_consensus(self):
        """Test explanation for low consensus"""
        result = VotingResult(
            winner=Response(text="Answer"),
            all_responses=[Response(text="A"), Response(text="B"), Response(text="C")],
            vote_counts={"cluster_0": 1, "cluster_1": 1, "cluster_2": 1},
            consensus_score=0.33
        )
        
        voter = SelfConsistencyVoter()
        explanation = voter.explain_voting(result)
        
        assert "Low agreement" in explanation or "⚠" in explanation
        assert "results may vary" in explanation.lower() or "vary" in explanation.lower()


class TestMajorityVoter:
    """Test MajorityVoter specialization"""
    
    def test_majority_voter_initialization(self):
        """Test majority voter has higher sample count"""
        voter = MajorityVoter()
        
        assert voter.num_samples == 5  # More samples for better majority
        assert voter.temperature == 0.8  # Higher temperature for diversity


class TestWeightedVoter:
    """Test WeightedVoter specialization"""
    
    def test_weighted_voter_initialization(self):
        """Test weighted voter initialization"""
        voter = WeightedVoter()
        
        assert voter.num_samples == 3
        assert voter.temperature == 0.7
    
    def test_weighted_selection_considers_confidence(self):
        """Test weighted voter prioritizes confidence"""
        voter = WeightedVoter()
        
        cluster = [
            Response(text="A" * 100, confidence=0.6),   # Medium length, low confidence
            Response(text="B" * 400, confidence=0.95),  # Longer AND high confidence
        ]
        
        best = voter._select_best_from_cluster(cluster)
        
        # Should select the high confidence response
        assert best.confidence == 0.95


class TestConservativeVoter:
    """Test ConservativeVoter specialization"""
    
    def test_conservative_voter_initialization(self):
        """Test conservative voter has lower temperature"""
        voter = ConservativeVoter()
        
        assert voter.num_samples == 5  # More samples
        assert voter.temperature == 0.5  # Lower temperature (less random)
        assert voter.min_consensus == 0.8
    
    @pytest.mark.asyncio
    async def test_conservative_voter_adds_warning(self):
        """Test conservative voter adds warning for low consensus"""
        voter = ConservativeVoter(min_consensus=0.8)
        
        responses_to_return = [
            Response(text="A"),
            Response(text="A"),
            Response(text="B"),
            Response(text="B"),
            Response(text="C")
        ]
        
        call_count = [0]
        
        async def generator(prompt, temperature):
            response = responses_to_return[call_count[0]]
            call_count[0] += 1
            return response
        
        result = await voter.vote("Test?", generator, similarity_threshold=0.9)
        
        # Low consensus (2/5 = 40%) should trigger warning
        if result.consensus_score < 0.8:
            assert "warning" in result.winner.metadata
            assert "Low consensus" in result.winner.metadata["warning"]


@pytest.mark.integration
class TestSelfConsistencyIntegration:
    """Integration tests for self-consistency voting"""
    
    @pytest.mark.asyncio
    async def test_vote_with_realistic_llm_responses(self):
        """Test voting with realistic varied LLM responses"""
        voter = SelfConsistencyVoter(num_samples=5)
        
        # Simulate realistic LLM responses with slight variations
        realistic_responses = [
            "The answer is 42 because that's the result of the calculation.",
            "After calculation, I get 42 as the answer.",
            "42 is the correct answer here.",
            "The result is 42.",
            "I calculate this to be 41."  # Outlier
        ]
        
        call_count = [0]
        
        async def generator(prompt, temperature):
            response = realistic_responses[call_count[0]]
            call_count[0] += 1
            return Response(text=response, confidence=0.85)
        
        result = await voter.vote("What is 6 * 7?", generator)
        
        # Should identify "42" as consensus despite wording differences
        assert "42" in result.winner.text
        assert result.consensus_score >= 0.6  # At least 60% agree
