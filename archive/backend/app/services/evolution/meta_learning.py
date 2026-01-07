"""
Meta-Learning & Transfer Learning Engine - Story 5.6.4

Epic 5.6: Self-Evolving Agent System

Agents learn how to learn more effectively, adapt quickly to new task types,
transfer knowledge across domains, and compose skills for novel problems.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Set
from collections import defaultdict


class LearningStrategy(Enum):
    """Types of learning strategies"""
    SUPERVISED = "supervised"         # Learn from examples
    EXPERIENTIAL = "experiential"     # Learn by doing
    OBSERVATIONAL = "observational"   # Learn from others
    REFLECTIVE = "reflective"         # Learn from reflection
    COLLABORATIVE = "collaborative"   # Learn with others


class DomainType(Enum):
    """Knowledge domains"""
    MARKETING = "marketing"
    EDUCATION = "education"
    SALES = "sales"
    CONTENT_CREATION = "content_creation"
    CUSTOMER_SERVICE = "customer_service"
    TECHNICAL = "technical"
    CREATIVE = "creative"
    ANALYTICAL = "analytical"


@dataclass
class LearningExperience:
    """Record of a learning experience"""
    experience_id: str
    agent_variant_id: str
    
    # What was learned
    task_type: str
    domain: DomainType
    skill_acquired: str
    strategy_used: LearningStrategy
    
    # Learning efficiency
    attempts_to_competence: int  # How many tries until competent
    time_to_competence_hours: float
    final_proficiency: float  # 0.0 to 1.0
    
    # Context
    prior_knowledge: List[str]  # Related skills already known
    transferred_from: Optional[str] = None  # Domain transferred from
    
    learned_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "experience_id": self.experience_id,
            "agent_variant_id": self.agent_variant_id,
            "task_type": self.task_type,
            "domain": self.domain.value,
            "skill_acquired": self.skill_acquired,
            "strategy_used": self.strategy_used.value,
            "attempts_to_competence": self.attempts_to_competence,
            "time_to_competence_hours": self.time_to_competence_hours,
            "final_proficiency": self.final_proficiency,
            "prior_knowledge": self.prior_knowledge,
            "transferred_from": self.transferred_from,
            "learned_at": self.learned_at.isoformat(),
        }


@dataclass
class TransferPath:
    """A path for transferring knowledge between domains"""
    transfer_id: str
    agent_variant_id: str
    
    # Transfer details
    source_domain: DomainType
    target_domain: DomainType
    transferable_skill: str
    
    # Effectiveness
    adaptation_required: str  # How to adapt the skill
    transfer_efficiency: float  # 0.0 to 1.0 (1.0 = perfect transfer)
    success_count: int  # Times successfully transferred
    
    identified_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "transfer_id": self.transfer_id,
            "agent_variant_id": self.agent_variant_id,
            "source_domain": self.source_domain.value,
            "target_domain": self.target_domain.value,
            "transferable_skill": self.transferable_skill,
            "adaptation_required": self.adaptation_required,
            "transfer_efficiency": self.transfer_efficiency,
            "success_count": self.success_count,
            "identified_at": self.identified_at.isoformat(),
        }


@dataclass
class SkillComposition:
    """Combination of skills for a complex task"""
    composition_id: str
    agent_variant_id: str
    
    # Composition details
    complex_task: str
    component_skills: List[str]  # Skills that combine
    composition_strategy: str  # How skills are combined
    
    # Effectiveness
    success_rate: float  # 0.0 to 1.0
    times_applied: int
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "composition_id": self.composition_id,
            "agent_variant_id": self.agent_variant_id,
            "complex_task": self.complex_task,
            "component_skills": self.component_skills,
            "composition_strategy": self.composition_strategy,
            "success_rate": self.success_rate,
            "times_applied": self.times_applied,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class MetaLearningInsight:
    """Insight about learning itself"""
    insight_id: str
    agent_variant_id: str
    
    # Insight details
    insight_type: str  # e.g., "optimal_strategy", "common_mistake", "efficiency_factor"
    description: str
    evidence: List[str]  # Experience IDs supporting this insight
    
    # Application
    applicable_contexts: List[str]
    recommended_action: str
    impact_on_learning_speed: float  # Multiplier (1.5 = 50% faster)
    
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "insight_id": self.insight_id,
            "agent_variant_id": self.agent_variant_id,
            "insight_type": self.insight_type,
            "description": self.description,
            "evidence": self.evidence,
            "applicable_contexts": self.applicable_contexts,
            "recommended_action": self.recommended_action,
            "impact_on_learning_speed": self.impact_on_learning_speed,
            "discovered_at": self.discovered_at.isoformat(),
        }


class MetaLearningEngine:
    """
    Meta-learning and transfer learning system.
    
    Enables agents to optimize their learning processes, transfer knowledge
    across domains, and compose skills for novel problems.
    """
    
    def __init__(self):
        self._experiences: Dict[str, LearningExperience] = {}
        self._transfer_paths: Dict[str, TransferPath] = {}
        self._compositions: Dict[str, SkillComposition] = {}
        self._insights: Dict[str, MetaLearningInsight] = {}
        
        # Indexing
        self._experiences_by_agent: Dict[str, List[str]] = defaultdict(list)
        self._experiences_by_domain: Dict[DomainType, List[str]] = defaultdict(list)
        self._experiences_by_strategy: Dict[LearningStrategy, List[str]] = defaultdict(list)
        
        self._transfer_paths_by_agent: Dict[str, List[str]] = defaultdict(list)
        self._compositions_by_agent: Dict[str, List[str]] = defaultdict(list)
        self._insights_by_agent: Dict[str, List[str]] = defaultdict(list)
    
    def record_learning_experience(
        self,
        agent_variant_id: str,
        task_type: str,
        domain: DomainType,
        skill_acquired: str,
        strategy_used: LearningStrategy,
        attempts_to_competence: int,
        time_to_competence_hours: float,
        prior_knowledge: List[str]
    ) -> LearningExperience:
        """
        Record a learning experience.
        """
        experience_id = f"exp_{agent_variant_id}_{datetime.utcnow().timestamp()}"
        
        # Calculate final proficiency based on attempts and time
        # Fewer attempts and less time = higher proficiency
        base_proficiency = 0.6
        attempt_bonus = max(0, (10 - attempts_to_competence) * 0.03)  # Up to +0.30
        time_bonus = max(0, (20 - time_to_competence_hours) * 0.01)  # Up to +0.20
        final_proficiency = min(1.0, base_proficiency + attempt_bonus + time_bonus)
        
        experience = LearningExperience(
            experience_id=experience_id,
            agent_variant_id=agent_variant_id,
            task_type=task_type,
            domain=domain,
            skill_acquired=skill_acquired,
            strategy_used=strategy_used,
            attempts_to_competence=attempts_to_competence,
            time_to_competence_hours=time_to_competence_hours,
            final_proficiency=final_proficiency,
            prior_knowledge=prior_knowledge
        )
        
        self._experiences[experience_id] = experience
        self._experiences_by_agent[agent_variant_id].append(experience_id)
        self._experiences_by_domain[domain].append(experience_id)
        self._experiences_by_strategy[strategy_used].append(experience_id)
        
        return experience
    
    def analyze_learning_efficiency(self, agent_variant_id: str) -> Dict[str, Any]:
        """
        Analyze how efficiently the agent learns.
        """
        exp_ids = self._experiences_by_agent[agent_variant_id]
        if not exp_ids:
            return {"has_data": False}
        
        experiences = [self._experiences[eid] for eid in exp_ids]
        
        # Calculate metrics
        avg_attempts = sum(e.attempts_to_competence for e in experiences) / len(experiences)
        avg_time = sum(e.time_to_competence_hours for e in experiences) / len(experiences)
        avg_proficiency = sum(e.final_proficiency for e in experiences) / len(experiences)
        
        # Identify most effective strategy
        strategy_effectiveness = defaultdict(list)
        for exp in experiences:
            strategy_effectiveness[exp.strategy_used].append(exp.final_proficiency)
        
        best_strategy = max(
            strategy_effectiveness.items(),
            key=lambda x: sum(x[1]) / len(x[1]) if x[1] else 0
        )[0] if strategy_effectiveness else None
        
        # Identify fast vs slow learning areas
        domain_speed = defaultdict(list)
        for exp in experiences:
            domain_speed[exp.domain].append(exp.time_to_competence_hours)
        
        fast_domains = [
            domain for domain, times in domain_speed.items()
            if sum(times) / len(times) < avg_time
        ]
        
        return {
            "has_data": True,
            "total_skills_learned": len(experiences),
            "avg_attempts_to_competence": avg_attempts,
            "avg_time_to_competence_hours": avg_time,
            "avg_final_proficiency": avg_proficiency,
            "most_effective_strategy": best_strategy.value if best_strategy else None,
            "fast_learning_domains": [d.value for d in fast_domains],
            "learning_acceleration": max(0.5, 1.0 / max(1, avg_attempts / 5))  # Speed multiplier
        }
    
    def identify_transfer_opportunity(
        self,
        agent_variant_id: str,
        source_domain: DomainType,
        target_domain: DomainType,
        skill: str
    ) -> TransferPath:
        """
        Identify opportunity to transfer knowledge between domains.
        """
        transfer_id = f"transfer_{agent_variant_id}_{datetime.utcnow().timestamp()}"
        
        # Analyze similarity between domains
        transfer_efficiency = self._calculate_domain_similarity(source_domain, target_domain)
        
        # Determine adaptation needed
        adaptation = self._determine_adaptation(source_domain, target_domain, skill)
        
        transfer_path = TransferPath(
            transfer_id=transfer_id,
            agent_variant_id=agent_variant_id,
            source_domain=source_domain,
            target_domain=target_domain,
            transferable_skill=skill,
            adaptation_required=adaptation,
            transfer_efficiency=transfer_efficiency,
            success_count=0
        )
        
        self._transfer_paths[transfer_id] = transfer_path
        self._transfer_paths_by_agent[agent_variant_id].append(transfer_id)
        
        return transfer_path
    
    def _calculate_domain_similarity(
        self,
        domain1: DomainType,
        domain2: DomainType
    ) -> float:
        """Calculate similarity between domains (0-1)"""
        if domain1 == domain2:
            return 1.0
        
        # Domain similarity matrix (simplified)
        similarities = {
            (DomainType.MARKETING, DomainType.SALES): 0.7,
            (DomainType.MARKETING, DomainType.CONTENT_CREATION): 0.6,
            (DomainType.SALES, DomainType.CUSTOMER_SERVICE): 0.65,
            (DomainType.CONTENT_CREATION, DomainType.CREATIVE): 0.75,
            (DomainType.TECHNICAL, DomainType.ANALYTICAL): 0.7,
            (DomainType.EDUCATION, DomainType.CONTENT_CREATION): 0.6,
        }
        
        # Check both directions
        key1 = (domain1, domain2)
        key2 = (domain2, domain1)
        
        return similarities.get(key1, similarities.get(key2, 0.4))  # Default 0.4 similarity
    
    def _determine_adaptation(
        self,
        source_domain: DomainType,
        target_domain: DomainType,
        skill: str
    ) -> str:
        """Determine how to adapt skill for new domain"""
        if source_domain == DomainType.MARKETING and target_domain == DomainType.SALES:
            return "Adapt messaging from broad audience to 1-on-1 conversations"
        elif source_domain == DomainType.SALES and target_domain == DomainType.CUSTOMER_SERVICE:
            return "Shift from persuasion to problem-solving focus"
        elif source_domain == DomainType.CONTENT_CREATION and target_domain == DomainType.EDUCATION:
            return "Add more structure and learning objectives"
        else:
            return f"Apply {skill} principles with domain-specific context"
    
    def execute_transfer(
        self,
        transfer_id: str,
        success: bool
    ) -> bool:
        """Record the result of executing a transfer"""
        if transfer_id not in self._transfer_paths:
            return False
        
        transfer = self._transfer_paths[transfer_id]
        
        if success:
            transfer.success_count += 1
            # Improve efficiency with successful transfers
            transfer.transfer_efficiency = min(1.0, transfer.transfer_efficiency + 0.05)
        else:
            # Reduce efficiency with failures
            transfer.transfer_efficiency = max(0.1, transfer.transfer_efficiency - 0.1)
        
        return True
    
    def compose_skills(
        self,
        agent_variant_id: str,
        complex_task: str,
        component_skills: List[str],
        composition_strategy: str
    ) -> SkillComposition:
        """
        Create a composition of skills for a complex task.
        """
        composition_id = f"comp_{agent_variant_id}_{datetime.utcnow().timestamp()}"
        
        composition = SkillComposition(
            composition_id=composition_id,
            agent_variant_id=agent_variant_id,
            complex_task=complex_task,
            component_skills=component_skills,
            composition_strategy=composition_strategy,
            success_rate=0.0,
            times_applied=0
        )
        
        self._compositions[composition_id] = composition
        self._compositions_by_agent[agent_variant_id].append(composition_id)
        
        return composition
    
    def record_composition_result(
        self,
        composition_id: str,
        success: bool
    ) -> bool:
        """Record the result of applying a skill composition"""
        if composition_id not in self._compositions:
            return False
        
        composition = self._compositions[composition_id]
        composition.times_applied += 1
        
        # Update success rate
        if success:
            composition.success_rate = (
                (composition.success_rate * (composition.times_applied - 1) + 1.0) / 
                composition.times_applied
            )
        else:
            composition.success_rate = (
                (composition.success_rate * (composition.times_applied - 1)) / 
                composition.times_applied
            )
        
        return True
    
    def discover_meta_insight(
        self,
        agent_variant_id: str,
        insight_type: str,
        description: str,
        evidence_experience_ids: List[str],
        applicable_contexts: List[str],
        recommended_action: str,
        impact_multiplier: float
    ) -> MetaLearningInsight:
        """
        Discover an insight about learning itself.
        """
        insight_id = f"insight_{agent_variant_id}_{datetime.utcnow().timestamp()}"
        
        insight = MetaLearningInsight(
            insight_id=insight_id,
            agent_variant_id=agent_variant_id,
            insight_type=insight_type,
            description=description,
            evidence=evidence_experience_ids,
            applicable_contexts=applicable_contexts,
            recommended_action=recommended_action,
            impact_on_learning_speed=impact_multiplier
        )
        
        self._insights[insight_id] = insight
        self._insights_by_agent[agent_variant_id].append(insight_id)
        
        return insight
    
    def get_optimal_learning_strategy(
        self,
        agent_variant_id: str,
        target_domain: DomainType
    ) -> Dict[str, Any]:
        """
        Recommend optimal learning strategy for a domain.
        """
        exp_ids = self._experiences_by_agent[agent_variant_id]
        
        if not exp_ids:
            # Default recommendation
            return {
                "recommended_strategy": LearningStrategy.EXPERIENTIAL.value,
                "reason": "No learning history - start with hands-on practice",
                "expected_efficiency": 0.7
            }
        
        # Find experiences in this domain
        domain_experiences = [
            self._experiences[eid] for eid in exp_ids
            if self._experiences[eid].domain == target_domain
        ]
        
        if domain_experiences:
            # Find best strategy used in this domain
            strategy_results = defaultdict(list)
            for exp in domain_experiences:
                strategy_results[exp.strategy_used].append({
                    "attempts": exp.attempts_to_competence,
                    "time": exp.time_to_competence_hours,
                    "proficiency": exp.final_proficiency
                })
            
            best_strategy = max(
                strategy_results.items(),
                key=lambda x: sum(r["proficiency"] for r in x[1]) / len(x[1])
            )[0]
            
            avg_efficiency = sum(r["proficiency"] for r in strategy_results[best_strategy]) / len(strategy_results[best_strategy])
            
            return {
                "recommended_strategy": best_strategy.value,
                "reason": f"Best results in {target_domain.value} domain",
                "expected_efficiency": avg_efficiency
            }
        else:
            # Look for transfer opportunities
            similar_domains = [
                domain for domain in DomainType
                if self._calculate_domain_similarity(domain, target_domain) > 0.6
            ]
            
            # Find best strategy in similar domains
            all_experiences = [self._experiences[eid] for eid in exp_ids]
            similar_exp = [
                exp for exp in all_experiences
                if exp.domain in similar_domains
            ]
            
            if similar_exp:
                strategy_results = defaultdict(list)
                for exp in similar_exp:
                    strategy_results[exp.strategy_used].append(exp.final_proficiency)
                
                best_strategy = max(
                    strategy_results.items(),
                    key=lambda x: sum(x[1]) / len(x[1])
                )[0]
                
                return {
                    "recommended_strategy": best_strategy.value,
                    "reason": f"Successful in similar domains",
                    "expected_efficiency": 0.8
                }
            else:
                return {
                    "recommended_strategy": LearningStrategy.OBSERVATIONAL.value,
                    "reason": "Learn from experts in new domain",
                    "expected_efficiency": 0.75
                }
    
    def get_transfer_recommendations(
        self,
        agent_variant_id: str,
        target_domain: DomainType
    ) -> List[Dict[str, Any]]:
        """
        Recommend skills that can be transferred to target domain.
        """
        exp_ids = self._experiences_by_agent[agent_variant_id]
        
        if not exp_ids:
            return []
        
        experiences = [self._experiences[eid] for eid in exp_ids]
        
        # Find skills from other domains
        recommendations = []
        for exp in experiences:
            if exp.domain != target_domain:
                similarity = self._calculate_domain_similarity(exp.domain, target_domain)
                
                if similarity > 0.5:  # Worth transferring
                    recommendations.append({
                        "skill": exp.skill_acquired,
                        "from_domain": exp.domain.value,
                        "transfer_efficiency": similarity,
                        "proficiency_in_source": exp.final_proficiency,
                        "expected_proficiency_in_target": exp.final_proficiency * similarity
                    })
        
        # Sort by expected proficiency in target
        recommendations.sort(key=lambda x: x["expected_proficiency_in_target"], reverse=True)
        
        return recommendations[:5]  # Top 5 recommendations
    
    def get_agent_meta_profile(self, agent_variant_id: str) -> Dict[str, Any]:
        """
        Get comprehensive meta-learning profile for an agent.
        """
        learning_efficiency = self.analyze_learning_efficiency(agent_variant_id)
        
        # Count experiences, transfers, compositions, insights
        num_experiences = len(self._experiences_by_agent[agent_variant_id])
        num_transfers = len(self._transfer_paths_by_agent[agent_variant_id])
        num_compositions = len(self._compositions_by_agent[agent_variant_id])
        num_insights = len(self._insights_by_agent[agent_variant_id])
        
        # Calculate transfer success rate
        transfers = [
            self._transfer_paths[tid]
            for tid in self._transfer_paths_by_agent[agent_variant_id]
        ]
        avg_transfer_efficiency = (
            sum(t.transfer_efficiency for t in transfers) / len(transfers)
            if transfers else 0.0
        )
        
        # Calculate composition success rate
        compositions = [
            self._compositions[cid]
            for cid in self._compositions_by_agent[agent_variant_id]
        ]
        avg_composition_success = (
            sum(c.success_rate for c in compositions) / len(compositions)
            if compositions else 0.0
        )
        
        return {
            "agent_variant_id": agent_variant_id,
            "learning_efficiency": learning_efficiency,
            "total_learning_experiences": num_experiences,
            "transfer_paths_discovered": num_transfers,
            "avg_transfer_efficiency": avg_transfer_efficiency,
            "skill_compositions_created": num_compositions,
            "avg_composition_success_rate": avg_composition_success,
            "meta_insights_discovered": num_insights,
            "meta_learning_maturity": self._calculate_maturity(
                num_experiences, num_transfers, num_compositions, num_insights
            )
        }
    
    def _calculate_maturity(
        self,
        experiences: int,
        transfers: int,
        compositions: int,
        insights: int
    ) -> str:
        """Calculate meta-learning maturity level"""
        score = experiences + (transfers * 2) + (compositions * 3) + (insights * 5)
        
        if score < 10:
            return "Novice"
        elif score < 30:
            return "Developing"
        elif score < 60:
            return "Proficient"
        elif score < 100:
            return "Advanced"
        else:
            return "Expert"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get engine-wide statistics"""
        total_experiences = len(self._experiences)
        total_transfers = len(self._transfer_paths)
        total_compositions = len(self._compositions)
        total_insights = len(self._insights)
        
        # Calculate averages
        avg_attempts = (
            sum(e.attempts_to_competence for e in self._experiences.values()) / total_experiences
            if total_experiences > 0 else 0
        )
        
        avg_proficiency = (
            sum(e.final_proficiency for e in self._experiences.values()) / total_experiences
            if total_experiences > 0 else 0
        )
        
        successful_transfers = sum(
            1 for t in self._transfer_paths.values() if t.success_count > 0
        )
        
        return {
            "total_learning_experiences": total_experiences,
            "total_transfer_paths": total_transfers,
            "successful_transfers": successful_transfers,
            "total_skill_compositions": total_compositions,
            "total_meta_insights": total_insights,
            "avg_attempts_to_competence": avg_attempts,
            "avg_final_proficiency": avg_proficiency,
            "contributing_agents": len(self._experiences_by_agent)
        }
