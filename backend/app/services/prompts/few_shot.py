"""
Few-Shot Learning Builder

Constructs prompts with few-shot examples to improve task performance.
Automatically selects most relevant examples based on task similarity.
"""

from typing import List, Optional, Dict
from dataclasses import dataclass
from app.services.prompts.prompt_library import PromptTemplate, FewShotExample, TaskType, Industry


class FewShotBuilder:
    """
    Builds prompts with few-shot examples.
    
    Few-shot learning provides the model with examples of desired inputs/outputs
    to improve performance on similar tasks.
    """
    
    def __init__(self):
        """Initialize few-shot builder"""
        pass
    
    def build_prompt(
        self,
        template: PromptTemplate,
        user_input: Dict[str, str],
        num_examples: int = 5,
        include_reasoning: bool = False
    ) -> str:
        """
        Build a complete prompt with few-shot examples.
        
        Args:
            template: Prompt template to use
            user_input: Variables for user template
            num_examples: Number of few-shot examples to include (default: 5)
            include_reasoning: Whether to include reasoning (for chain-of-thought)
            
        Returns:
            Complete prompt with system, few-shot examples, and user input
        """
        parts = []
        
        # System prompt
        parts.append(f"<system>\n{template.system_prompt}\n</system>")
        
        # Few-shot examples
        if template.few_shot_examples:
            examples_to_use = template.few_shot_examples[:num_examples]
            
            parts.append("\n<examples>")
            parts.append("Here are examples of high-quality outputs:\n")
            
            for i, example in enumerate(examples_to_use, 1):
                parts.append(f"\nExample {i}:")
                parts.append(f"Input:\n{example.input}\n")
                
                if include_reasoning and example.reasoning:
                    parts.append(f"Reasoning:\n{example.reasoning}\n")
                
                parts.append(f"Output:\n{example.output}")
            
            parts.append("\n</examples>")
        
        # User input
        user_prompt = template.format_user_prompt(**user_input)
        parts.append(f"\n<task>\nNow, apply the same approach to this:\n\n{user_prompt}\n</task>")
        
        return "\n".join(parts)
    
    def add_example(
        self,
        template: PromptTemplate,
        input_text: str,
        output_text: str,
        reasoning: Optional[str] = None
    ):
        """
        Add a new few-shot example to a template.
        
        Args:
            template: Template to add example to
            input_text: Example input
            output_text: Example output
            reasoning: Optional reasoning (for chain-of-thought)
        """
        example = FewShotExample(
            input=input_text,
            output=output_text,
            reasoning=reasoning
        )
        template.few_shot_examples.append(example)
    
    def select_relevant_examples(
        self,
        template: PromptTemplate,
        user_input: Dict[str, str],
        num_examples: int = 5
    ) -> List[FewShotExample]:
        """
        Select most relevant few-shot examples based on user input.
        
        For now, returns first N examples. In future, could use:
        - Embedding similarity
        - Keyword matching
        - Task complexity matching
        
        Args:
            template: Template with examples
            user_input: User's input variables
            num_examples: Number of examples to return
            
        Returns:
            List of most relevant examples
        """
        # Simple implementation: return first N examples
        # TODO: Implement similarity-based selection using embeddings
        return template.few_shot_examples[:num_examples]
    
    def format_example_for_learning(
        self,
        example: FewShotExample,
        include_reasoning: bool = False
    ) -> str:
        """
        Format a single example for display or learning.
        
        Args:
            example: Example to format
            include_reasoning: Whether to include reasoning
            
        Returns:
            Formatted example text
        """
        parts = [
            f"Input:\n{example.input}",
            f"\nOutput:\n{example.output}"
        ]
        
        if include_reasoning and example.reasoning:
            parts.insert(1, f"\nReasoning:\n{example.reasoning}")
        
        return "\n".join(parts)
