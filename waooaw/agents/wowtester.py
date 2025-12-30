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
