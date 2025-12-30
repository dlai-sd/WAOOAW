"""
Interactive Questionnaire System

Gather agent specifications through structured questions.

Story: #81 Questionnaire System (3 pts)
Epic: #68 WowAgentFactory Core (v0.4.1)
Theme: CONCEIVE
"""

import logging
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from waooaw.factory.config.schema import AgentSpecConfig, AgentDomain, validate_agent_spec

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class QuestionType(Enum):
    """Question types"""
    TEXT = "text"
    NUMBER = "number"
    CHOICE = "choice"
    MULTI_CHOICE = "multi_choice"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Question:
    """
    Questionnaire question.
    
    Attributes:
        id: Question identifier
        text: Question text
        type: Question type
        required: Whether question is required
        default: Default value
        choices: Valid choices (for choice/multi_choice)
        validation: Validation function
        depends_on: Question ID this depends on
        help_text: Help text
    """
    id: str
    text: str
    type: QuestionType
    required: bool = True
    default: Optional[Any] = None
    choices: List[Any] = field(default_factory=list)
    validation: Optional[Callable[[Any], tuple[bool, Optional[str]]]] = None
    depends_on: Optional[str] = None
    help_text: str = ""
    
    def validate_answer(self, answer: Any) -> tuple[bool, Optional[str]]:
        """
        Validate answer.
        
        Args:
            answer: User's answer
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required
        if self.required and answer is None:
            return False, "This question is required"
        
        # Check choices
        if self.type == QuestionType.CHOICE and answer not in self.choices:
            return False, f"Must be one of: {', '.join(str(c) for c in self.choices)}"
        
        if self.type == QuestionType.MULTI_CHOICE:
            if not isinstance(answer, list):
                return False, "Must be a list"
            for item in answer:
                if item not in self.choices:
                    return False, f"{item} not in valid choices"
        
        # Custom validation
        if self.validation:
            return self.validation(answer)
        
        return True, None


# =============================================================================
# QUESTIONNAIRE
# =============================================================================

class Questionnaire:
    """
    Interactive questionnaire for gathering agent specifications.
    
    Asks structured questions to collect:
    - Agent identity (name, tier, domain)
    - Capabilities
    - Constraints
    - Dependencies
    - Wake patterns
    - Resource budget
    - Specialization
    """
    
    def __init__(self):
        """Initialize questionnaire"""
        self.questions = self._build_questions()
        self.answers: Dict[str, Any] = {}
        logger.info("✅ Questionnaire initialized")
    
    def _build_questions(self) -> List[Question]:
        """Build question list"""
        return [
            # Basic Info
            Question(
                id="coe_name",
                text="What is the agent name? (must start with 'Wow')",
                type=QuestionType.TEXT,
                required=True,
                validation=lambda x: (
                    (True, None) if x and x.startswith("Wow") and x[3].isupper()
                    else (False, "Name must start with 'Wow' followed by uppercase letter")
                ),
                help_text="Example: WowDomain, WowMemory, WowCache"
            ),
            
            Question(
                id="display_name",
                text="What is the display name?",
                type=QuestionType.TEXT,
                required=True,
                help_text="Human-readable name (same as agent name usually)"
            ),
            
            Question(
                id="tier",
                text="What tier is this agent? (1-6)",
                type=QuestionType.CHOICE,
                choices=[1, 2, 3, 4, 5, 6],
                required=True,
                help_text=(
                    "Tier 1: Guardian (WowVision)\n"
                    "Tier 2: Creation & Domain\n"
                    "Tier 3: Communication\n"
                    "Tier 4: Intelligence & Memory\n"
                    "Tier 5: Security & Integrity\n"
                    "Tier 6: Scale & Operations"
                )
            ),
            
            Question(
                id="domain",
                text="What is the agent domain?",
                type=QuestionType.CHOICE,
                choices=[d.value for d in AgentDomain],
                required=True,
                help_text="Domain category for the agent"
            ),
            
            Question(
                id="version",
                text="What is the initial version?",
                type=QuestionType.TEXT,
                default="0.4.2",
                validation=lambda x: (
                    (True, None) if x and len(x.split('.')) == 3
                    else (False, "Must be semantic version (e.g., 0.4.2)")
                ),
                help_text="Semantic version (major.minor.patch)"
            ),
            
            Question(
                id="description",
                text="Describe the agent's purpose (min 10 chars)",
                type=QuestionType.TEXT,
                required=True,
                validation=lambda x: (
                    (True, None) if x and len(x) >= 10
                    else (False, "Description must be at least 10 characters")
                ),
                help_text="One-sentence description of what this agent does"
            ),
            
            # Capabilities
            Question(
                id="capability_categories",
                text="What capability categories does this agent have?",
                type=QuestionType.LIST,
                required=True,
                help_text="Examples: modeling, validation, events, messaging, storage"
            ),
            
            # Constraints
            Question(
                id="has_constraints",
                text="Does this agent have behavioral constraints?",
                type=QuestionType.BOOLEAN,
                default=False,
                help_text="Constraints limit what the agent can do"
            ),
            
            Question(
                id="constraints",
                text="Enter constraints (rule:reason format, comma-separated)",
                type=QuestionType.LIST,
                required=False,
                depends_on="has_constraints",
                help_text="Example: infrastructure-independent:DDD separation"
            ),
            
            # Dependencies
            Question(
                id="dependencies",
                text="Which agents does this depend on?",
                type=QuestionType.MULTI_CHOICE,
                choices=[
                    "WowVisionPrime", "WowAgentFactory", "WowDomain",
                    "WowEvent", "WowCommunication", "WowMemory",
                    "WowCache", "WowSearch", "WowSecurity",
                    "WowSupport", "WowNotification", "WowScaling",
                    "WowIntegration", "WowAnalytics"
                ],
                required=False,
                default=[],
                help_text="Select all that apply"
            ),
            
            # Wake Patterns
            Question(
                id="wake_patterns",
                text="What event patterns wake this agent?",
                type=QuestionType.LIST,
                required=True,
                help_text="Examples: domain.*, wowdomain.*, *.created"
            ),
            
            # Resource Budget
            Question(
                id="resource_budget",
                text="What is the monthly cost budget (USD)?",
                type=QuestionType.NUMBER,
                default=30.0,
                validation=lambda x: (
                    (True, None) if x and x >= 0
                    else (False, "Budget must be non-negative")
                ),
                help_text="Estimated monthly operational cost"
            ),
            
            # Specialization
            Question(
                id="has_specialization",
                text="Does this agent have domain-specific configuration?",
                type=QuestionType.BOOLEAN,
                default=False,
                help_text="Specialization for domain-specific needs"
            ),
        ]
    
    def ask_question(self, question: Question) -> Any:
        """
        Ask single question (placeholder - would be interactive in real implementation).
        
        Args:
            question: Question to ask
        
        Returns:
            User's answer
        """
        # In real implementation, this would:
        # - Display question text and help
        # - Get user input (CLI, web form, API)
        # - Validate answer
        # - Return validated answer
        
        # For now, return default if available
        if question.default is not None:
            logger.info(f"📋 {question.text} -> Using default: {question.default}")
            return question.default
        
        # Otherwise return placeholder based on type
        if question.type == QuestionType.TEXT:
            return f"Placeholder_{question.id}"
        elif question.type == QuestionType.NUMBER:
            return 0
        elif question.type == QuestionType.BOOLEAN:
            return False
        elif question.type == QuestionType.CHOICE:
            return question.choices[0] if question.choices else None
        elif question.type == QuestionType.MULTI_CHOICE:
            return []
        elif question.type == QuestionType.LIST:
            return []
        elif question.type == QuestionType.DICT:
            return {}
        
        return None
    
    def should_ask(self, question: Question) -> bool:
        """
        Determine if question should be asked based on dependencies.
        
        Args:
            question: Question to check
        
        Returns:
            True if should ask
        """
        if not question.depends_on:
            return True
        
        # Check if dependency was answered positively
        dep_answer = self.answers.get(question.depends_on)
        if isinstance(dep_answer, bool):
            return dep_answer
        
        return dep_answer is not None
    
    def run(self) -> AgentSpecConfig:
        """
        Run questionnaire and collect answers.
        
        Returns:
            Agent specification config
        """
        logger.info("📋 Starting questionnaire...")
        
        for question in self.questions:
            if not self.should_ask(question):
                continue
            
            answer = self.ask_question(question)
            
            # Validate
            is_valid, error = question.validate_answer(answer)
            if not is_valid:
                logger.warning(f"⚠️  Invalid answer for {question.id}: {error}")
                # In real implementation, would re-ask
                continue
            
            self.answers[question.id] = answer
        
        # Build capabilities dict
        capabilities = {}
        for category in self.answers.get("capability_categories", []):
            capabilities[category] = [f"can:{category}"]
        
        # Build constraints list
        constraints = []
        if self.answers.get("has_constraints"):
            for constraint_str in self.answers.get("constraints", []):
                if ":" in constraint_str:
                    rule, reason = constraint_str.split(":", 1)
                    constraints.append({"rule": rule.strip(), "reason": reason.strip()})
        
        # Build spec
        spec = AgentSpecConfig(
            coe_name=self.answers.get("coe_name", "WowDefault"),
            display_name=self.answers.get("display_name", "WowDefault"),
            tier=self.answers.get("tier", 3),
            domain=AgentDomain(self.answers.get("domain", "communication")),
            version=self.answers.get("version", "0.4.2"),
            description=self.answers.get("description", "Generated agent"),
            capabilities=capabilities,
            constraints=constraints,
            dependencies=self.answers.get("dependencies", []),
            wake_patterns=self.answers.get("wake_patterns", ["*"]),
            resource_budget=self.answers.get("resource_budget", 30.0),
            specialization={}
        )
        
        # Validate spec
        spec_dict = spec.to_dict()
        is_valid, error = validate_agent_spec(spec_dict)
        if not is_valid:
            logger.error(f"❌ Generated spec is invalid: {error}")
            raise ValueError(f"Invalid spec: {error}")
        
        logger.info(f"✅ Questionnaire complete: {spec.coe_name}")
        return spec
    
    def run_with_initial(self, initial_spec: Dict[str, Any]) -> AgentSpecConfig:
        """
        Run questionnaire with initial values pre-filled.
        
        Args:
            initial_spec: Initial values
        
        Returns:
            Agent specification config
        """
        # Pre-fill answers
        self.answers.update(initial_spec)
        
        # Run questionnaire (will skip pre-filled questions)
        return self.run()


# =============================================================================
# USAGE EXAMPLES
# =============================================================================

"""
Example: Using Questionnaire

```python
from waooaw.factory.questionnaire import Questionnaire

# Example 1: Full questionnaire
questionnaire = Questionnaire()
spec = questionnaire.run()
print(f"Generated spec: {spec.coe_name}")

# Example 2: With initial values
initial = {
    "coe_name": "WowExample",
    "tier": 3,
    "domain": "communication"
}
spec = questionnaire.run_with_initial(initial)

# Example 3: Access answers
questionnaire = Questionnaire()
spec = questionnaire.run()
print(f"Answers: {questionnaire.answers}")
```
"""
