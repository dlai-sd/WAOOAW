"""
Constitutional Alignment Validator - L0/L1 compliance checks
Ensures every entity meets constitutional principles
"""

from typing import Dict, List, Any
from models.base_entity import BaseEntity
from core.exceptions import ConstitutionalAlignmentError


def validate_constitutional_alignment(entity: BaseEntity) -> Dict[str, Any]:
    """
    Validate entity against L0/L1 constitutional principles.
    
    L0 Checks (Foundational Governance):
    - L0-01: governance_agent_id present (governance chain exists)
    - L0-02: amendment_history tracked (all changes recorded)
    - L0-03: append-only enforced (no manual UPDATEs to past amendments)
    - L0-04: supersession chain preserved (entity evolution trackable)
    - L0-05: compliance gate possible (validation result exportable)
    
    L1 Checks (Specific Entity Rules):
    - Per entity type (Skill, JobRole, Team, Agent, Industry)
    
    Args:
        entity: BaseEntity instance to validate
        
    Returns:
        Dict with compliance status, checks, violations
        
    Raises:
        ConstitutionalAlignmentError: If critical violations found
        
    Example:
        >>> result = validate_constitutional_alignment(skill)
        >>> if not result["compliant"]:
        ...     raise ConstitutionalAlignmentError(result["violations"])
    """
    
    # Run entity's self-validation (returns basic L0 checks)
    compliance_result = entity.validate_self()
    
    violations = list(compliance_result.get("violations", []))
    checks = dict(compliance_result.get("checks", {}))
    
    # L1 specific checks based on entity type
    entity_type = getattr(entity, "entity_type", "Unknown")
    
    if entity_type == "Skill":
        l1_violations = _validate_skill(entity)
        violations.extend(l1_violations)
        checks["l1_skill_validation"] = len(l1_violations) == 0
    
    elif entity_type == "JobRole":
        l1_violations = _validate_job_role(entity)
        violations.extend(l1_violations)
        checks["l1_job_role_validation"] = len(l1_violations) == 0
    
    elif entity_type == "Team":
        l1_violations = _validate_team(entity)
        violations.extend(l1_violations)
        checks["l1_team_validation"] = len(l1_violations) == 0
    
    elif entity_type == "Agent":
        l1_violations = _validate_agent(entity)
        violations.extend(l1_violations)
        checks["l1_agent_validation"] = len(l1_violations) == 0
    
    elif entity_type == "Industry":
        l1_violations = _validate_industry(entity)
        violations.extend(l1_violations)
        checks["l1_industry_validation"] = len(l1_violations) == 0
    
    compliant = len(violations) == 0
    
    return {
        "compliant": compliant,
        "checks": checks,
        "violations": violations,
        "entity_type": entity_type,
    }


def _validate_skill(entity: BaseEntity) -> List[str]:
    """Validate Skill-specific rules."""
    violations = []
    
    # L1-SKILL-01: Name must be non-empty
    if not getattr(entity, "name", "").strip():
        violations.append("L1-SKILL-01: name is required and cannot be empty")
    
    # L1-SKILL-02: Description required
    if not getattr(entity, "description", "").strip():
        violations.append("L1-SKILL-02: description is required")
    
    # L1-SKILL-03: Category must be valid
    category = getattr(entity, "category", "")
    valid_categories = ["technical", "soft_skill", "domain_expertise", "certification"]
    if category not in valid_categories:
        violations.append(f"L1-SKILL-03: category must be one of {valid_categories}")
    
    return violations


def _validate_job_role(entity: BaseEntity) -> List[str]:
    """Validate JobRole-specific rules."""
    violations = []
    
    # L1-JOBROLE-01: Required skills must not be empty
    required_skills = getattr(entity, "required_skills", [])
    if not required_skills or len(required_skills) == 0:
        violations.append("L1-JOBROLE-01: required_skills cannot be empty")
    
    # L1-JOBROLE-02: Seniority level must be valid
    seniority = getattr(entity, "seniority_level", "")
    valid_seniorities = ["junior", "mid", "senior"]
    if seniority not in valid_seniorities:
        violations.append(f"L1-JOBROLE-02: seniority_level must be one of {valid_seniorities}")
    
    # L1-JOBROLE-03: Name must be non-empty
    if not getattr(entity, "name", "").strip():
        violations.append("L1-JOBROLE-03: name is required")
    
    return violations


def _validate_team(entity: BaseEntity) -> List[str]:
    """Validate Team-specific rules."""
    violations = []
    
    # L1-TEAM-01: Team must have at least one agent
    agents = getattr(entity, "agents", [])
    if not agents or len(agents) == 0:
        violations.append("L1-TEAM-01: team must have at least one agent")
    
    # L1-TEAM-02: JobRole must be set
    if not getattr(entity, "job_role_id", None):
        violations.append("L1-TEAM-02: job_role_id must be set")
    
    return violations


def _validate_agent(entity: BaseEntity) -> List[str]:
    """Validate Agent-specific rules."""
    violations = []
    
    # L1-AGENT-01: Skill must be set
    if not getattr(entity, "skill_id", None):
        violations.append("L1-AGENT-01: skill_id must be set")
    
    # L1-AGENT-02: JobRole must be set
    if not getattr(entity, "job_role_id", None):
        violations.append("L1-AGENT-02: job_role_id must be set")
    
    # L1-AGENT-03: Industry must be set
    if not getattr(entity, "industry_id", None):
        violations.append("L1-AGENT-03: industry_id must be set")
    
    return violations


def _validate_industry(entity: BaseEntity) -> List[str]:
    """Validate Industry-specific rules."""
    violations = []
    
    # L1-INDUSTRY-01: Name must be non-empty
    if not getattr(entity, "name", "").strip():
        violations.append("L1-INDUSTRY-01: name is required")
    
    return violations
