"""
Tests for Chain-of-Thought Reasoning
"""

import pytest
from app.services.prompts.chain_of_thought import ChainOfThoughtBuilder, ReasoningStep
from app.services.prompts.prompt_library import (
    PromptTemplate,
    FewShotExample,
    TaskType,
    Industry
)


class TestChainOfThoughtBuilder:
    """Test ChainOfThoughtBuilder functionality"""
    
    def test_build_cot_prompt_detailed(self):
        """Test building detailed CoT prompt"""
        template = PromptTemplate(
            task_type=TaskType.CONCEPT_EXPLANATION,
            industry=Industry.EDUCATION,
            system_prompt="Explain concepts clearly",
            user_template="Explain {concept} to a {level} student",
            variables=["concept", "level"]
        )
        
        builder = ChainOfThoughtBuilder()
        
        prompt = builder.build_cot_prompt(
            template=template,
            user_input={"concept": "gravity", "level": "5th grade"},
            cot_style="detailed"
        )
        
        assert "<reasoning_instructions>" in prompt
        assert "step by step" in prompt.lower()
        assert "gravity" in prompt
        assert "<format>" in prompt
        assert "**Reasoning:**" in prompt
    
    def test_build_cot_prompt_concise(self):
        """Test building concise CoT prompt"""
        template = PromptTemplate(
            task_type=TaskType.CONTENT_CREATION,
            industry=Industry.MARKETING,
            system_prompt="Create content",
            user_template="Write about {topic}",
            variables=["topic"]
        )
        
        builder = ChainOfThoughtBuilder()
        
        prompt = builder.build_cot_prompt(
            template=template,
            user_input={"topic": "AI"},
            cot_style="concise"
        )
        
        assert "briefly" in prompt.lower() or "concise" in prompt.lower()
        assert "reasoning" in prompt.lower()
    
    def test_build_cot_prompt_structured(self):
        """Test building structured CoT prompt"""
        template = PromptTemplate(
            task_type=TaskType.CONCEPT_EXPLANATION,
            industry=Industry.EDUCATION,
            system_prompt="Test",
            user_template="Explain {topic}",
            variables=["topic"]
        )
        
        builder = ChainOfThoughtBuilder()
        
        prompt = builder.build_cot_prompt(
            template=template,
            user_input={"topic": "test"},
            cot_style="structured"
        )
        
        # Should have structured steps
        assert "1." in prompt or "Analyze:" in prompt
        assert "2." in prompt or "Plan:" in prompt
    
    def test_build_cot_with_examples_with_reasoning(self):
        """Test CoT prompt includes reasoning from examples"""
        template = PromptTemplate(
            task_type=TaskType.CONCEPT_EXPLANATION,
            industry=Industry.EDUCATION,
            system_prompt="Test",
            user_template="Test",
            variables=[],
            few_shot_examples=[
                FewShotExample(
                    input="Explain E=mc²",
                    output="Energy equals mass times speed of light squared",
                    reasoning="First, identify the variables. E is energy..."
                )
            ]
        )
        
        builder = ChainOfThoughtBuilder()
        
        prompt = builder.build_cot_prompt(
            template=template,
            user_input={},
            cot_style="detailed"
        )
        
        assert "First, identify the variables" in prompt
        assert "Reasoning:" in prompt
    
    def test_build_cot_generates_reasoning_when_missing(self):
        """Test CoT generates basic reasoning for examples without it"""
        template = PromptTemplate(
            task_type=TaskType.CONTENT_CREATION,
            industry=Industry.MARKETING,
            system_prompt="Test",
            user_template="Test",
            variables=[],
            few_shot_examples=[
                FewShotExample(
                    input="Write a tweet",
                    output="Great tweet content here"
                    # No reasoning provided
                )
            ]
        )
        
        builder = ChainOfThoughtBuilder()
        
        prompt = builder.build_cot_prompt(
            template=template,
            user_input={},
            cot_style="detailed"
        )
        
        # Should generate placeholder reasoning
        assert "Reasoning:" in prompt
        assert "Input analysis" in prompt or "reasoning steps" in prompt.lower()
    
    def test_parse_cot_response_with_markers(self):
        """Test parsing CoT response with reasoning markers"""
        response = """**Reasoning:**
Let me think through this step by step:
1. First, I need to understand the question
2. Then, I'll analyze the key components
3. Finally, I'll provide a clear answer

**Final Output:**
The answer is 42."""
        
        builder = ChainOfThoughtBuilder()
        parsed = builder.parse_cot_response(response)
        
        assert "reasoning" in parsed
        assert "output" in parsed
        assert "step by step" in parsed["reasoning"]
        assert "42" in parsed["output"]
    
    def test_parse_cot_response_alternative_markers(self):
        """Test parsing with alternative marker formats"""
        response = """Reasoning:
I need to solve this carefully.

Output:
Here's the solution."""
        
        builder = ChainOfThoughtBuilder()
        parsed = builder.parse_cot_response(response)
        
        assert "carefully" in parsed["reasoning"]
        assert "solution" in parsed["output"]
    
    def test_parse_cot_response_no_markers(self):
        """Test parsing response without markers (fallback)"""
        response = "Just a plain response without any markers"
        
        builder = ChainOfThoughtBuilder()
        parsed = builder.parse_cot_response(response)
        
        # Should treat entire response as output
        assert parsed["reasoning"] == ""
        assert parsed["output"] == response
    
    def test_validate_reasoning_good_quality(self):
        """Test validating high-quality reasoning"""
        good_reasoning = """First, I need to understand the problem. The key is to break it down into steps.
Then, I'll analyze each component because they're interconnected.
Therefore, the solution requires considering all factors together."""
        
        builder = ChainOfThoughtBuilder()
        result = builder.validate_reasoning(good_reasoning)
        
        assert result["is_valid"] is True
        assert len(result["issues"]) == 0
        assert result["score"] >= 70
    
    def test_validate_reasoning_too_brief(self):
        """Test validating too-brief reasoning"""
        brief_reasoning = "The answer is obvious"
        
        builder = ChainOfThoughtBuilder()
        result = builder.validate_reasoning(brief_reasoning)
        
        assert result["is_valid"] is False
        assert any("brief" in issue.lower() for issue in result["issues"])
    
    def test_validate_reasoning_no_steps(self):
        """Test validating reasoning without clear step markers"""
        no_steps = "Just a plain explanation lacking any markers or logical connectors for proper reasoning."
        
        builder = ChainOfThoughtBuilder()
        result = builder.validate_reasoning(no_steps)
        
        # Should fail due to missing step markers
        assert result["is_valid"] is False
        assert any("steps" in issue.lower() for issue in result["issues"])
    
    def test_validate_reasoning_no_logical_connectors(self):
        """Test validating reasoning without logical flow"""
        no_logic = "I looked at the data. The numbers are big. Here is my answer based on what I saw in the information provided."
        
        builder = ChainOfThoughtBuilder()
        result = builder.validate_reasoning(no_logic)
        
        assert result["is_valid"] is False
        assert any("connector" in issue.lower() for issue in result["issues"])


