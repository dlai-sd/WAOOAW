"""
Knowledge Synthesis & Creation Engine - Story 5.6.2

Epic 5.6: Self-Evolving Agent System

Agents discover patterns, create frameworks, author best practices, and generate
reusable case studies to contribute new knowledge to the platform.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Set
from collections import defaultdict


class PatternType(Enum):
    """Types of patterns that can be discovered"""
    WORKFLOW = "workflow"                 # Common task sequences
    CUSTOMER_BEHAVIOR = "customer_behavior"  # Customer preference patterns
    SUCCESS_FACTOR = "success_factor"     # What makes tasks successful
    FAILURE_INDICATOR = "failure_indicator"  # Warning signs of failure
    OPTIMIZATION = "optimization"         # Efficiency improvements
    INNOVATION = "innovation"             # Novel approaches that work


class FrameworkType(Enum):
    """Types of frameworks that can be created"""
    METHODOLOGY = "methodology"           # Step-by-step approach
    DECISION_TREE = "decision_tree"       # Decision-making framework
    CHECKLIST = "checklist"               # Quality/completeness checklist
    TEMPLATE = "template"                 # Reusable structure
    RUBRIC = "rubric"                     # Evaluation criteria
    PLAYBOOK = "playbook"                 # Comprehensive guide


class KnowledgeStatus(Enum):
    """Status of knowledge contribution"""
    DRAFT = "draft"                       # Initial creation
    UNDER_REVIEW = "under_review"         # Being validated
    APPROVED = "approved"                 # Ready for use
    PUBLISHED = "published"               # Available to all agents
    DEPRECATED = "deprecated"             # No longer recommended


@dataclass
class DiscoveredPattern:
    """A pattern discovered from data analysis"""
    pattern_id: str
    pattern_type: PatternType
    agent_variant_id: str  # Agent who discovered it
    
    pattern_name: str
    pattern_description: str
    
    # Evidence
    observed_instances: int  # How many times observed
    confidence_score: float  # 0.0 to 1.0
    supporting_data: List[str]  # Task IDs or data points
    
    # Application
    applicable_contexts: List[str]  # When to apply this pattern
    expected_benefit: str
    implementation_notes: str
    
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    validation_count: int = 0  # Times pattern was validated by others
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type.value,
            "agent_variant_id": self.agent_variant_id,
            "pattern_name": self.pattern_name,
            "pattern_description": self.pattern_description,
            "observed_instances": self.observed_instances,
            "confidence_score": self.confidence_score,
            "supporting_data": self.supporting_data,
            "applicable_contexts": self.applicable_contexts,
            "expected_benefit": self.expected_benefit,
            "implementation_notes": self.implementation_notes,
            "discovered_at": self.discovered_at.isoformat(),
            "validation_count": self.validation_count,
        }


@dataclass
class CreatedFramework:
    """A framework created for a novel situation"""
    framework_id: str
    framework_type: FrameworkType
    agent_variant_id: str
    
    framework_name: str
    purpose: str  # What problem it solves
    
    # Structure
    steps: List[Dict[str, str]]  # Ordered steps with descriptions
    decision_points: List[Dict[str, Any]]  # Key decisions to make
    success_criteria: List[str]
    
    # Context
    applicable_scenarios: List[str]
    prerequisites: List[str]
    limitations: List[str]
    
    # Validation
    times_used: int
    success_rate: float  # 0.0 to 1.0
    user_feedback: List[str]
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: KnowledgeStatus = KnowledgeStatus.DRAFT
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "framework_id": self.framework_id,
            "framework_type": self.framework_type.value,
            "agent_variant_id": self.agent_variant_id,
            "framework_name": self.framework_name,
            "purpose": self.purpose,
            "steps": self.steps,
            "decision_points": self.decision_points,
            "success_criteria": self.success_criteria,
            "applicable_scenarios": self.applicable_scenarios,
            "prerequisites": self.prerequisites,
            "limitations": self.limitations,
            "times_used": self.times_used,
            "success_rate": self.success_rate,
            "user_feedback": self.user_feedback,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
        }


@dataclass
class BestPractice:
    """A best practice authored from experience"""
    practice_id: str
    agent_variant_id: str
    
    title: str
    category: str  # e.g., "content_creation", "customer_service"
    
    # Core content
    principle: str  # The core principle
    rationale: str  # Why this works
    how_to: str     # How to implement
    examples: List[str]  # Real examples
    
    # Evidence
    success_stories: List[str]  # Task IDs where this worked
    measured_impact: Dict[str, float]  # Metrics showing improvement
    
    # Guidance
    when_to_use: List[str]
    when_not_to_use: List[str]
    common_mistakes: List[str]
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: KnowledgeStatus = KnowledgeStatus.DRAFT
    adoption_count: int = 0  # How many agents adopted this
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "practice_id": self.practice_id,
            "agent_variant_id": self.agent_variant_id,
            "title": self.title,
            "category": self.category,
            "principle": self.principle,
            "rationale": self.rationale,
            "how_to": self.how_to,
            "examples": self.examples,
            "success_stories": self.success_stories,
            "measured_impact": self.measured_impact,
            "when_to_use": self.when_to_use,
            "when_not_to_use": self.when_not_to_use,
            "common_mistakes": self.common_mistakes,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "adoption_count": self.adoption_count,
        }


@dataclass
class CaseStudy:
    """A case study generated as reusable template"""
    case_study_id: str
    agent_variant_id: str
    
    title: str
    category: str
    
    # Context
    situation: str  # Initial situation/challenge
    customer_profile: str  # Type of customer
    requirements: List[str]
    constraints: List[str]
    
    # Solution
    approach_taken: str
    key_decisions: List[Dict[str, str]]
    tools_used: List[str]
    timeline: str
    
    # Outcome
    results: str
    metrics: Dict[str, Any]  # Quantitative results
    customer_feedback: str
    lessons_learned: List[str]
    
    # Reusability
    template_steps: List[str]  # How to replicate this success
    adaptation_notes: str  # How to adapt for different contexts
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: KnowledgeStatus = KnowledgeStatus.DRAFT
    times_referenced: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "case_study_id": self.case_study_id,
            "agent_variant_id": self.agent_variant_id,
            "title": self.title,
            "category": self.category,
            "situation": self.situation,
            "customer_profile": self.customer_profile,
            "requirements": self.requirements,
            "constraints": self.constraints,
            "approach_taken": self.approach_taken,
            "key_decisions": self.key_decisions,
            "tools_used": self.tools_used,
            "timeline": self.timeline,
            "results": self.results,
            "metrics": self.metrics,
            "customer_feedback": self.customer_feedback,
            "lessons_learned": self.lessons_learned,
            "template_steps": self.template_steps,
            "adaptation_notes": self.adaptation_notes,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "times_referenced": self.times_referenced,
        }


class KnowledgeSynthesisEngine:
    """
    Agent knowledge creation and synthesis system.
    
    Enables agents to discover patterns, create frameworks, author best
    practices, and generate case studies from their experiences.
    """
    
    def __init__(self):
        self._patterns: Dict[str, DiscoveredPattern] = {}
        self._frameworks: Dict[str, CreatedFramework] = {}
        self._best_practices: Dict[str, BestPractice] = {}
        self._case_studies: Dict[str, CaseStudy] = {}
        
        # Indexing for search
        self._patterns_by_agent: Dict[str, List[str]] = defaultdict(list)
        self._frameworks_by_agent: Dict[str, List[str]] = defaultdict(list)
        self._practices_by_agent: Dict[str, List[str]] = defaultdict(list)
        self._case_studies_by_agent: Dict[str, List[str]] = defaultdict(list)
        
        self._patterns_by_type: Dict[PatternType, List[str]] = defaultdict(list)
        self._frameworks_by_type: Dict[FrameworkType, List[str]] = defaultdict(list)
        self._practices_by_category: Dict[str, List[str]] = defaultdict(list)
        self._case_studies_by_category: Dict[str, List[str]] = defaultdict(list)
    
    def discover_pattern(
        self,
        agent_variant_id: str,
        pattern_type: PatternType,
        pattern_name: str,
        pattern_description: str,
        supporting_data: List[str],
        applicable_contexts: List[str],
        expected_benefit: str,
        implementation_notes: str = ""
    ) -> DiscoveredPattern:
        """
        Agent discovers and documents a pattern from data.
        """
        pattern_id = f"pattern_{agent_variant_id}_{datetime.utcnow().timestamp()}"
        
        # Calculate confidence based on supporting data quantity
        observed_instances = len(supporting_data)
        confidence_score = min(0.5 + (observed_instances * 0.05), 1.0)
        
        pattern = DiscoveredPattern(
            pattern_id=pattern_id,
            pattern_type=pattern_type,
            agent_variant_id=agent_variant_id,
            pattern_name=pattern_name,
            pattern_description=pattern_description,
            observed_instances=observed_instances,
            confidence_score=confidence_score,
            supporting_data=supporting_data,
            applicable_contexts=applicable_contexts,
            expected_benefit=expected_benefit,
            implementation_notes=implementation_notes
        )
        
        self._patterns[pattern_id] = pattern
        self._patterns_by_agent[agent_variant_id].append(pattern_id)
        self._patterns_by_type[pattern_type].append(pattern_id)
        
        return pattern
    
    def validate_pattern(self, pattern_id: str) -> bool:
        """
        Another agent validates a pattern, increasing its confidence.
        """
        if pattern_id not in self._patterns:
            return False
        
        pattern = self._patterns[pattern_id]
        pattern.validation_count += 1
        
        # Increase confidence with validation
        pattern.confidence_score = min(pattern.confidence_score + 0.1, 1.0)
        
        return True
    
    def create_framework(
        self,
        agent_variant_id: str,
        framework_type: FrameworkType,
        framework_name: str,
        purpose: str,
        steps: List[Dict[str, str]],
        applicable_scenarios: List[str],
        success_criteria: List[str]
    ) -> CreatedFramework:
        """
        Agent creates a new framework for solving a type of problem.
        """
        framework_id = f"framework_{agent_variant_id}_{datetime.utcnow().timestamp()}"
        
        framework = CreatedFramework(
            framework_id=framework_id,
            framework_type=framework_type,
            agent_variant_id=agent_variant_id,
            framework_name=framework_name,
            purpose=purpose,
            steps=steps,
            decision_points=[],
            success_criteria=success_criteria,
            applicable_scenarios=applicable_scenarios,
            prerequisites=[],
            limitations=[],
            times_used=0,
            success_rate=0.0,
            user_feedback=[]
        )
        
        self._frameworks[framework_id] = framework
        self._frameworks_by_agent[agent_variant_id].append(framework_id)
        self._frameworks_by_type[framework_type].append(framework_id)
        
        return framework
    
    def use_framework(
        self,
        framework_id: str,
        successful: bool,
        feedback: Optional[str] = None
    ) -> bool:
        """
        Record usage of a framework and its outcome.
        """
        if framework_id not in self._frameworks:
            return False
        
        framework = self._frameworks[framework_id]
        framework.times_used += 1
        
        # Update success rate
        if successful:
            framework.success_rate = (
                (framework.success_rate * (framework.times_used - 1) + 1.0) / 
                framework.times_used
            )
        else:
            framework.success_rate = (
                (framework.success_rate * (framework.times_used - 1)) / 
                framework.times_used
            )
        
        if feedback:
            framework.user_feedback.append(feedback)
        
        # Promote to published if proven successful
        if framework.times_used >= 10 and framework.success_rate >= 0.8:
            framework.status = KnowledgeStatus.PUBLISHED
        elif framework.times_used >= 3:
            framework.status = KnowledgeStatus.APPROVED
        
        return True
    
    def author_best_practice(
        self,
        agent_variant_id: str,
        title: str,
        category: str,
        principle: str,
        rationale: str,
        how_to: str,
        success_stories: List[str],
        when_to_use: List[str]
    ) -> BestPractice:
        """
        Agent authors a best practice from successful experiences.
        """
        practice_id = f"practice_{agent_variant_id}_{datetime.utcnow().timestamp()}"
        
        practice = BestPractice(
            practice_id=practice_id,
            agent_variant_id=agent_variant_id,
            title=title,
            category=category,
            principle=principle,
            rationale=rationale,
            how_to=how_to,
            examples=[],
            success_stories=success_stories,
            measured_impact={},
            when_to_use=when_to_use,
            when_not_to_use=[],
            common_mistakes=[]
        )
        
        self._best_practices[practice_id] = practice
        self._practices_by_agent[agent_variant_id].append(practice_id)
        self._practices_by_category[category].append(practice_id)
        
        return practice
    
    def adopt_best_practice(self, practice_id: str) -> bool:
        """
        Agent adopts a best practice created by another agent.
        """
        if practice_id not in self._best_practices:
            return False
        
        practice = self._best_practices[practice_id]
        practice.adoption_count += 1
        
        # Promote to published if widely adopted
        if practice.adoption_count >= 5:
            practice.status = KnowledgeStatus.PUBLISHED
        elif practice.adoption_count >= 2:
            practice.status = KnowledgeStatus.APPROVED
        
        return True
    
    def generate_case_study(
        self,
        agent_variant_id: str,
        title: str,
        category: str,
        situation: str,
        approach_taken: str,
        results: str,
        lessons_learned: List[str],
        template_steps: List[str]
    ) -> CaseStudy:
        """
        Agent generates a case study from a successful engagement.
        """
        case_study_id = f"case_{agent_variant_id}_{datetime.utcnow().timestamp()}"
        
        case_study = CaseStudy(
            case_study_id=case_study_id,
            agent_variant_id=agent_variant_id,
            title=title,
            category=category,
            situation=situation,
            customer_profile="",
            requirements=[],
            constraints=[],
            approach_taken=approach_taken,
            key_decisions=[],
            tools_used=[],
            timeline="",
            results=results,
            metrics={},
            customer_feedback="",
            lessons_learned=lessons_learned,
            template_steps=template_steps,
            adaptation_notes=""
        )
        
        self._case_studies[case_study_id] = case_study
        self._case_studies_by_agent[agent_variant_id].append(case_study_id)
        self._case_studies_by_category[category].append(case_study_id)
        
        return case_study
    
    def reference_case_study(self, case_study_id: str) -> bool:
        """
        Record that a case study was referenced/used.
        """
        if case_study_id not in self._case_studies:
            return False
        
        case_study = self._case_studies[case_study_id]
        case_study.times_referenced += 1
        
        # Promote if frequently referenced
        if case_study.times_referenced >= 10:
            case_study.status = KnowledgeStatus.PUBLISHED
        elif case_study.times_referenced >= 3:
            case_study.status = KnowledgeStatus.APPROVED
        
        return True
    
    def search_patterns(
        self,
        pattern_type: Optional[PatternType] = None,
        min_confidence: float = 0.0,
        applicable_context: Optional[str] = None
    ) -> List[DiscoveredPattern]:
        """
        Search for patterns by criteria.
        """
        if pattern_type:
            pattern_ids = self._patterns_by_type.get(pattern_type, [])
        else:
            pattern_ids = list(self._patterns.keys())
        
        results = []
        for pid in pattern_ids:
            pattern = self._patterns[pid]
            
            # Filter by confidence
            if pattern.confidence_score < min_confidence:
                continue
            
            # Filter by context
            if applicable_context and applicable_context not in pattern.applicable_contexts:
                continue
            
            results.append(pattern)
        
        # Sort by confidence
        results.sort(key=lambda p: p.confidence_score, reverse=True)
        
        return results
    
    def search_frameworks(
        self,
        framework_type: Optional[FrameworkType] = None,
        scenario: Optional[str] = None,
        min_success_rate: float = 0.0
    ) -> List[CreatedFramework]:
        """
        Search for frameworks by criteria.
        """
        if framework_type:
            framework_ids = self._frameworks_by_type.get(framework_type, [])
        else:
            framework_ids = list(self._frameworks.keys())
        
        results = []
        for fid in framework_ids:
            framework = self._frameworks[fid]
            
            # Filter by success rate
            if framework.success_rate < min_success_rate:
                continue
            
            # Filter by scenario
            if scenario and scenario not in framework.applicable_scenarios:
                continue
            
            results.append(framework)
        
        # Sort by success rate
        results.sort(key=lambda f: f.success_rate, reverse=True)
        
        return results
    
    def search_best_practices(
        self,
        category: Optional[str] = None,
        min_adoption: int = 0
    ) -> List[BestPractice]:
        """
        Search for best practices by criteria.
        """
        if category:
            practice_ids = self._practices_by_category.get(category, [])
        else:
            practice_ids = list(self._best_practices.keys())
        
        results = []
        for pid in practice_ids:
            practice = self._best_practices[pid]
            
            # Filter by adoption
            if practice.adoption_count < min_adoption:
                continue
            
            results.append(practice)
        
        # Sort by adoption count
        results.sort(key=lambda p: p.adoption_count, reverse=True)
        
        return results
    
    def search_case_studies(
        self,
        category: Optional[str] = None,
        min_references: int = 0
    ) -> List[CaseStudy]:
        """
        Search for case studies by criteria.
        """
        if category:
            case_ids = self._case_studies_by_category.get(category, [])
        else:
            case_ids = list(self._case_studies.keys())
        
        results = []
        for cid in case_ids:
            case_study = self._case_studies[cid]
            
            # Filter by references
            if case_study.times_referenced < min_references:
                continue
            
            results.append(case_study)
        
        # Sort by times referenced
        results.sort(key=lambda c: c.times_referenced, reverse=True)
        
        return results
    
    def get_agent_contributions(self, agent_variant_id: str) -> Dict[str, Any]:
        """
        Get all knowledge contributions by an agent.
        """
        return {
            "agent_variant_id": agent_variant_id,
            "patterns_discovered": len(self._patterns_by_agent[agent_variant_id]),
            "frameworks_created": len(self._frameworks_by_agent[agent_variant_id]),
            "best_practices_authored": len(self._practices_by_agent[agent_variant_id]),
            "case_studies_generated": len(self._case_studies_by_agent[agent_variant_id]),
            "total_contributions": (
                len(self._patterns_by_agent[agent_variant_id]) +
                len(self._frameworks_by_agent[agent_variant_id]) +
                len(self._practices_by_agent[agent_variant_id]) +
                len(self._case_studies_by_agent[agent_variant_id])
            )
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get knowledge synthesis statistics.
        """
        # Pattern statistics
        total_patterns = len(self._patterns)
        high_confidence_patterns = sum(
            1 for p in self._patterns.values() if p.confidence_score >= 0.8
        )
        validated_patterns = sum(
            1 for p in self._patterns.values() if p.validation_count > 0
        )
        
        # Framework statistics
        total_frameworks = len(self._frameworks)
        published_frameworks = sum(
            1 for f in self._frameworks.values() if f.status == KnowledgeStatus.PUBLISHED
        )
        avg_framework_success = (
            sum(f.success_rate for f in self._frameworks.values()) / total_frameworks
            if total_frameworks > 0 else 0.0
        )
        
        # Best practice statistics
        total_practices = len(self._best_practices)
        adopted_practices = sum(
            1 for p in self._best_practices.values() if p.adoption_count > 0
        )
        
        # Case study statistics
        total_case_studies = len(self._case_studies)
        referenced_case_studies = sum(
            1 for c in self._case_studies.values() if c.times_referenced > 0
        )
        
        # Contributing agents
        contributing_agents = set()
        contributing_agents.update(self._patterns_by_agent.keys())
        contributing_agents.update(self._frameworks_by_agent.keys())
        contributing_agents.update(self._practices_by_agent.keys())
        contributing_agents.update(self._case_studies_by_agent.keys())
        
        return {
            "total_patterns": total_patterns,
            "high_confidence_patterns": high_confidence_patterns,
            "validated_patterns": validated_patterns,
            "total_frameworks": total_frameworks,
            "published_frameworks": published_frameworks,
            "avg_framework_success_rate": avg_framework_success,
            "total_best_practices": total_practices,
            "adopted_practices": adopted_practices,
            "total_case_studies": total_case_studies,
            "referenced_case_studies": referenced_case_studies,
            "contributing_agents": len(contributing_agents),
            "total_knowledge_items": (
                total_patterns + total_frameworks + 
                total_practices + total_case_studies
            )
        }
