"""
Tests for Prompt Library

Tests task-specific prompts, few-shot examples, and template management.
"""

import pytest
from app.services.prompts.prompt_library import (
    PromptLibrary,
    PromptTemplate,
    FewShotExample,
    TaskType,
    Industry
)


class TestPromptTemplate:
    """Test PromptTemplate functionality"""
    
    def test_format_user_prompt_success(self):
        """Test formatting user prompt with all variables"""
        template = PromptTemplate(
            task_type=TaskType.CONTENT_CREATION,
            industry=Industry.MARKETING,
            system_prompt="Test system prompt",
            user_template="Create {content_type} about {topic}",
            variables=["content_type", "topic"]
        )
        
        result = template.format_user_prompt(
            content_type="blog post",
            topic="AI"
        )
        
        assert result == "Create blog post about AI"
    
    def test_format_user_prompt_missing_variables(self):
        """Test error when required variables are missing"""
        template = PromptTemplate(
            task_type=TaskType.CONTENT_CREATION,
            industry=Industry.MARKETING,
            system_prompt="Test",
            user_template="Create {content_type} about {topic}",
            variables=["content_type", "topic"]
        )
        
        with pytest.raises(ValueError, match="Missing required variables"):
            template.format_user_prompt(content_type="blog post")
    
    def test_get_few_shot_text_without_reasoning(self):
        """Test formatting few-shot examples without reasoning"""
        example1 = FewShotExample(input="Test input 1", output="Test output 1")
        example2 = FewShotExample(input="Test input 2", output="Test output 2")
        
        template = PromptTemplate(
            task_type=TaskType.CONTENT_CREATION,
            industry=Industry.MARKETING,
            system_prompt="Test",
            user_template="Test",
            few_shot_examples=[example1, example2]
        )
        
        result = template.get_few_shot_text()
        
        assert "Example 1:" in result
        assert "Test input 1" in result
        assert "Test output 1" in result
        assert "Example 2:" in result
    
    def test_get_few_shot_text_with_reasoning(self):
        """Test formatting few-shot examples with reasoning"""
        example = FewShotExample(
            input="Calculate 5 + 3",
            output="8",
            reasoning="5 plus 3 equals 8"
        )
        
        template = PromptTemplate(
            task_type=TaskType.CONTENT_CREATION,
            industry=Industry.MARKETING,
            system_prompt="Test",
            user_template="Test",
            few_shot_examples=[example]
        )
        
        result = template.get_few_shot_text(include_reasoning=True)
        
        assert "Reasoning: 5 plus 3 equals 8" in result


class TestPromptLibrary:
    """Test PromptLibrary functionality"""
    
    def test_library_initialization(self):
        """Test library loads prompts on init"""
        library = PromptLibrary()
        
        # Should have prompts loaded
        all_prompts = library.list_prompts()
        assert len(all_prompts) > 0
    
    def test_get_marketing_content_creation_prompt(self):
        """Test retrieving marketing content creation prompt"""
        library = PromptLibrary()
        
        prompt = library.get_prompt(
            TaskType.CONTENT_CREATION,
            Industry.MARKETING
        )
        
        assert prompt is not None
        assert prompt.task_type == TaskType.CONTENT_CREATION
        assert prompt.industry == Industry.MARKETING
        assert len(prompt.few_shot_examples) == 5
        assert "content marketing" in prompt.system_prompt.lower()
    
    def test_get_marketing_social_media_prompt(self):
        """Test retrieving marketing social media prompt"""
        library = PromptLibrary()
        
        prompt = library.get_prompt(
            TaskType.SOCIAL_MEDIA,
            Industry.MARKETING
        )
        
        assert prompt is not None
        assert prompt.task_type == TaskType.SOCIAL_MEDIA
        assert len(prompt.few_shot_examples) == 5
        assert "platform" in prompt.variables
    
    def test_get_marketing_seo_prompt(self):
        """Test retrieving SEO optimization prompt"""
        library = PromptLibrary()
        
        prompt = library.get_prompt(
            TaskType.SEO_OPTIMIZATION,
            Industry.MARKETING
        )
        
        assert prompt is not None
        assert len(prompt.few_shot_examples) == 5
        assert "keyword" in prompt.system_prompt.lower()
    
    def test_get_education_concept_explanation_prompt(self):
        """Test retrieving education concept explanation prompt"""
        library = PromptLibrary()
        
        prompt = library.get_prompt(
            TaskType.CONCEPT_EXPLANATION,
            Industry.EDUCATION
        )
        
        assert prompt is not None
        assert prompt.task_type == TaskType.CONCEPT_EXPLANATION
        assert prompt.use_chain_of_thought is True
        assert len(prompt.few_shot_examples) == 5
    
    def test_get_sales_outreach_prompt(self):
        """Test retrieving sales outreach prompt"""
        library = PromptLibrary()
        
        prompt = library.get_prompt(
            TaskType.OUTREACH_MESSAGE,
            Industry.SALES
        )
        
        assert prompt is not None
        assert len(prompt.few_shot_examples) == 5
        assert "prospect_name" in prompt.variables
    
    def test_get_nonexistent_prompt(self):
        """Test retrieving prompt that doesn't exist"""
        library = PromptLibrary()
        
        prompt = library.get_prompt(
            TaskType.CONTENT_CREATION,
            Industry.SALES  # Content creation not defined for sales
        )
        
        assert prompt is None
    
    def test_register_custom_prompt(self):
        """Test registering a new custom prompt"""
        library = PromptLibrary()
        
        custom_prompt = PromptTemplate(
            task_type=TaskType.EMAIL_CAMPAIGN,
            industry=Industry.MARKETING,
            system_prompt="Custom email prompt",
            user_template="Write email about {topic}",
            variables=["topic"]
        )
        
        library.register_prompt(custom_prompt)
        
        retrieved = library.get_prompt(TaskType.EMAIL_CAMPAIGN, Industry.MARKETING)
        assert retrieved is not None
        assert retrieved.system_prompt == "Custom email prompt"
    
    def test_list_prompts_all(self):
        """Test listing all prompts"""
        library = PromptLibrary()
        
        prompts = library.list_prompts()
        
        assert len(prompts) >= 5  # At least 5 prompts loaded
        assert all(isinstance(p, PromptTemplate) for p in prompts)
    
    def test_list_prompts_by_industry(self):
        """Test filtering prompts by industry"""
        library = PromptLibrary()
        
        marketing_prompts = library.list_prompts(Industry.MARKETING)
        
        assert len(marketing_prompts) >= 3  # At least 3 marketing prompts
        assert all(p.industry == Industry.MARKETING for p in marketing_prompts)


