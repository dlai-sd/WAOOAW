"""
Unit Tests for Decision Framework - Story 3.2
"""
import pytest
from unittest.mock import Mock, MagicMock, patch

import sys
sys.path.insert(0, '/workspaces/WAOOAW')

from waooaw.llm.decision_framework import (
    DecisionFramework,
    Decision,
    DecisionType,
    pr_size_rule,
    critical_violation_rule,
    clean_pr_rule
)


class TestDecisionFramework:
    """Test decision framework."""
    
    def test_init(self):
        """Should initialize without LLM."""
        framework = DecisionFramework()
        
        assert framework.llm is None
        assert framework.decision_count == 0
    
    def test_deterministic_decision(self):
        """Should use deterministic rule."""
        framework = DecisionFramework()
        
        context = {"total_changes": 50, "violations": []}
        rules = [clean_pr_rule]
        
        decision = framework.make_decision(
            question="Should I approve this PR?",
            context=context,
            deterministic_rules=rules,
            fallback_to_llm=False
        )
        
        assert decision.choice == "approve"
        assert decision.confidence == 1.0
        assert decision.decision_type == DecisionType.DETERMINISTIC
        assert framework.deterministic_count == 1
    
    def test_fallback_to_llm(self):
        """Should fall back to LLM if rules don't match."""
        mock_llm = MagicMock()
        mock_llm.simple_call.return_value = "I approve this PR because it looks good. Confident."
        mock_llm.model = "claude-sonnet-4"
        
        framework = DecisionFramework(llm=mock_llm)
        
        context = {"total_changes": 500, "violations": [{"severity": "low"}]}
        rules = [clean_pr_rule]  # Won't match (has violation)
        
        decision = framework.make_decision(
            question="Should I approve this PR?",
            context=context,
            deterministic_rules=rules,
            llm_prompt_template="Question: {question}\nContext: {context}\nDecision:",
            fallback_to_llm=True
        )
        
        assert decision.choice == "approve"
        assert decision.decision_type == DecisionType.LLM_DRIVEN
        assert framework.llm_count == 1
        mock_llm.simple_call.assert_called_once()
    
    def test_no_decision_possible(self):
        """Should return None if no rule matches and no LLM."""
        framework = DecisionFramework()
        
        context = {"total_changes": 500}
        rules = [clean_pr_rule]  # Won't match
        
        decision = framework.make_decision(
            question="Should I approve?",
            context=context,
            deterministic_rules=rules,
            fallback_to_llm=False
        )
        
        assert decision.choice is None
        assert decision.confidence == 0.0
    
    def test_get_stats(self):
        """Should track decision statistics."""
        framework = DecisionFramework()
        
        # Make 3 deterministic decisions
        for _ in range(3):
            framework.make_decision(
                question="Test",
                context={"total_changes": 50, "violations": []},
                deterministic_rules=[clean_pr_rule],
                fallback_to_llm=False
            )
        
        stats = framework.get_stats()
        assert stats["total_decisions"] == 3
        assert stats["deterministic_decisions"] == 3
        assert stats["llm_decisions"] == 0
        assert stats["deterministic_pct"] == 100


class TestDeterministicRules:
    """Test deterministic decision rules."""
    
    def test_pr_size_rule_large(self):
        """Should reject large PRs."""
        context = {"total_changes": 1500}
        decision = pr_size_rule(context)
        
        assert decision is not None
        assert decision.choice == "reject"
        assert "too large" in decision.reasoning.lower()
    
    def test_pr_size_rule_small(self):
        """Should not match small PRs."""
        context = {"total_changes": 100}
        decision = pr_size_rule(context)
        
        assert decision is None
    
    def test_critical_violation_rule(self):
        """Should reject PRs with critical violations."""
        context = {
            "violations": [
                {"severity": "critical", "type": "Security"},
                {"severity": "high", "type": "Bug"}
            ]
        }
        decision = critical_violation_rule(context)
        
        assert decision is not None
        assert decision.choice == "reject"
        assert "critical" in decision.reasoning.lower()
    
    def test_critical_violation_rule_no_critical(self):
        """Should not match if no critical violations."""
        context = {
            "violations": [
                {"severity": "high", "type": "Bug"}
            ]
        }
        decision = critical_violation_rule(context)
        
        assert decision is None
    
    def test_clean_pr_rule(self):
        """Should approve clean PRs."""
        context = {"total_changes": 200, "violations": []}
        decision = clean_pr_rule(context)
        
        assert decision is not None
        assert decision.choice == "approve"
        assert "clean" in decision.reasoning.lower()
    
    def test_clean_pr_rule_has_violations(self):
        """Should not match if violations present."""
        context = {"total_changes": 100, "violations": [{"severity": "low"}]}
        decision = clean_pr_rule(context)
        
        assert decision is None


class TestLLMDecision:
    """Test LLM-driven decisions."""
    
    def test_llm_extract_choice_approve(self):
        """Should extract 'approve' from LLM response."""
        framework = DecisionFramework()
        
        response = "After reviewing the changes, I approve this PR."
        choice = framework._extract_choice(response)
        
        assert choice == "approve"
    
    def test_llm_extract_choice_reject(self):
        """Should extract 'reject' from LLM response."""
        framework = DecisionFramework()
        
        response = "I must reject this PR due to security concerns."
        choice = framework._extract_choice(response)
        
        assert choice == "reject"
    
    def test_llm_extract_confidence(self):
        """Should extract confidence level."""
        framework = DecisionFramework()
        
        assert framework._extract_confidence("I'm highly confident") >= 0.9
        assert framework._extract_confidence("I'm confident") >= 0.7
        assert framework._extract_confidence("Somewhat confident") >= 0.5
        assert framework._extract_confidence("Uncertain") <= 0.4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
