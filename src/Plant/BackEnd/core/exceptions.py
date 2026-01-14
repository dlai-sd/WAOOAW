"""
Custom domain exceptions for Plant backend
Used for business logic errors with clear semantics
"""


class PlantException(Exception):
    """Base exception for all Plant-specific errors."""
    pass


class ConstitutionalAlignmentError(PlantException):
    """
    Raised when entity fails L0/L1 constitutional alignment checks.
    
    Example:
        raise ConstitutionalAlignmentError(
            f"L0-02 violation: amendment_history not tracked for {entity_id}"
        )
    """
    pass


class HashChainBrokenError(PlantException):
    """
    Raised when audit trail hash chain is broken (tampering detected).
    
    Example:
        raise HashChainBrokenError(
            f"Hash chain broken: expected {expected_hash}, got {computed_hash}"
        )
    """
    pass


class AmendmentSignatureError(PlantException):
    """
    Raised when RSA signature verification fails.
    
    Example:
        raise AmendmentSignatureError(
            "RSA signature verification failed: data may have been tampered"
        )
    """
    pass


class EntityNotFoundError(PlantException):
    """
    Raised when entity is not found in database.
    
    Example:
        raise EntityNotFoundError(f"Skill {skill_id} not found")
    """
    pass


class DuplicateEntityError(PlantException):
    """
    Raised when attempting to create duplicate entity (unique constraint).
    
    Example:
        raise DuplicateEntityError(f"Skill with name '{name}' already exists")
    """
    pass


class ValidationError(PlantException):
    """
    Raised when entity validation fails.
    
    Example:
        raise ValidationError("JobRole must have at least one required skill")
    """
    pass


class ConstitutionalDriftError(PlantException):
    """
    Raised when entity drifts from constitutional principles.
    
    Example:
        raise ConstitutionalDriftError(
            f"Skill embedding stability {stability_score} < threshold {threshold}"
        )
    """
    pass


class SchemaEvolutionError(PlantException):
    """
    Raised when schema migration violates evolution rules.
    
    Example:
        raise SchemaEvolutionError("Breaking change without 3-gate approval")
    """
    pass


class CostGovernanceError(PlantException):
    """
    Raised when query would exceed customer budget.
    
    Example:
        raise CostGovernanceError(
            f"Query cost ${query_cost} exceeds budget ${remaining_budget}"
        )
    """
    pass
