"""
WowAgentCoach Integration Module

Provides integration interface between WowTester and WowAgentCoach training system.
WowAgentCoach can use this to evaluate agents during training.

Story 0.1.11: Integration with WowAgentCoach
Version: v0.2.7
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

from waooaw.agents.wowtester import WowTester, Scenario, EvaluationReport

logger = logging.getLogger(__name__)


@dataclass
class TrainingEvaluationRequest:
    """Request for agent evaluation during training"""
    agent_id: str
    agent_output: str
    scenario_config: Dict[str, Any]
    training_phase: Optional[str] = None  # 'simple', 'moderate', 'complex', 'expert'
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TrainingEvaluationResponse:
    """Response from WowTester evaluation for training"""
    success: bool
    evaluation_report: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)


class WowAgentCoachIntegration:
    """
    Integration layer between WowTester and WowAgentCoach.
    
    Provides simple API for WowAgentCoach to evaluate agents during training.
    """
    
    def __init__(self):
        """Initialize integration with WowTester instance"""
        self.tester = WowTester()
        self.evaluation_count = 0
        logger.info("🔗 WowAgentCoach integration initialized")
    
    async def evaluate_for_training(
        self,
        request: TrainingEvaluationRequest,
        timeout_seconds: float = 5.0
    ) -> TrainingEvaluationResponse:
        """
        Evaluate agent output during training.
        
        Args:
            request: Training evaluation request
            timeout_seconds: Maximum time for evaluation (default: 5s)
            
        Returns:
            TrainingEvaluationResponse with evaluation results or error
        """
        try:
            # Convert request to WowTester scenario
            scenario = self._create_scenario(request.scenario_config)
            
            # Evaluate using WowTester
            logger.info(f"🎓 Evaluating agent {request.agent_id} (phase: {request.training_phase})")
            
            report = await self.tester.evaluate_output(
                agent_id=request.agent_id,
                agent_output=request.agent_output,
                scenario=scenario
            )
            
            self.evaluation_count += 1
            
            # Convert report to dictionary
            report_dict = {
                'overall_score': report.overall_score,
                'passed': report.passed,
                'dimension_scores': {
                    dim: {
                        'score': score.score, 
                        'explanation': score.explanation,
                        'strengths': score.strengths,
                        'weaknesses': score.weaknesses,
                        'suggestions': score.suggestions
                    }
                    for dim, score in report.dimension_scores.items()
                },
                'feedback': report.feedback,
                'strengths': report.strengths,
                'weaknesses': report.weaknesses,
                'suggestions': report.suggestions,
                'created_at': report.created_at.isoformat()
            }
            
            logger.info(f"✅ Evaluation complete: {report.overall_score:.1f}/10 "
                       f"({'PASS' if report.passed else 'FAIL'})")
            
            return TrainingEvaluationResponse(
                success=True,
                evaluation_report=report_dict
            )
            
        except TimeoutError as e:
            logger.error(f"⏱️ Evaluation timeout for agent {request.agent_id}")
            return TrainingEvaluationResponse(
                success=False,
                error=f"Evaluation timeout after {timeout_seconds}s"
            )
            
        except Exception as e:
            logger.error(f"❌ Evaluation error for agent {request.agent_id}: {e}")
            return TrainingEvaluationResponse(
                success=False,
                error=str(e)
            )
    
    def _create_scenario(self, config: Dict[str, Any]) -> Scenario:
        """
        Create Scenario object from configuration dictionary.
        
        Args:
            config: Scenario configuration
            
        Returns:
            Scenario object
        """
        return Scenario(
            id=config.get('id', 'training-scenario'),
            title=config.get('title', 'Training Scenario'),
            description=config.get('description', ''),
            content_type=config.get('content_type', 'blog_post'),
            requirements=config.get('requirements', []),
            target_audience=config.get('target_audience', 'general'),
            purpose=config.get('purpose', 'training'),
            industry=config.get('industry'),
            metadata=config.get('metadata', {})
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get integration statistics"""
        return {
            'evaluations_count': self.evaluation_count,
            'tester_stats': {
                'is_trained': self.tester.is_trained,
                'training_phase': self.tester.training_phase,
                'total_evaluations': self.tester.evaluation_count
            }
        }


# Convenience functions for WowAgentCoach

async def evaluate_agent_during_training(
    agent_id: str,
    agent_output: str,
    scenario_config: Dict[str, Any],
    training_phase: Optional[str] = None
) -> TrainingEvaluationResponse:
    """
    Convenience function for quick evaluation during training.
    
    Args:
        agent_id: Agent being trained
        agent_output: Output to evaluate
        scenario_config: Scenario configuration
        training_phase: Training phase (simple, moderate, complex, expert)
        
    Returns:
        TrainingEvaluationResponse with results
    """
    integration = WowAgentCoachIntegration()
    request = TrainingEvaluationRequest(
        agent_id=agent_id,
        agent_output=agent_output,
        scenario_config=scenario_config,
        training_phase=training_phase
    )
    return await integration.evaluate_for_training(request)
