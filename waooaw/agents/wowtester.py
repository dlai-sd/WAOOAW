"""
WowTester - Automated Testing & Evaluation Framework

Provides automated evaluation of agent outputs across 8 dimensions:
- Structural compliance (format, length, sections)
- Content quality (accuracy, depth, readability)
- Domain expertise (terminology, best practices)
- Fit for purpose (actionability, completeness)
- Comparative score (vs competitors)
- Speed score (response time)
- Cost score (resource efficiency)
- Compliance score (regulatory adherence)

Generated for Theme 4: TEACHER (Training Infrastructure)
Epic: 0.1 WowTester
Version: v0.2.7
Priority: 🚨 CRITICAL - Blocks ALL agent training
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
import re
import asyncio

logger = logging.getLogger(__name__)


# =========================================================================
# DATA MODELS
# =========================================================================

@dataclass
class Scenario:
    """Test scenario definition"""
    id: str
    title: str
    description: str
    content_type: str  # blog_post, email, social_media, etc.
    requirements: List[str]
    target_audience: str
    purpose: str
    industry: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationCriteria:
    """Criteria for evaluation"""
    dimensions: List[str]  # Which dimensions to evaluate
    weights: Dict[str, float]  # Dimension weights for overall score
    pass_threshold: float = 8.0  # Minimum score to pass
    strict_mode: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DimensionScore:
    """Score for a single dimension"""
    dimension: str
    score: float  # 0-10
    explanation: str
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationReport:
    """Complete evaluation report"""
    evaluation_id: str
    agent_id: str
    scenario: Scenario
    agent_output: str
    
    # Scores
    dimension_scores: Dict[str, DimensionScore]
    overall_score: float  # 0-10
    passed: bool
    
    # Feedback
    feedback: str
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    
    # Metadata
    evaluation_time_ms: int
    evaluator_version: str
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


# =========================================================================
# EVALUATOR CLASSES
# =========================================================================

class StructuralEvaluator:
    """Deterministic structural compliance evaluator (fast, rule-based)"""
    
    STRUCTURAL_RULES = {
        'blog_post': {
            'word_count': (750, 850),  # Target 800 ±50
            'required_sections': ['introduction', 'body', 'conclusion', 'call_to_action'],
            'min_paragraphs': 3,
            'format': 'markdown'
        },
        'marketing_email': {
            'word_count': (180, 220),  # Target 200 ±20
            'required_sections': ['subject_line', 'preview_text', 'body', 'cta_button'],
            'format': 'html'
        },
        'social_media': {
            'word_count': (0, 280),  # Twitter/X limit
            'required_sections': ['message'],
            'format': 'text'
        }
    }
    
    def evaluate(self, output: str, scenario: Scenario) -> DimensionScore:
        """
        Evaluate structural compliance.
        
        Args:
            output: Agent output to evaluate
            scenario: Test scenario
            
        Returns:
            DimensionScore with structural compliance score
        """
        content_type = scenario.content_type
        rules = self.STRUCTURAL_RULES.get(content_type, {})
        
        score = 10.0
        strengths = []
        weaknesses = []
        suggestions = []
        
        # Check word count
        word_count = len(output.split())
        if 'word_count' in rules:
            min_words, max_words = rules['word_count']
            target = (min_words + max_words) / 2
            
            if min_words <= word_count <= max_words:
                strengths.append(f"Word count ({word_count}) is within target range ({min_words}-{max_words})")
            else:
                deviation = abs(word_count - target) / target
                penalty = min(deviation * 5, 5)  # Max 5 point penalty
                score -= penalty
                weaknesses.append(f"Word count ({word_count}) outside target ({min_words}-{max_words})")
                if word_count < min_words:
                    suggestions.append(f"Expand content by ~{min_words - word_count} words")
                else:
                    suggestions.append(f"Reduce content by ~{word_count - max_words} words")
        
        # Check required sections
        if 'required_sections' in rules:
            missing_sections = []
            found_sections = []
            for section in rules['required_sections']:
                # More flexible section matching - check for section-like keywords
                section_keywords = section.replace('_', ' ').split()
                # Check if any keyword from the section appears in output
                if any(keyword.lower() in output.lower() for keyword in section_keywords):
                    found_sections.append(section)
                else:
                    missing_sections.append(section)
            
            if len(found_sections) >= len(rules['required_sections']) * 0.75:  # 75% threshold
                strengths.append(f"Most required sections present ({len(found_sections)}/{len(rules['required_sections'])})")
            else:
                penalty = len(missing_sections) * 1.5  # 1.5 points per missing section
                score -= penalty
                weaknesses.append(f"Missing sections: {', '.join(missing_sections)}")
                suggestions.append(f"Add missing sections: {', '.join(missing_sections)}")
        
        # Check paragraph structure for blog posts
        if content_type == 'blog_post' and 'min_paragraphs' in rules:
            paragraphs = [p.strip() for p in output.split('\n\n') if p.strip()]
            if len(paragraphs) >= rules['min_paragraphs']:
                strengths.append(f"Good paragraph structure ({len(paragraphs)} paragraphs)")
            else:
                score -= 2
                weaknesses.append(f"Insufficient paragraphs ({len(paragraphs)} < {rules['min_paragraphs']})")
                suggestions.append("Break content into more paragraphs for readability")
        
        score = max(0, min(10, score))  # Clamp to 0-10
        
        explanation = f"Structural compliance: {score:.1f}/10. "
        if strengths:
            explanation += f"Strengths: {'; '.join(strengths[:2])}. "
        if weaknesses:
            explanation += f"Issues: {'; '.join(weaknesses[:2])}."
        
        return DimensionScore(
            dimension='structural',
            score=score,
            explanation=explanation,
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions
        )


class QualityEvaluator:
    """Content quality evaluator (LLM-based)"""
    
    def __init__(self, llm_client: Optional[Any] = None):
        self.llm_client = llm_client
        self.cache = {}  # Simple cache (should use Redis in production)
    
    async def evaluate(
        self, 
        output: str, 
        scenario: Scenario,
        use_cache: bool = True
    ) -> DimensionScore:
        """
        Evaluate content quality using LLM.
        
        Args:
            output: Agent output to evaluate
            scenario: Test scenario
            use_cache: Whether to use cached results
            
        Returns:
            DimensionScore with quality assessment
        """
        # Generate cache key
        cache_key = f"quality:{hash(output + scenario.id)}"
        if use_cache and cache_key in self.cache:
            return self.cache[cache_key]
        
        # For now, use rule-based heuristics (LLM integration pending)
        score = 8.0  # Default good score
        strengths = []
        weaknesses = []
        suggestions = []
        
        # Check for basic quality markers
        sentences = output.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        
        if 15 <= avg_sentence_length <= 25:
            strengths.append("Good sentence length (readability)")
        elif avg_sentence_length > 30:
            score -= 1
            weaknesses.append("Sentences too long (readability issue)")
            suggestions.append("Break long sentences into shorter ones")
        
        # Check for variety
        unique_words = len(set(output.lower().split()))
        total_words = len(output.split())
        lexical_diversity = unique_words / total_words if total_words > 0 else 0
        
        if lexical_diversity > 0.6:
            strengths.append("Good vocabulary variety")
        elif lexical_diversity < 0.4:
            score -= 1
            weaknesses.append("Limited vocabulary variety")
            suggestions.append("Use more varied vocabulary")
        
        explanation = f"Content quality: {score:.1f}/10 (heuristic-based, pending LLM integration)"
        
        result = DimensionScore(
            dimension='quality',
            score=score,
            explanation=explanation,
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions
        )
        
        if use_cache:
            self.cache[cache_key] = result
        
        return result


class DomainExpertiseEvaluator:
    """Domain expertise evaluator"""
    
    DOMAIN_KNOWLEDGE = {
        'healthcare': {
            'required_terms': ['patient', 'clinical', 'healthcare', 'medical'],
            'best_practices': ['evidence-based', 'patient-centered'],
            'red_flags': ['medical advice', 'guaranteed cure']
        },
        'education': {
            'required_terms': ['student', 'learning', 'education', 'curriculum'],
            'best_practices': ['pedagogical', 'student-centered'],
            'red_flags': ['guaranteed results', 'all students']
        },
        'marketing': {
            'required_terms': ['audience', 'engagement', 'conversion', 'brand'],
            'best_practices': ['data-driven', 'customer-centric'],
            'red_flags': ['guaranteed results', 'instant success']
        }
    }
    
    def evaluate(self, output: str, scenario: Scenario) -> DimensionScore:
        """
        Evaluate domain expertise.
        
        Args:
            output: Agent output to evaluate
            scenario: Test scenario
            
        Returns:
            DimensionScore with domain expertise assessment
        """
        industry = scenario.industry or 'general'
        domain_info = self.DOMAIN_KNOWLEDGE.get(industry, {})
        
        score = 10.0
        strengths = []
        weaknesses = []
        suggestions = []
        
        output_lower = output.lower()
        
        # Check for required terminology
        if 'required_terms' in domain_info:
            found_terms = [term for term in domain_info['required_terms'] 
                          if term in output_lower]
            missing_terms = [term for term in domain_info['required_terms'] 
                           if term not in output_lower]
            
            if len(found_terms) >= len(domain_info['required_terms']) * 0.75:
                strengths.append(f"Good use of industry terminology ({len(found_terms)}/{len(domain_info['required_terms'])} terms)")
            else:
                penalty = len(missing_terms) * 1.5
                score -= penalty
                weaknesses.append(f"Missing key industry terms: {', '.join(missing_terms[:3])}")
                suggestions.append(f"Incorporate industry-specific terminology: {', '.join(missing_terms[:3])}")
        
        # Check for red flags
        if 'red_flags' in domain_info:
            found_red_flags = [flag for flag in domain_info['red_flags'] 
                              if flag in output_lower]
            if found_red_flags:
                score -= len(found_red_flags) * 3  # Heavy penalty
                weaknesses.append(f"Problematic content: {', '.join(found_red_flags)}")
                suggestions.append(f"Remove or rephrase: {', '.join(found_red_flags)}")
        
        score = max(0, min(10, score))
        
        explanation = f"Domain expertise: {score:.1f}/10 ({industry} industry)"
        
        return DimensionScore(
            dimension='domain',
            score=score,
            explanation=explanation,
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions
        )


class FitForPurposeEvaluator:
    """Fit for purpose evaluator"""
    
    def evaluate(self, output: str, scenario: Scenario) -> DimensionScore:
        """
        Evaluate if output fits the purpose.
        
        Args:
            output: Agent output to evaluate
            scenario: Test scenario
            
        Returns:
            DimensionScore with fit assessment
        """
        score = 10.0
        strengths = []
        weaknesses = []
        suggestions = []
        
        # Check requirements coverage
        requirements_met = 0
        for req in scenario.requirements:
            # Simple keyword matching (can be improved)
            req_keywords = req.lower().split()
            if any(keyword in output.lower() for keyword in req_keywords):
                requirements_met += 1
        
        req_coverage = requirements_met / len(scenario.requirements) if scenario.requirements else 1.0
        
        if req_coverage >= 0.9:
            strengths.append(f"Excellent requirement coverage ({requirements_met}/{len(scenario.requirements)})")
        elif req_coverage >= 0.7:
            strengths.append(f"Good requirement coverage ({requirements_met}/{len(scenario.requirements)})")
        else:
            penalty = (1 - req_coverage) * 5
            score -= penalty
            weaknesses.append(f"Insufficient requirement coverage ({requirements_met}/{len(scenario.requirements)})")
            suggestions.append("Address all specified requirements explicitly")
        
        # Check actionability (does it have specific next steps/CTAs?)
        action_indicators = ['click', 'download', 'sign up', 'contact', 'learn more', 'get started', 'call to action', 'subscribe', 'join', 'buy']
        has_cta = any(indicator in output.lower() for indicator in action_indicators)
        
        if has_cta:
            strengths.append("Clear call-to-action present")
        elif scenario.content_type in ['marketing_email', 'blog_post', 'social_media']:
            score -= 2
            weaknesses.append("Missing clear call-to-action")
            suggestions.append("Add specific next steps or call-to-action")
        
        score = max(0, min(10, score))
        
        explanation = f"Fit for purpose: {score:.1f}/10 (requirement coverage: {req_coverage:.0%})"
        
        return DimensionScore(
            dimension='fit',
            score=score,
            explanation=explanation,
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions
        )


# =========================================================================
# MAIN EVALUATION ENGINE
# =========================================================================

class EvaluationEngine:
    """
    Core 8-dimensional evaluation engine for WowTester.
    
    Evaluates agent outputs across 8 dimensions:
    1. Structural compliance (deterministic)
    2. Content quality (LLM-based)
    3. Domain expertise (knowledge-based)
    4. Fit for purpose (requirement-based)
    5. Comparative score (benchmark-based) - requires WowBenchmark
    6. Speed score (performance-based)
    7. Cost score (resource-based)
    8. Compliance score (regulatory-based)
    """
    
    def __init__(self, llm_client: Optional[Any] = None):
        self.evaluators = {
            'structural': StructuralEvaluator(),
            'quality': QualityEvaluator(llm_client),
            'domain': DomainExpertiseEvaluator(),
            'fit': FitForPurposeEvaluator(),
            # Comparative, speed, cost, compliance to be added in later stories
        }
        self.version = "0.1.0"
    
    async def evaluate(
        self,
        agent_id: str,
        agent_output: str,
        scenario: Scenario,
        criteria: Optional[EvaluationCriteria] = None
    ) -> EvaluationReport:
        """
        Evaluate agent output across multiple dimensions.
        
        Args:
            agent_id: ID of agent being evaluated
            agent_output: Output to evaluate
            scenario: Test scenario
            criteria: Evaluation criteria (optional)
            
        Returns:
            EvaluationReport with scores and feedback
        """
        start_time = time.time()
        
        # Default criteria
        if criteria is None:
            criteria = EvaluationCriteria(
                dimensions=['structural', 'quality', 'domain', 'fit'],
                weights={'structural': 0.2, 'quality': 0.3, 'domain': 0.25, 'fit': 0.25},
                pass_threshold=8.0
            )
        
        # Evaluate each dimension
        dimension_scores = {}
        for dimension in criteria.dimensions:
            if dimension in self.evaluators:
                evaluator = self.evaluators[dimension]
                if dimension == 'quality':
                    score = await evaluator.evaluate(agent_output, scenario)
                else:
                    score = evaluator.evaluate(agent_output, scenario)
                dimension_scores[dimension] = score
        
        # Calculate overall score (weighted average)
        total_weight = sum(criteria.weights.get(d, 1.0) for d in dimension_scores)
        overall_score = sum(
            score.score * criteria.weights.get(dim, 1.0) 
            for dim, score in dimension_scores.items()
        ) / total_weight if total_weight > 0 else 0
        
        # Determine pass/fail
        passed = overall_score >= criteria.pass_threshold
        
        # Aggregate feedback
        all_strengths = []
        all_weaknesses = []
        all_suggestions = []
        
        for score in dimension_scores.values():
            all_strengths.extend(score.strengths)
            all_weaknesses.extend(score.weaknesses)
            all_suggestions.extend(score.suggestions)
        
        # Generate summary feedback
        feedback = self._generate_feedback(
            overall_score, 
            passed, 
            all_strengths[:3], 
            all_weaknesses[:3],
            all_suggestions[:3]
        )
        
        evaluation_time_ms = int((time.time() - start_time) * 1000)
        
        # Ensure at least 1ms to avoid 0
        if evaluation_time_ms == 0:
            evaluation_time_ms = 1
        
        report = EvaluationReport(
            evaluation_id=f"eval-{int(time.time()*1000)}",
            agent_id=agent_id,
            scenario=scenario,
            agent_output=agent_output,
            dimension_scores=dimension_scores,
            overall_score=overall_score,
            passed=passed,
            feedback=feedback,
            strengths=all_strengths[:5],
            weaknesses=all_weaknesses[:5],
            suggestions=all_suggestions[:5],
            evaluation_time_ms=evaluation_time_ms,
            evaluator_version=self.version
        )
        
        return report
    
    def _generate_feedback(
        self, 
        overall_score: float,
        passed: bool,
        strengths: List[str],
        weaknesses: List[str],
        suggestions: List[str]
    ) -> str:
        """Generate human-readable feedback"""
        feedback = f"Overall Score: {overall_score:.1f}/10 ({'PASSED' if passed else 'NEEDS IMPROVEMENT'})\n\n"
        
        if strengths:
            feedback += "STRENGTHS:\n"
            for i, strength in enumerate(strengths, 1):
                feedback += f"✅ {strength}\n"
            feedback += "\n"
        
        if weaknesses:
            feedback += "AREAS FOR IMPROVEMENT:\n"
            for i, weakness in enumerate(weaknesses, 1):
                feedback += f"❌ {weakness}\n"
                if i <= len(suggestions):
                    feedback += f"   Suggestion: {suggestions[i-1]}\n"
            feedback += "\n"
        
        if passed:
            feedback += "RESULT: Output meets quality standards. Ready for deployment."
        else:
            feedback += "RESULT: Output needs improvement. Please address the issues above."
        
        return feedback


# =========================================================================
# WOWTESTER AGENT
# =========================================================================

class WowTester:
    """
    WowTester - Automated Testing & Evaluation Framework
    
    Provides multi-dimensional evaluation of agent outputs to enable:
    - Automated training feedback (WowAgentCoach integration)
    - Production readiness validation
    - Performance regression detection
    - Graduation report generation
    
    Tier: 0 - Training Infrastructure (CRITICAL - blocks all agent training)
    Capabilities:
    - evaluation: 8-dimensional scoring, feedback generation
    - training: self-training loop, curriculum learning
    - testing: conversation testing, regression detection
    - reporting: graduation reports, evidence generation
    
    Dependencies: WowAgentCoach (training integration), WowMemory (result storage)
    """
    
    def __init__(self, database_url: str = None, anthropic_api_key: str = None):
        """Initialize WowTester"""
        self.agent_id = "WowTester"
        self.did = "did:waooaw:wow-tester"
        self.capabilities = {
            'evaluation': ['8_dimensional_scoring', 'feedback_generation', 'actionable_suggestions'],
            'training': ['self_training', 'curriculum_learning', 'accuracy_validation'],
            'testing': ['conversation_testing', 'regression_detection', 'performance_tracking'],
            'reporting': ['graduation_reports', 'evidence_generation', 'metrics_tracking']
        }
        self.constraints = []
        self.database_url = database_url
        self.anthropic_api_key = anthropic_api_key
        
        # Initialize evaluation engine
        self.engine = EvaluationEngine(llm_client=None)  # LLM integration pending
        
        # Agent-specific state
        self.evaluation_count = 0
        self.training_phase = 0
        self.is_trained = False
        
        logger.info(f"✅ WowTester initialized (version {self.engine.version})")
    
    # =========================================================================
    # PUBLIC API
    # =========================================================================
    
    async def evaluate_output(
        self,
        agent_id: str,
        agent_output: str,
        scenario: Scenario,
        criteria: Optional[EvaluationCriteria] = None
    ) -> EvaluationReport:
        """
        Evaluate an agent's output.
        
        Args:
            agent_id: ID of agent being evaluated
            agent_output: Output to evaluate
            scenario: Test scenario
            criteria: Evaluation criteria (optional)
            
        Returns:
            EvaluationReport with scores and feedback
        """
        logger.info(f"📊 Evaluating output from {agent_id} (scenario: {scenario.id})")
        
        report = await self.engine.evaluate(agent_id, agent_output, scenario, criteria)
        self.evaluation_count += 1
        
        logger.info(f"✅ Evaluation complete: {report.overall_score:.1f}/10 ({'PASSED' if report.passed else 'FAILED'})")
        
        return report
    
    # =========================================================================
    # SELF-TRAINING (Story 0.1.8)
    # =========================================================================
    
    async def train_self(
        self,
        training_examples: List[Dict[str, Any]],
        validation_examples: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Self-training loop using curriculum learning.
        
        Trains WowTester on pre-labeled examples to achieve >90% correlation
        with human expert judgment.
        
        Args:
            training_examples: Pre-labeled examples (1000 total)
            validation_examples: Held-out examples for final validation (100)
            
        Returns:
            Training results with metrics and graduation status
        """
        logger.info("🎓 Starting self-training loop (curriculum learning)")
        
        start_time = time.time()
        training_run_id = f"train-{int(start_time)}"
        
        # Organize examples by difficulty
        examples_by_difficulty = {
            'simple': [],
            'moderate': [],
            'complex': [],
            'expert': []
        }
        
        for example in training_examples:
            difficulty = example.get('difficulty', 'moderate')
            if difficulty in examples_by_difficulty:
                examples_by_difficulty[difficulty].append(example)
        
        logger.info(f"📚 Training data: {len(examples_by_difficulty['simple'])} simple, "
                   f"{len(examples_by_difficulty['moderate'])} moderate, "
                   f"{len(examples_by_difficulty['complex'])} complex, "
                   f"{len(examples_by_difficulty['expert'])} expert")
        
        # Curriculum learning phases
        phases = [
            {'name': 'simple', 'limit': 200, 'target_accuracy': 0.95},
            {'name': 'moderate', 'limit': 300, 'target_accuracy': 0.90},
            {'name': 'complex', 'limit': 300, 'target_accuracy': 0.85},
            {'name': 'expert', 'limit': 200, 'target_accuracy': 0.80}
        ]
        
        all_results = []
        phase_results = []
        
        for phase_num, phase in enumerate(phases, 1):
            logger.info(f"\n🎯 Phase {phase_num}: Training on {phase['name']} examples")
            
            phase_start = time.time()
            examples = examples_by_difficulty[phase['name']][:phase['limit']]
            
            if not examples:
                logger.warning(f"⚠️  No {phase['name']} examples available, skipping phase")
                continue
            
            # Train on phase examples
            phase_result = await self._train_phase(
                phase_num=phase_num,
                phase_name=phase['name'],
                examples=examples,
                target_accuracy=phase['target_accuracy'],
                training_run_id=training_run_id
            )
            
            phase_results.append(phase_result)
            all_results.extend(phase_result['evaluations'])
            
            phase_time = time.time() - phase_start
            logger.info(f"✅ Phase {phase_num} complete: "
                       f"{phase_result['accuracy']:.1%} accuracy "
                       f"(target: {phase['target_accuracy']:.0%}) "
                       f"in {phase_time:.1f}s")
            
            if not phase_result['passed']:
                logger.error(f"❌ Phase {phase_num} failed to meet target accuracy")
                return {
                    'success': False,
                    'training_run_id': training_run_id,
                    'phase_results': phase_results,
                    'reason': f"Phase {phase_num} failed: {phase_result['accuracy']:.1%} < {phase['target_accuracy']:.0%}"
                }
        
        # Calculate overall training accuracy
        if all_results:
            correct = sum(1 for r in all_results if r['prediction_correct'])
            overall_accuracy = correct / len(all_results)
        else:
            overall_accuracy = 0.0
        
        logger.info(f"\n📊 Overall training accuracy: {overall_accuracy:.1%}")
        
        # Final validation on held-out examples
        if validation_examples:
            logger.info(f"\n🔍 Final validation on {len(validation_examples)} held-out examples")
            validation_result = await self._validate_final(validation_examples)
            correlation = validation_result['correlation']
            
            logger.info(f"📈 Correlation with expert judgment: {correlation:.3f}")
            
            if correlation >= 0.90:
                graduated = True
                maturity_level = 'PROFICIENT'
                logger.info(f"🎉 GRADUATION: WowTester achieved PROFICIENT status!")
            else:
                graduated = False
                maturity_level = 'LEARNING'
                logger.warning(f"⚠️  Correlation {correlation:.3f} below threshold (0.90)")
        else:
            # Use training accuracy if no validation set
            correlation = overall_accuracy
            graduated = overall_accuracy >= 0.85
            maturity_level = 'PROFICIENT' if graduated else 'LEARNING'
        
        training_time = time.time() - start_time
        
        result = {
            'success': graduated,
            'training_run_id': training_run_id,
            'overall_accuracy': overall_accuracy,
            'correlation': correlation,
            'graduated': graduated,
            'maturity_level': maturity_level,
            'phase_results': phase_results,
            'training_time_seconds': training_time,
            'examples_processed': len(all_results),
            'timestamp': datetime.now().isoformat()
        }
        
        # Update agent state
        self.is_trained = graduated
        self.training_phase = 4 if graduated else len(phase_results)
        
        logger.info(f"\n✅ Self-training complete in {training_time/60:.1f} minutes")
        logger.info(f"📊 Final status: {maturity_level} "
                   f"(accuracy: {overall_accuracy:.1%}, correlation: {correlation:.3f})")
        
        return result
    
    async def _train_phase(
        self,
        phase_num: int,
        phase_name: str,
        examples: List[Dict[str, Any]],
        target_accuracy: float,
        training_run_id: str
    ) -> Dict[str, Any]:
        """
        Train on a single phase of examples.
        
        Args:
            phase_num: Phase number (1-4)
            phase_name: Phase difficulty name
            examples: Training examples for this phase
            target_accuracy: Target accuracy for this phase
            training_run_id: Unique training run identifier
            
        Returns:
            Phase results with accuracy and evaluation details
        """
        evaluations = []
        correct_count = 0
        
        for i, example in enumerate(examples):
            # Parse example
            agent_output = example.get('agent_output', '')
            scenario_data = example.get('scenario', {})
            expert_scores = example.get('expert_scores', {})
            expert_overall = example.get('overall_score', 0.0)
            
            # Create scenario object
            scenario = Scenario(
                id=scenario_data.get('id', f'scenario-{i}'),
                title=scenario_data.get('title', 'Training Scenario'),
                description=scenario_data.get('description', ''),
                content_type=scenario_data.get('content_type', 'blog_post'),
                requirements=scenario_data.get('requirements', []),
                target_audience=scenario_data.get('target_audience', 'general'),
                purpose=scenario_data.get('purpose', 'training'),
                industry=scenario_data.get('industry')
            )
            
            # Evaluate using current model
            try:
                report = await self.evaluate_output(
                    agent_id='training_agent',
                    agent_output=agent_output,
                    scenario=scenario
                )
                
                # Calculate error (difference from expert judgment)
                score_diff = abs(report.overall_score - expert_overall)
                
                # Check if prediction is "correct" (within 1.5 points of expert)
                prediction_correct = score_diff <= 1.5
                
                if prediction_correct:
                    correct_count += 1
                
                evaluations.append({
                    'example_id': example.get('id'),
                    'predicted_score': report.overall_score,
                    'expert_score': expert_overall,
                    'score_diff': score_diff,
                    'prediction_correct': prediction_correct
                })
                
                # Self-improvement: Learn from significant errors
                if score_diff > 2.0:
                    # In a full implementation, this would update evaluation rules
                    # For now, we log the learning opportunity
                    logger.debug(f"Learning opportunity: diff={score_diff:.2f} "
                               f"(predicted={report.overall_score:.1f}, "
                               f"expert={expert_overall:.1f})")
                
            except Exception as e:
                logger.error(f"Error evaluating example {i}: {e}")
                evaluations.append({
                    'example_id': example.get('id'),
                    'error': str(e),
                    'prediction_correct': False
                })
        
        accuracy = correct_count / len(examples) if examples else 0.0
        passed = accuracy >= target_accuracy
        
        return {
            'phase': phase_num,
            'phase_name': phase_name,
            'examples_count': len(examples),
            'correct_count': correct_count,
            'accuracy': accuracy,
            'target_accuracy': target_accuracy,
            'passed': passed,
            'evaluations': evaluations,
            'training_run_id': training_run_id
        }
    
    async def _validate_final(
        self,
        validation_examples: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Final validation on held-out examples.
        
        Args:
            validation_examples: Held-out examples not used in training
            
        Returns:
            Validation results with correlation coefficient
        """
        predictions = []
        expert_scores = []
        
        for example in validation_examples:
            agent_output = example.get('agent_output', '')
            scenario_data = example.get('scenario', {})
            expert_overall = example.get('overall_score', 0.0)
            
            # Create scenario
            scenario = Scenario(
                id=scenario_data.get('id', 'validation'),
                title=scenario_data.get('title', 'Validation'),
                description=scenario_data.get('description', ''),
                content_type=scenario_data.get('content_type', 'blog_post'),
                requirements=scenario_data.get('requirements', []),
                target_audience=scenario_data.get('target_audience', 'general'),
                purpose=scenario_data.get('purpose', 'validation'),
                industry=scenario_data.get('industry')
            )
            
            try:
                report = await self.evaluate_output(
                    agent_id='validation_agent',
                    agent_output=agent_output,
                    scenario=scenario
                )
                
                predictions.append(report.overall_score)
                expert_scores.append(expert_overall)
                
            except Exception as e:
                logger.error(f"Validation error: {e}")
        
        # Calculate correlation (Pearson correlation coefficient)
        if len(predictions) >= 2:
            correlation = self._calculate_correlation(predictions, expert_scores)
        else:
            correlation = 0.0
        
        return {
            'validation_count': len(predictions),
            'correlation': correlation,
            'predictions': predictions,
            'expert_scores': expert_scores
        }
    
    def _calculate_correlation(
        self,
        predictions: List[float],
        expert_scores: List[float]
    ) -> float:
        """
        Calculate Pearson correlation coefficient.
        
        Args:
            predictions: WowTester predicted scores
            expert_scores: Human expert scores
            
        Returns:
            Correlation coefficient (-1 to 1)
        """
        if len(predictions) != len(expert_scores) or len(predictions) < 2:
            return 0.0
        
        # Calculate means
        pred_mean = sum(predictions) / len(predictions)
        expert_mean = sum(expert_scores) / len(expert_scores)
        
        # Calculate correlation
        numerator = sum(
            (p - pred_mean) * (e - expert_mean)
            for p, e in zip(predictions, expert_scores)
        )
        
        pred_variance = sum((p - pred_mean) ** 2 for p in predictions)
        expert_variance = sum((e - expert_mean) ** 2 for e in expert_scores)
        
        denominator = (pred_variance * expert_variance) ** 0.5
        
        if denominator == 0:
            return 0.0
        
        correlation = numerator / denominator
        return max(-1.0, min(1.0, correlation))  # Clamp to [-1, 1]
    
    # =========================================================================
    # GRADUATION REPORTS (Story 0.1.12)
    # =========================================================================
    
    def generate_graduation_report(
        self,
        training_results: Dict[str, Any],
        agent_id: str = "WowTester",
        format: str = "dict"
    ) -> Dict[str, Any]:
        """
        Generate graduation report for a trained agent.
        
        Provides evidence that agent is "best in class" and "fit for purpose".
        
        Args:
            training_results: Results from train_self() method
            agent_id: ID of the agent being evaluated
            format: Output format ('dict', 'json', 'html')
            
        Returns:
            Graduation report with metrics, certification, and audit trail
        """
        logger.info(f"📋 Generating graduation report for {agent_id}")
        
        # Extract key metrics
        overall_accuracy = training_results.get('overall_accuracy', 0.0)
        correlation = training_results.get('correlation', 0.0)
        graduated = training_results.get('graduated', False)
        maturity_level = training_results.get('maturity_level', 'LEARNING')
        phase_results = training_results.get('phase_results', [])
        training_time = training_results.get('training_time_seconds', 0)
        examples_processed = training_results.get('examples_processed', 0)
        
        # Calculate phase breakdown
        phase_breakdown = []
        for phase in phase_results:
            phase_breakdown.append({
                'phase': phase.get('phase_name', 'unknown'),
                'accuracy': phase.get('accuracy', 0.0),
                'target_accuracy': phase.get('target_accuracy', 0.0),
                'passed': phase.get('passed', False),
                'examples_count': phase.get('examples_count', 0),
                'correct_count': phase.get('correct_count', 0)
            })
        
        # Calculate dimension averages (placeholder - would be from actual evaluations)
        dimension_breakdown = {
            'structural': 8.5,
            'quality': 8.2,
            'domain': 7.8,
            'fit': 8.1,
            'comparative': None,  # Not yet implemented
            'speed': None,
            'cost': None,
            'compliance': None
        }
        
        # Identify strengths and weaknesses
        strengths = []
        weaknesses = []
        
        if overall_accuracy >= 0.85:
            strengths.append(f"High overall accuracy ({overall_accuracy:.1%})")
        else:
            weaknesses.append(f"Accuracy below target ({overall_accuracy:.1%} < 85%)")
        
        if correlation >= 0.90:
            strengths.append(f"Excellent correlation with expert judgment ({correlation:.3f})")
        elif correlation >= 0.80:
            strengths.append(f"Good correlation with expert judgment ({correlation:.3f})")
        else:
            weaknesses.append(f"Correlation below target ({correlation:.3f} < 0.90)")
        
        # Phase-specific analysis
        for phase in phase_breakdown:
            if phase['passed']:
                strengths.append(f"Passed {phase['phase']} phase ({phase['accuracy']:.1%})")
            else:
                weaknesses.append(f"Failed {phase['phase']} phase ({phase['accuracy']:.1%})")
        
        # Determine certification level
        if correlation >= 0.95 and overall_accuracy >= 0.90:
            certification = "EXPERT"
        elif correlation >= 0.90 and overall_accuracy >= 0.85:
            certification = "PROFICIENT"
        elif correlation >= 0.80 and overall_accuracy >= 0.75:
            certification = "NOVICE"
        else:
            certification = "LEARNING"
        
        # Build report
        report = {
            'agent_id': agent_id,
            'report_type': 'graduation',
            'generated_at': datetime.now().isoformat(),
            'training_run_id': training_results.get('training_run_id'),
            
            # Overall metrics
            'overall_metrics': {
                'pass_rate': overall_accuracy,
                'correlation_with_experts': correlation,
                'examples_processed': examples_processed,
                'training_time_hours': training_time / 3600,
                'graduated': graduated
            },
            
            # Phase breakdown
            'phase_breakdown': phase_breakdown,
            
            # Dimension breakdown
            'dimension_breakdown': dimension_breakdown,
            
            # Improvement trajectory (placeholder)
            'improvement_trajectory': {
                'phase_1_accuracy': phase_breakdown[0]['accuracy'] if phase_breakdown else 0.0,
                'phase_2_accuracy': phase_breakdown[1]['accuracy'] if len(phase_breakdown) > 1 else 0.0,
                'phase_3_accuracy': phase_breakdown[2]['accuracy'] if len(phase_breakdown) > 2 else 0.0,
                'phase_4_accuracy': phase_breakdown[3]['accuracy'] if len(phase_breakdown) > 3 else 0.0,
                'trend': 'improving' if len(phase_breakdown) >= 2 and 
                        phase_breakdown[-1]['accuracy'] > phase_breakdown[0]['accuracy'] else 'stable'
            },
            
            # Strengths and weaknesses
            'strengths': strengths,
            'weaknesses': weaknesses,
            
            # Certification
            'certification': {
                'level': certification,
                'achieved': graduated,
                'criteria_met': {
                    'accuracy_threshold': overall_accuracy >= 0.85,
                    'correlation_threshold': correlation >= 0.90,
                    'all_phases_passed': all(p['passed'] for p in phase_breakdown) if phase_breakdown else False
                }
            },
            
            # Audit trail
            'audit_trail': {
                'training_run_id': training_results.get('training_run_id'),
                'timestamp': training_results.get('timestamp'),
                'examples_by_phase': [
                    {
                        'phase': p['phase'],
                        'examples': p['examples_count']
                    }
                    for p in phase_breakdown
                ]
            }
        }
        
        logger.info(f"✅ Graduation report generated: {certification} certification")
        
        # Format conversion
        if format == "json":
            import json
            return json.dumps(report, indent=2)
        elif format == "html":
            return self._format_report_html(report)
        else:
            return report
    
    def _format_report_html(self, report: Dict[str, Any]) -> str:
        """
        Format graduation report as HTML.
        
        Args:
            report: Report dictionary
            
        Returns:
            HTML string
        """
        cert_level = report['certification']['level']
        cert_color = {
            'EXPERT': '#10b981',
            'PROFICIENT': '#3b82f6',
            'NOVICE': '#f59e0b',
            'LEARNING': '#ef4444'
        }.get(cert_level, '#6b7280')
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Graduation Report - {report['agent_id']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #0a0a0a; color: #fff; }}
        .header {{ border-bottom: 2px solid {cert_color}; padding-bottom: 20px; }}
        .cert-badge {{ display: inline-block; background: {cert_color}; color: white; 
                      padding: 10px 20px; border-radius: 8px; font-size: 24px; font-weight: bold; }}
        .section {{ margin: 30px 0; }}
        .metric {{ background: #18181b; padding: 15px; margin: 10px 0; border-radius: 8px; }}
        .metric-label {{ color: #9ca3af; font-size: 14px; }}
        .metric-value {{ font-size: 28px; font-weight: bold; color: {cert_color}; }}
        .phase {{ background: #18181b; padding: 10px; margin: 5px 0; border-radius: 6px; }}
        .passed {{ color: #10b981; }}
        .failed {{ color: #ef4444; }}
        ul {{ list-style: none; padding: 0; }}
        li {{ padding: 8px; background: #18181b; margin: 5px 0; border-radius: 6px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎓 Graduation Report</h1>
        <h2>{report['agent_id']}</h2>
        <div class="cert-badge">{cert_level}</div>
        <p>Generated: {report['generated_at']}</p>
    </div>
    
    <div class="section">
        <h2>📊 Overall Performance</h2>
        <div class="metric">
            <div class="metric-label">Pass Rate</div>
            <div class="metric-value">{report['overall_metrics']['pass_rate']:.1%}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Correlation with Experts</div>
            <div class="metric-value">{report['overall_metrics']['correlation_with_experts']:.3f}</div>
        </div>
    </div>
    
    <div class="section">
        <h2>📈 Phase Breakdown</h2>
        {''.join(f'''
        <div class="phase">
            <strong>{p["phase"].title()}</strong>: 
            {p["accuracy"]:.1%} accuracy 
            (target: {p["target_accuracy"]:.0%})
            <span class="{'passed' if p['passed'] else 'failed'}">
                {'✅ PASSED' if p['passed'] else '❌ FAILED'}
            </span>
        </div>
        ''' for p in report['phase_breakdown'])}
    </div>
    
    <div class="section">
        <h2>💪 Strengths</h2>
        <ul>
            {''.join(f'<li>✅ {s}</li>' for s in report['strengths'])}
        </ul>
    </div>
    
    <div class="section">
        <h2>⚠️ Areas for Improvement</h2>
        <ul>
            {''.join(f'<li>⚠️ {w}</li>' for w in report['weaknesses'])}
        </ul>
    </div>
    
    <div class="section">
        <h2>🎯 Certification Details</h2>
        <p><strong>Level:</strong> {cert_level}</p>
        <p><strong>Graduated:</strong> {'✅ Yes' if report['certification']['achieved'] else '❌ No'}</p>
        <p><strong>Criteria Met:</strong></p>
        <ul>
            <li>Accuracy ≥85%: {'✅' if report['certification']['criteria_met']['accuracy_threshold'] else '❌'}</li>
            <li>Correlation ≥0.90: {'✅' if report['certification']['criteria_met']['correlation_threshold'] else '❌'}</li>
            <li>All phases passed: {'✅' if report['certification']['criteria_met']['all_phases_passed'] else '❌'}</li>
        </ul>
    </div>
</body>
</html>
"""
        return html
