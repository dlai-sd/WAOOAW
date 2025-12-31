"""
Chain-of-Thought (CoT) Reasoning

Enhances prompts with step-by-step reasoning patterns to improve
complex task performance and explainability.
"""

from typing import List, Optional, Dict
from dataclasses import dataclass
from app.services.prompts.prompt_library import PromptTemplate


@dataclass
class ReasoningStep:
    """Single step in chain-of-thought reasoning"""
    step_number: int
    description: str
    input: str
    output: str
    explanation: Optional[str] = None


class ChainOfThoughtBuilder:
    """
    Builds prompts with chain-of-thought reasoning patterns.
    
    Chain-of-thought prompting encourages the model to break down
    complex tasks into intermediate reasoning steps, improving
    accuracy and making the process transparent.
    """
    
    COT_INSTRUCTIONS = """
Before providing your final answer, think through the problem step by step:

1. Understand the task: What is being asked? What information is provided?
2. Break it down: What are the key sub-tasks or components?
3. Reason through each step: Work through the logic systematically
4. Verify: Does your reasoning make sense? Are there edge cases?
5. Conclude: Provide your final answer based on the reasoning

Show your thinking process, then provide the final output.
"""
    
    def __init__(self):
        """Initialize chain-of-thought builder"""
        pass
    
    def build_cot_prompt(
        self,
        template: PromptTemplate,
        user_input: Dict[str, str],
        cot_style: str = "detailed"
    ) -> str:
        """
        Build a prompt that encourages chain-of-thought reasoning.
        
        Args:
            template: Base prompt template
            user_input: Variables for user template
            cot_style: Style of CoT ('detailed', 'concise', 'structured')
            
        Returns:
            Prompt enhanced with CoT instructions
        """
        parts = []
        
        # System prompt
        parts.append(f"<system>\n{template.system_prompt}\n</system>")
        
        # Add CoT instructions
        cot_instruction = self._get_cot_instruction(cot_style)
        parts.append(f"\n<reasoning_instructions>\n{cot_instruction}\n</reasoning_instructions>")
        
        # Few-shot examples with reasoning
        if template.few_shot_examples:
            parts.append("\n<examples>")
            parts.append("Here are examples showing step-by-step reasoning:\n")
            
            for i, example in enumerate(template.few_shot_examples[:3], 1):
                parts.append(f"\nExample {i}:")
                parts.append(f"Input:\n{example.input}\n")
                
                if example.reasoning:
                    parts.append(f"Reasoning:\n{example.reasoning}\n")
                else:
                    # Generate basic reasoning structure if not provided
                    parts.append(f"Reasoning:\n{self._generate_basic_reasoning(example)}\n")
                
                parts.append(f"Final Output:\n{example.output}")
            
            parts.append("\n</examples>")
        
        # User input
        user_prompt = template.format_user_prompt(**user_input)
        parts.append(f"\n<task>\nNow apply this reasoning approach:\n\n{user_prompt}\n</task>")
        
        parts.append("\n<format>")
        parts.append("Please provide your response in this format:")
        parts.append("**Reasoning:**")
        parts.append("[Your step-by-step thinking]")
        parts.append("\n**Final Output:**")
        parts.append("[Your complete answer]")
        parts.append("</format>")
        
        return "\n".join(parts)
    
    def _get_cot_instruction(self, style: str) -> str:
        """Get CoT instructions based on style"""
        if style == "concise":
            return """Think through the problem briefly before answering. Show your key reasoning steps."""
        
        elif style == "structured":
            return """Approach this systematically:
1. Analyze: What information do I have?
2. Plan: What steps do I need to take?
3. Execute: Work through each step
4. Verify: Does my answer make sense?

Show each step, then provide your final answer."""
        
        else:  # detailed
            return self.COT_INSTRUCTIONS
    
    def _generate_basic_reasoning(self, example) -> str:
        """Generate basic reasoning structure for examples without explicit reasoning"""
        return f"""Let me work through this:
- Input analysis: {example.input[:100]}...
- Key considerations: [approach to solve this]
- Step-by-step solution: [reasoning steps]
- Conclusion: {example.output[:50]}..."""
    
    def parse_cot_response(self, response: str) -> Dict[str, str]:
        """
        Parse a chain-of-thought response into reasoning and output.
        
        Args:
            response: Model response with reasoning
            
        Returns:
            Dict with 'reasoning' and 'output' keys
        """
        # Try to split on common markers
        markers = [
            ("**Reasoning:**", "**Final Output:**"),
            ("**Reasoning:**", "**Output:**"),
            ("Reasoning:", "Final Output:"),
            ("Reasoning:", "Output:"),
        ]
        
        for reasoning_marker, output_marker in markers:
            if reasoning_marker in response and output_marker in response:
                parts = response.split(output_marker)
                reasoning = parts[0].replace(reasoning_marker, "").strip()
                output = parts[1].strip()
                
                return {
                    "reasoning": reasoning,
                    "output": output
                }
        
        # Fallback: entire response is output
        return {
            "reasoning": "",
            "output": response
        }
    
    def validate_reasoning(self, reasoning: str) -> Dict[str, any]:
        """
        Validate the quality of reasoning.
        
        Checks for:
        - Sufficient length (not too brief)
        - Multiple steps (not single-step)
        - Logical flow markers
        
        Args:
            reasoning: Reasoning text to validate
            
        Returns:
            Dict with 'is_valid' and 'issues' keys
        """
        issues = []
        
        # Check length
        if len(reasoning) < 50:
            issues.append("Reasoning too brief (< 50 chars)")
        
        # Check for step markers
        step_markers = ["first", "then", "next", "finally", "1.", "2.", "step"]
        has_steps = any(marker in reasoning.lower() for marker in step_markers)
        if not has_steps:
            issues.append("No clear reasoning steps found")
        
        # Check for logical connectors
        connectors = ["because", "therefore", "since", "thus", "so", "which means"]
        has_logic = any(conn in reasoning.lower() for conn in connectors)
        if not has_logic:
            issues.append("Missing logical connectors")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "score": max(0, 100 - (len(issues) * 30))  # Simple scoring
        }
