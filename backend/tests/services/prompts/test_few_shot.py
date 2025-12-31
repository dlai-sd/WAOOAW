"""
Tests for Few-Shot Learning Builder
"""

import pytest
from app.services.prompts.few_shot import FewShotBuilder
from app.services.prompts.prompt_library import (
    PromptTemplate,
    FewShotExample,
    TaskType,
    Industry
)


class TestFewShotBuilder:
    """Test FewShotBuilder functionality"""
    
    def test_build_prompt_basic(self):
        """Test building basic prompt with examples"""
        template = PromptTemplate(
            task_type=TaskType.CONTENT_CREATION,
            industry=Industry.MARKETING,
            system_prompt="You are a content creator",
            user_template="Create {content_type} about {topic}",
            variables=["content_type", "topic"],
            few_shot_examples=[
                FewShotExample(
                    input="Create blog post about AI",
                    output="# AI Revolution\n\nAI is transforming..."
                ),
                FewShotExample(
                    input="Create tweet about productivity",
                    output="Boost productivity: Focus on one task at a time"
                )
            ]
        )
        
        builder = FewShotBuilder()
        
        prompt = builder.build_prompt(
            template=template,
            user_input={"content_type": "article", "topic": "machine learning"},
            num_examples=2
        )
        
        # Should contain all components
        assert "<system>" in prompt
        assert "content creator" in prompt
        assert "<examples>" in prompt
        assert "Example 1:" in prompt
        assert "Example 2:" in prompt
        assert "<task>" in prompt
        assert "machine learning" in prompt
    
    def test_build_prompt_with_reasoning(self):
        """Test building prompt with chain-of-thought reasoning"""
        template = PromptTemplate(
            task_type=TaskType.CONCEPT_EXPLANATION,
            industry=Industry.EDUCATION,
            system_prompt="Explain concepts clearly",
            user_template="Explain {concept}",
            variables=["concept"],
            few_shot_examples=[
                FewShotExample(
                    input="Explain photosynthesis",
                    output="Plants convert sunlight to energy...",
                    reasoning="First, understand what photosynthesis means. Then break down the steps..."
                )
            ]
        )
        
        builder = FewShotBuilder()
        
        prompt = builder.build_prompt(
            template=template,
            user_input={"concept": "gravity"},
            include_reasoning=True
        )
        
        assert "Reasoning:" in prompt
        assert "First, understand" in prompt
    
    def test_build_prompt_limits_examples(self):
        """Test limiting number of examples"""
        many_examples = [
            FewShotExample(input=f"Test {i}", output=f"Output {i}")
            for i in range(10)
        ]
        
        template = PromptTemplate(
            task_type=TaskType.CONTENT_CREATION,
            industry=Industry.MARKETING,
            system_prompt="Test",
            user_template="Test {var}",
            variables=["var"],
            few_shot_examples=many_examples
        )
        
        builder = FewShotBuilder()
        
        prompt = builder.build_prompt(
            template=template,
            user_input={"var": "test"},
            num_examples=3
        )
        
        # Should only have 3 examples
        assert prompt.count("Example 1:") == 1
        assert prompt.count("Example 2:") == 1
        assert prompt.count("Example 3:") == 1
        assert prompt.count("Example 4:") == 0
    
    def test_add_example(self):
        """Test adding new example to template"""
        template = PromptTemplate(
            task_type=TaskType.CONTENT_CREATION,
            industry=Industry.MARKETING,
            system_prompt="Test",
            user_template="Test",
            few_shot_examples=[]
        )
        
        builder = FewShotBuilder()
        
        assert len(template.few_shot_examples) == 0
        
        builder.add_example(
            template=template,
            input_text="New input",
            output_text="New output",
            reasoning="New reasoning"
        )
        
        assert len(template.few_shot_examples) == 1
        assert template.few_shot_examples[0].input == "New input"
        assert template.few_shot_examples[0].reasoning == "New reasoning"
    
    def test_select_relevant_examples(self):
        """Test selecting relevant examples (basic implementation)"""
        examples = [
            FewShotExample(input=f"Example {i}", output=f"Output {i}")
            for i in range(10)
        ]
        
        template = PromptTemplate(
            task_type=TaskType.CONTENT_CREATION,
            industry=Industry.MARKETING,
            system_prompt="Test",
            user_template="Test",
            few_shot_examples=examples
        )
        
        builder = FewShotBuilder()
        
        selected = builder.select_relevant_examples(
            template=template,
            user_input={"topic": "AI"},
            num_examples=3
        )
        
        assert len(selected) == 3
        assert all(isinstance(ex, FewShotExample) for ex in selected)
    
    def test_format_example_for_learning(self):
        """Test formatting single example"""
        example = FewShotExample(
            input="Test input",
            output="Test output",
            reasoning="Test reasoning"
        )
        
        builder = FewShotBuilder()
        
        # Without reasoning
        formatted = builder.format_example_for_learning(example, include_reasoning=False)
        assert "Input:\nTest input" in formatted
        assert "Output:\nTest output" in formatted
        assert "Reasoning" not in formatted
        
        # With reasoning
        formatted_with_reasoning = builder.format_example_for_learning(
            example,
            include_reasoning=True
        )
        assert "Reasoning:\nTest reasoning" in formatted_with_reasoning
    
    def test_build_prompt_no_examples(self):
        """Test building prompt when template has no examples"""
        template = PromptTemplate(
            task_type=TaskType.CONTENT_CREATION,
            industry=Industry.MARKETING,
            system_prompt="System prompt",
            user_template="User {input}",
            variables=["input"],
            few_shot_examples=[]
        )
        
        builder = FewShotBuilder()
        
        prompt = builder.build_prompt(
            template=template,
            user_input={"input": "test"}
        )
        
        # Should still work, just no examples section
        assert "<system>" in prompt
        assert "<task>" in prompt
        # Examples section might be present but empty


