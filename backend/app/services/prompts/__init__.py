"""
Prompt Engineering Services

Provides advanced prompt engineering capabilities:
- Few-shot learning templates
- Chain-of-thought reasoning
- Self-consistency voting
- Task-specific prompt library
"""

from .prompt_library import PromptLibrary, PromptTemplate
from .few_shot import FewShotBuilder
from .chain_of_thought import ChainOfThoughtBuilder
from .self_consistency import SelfConsistencyVoter

__all__ = [
    "PromptLibrary",
    "PromptTemplate",
    "FewShotBuilder",
    "ChainOfThoughtBuilder",
    "SelfConsistencyVoter",
]
