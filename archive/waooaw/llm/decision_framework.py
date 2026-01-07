"""
Decision Framework - Story 3.2

Combines deterministic rules with LLM reasoning for agent decisions.
Part of Epic 3: LLM Integration.
"""
import logging
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from dataclasses import dataclass

from .claude_wrapper import ClaudeAPIWrapper

logger = logging.getLogger(__name__)


class DecisionType(Enum):
    """Types of decisions agents can make."""
    DETERMINISTIC = "deterministic"  # Rule-based, no LLM
    LLM_ASSISTED = "llm_assisted"  # LLM provides reasoning, rules decide
    LLM_DRIVEN = "llm_driven"  # LLM makes final decision


@dataclass
class Decision:
    """Result of a decision."""
    choice: Any
    reasoning: str
    confidence: float  # 0.0 to 1.0
    decision_type: DecisionType
    metadata: Dict[str, Any]


class DecisionFramework:
    """
    Framework for making decisions with deterministic + LLM reasoning.
    
    Hierarchy:
    1. Try deterministic rules first (fast, reliable)
    2. Fall back to LLM if ambiguous (smart, flexible)
    3. Return decision with reasoning and confidence
    """
    
    def __init__(self, llm: Optional[ClaudeAPIWrapper] = None):
        """
        Initialize decision framework.
        
        Args:
            llm: ClaudeAPIWrapper instance (optional, for LLM decisions)
        """
        self.llm = llm
        self.decision_count = 0
        self.deterministic_count = 0
        self.llm_count = 0
        
        logger.info("DecisionFramework initialized")
    
    def make_decision(
        self,
        question: str,
        context: Dict[str, Any],
        deterministic_rules: Optional[List[Callable]] = None,
        llm_prompt_template: Optional[str] = None,
        fallback_to_llm: bool = True
    ) -> Decision:
        """
        Make a decision using deterministic rules + optional LLM.
        
        Args:
            question: Decision question (e.g., "Should I approve this PR?")
            context: Decision context (PR details, files, violations, etc.)
            deterministic_rules: List of rule functions (return Decision or None)
            llm_prompt_template: Template for LLM prompt (used if rules fail)
            fallback_to_llm: Fall back to LLM if rules inconclusive
            
        Returns:
            Decision with choice, reasoning, confidence
        """
        self.decision_count += 1
        
        logger.info(f"Making decision: {question}")
        
        # Step 1: Try deterministic rules
        if deterministic_rules:
            for rule in deterministic_rules:
                try:
                    decision = rule(context)
                    if decision is not None:
                        self.deterministic_count += 1
                        logger.info(
                            f"Decision made by rule: {decision.choice}",
                            extra={"confidence": decision.confidence}
                        )
                        return decision
                except Exception as e:
                    logger.warning(f"Rule failed: {e}", exc_info=True)
                    continue
        
        # Step 2: Fall back to LLM if enabled
        if fallback_to_llm and self.llm and llm_prompt_template:
            self.llm_count += 1
            return self._llm_decision(
                question=question,
                context=context,
                prompt_template=llm_prompt_template
            )
        
        # Step 3: No decision possible
        return Decision(
            choice=None,
            reasoning="No deterministic rule matched and LLM not available",
            confidence=0.0,
            decision_type=DecisionType.DETERMINISTIC,
            metadata={"rules_tried": len(deterministic_rules or [])}
        )
    
    def _llm_decision(
        self,
        question: str,
        context: Dict[str, Any],
        prompt_template: str
    ) -> Decision:
        """
        Make decision using LLM.
        
        Args:
            question: Decision question
            context: Context dict
            prompt_template: Prompt template with {question} and {context}
            
        Returns:
            Decision from LLM
        """
        try:
            # Format prompt
            prompt = prompt_template.format(
                question=question,
                context=self._format_context(context)
            )
            
            # Call LLM
            response = self.llm.simple_call(
                prompt=prompt,
                system="You are a decision-making assistant. Provide clear, actionable decisions with reasoning."
            )
            
            # Parse response (simple extraction for now)
            choice = self._extract_choice(response)
            confidence = self._extract_confidence(response)
            
            logger.info(
                f"LLM decision: {choice}",
                extra={"confidence": confidence}
            )
            
            return Decision(
                choice=choice,
                reasoning=response,
                confidence=confidence,
                decision_type=DecisionType.LLM_DRIVEN,
                metadata={"llm_model": self.llm.model}
            )
            
        except Exception as e:
            logger.error(f"LLM decision failed: {e}", exc_info=True)
            return Decision(
                choice=None,
                reasoning=f"LLM error: {str(e)}",
                confidence=0.0,
                decision_type=DecisionType.LLM_DRIVEN,
                metadata={"error": str(e)}
            )
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context dict as string for LLM."""
        lines = []
        for key, value in context.items():
            if isinstance(value, (list, dict)):
                lines.append(f"- {key}: {len(value)} items")
            else:
                lines.append(f"- {key}: {value}")
        return "\n".join(lines)
    
    def _extract_choice(self, response: str) -> Optional[Any]:
        """Extract decision choice from LLM response."""
        # Simple heuristic: look for "approve", "reject", "yes", "no"
        response_lower = response.lower()
        
        if "approve" in response_lower or "yes" in response_lower:
            return "approve"
        elif "reject" in response_lower or "no" in response_lower:
            return "reject"
        elif "escalate" in response_lower:
            return "escalate"
        
        return None
    
    def _extract_confidence(self, response: str) -> float:
        """Extract confidence from LLM response."""
        # Simple heuristic: look for confidence keywords
        response_lower = response.lower()
        
        if "highly confident" in response_lower or "certain" in response_lower:
            return 0.9
        elif "confident" in response_lower:
            return 0.8
        elif "somewhat confident" in response_lower or "likely" in response_lower:
            return 0.6
        elif "uncertain" in response_lower or "unclear" in response_lower:
            return 0.3
        
        return 0.5  # Default
    
    def get_stats(self) -> Dict[str, int]:
        """Get decision statistics."""
        return {
            "total_decisions": self.decision_count,
            "deterministic_decisions": self.deterministic_count,
            "llm_decisions": self.llm_count,
            "deterministic_pct": (
                int(100 * self.deterministic_count / self.decision_count)
                if self.decision_count > 0 else 0
            )
        }


# Common decision rules

def pr_size_rule(context: Dict[str, Any]) -> Optional[Decision]:
    """
    Deterministic rule: Reject PRs with >1000 line changes.
    
    Args:
        context: Must contain 'total_changes' key
        
    Returns:
        Decision or None
    """
    total_changes = context.get("total_changes", 0)
    
    if total_changes > 1000:
        return Decision(
            choice="reject",
            reasoning=f"PR too large ({total_changes} changes). Break into smaller PRs.",
            confidence=1.0,
            decision_type=DecisionType.DETERMINISTIC,
            metadata={"rule": "pr_size_rule", "total_changes": total_changes}
        )
    
    return None


def critical_violation_rule(context: Dict[str, Any]) -> Optional[Decision]:
    """
    Deterministic rule: Reject PRs with critical violations.
    
    Args:
        context: Must contain 'violations' list
        
    Returns:
        Decision or None
    """
    violations = context.get("violations", [])
    critical = [v for v in violations if v.get("severity") == "critical"]
    
    if critical:
        return Decision(
            choice="reject",
            reasoning=f"Found {len(critical)} critical violation(s). Must fix before merge.",
            confidence=1.0,
            decision_type=DecisionType.DETERMINISTIC,
            metadata={"rule": "critical_violation_rule", "critical_count": len(critical)}
        )
    
    return None


def clean_pr_rule(context: Dict[str, Any]) -> Optional[Decision]:
    """
    Deterministic rule: Approve clean PRs (no violations, small size).
    
    Args:
        context: Must contain 'violations' and 'total_changes'
        
    Returns:
        Decision or None
    """
    violations = context.get("violations", [])
    total_changes = context.get("total_changes", 0)
    
    if len(violations) == 0 and total_changes < 300:
        return Decision(
            choice="approve",
            reasoning="Clean PR with no violations and reasonable size.",
            confidence=1.0,
            decision_type=DecisionType.DETERMINISTIC,
            metadata={"rule": "clean_pr_rule"}
        )
    
    return None
