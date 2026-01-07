"""
Prompt Templates - Story 3.3

Structured prompts for common agent tasks.
Part of Epic 3: LLM Integration.
"""
import logging
from typing import Dict, Any, List, Optional
from string import Template

logger = logging.getLogger(__name__)


class PromptTemplates:
    """
    Collection of structured prompts for agent tasks.
    
    Features:
    - Vision validation prompts
    - Code review prompts
    - Ambiguity resolution prompts
    - Decision-making prompts
    - Variable substitution
    - Few-shot examples
    """
    
    # System prompts
    
    VISION_GUARDIAN_SYSTEM = """You are WowVision Prime, a vision guardian agent.
Your role: Ensure all code changes align with the product vision defined in vision.yaml.
You have deep understanding of:
- Product vision and strategic goals
- Feature requirements and acceptance criteria
- Quality standards and best practices

Be thorough, direct, and constructive. Flag misalignments immediately."""
    
    CODE_REVIEWER_SYSTEM = """You are WowVision Prime, a code review agent.
Your role: Review code for quality, security, and maintainability.
You check for:
- Security vulnerabilities
- Performance issues
- Code smells
- Best practice violations
- Test coverage

Provide actionable feedback with specific line references."""
    
    DECISION_MAKER_SYSTEM = """You are WowVision Prime, a decision-making agent.
Your role: Make informed decisions based on context and constraints.
You consider:
- Technical feasibility
- Risk assessment
- Business impact
- Resource constraints

Provide clear decisions with reasoning and confidence level."""
    
    # Task prompts
    
    @staticmethod
    def vision_validation_prompt(
        change_description: str,
        files_changed: List[str],
        vision_context: str,
        pr_number: Optional[int] = None
    ) -> str:
        """
        Generate prompt for vision validation.
        
        Args:
            change_description: Description of changes
            files_changed: List of files modified
            vision_context: Relevant vision.yaml content
            pr_number: PR number (optional)
            
        Returns:
            Formatted prompt
        """
        template = Template("""# Vision Validation Task

## Change Overview
$change_description

## Files Changed
$files_list

## Vision Context (from vision.yaml)
$vision_context

## Your Task
1. Analyze if these changes align with our product vision
2. Identify any misalignments or concerns
3. Provide specific recommendations

## Output Format
**Alignment Score**: [0-100]
**Decision**: [APPROVE / REJECT / ESCALATE]
**Reasoning**: [Your detailed analysis]
**Specific Concerns**: [List any issues]
**Recommendations**: [Actionable next steps]
""")
        
        files_list = "\n".join(f"- {f}" for f in files_changed)
        
        return template.substitute(
            change_description=change_description,
            files_list=files_list,
            vision_context=vision_context
        )
    
    @staticmethod
    def code_review_prompt(
        file_path: str,
        file_content: str,
        diff: Optional[str] = None,
        focus_areas: Optional[List[str]] = None
    ) -> str:
        """
        Generate prompt for code review.
        
        Args:
            file_path: Path to file being reviewed
            file_content: Full file content
            diff: Git diff (optional)
            focus_areas: Specific areas to focus on (security, performance, etc.)
            
        Returns:
            Formatted prompt
        """
        template = Template("""# Code Review Task

## File: $file_path

## Content
```
$file_content
```

$diff_section

$focus_section

## Your Task
1. Review the code for issues
2. Rate severity: CRITICAL / HIGH / MEDIUM / LOW
3. Provide specific line numbers
4. Suggest fixes

## Output Format
**Overall Quality**: [0-100]
**Issues Found**: [Count]

### Issues
1. **[SEVERITY]** Line X: [Description]
   - Suggested Fix: [Concrete fix]
   
2. **[SEVERITY]** Line Y: [Description]
   - Suggested Fix: [Concrete fix]

**Approval**: [APPROVE / REQUEST_CHANGES]
""")
        
        diff_section = f"\n## Changes (Diff)\n```diff\n{diff}\n```\n" if diff else ""
        
        focus_section = ""
        if focus_areas:
            focus_section = "\n## Focus Areas\n" + "\n".join(f"- {area}" for area in focus_areas)
        
        return template.substitute(
            file_path=file_path,
            file_content=file_content[:2000],  # Truncate for token limit
            diff_section=diff_section,
            focus_section=focus_section
        )
    
    @staticmethod
    def ambiguity_resolution_prompt(
        ambiguous_situation: str,
        context: Dict[str, Any],
        options: List[str]
    ) -> str:
        """
        Generate prompt for ambiguity resolution.
        
        Args:
            ambiguous_situation: Description of ambiguous situation
            context: Relevant context
            options: Possible resolution options
            
        Returns:
            Formatted prompt
        """
        template = Template("""# Ambiguity Resolution Task

## Situation
$ambiguous_situation

## Context
$context_str

## Possible Options
$options_list

## Your Task
1. Analyze the situation and context
2. Evaluate each option
3. Recommend the best path forward
4. If still unclear, escalate to human

## Output Format
**Recommended Option**: [Option number or "ESCALATE"]
**Confidence**: [0-100]
**Reasoning**: [Your analysis]
**Risks**: [Potential risks of chosen option]
**Alternative**: [Second-best option and why]
""")
        
        context_str = "\n".join(f"- {k}: {v}" for k, v in context.items())
        options_list = "\n".join(f"{i+1}. {opt}" for i, opt in enumerate(options))
        
        return template.substitute(
            ambiguous_situation=ambiguous_situation,
            context_str=context_str,
            options_list=options_list
        )
    
    @staticmethod
    def pr_approval_decision_prompt(
        pr_number: int,
        files_count: int,
        violations: List[Dict[str, Any]],
        test_results: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate prompt for PR approval decision.
        
        Args:
            pr_number: PR number
            files_count: Number of files changed
            violations: List of violations found
            test_results: Test results (optional)
            
        Returns:
            Formatted prompt
        """
        template = Template("""# PR Approval Decision

## PR #$pr_number

## Summary
- Files Changed: $files_count
- Violations: $violations_count
  - Critical: $critical_count
  - High: $high_count
  - Medium: $medium_count
  - Low: $low_count

$violations_details

$test_section

## Your Task
Decide whether to approve this PR based on:
1. Violation severity and count
2. Test results
3. Risk assessment
4. Business impact

## Output Format
**Decision**: [APPROVE / REQUEST_CHANGES / ESCALATE]
**Confidence**: [0-100]
**Reasoning**: [Detailed justification]
**Conditions**: [Any conditions for approval]
**Next Steps**: [What should happen next]
""")
        
        # Count violations by severity
        critical = sum(1 for v in violations if v.get("severity") == "critical")
        high = sum(1 for v in violations if v.get("severity") == "high")
        medium = sum(1 for v in violations if v.get("severity") == "medium")
        low = sum(1 for v in violations if v.get("severity") == "low")
        
        # Format violations
        violations_details = ""
        if violations:
            violations_details = "\n## Violations Detail\n"
            for v in violations[:5]:  # Show first 5
                violations_details += f"- [{v.get('severity', 'UNKNOWN').upper()}] {v.get('file_path', 'N/A')}: {v.get('description', 'No description')}\n"
        
        # Format test results
        test_section = ""
        if test_results:
            test_section = f"\n## Test Results\n- Passed: {test_results.get('passed', 0)}\n- Failed: {test_results.get('failed', 0)}\n- Coverage: {test_results.get('coverage', 0)}%\n"
        
        return template.substitute(
            pr_number=pr_number,
            files_count=files_count,
            violations_count=len(violations),
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            low_count=low,
            violations_details=violations_details,
            test_section=test_section
        )
    
    @staticmethod
    def escalation_prompt(
        trigger: str,
        reason: str,
        context: Dict[str, Any],
        attempted_actions: List[str]
    ) -> str:
        """
        Generate prompt for escalation to human.
        
        Args:
            trigger: What triggered escalation
            reason: Why escalating
            context: Relevant context
            attempted_actions: What agent tried
            
        Returns:
            Formatted prompt
        """
        template = Template("""# Escalation Required

## Trigger
$trigger

## Reason for Escalation
$reason

## Context
$context_str

## Actions Attempted
$actions_list

## Your Task
Summarize this situation for a human reviewer:
1. What is the core issue?
2. Why couldn't you resolve it?
3. What specific input is needed?
4. What are the implications of delay?

## Output Format
**Issue Summary**: [One-sentence summary]
**Core Problem**: [Detailed explanation]
**Blocker**: [What prevents autonomous resolution]
**Requested Input**: [Specific questions/decisions needed]
**Urgency**: [LOW / MEDIUM / HIGH / CRITICAL]
**Impact if Unresolved**: [Consequences]
""")
        
        context_str = "\n".join(f"- {k}: {v}" for k, v in context.items())
        actions_list = "\n".join(f"{i+1}. {action}" for i, action in enumerate(attempted_actions))
        
        return template.substitute(
            trigger=trigger,
            reason=reason,
            context_str=context_str,
            actions_list=actions_list
        )
    
    # Few-shot examples
    
    VISION_VALIDATION_EXAMPLES = [
        {
            "input": "Adding dark mode toggle to settings page",
            "output": """Alignment Score: 95
Decision: APPROVE
Reasoning: Dark mode aligns with our UX vision of customizable, accessible interfaces.
Specific Concerns: Ensure color contrast meets WCAG AA standards.
Recommendations: Add dark mode test coverage."""
        },
        {
            "input": "Replacing PostgreSQL with MongoDB",
            "output": """Alignment Score: 20
Decision: REJECT
Reasoning: Vision specifies PostgreSQL for relational data integrity. This change contradicts architectural decisions.
Specific Concerns: Loss of ACID guarantees, migration complexity.
Recommendations: Escalate if there's a compelling reason; otherwise reject."""
        }
    ]