class TestFewShotExamples:
    """Test few-shot example content quality"""
    
    def test_content_creation_examples_have_diversity(self):
        """Test content creation examples cover different formats"""
        library = PromptLibrary()
        prompt = library.get_prompt(TaskType.CONTENT_CREATION, Industry.MARKETING)
        
        examples = prompt.few_shot_examples
        
        # Check we have examples for different content types
        inputs = [ex.input for ex in examples]
        combined = " ".join(inputs).lower()
        
        # Should mention different formats
        assert "blog" in combined or "article" in combined
        assert "social" in combined or "post" in combined
        assert "email" in combined
    
    def test_social_media_examples_have_platforms(self):
        """Test social media examples cover different platforms"""
        library = PromptLibrary()
        prompt = library.get_prompt(TaskType.SOCIAL_MEDIA, Industry.MARKETING)
        
        examples = prompt.few_shot_examples
        inputs = [ex.input for ex in examples]
        combined = " ".join(inputs).lower()
        
        # Should cover multiple platforms
        platforms_mentioned = sum([
            "linkedin" in combined,
            "twitter" in combined,
            "instagram" in combined,
            "facebook" in combined,
            "tiktok" in combined
        ])
        
        assert platforms_mentioned >= 3  # At least 3 platforms
    
    def test_education_examples_have_reasoning(self):
        """Test education examples include reasoning (for CoT)"""
        library = PromptLibrary()
        prompt = library.get_prompt(TaskType.CONCEPT_EXPLANATION, Industry.EDUCATION)
        
        # Examples should include step-by-step reasoning in outputs
        outputs = [ex.output for ex in prompt.few_shot_examples]
        combined = " ".join(outputs).lower()
        
        # Should have step indicators
        assert any(marker in combined for marker in ["step", "first", "next", "then"])
    
    def test_sales_examples_are_personalized(self):
        """Test sales outreach examples are personalized"""
        library = PromptLibrary()
        prompt = library.get_prompt(TaskType.OUTREACH_MESSAGE, Industry.SALES)
        
        outputs = [ex.output for ex in prompt.few_shot_examples]
        
        # Each example should reference prospect or company
        for output in outputs:
            output_lower = output.lower()
            # Should have personalization signals
            assert any(signal in output_lower for signal in [
                "saw", "noticed", "read", "congrats", "your", "you",
                "company", "team"
            ])


class TestPromptConfiguration:
    """Test prompt configuration parameters"""
    
    def test_temperature_settings(self):
        """Test prompts have appropriate temperature settings"""
        library = PromptLibrary()
        
        # Creative tasks should have higher temperature
        creative_prompt = library.get_prompt(TaskType.SOCIAL_MEDIA, Industry.MARKETING)
        assert creative_prompt.temperature >= 0.7
        
        # Analytical tasks should have lower temperature
        seo_prompt = library.get_prompt(TaskType.SEO_OPTIMIZATION, Industry.MARKETING)
        assert seo_prompt.temperature <= 0.7
    
    def test_max_tokens_settings(self):
        """Test prompts have reasonable token limits"""
        library = PromptLibrary()
        
        prompts = library.list_prompts()
        
        for prompt in prompts:
            assert prompt.max_tokens >= 500
            assert prompt.max_tokens <= 4000
    
    def test_required_variables_defined(self):
        """Test all prompts have required variables defined"""
        library = PromptLibrary()
        
        prompts = library.list_prompts()
        
        for prompt in prompts:
            # Should have variables list
            assert isinstance(prompt.variables, list)
            
            # Variables should match template placeholders
            import re
            placeholders = re.findall(r'\{(\w+)\}', prompt.user_template)
            assert set(placeholders) == set(prompt.variables)


@pytest.mark.integration
class TestPromptLibraryIntegration:
    """Integration tests requiring full system"""
    
    def test_end_to_end_prompt_usage(self):
        """Test complete workflow: get prompt → format → use"""
        library = PromptLibrary()
        
        # Get prompt
        prompt = library.get_prompt(TaskType.CONTENT_CREATION, Industry.MARKETING)
        
        # Format user input
        user_input = prompt.format_user_prompt(
            content_type="blog post",
            topic="AI in healthcare",
            audience="hospital administrators",
            brand_voice="professional",
            word_count="800",
            keywords="AI healthcare, patient outcomes",
            context="Focus on ROI and implementation challenges"
        )
        
        assert "blog post" in user_input
        assert "AI in healthcare" in user_input
        
        # Build complete prompt (with examples)
        complete = f"{prompt.system_prompt}\n\n{prompt.get_few_shot_text()}\n\n{user_input}"
        
        assert len(complete) > 500  # Should be substantial prompt