class TestFewShotPromptQuality:
    """Test quality of generated few-shot prompts"""
    
    def test_prompt_structure_is_clear(self):
        """Test prompt has clear structure"""
        template = PromptTemplate(
            task_type=TaskType.CONTENT_CREATION,
            industry=Industry.MARKETING,
            system_prompt="Create content",
            user_template="Write about {topic}",
            variables=["topic"],
            few_shot_examples=[
                FewShotExample(input="Example", output="Output")
            ]
        )
        
        builder = FewShotBuilder()
        prompt = builder.build_prompt(template, {"topic": "test"})
        
        # Should have clear sections
        sections = ["<system>", "<examples>", "<task>"]
        for section in sections:
            assert section in prompt
    
    def test_prompt_includes_task_context(self):
        """Test prompt includes user's specific task"""
        template = PromptTemplate(
            task_type=TaskType.SOCIAL_MEDIA,
            industry=Industry.MARKETING,
            system_prompt="Social media expert",
            user_template="Create {platform} post about {topic}",
            variables=["platform", "topic"],
            few_shot_examples=[]
        )
        
        builder = FewShotBuilder()
        prompt = builder.build_prompt(
            template,
            {"platform": "Twitter", "topic": "sustainability"}
        )
        
        assert "Twitter" in prompt
        assert "sustainability" in prompt


@pytest.mark.integration
class TestFewShotBuilderIntegration:
    """Integration tests for few-shot building"""
    
    def test_build_complete_marketing_prompt(self):
        """Test building complete prompt for marketing task"""
        from app.services.prompts.prompt_library import prompt_library
        
        template = prompt_library.get_prompt(
            TaskType.CONTENT_CREATION,
            Industry.MARKETING
        )
        
        builder = FewShotBuilder()
        
        prompt = builder.build_prompt(
            template=template,
            user_input={
                "content_type": "LinkedIn post",
                "topic": "AI automation",
                "audience": "CTOs",
                "brand_voice": "authoritative",
                "word_count": "200",
                "keywords": "AI, automation, efficiency",
                "context": "Focus on ROI"
            },
            num_examples=3
        )
        
        # Should be well-formed
        assert len(prompt) > 1000  # Substantial prompt
        assert "AI automation" in prompt
        assert "Example" in prompt
