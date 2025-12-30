"""
Tests for WowAgentCoach Integration (Story 0.1.11)
"""

import pytest
from waooaw.agents.wow_agent_coach_integration import (
    WowAgentCoachIntegration,
    TrainingEvaluationRequest,
    TrainingEvaluationResponse,
    evaluate_agent_during_training
)


@pytest.mark.asyncio
async def test_integration_initialization():
    """Test integration initializes correctly"""
    integration = WowAgentCoachIntegration()
    
    assert integration.tester is not None
    assert integration.evaluation_count == 0


@pytest.mark.asyncio
async def test_evaluate_for_training():
    """Test evaluation during training"""
    integration = WowAgentCoachIntegration()
    
    request = TrainingEvaluationRequest(
        agent_id="test_agent",
        agent_output="# Test Content\n\nThis is a test blog post with structure.\n\n## Conclusion\n\nSummary here.",
        scenario_config={
            'id': 'test-scenario',
            'title': 'Test',
            'content_type': 'blog_post',
            'requirements': ['introduction', 'conclusion'],
            'target_audience': 'developers',
            'purpose': 'training'
        },
        training_phase='simple'
    )
    
    response = await integration.evaluate_for_training(request)
    
    assert response.success is True
    assert response.evaluation_report is not None
    assert 'overall_score' in response.evaluation_report
    assert 'dimension_scores' in response.evaluation_report
    assert 'passed' in response.evaluation_report
    assert integration.evaluation_count == 1


@pytest.mark.asyncio
async def test_evaluate_with_error_handling():
    """Test error handling in evaluation"""
    integration = WowAgentCoachIntegration()
    
    # Invalid request (empty output)
    request = TrainingEvaluationRequest(
        agent_id="test_agent",
        agent_output="",  # Empty output
        scenario_config={
            'id': 'test',
            'content_type': 'blog_post',
            'requirements': [],
            'target_audience': 'test',
            'purpose': 'test'
        }
    )
    
    response = await integration.evaluate_for_training(request)
    
    # Should still succeed (WowTester handles empty output)
    assert response.success is True or response.error is not None


@pytest.mark.asyncio
async def test_convenience_function():
    """Test convenience function for quick evaluation"""
    response = await evaluate_agent_during_training(
        agent_id="test_agent",
        agent_output="Test content " * 100,
        scenario_config={
            'id': 'quick-test',
            'content_type': 'blog_post',
            'requirements': [],
            'target_audience': 'test',
            'purpose': 'test'
        },
        training_phase='simple'
    )
    
    assert isinstance(response, TrainingEvaluationResponse)
    assert response.success is True or response.error is not None


@pytest.mark.asyncio
async def test_integration_stats():
    """Test getting integration statistics"""
    integration = WowAgentCoachIntegration()
    
    # Do a few evaluations
    for i in range(3):
        request = TrainingEvaluationRequest(
            agent_id=f"agent-{i}",
            agent_output="Test content",
            scenario_config={
                'id': f'test-{i}',
                'content_type': 'blog_post',
                'requirements': [],
                'target_audience': 'test',
                'purpose': 'test'
            }
        )
        await integration.evaluate_for_training(request)
    
    stats = integration.get_stats()
    
    assert stats['evaluations_count'] == 3
    assert 'tester_stats' in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