class TestReasoningStep:
    """Test ReasoningStep dataclass"""
    
    def test_create_reasoning_step(self):
        """Test creating reasoning step"""
        step = ReasoningStep(
            step_number=1,
            description="Analyze the problem",
            input="Problem statement",
            output="Analysis result",
            explanation="This step breaks down the problem"
        )
        
        assert step.step_number == 1
        assert step.description == "Analyze the problem"
        assert step.explanation is not None
    
    def test_reasoning_step_optional_explanation(self):
        """Test reasoning step without explanation"""
        step = ReasoningStep(
            step_number=1,
            description="Test",
            input="Input",
            output="Output"
        )
        
        assert step.explanation is None


class TestCoTPromptQuality:
    """Test quality of generated CoT prompts"""
    
    def test_cot_prompt_encourages_transparency(self):
        """Test CoT prompt asks for visible reasoning"""
        template = PromptTemplate(
            task_type=TaskType.CONCEPT_EXPLANATION,
            industry=Industry.EDUCATION,
            system_prompt="Explain",
            user_template="Topic: {topic}",
            variables=["topic"]
        )
        
        builder = ChainOfThoughtBuilder()
        prompt = builder.build_cot_prompt(template, {"topic": "test"})
        
        # Should encourage showing work
        assert any(phrase in prompt.lower() for phrase in [
            "show", "explain", "step", "think", "reasoning"
        ])
    
    def test_cot_prompt_provides_format_guidance(self):
        """Test CoT prompt includes format instructions"""
        template = PromptTemplate(
            task_type=TaskType.CONCEPT_EXPLANATION,
            industry=Industry.EDUCATION,
            system_prompt="Test",
            user_template="Test",
            variables=[]
        )
        
        builder = ChainOfThoughtBuilder()
        prompt = builder.build_cot_prompt(template, {})
        
        assert "<format>" in prompt
        assert "**Reasoning:**" in prompt or "Reasoning:" in prompt


@pytest.mark.integration
class TestChainOfThoughtIntegration:
    """Integration tests for chain-of-thought"""
    
    def test_cot_with_education_prompt(self):
        """Test CoT with education concept explanation"""
        from app.services.prompts.prompt_library import prompt_library
        
        template = prompt_library.get_prompt(
            TaskType.CONCEPT_EXPLANATION,
            Industry.EDUCATION
        )
        
        builder = ChainOfThoughtBuilder()
        
        prompt = builder.build_cot_prompt(
            template=template,
            user_input={
                "concept": "Newton's Laws",
                "level": "high school",
                "prior_knowledge": "basic physics",
                "learning_style": "visual",
                "common_confusion": "third law",
                "goal": "understand practical applications"
            },
            cot_style="detailed"
        )
        
        assert len(prompt) > 1000
        assert "Newton" in prompt
        assert "step" in prompt.lower()
        assert template.use_chain_of_thought is True
