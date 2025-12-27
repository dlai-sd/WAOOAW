"""
WAOOAW Common Components: Validator

Provides schema validation, business rule validation, and connectivity checks.

Usage:
    # Schema validation:
    validator = Validator()
    validator.add_schema("decision", decision_schema)
    is_valid = validator.validate_schema("decision", data)
    
    # Business rules:
    validator.add_rule("priority_check", lambda x: x['priority'] in ['low', 'medium', 'high'])
    is_valid = validator.validate_rules("priority_check", data)
    
    # Connectivity:
    is_healthy = validator.check_connectivity("database", db_check_fn)

Vision Compliance:
    ✅ Zero Risk: Validate before execution, catch errors early
    ✅ Agentic: Agent-specific validation rules
    ✅ Simplicity: Declarative schemas, reusable rules
"""

import logging
from typing import Any, Dict, Callable, Optional, List, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """
    Validation result.
    
    Attributes:
        valid: Whether validation passed
        errors: List of error messages
        warnings: List of warning messages
        data: Validated data (potentially transformed)
    """
    valid: bool
    errors: List[str]
    warnings: List[str] = None
    data: Optional[Any] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class Validator:
    """
    Schema validation, business rule validation, and connectivity checks.
    
    Features:
    - JSON schema validation
    - Custom business rules
    - Type checking
    - Range validation
    - Format validation (email, URL, etc.)
    - Connectivity checks
    - Health checks
    
    Example:
        validator = Validator()
        
        # Schema validation:
        schema = {
            'type': 'object',
            'required': ['name', 'priority'],
            'properties': {
                'name': {'type': 'string'},
                'priority': {'type': 'string', 'enum': ['low', 'medium', 'high']}
            }
        }
        validator.add_schema("task", schema)
        result = validator.validate_schema("task", data)
        
        # Business rules:
        validator.add_rule("cost_check", lambda x: x.get('cost', 0) <= 100)
        result = validator.validate_rules("cost_check", data)
        
        # Connectivity:
        def check_db():
            return db.is_connected()
        
        validator.add_connectivity_check("database", check_db)
        is_healthy = validator.check_connectivity("database")
    """
    
    def __init__(self):
        """Initialize validator."""
        self._schemas: Dict[str, Dict[str, Any]] = {}
        self._rules: Dict[str, Callable] = {}
        self._connectivity_checks: Dict[str, Callable] = {}
        
        logger.info("Validator initialized")
    
    # Schema Validation
    
    def add_schema(self, name: str, schema: Dict[str, Any]):
        """
        Add JSON schema.
        
        Args:
            name: Schema name
            schema: JSON schema definition
        """
        self._schemas[name] = schema
        logger.debug(f"Schema added: {name}")
    
    def validate_schema(
        self,
        schema_name: str,
        data: Any,
        strict: bool = True
    ) -> ValidationResult:
        """
        Validate data against schema.
        
        Args:
            schema_name: Schema name
            data: Data to validate
            strict: Strict mode (fail on warnings)
            
        Returns:
            ValidationResult
        """
        schema = self._schemas.get(schema_name)
        
        if not schema:
            return ValidationResult(
                valid=False,
                errors=[f"Schema '{schema_name}' not found"]
            )
        
        errors = []
        warnings = []
        
        # Type validation
        expected_type = schema.get('type')
        if expected_type:
            if not self._check_type(data, expected_type):
                errors.append(f"Expected type '{expected_type}', got '{type(data).__name__}'")
                return ValidationResult(valid=False, errors=errors)
        
        # Object validation
        if expected_type == 'object' and isinstance(data, dict):
            result = self._validate_object(data, schema, strict)
            errors.extend(result.errors)
            warnings.extend(result.warnings)
        
        # Array validation
        elif expected_type == 'array' and isinstance(data, list):
            result = self._validate_array(data, schema, strict)
            errors.extend(result.errors)
            warnings.extend(result.warnings)
        
        valid = len(errors) == 0 and (not strict or len(warnings) == 0)
        
        return ValidationResult(
            valid=valid,
            errors=errors,
            warnings=warnings,
            data=data
        )
    
    def _validate_object(
        self,
        data: Dict[str, Any],
        schema: Dict[str, Any],
        strict: bool
    ) -> ValidationResult:
        """Validate object against schema."""
        errors = []
        warnings = []
        
        # Required fields
        required = schema.get('required', [])
        for field in required:
            if field not in data:
                errors.append(f"Required field '{field}' missing")
        
        # Properties
        properties = schema.get('properties', {})
        for field, value in data.items():
            if field in properties:
                prop_schema = properties[field]
                
                # Type check
                expected_type = prop_schema.get('type')
                if expected_type and not self._check_type(value, expected_type):
                    errors.append(
                        f"Field '{field}': expected type '{expected_type}', "
                        f"got '{type(value).__name__}'"
                    )
                    continue
                
                # Enum check
                enum = prop_schema.get('enum')
                if enum and value not in enum:
                    errors.append(f"Field '{field}': value must be one of {enum}")
                
                # Range check
                minimum = prop_schema.get('minimum')
                if minimum is not None and value < minimum:
                    errors.append(f"Field '{field}': value must be >= {minimum}")
                
                maximum = prop_schema.get('maximum')
                if maximum is not None and value > maximum:
                    errors.append(f"Field '{field}': value must be <= {maximum}")
                
                # Pattern check
                pattern = prop_schema.get('pattern')
                if pattern and isinstance(value, str):
                    import re
                    if not re.match(pattern, value):
                        errors.append(f"Field '{field}': does not match pattern '{pattern}'")
                
                # Format check
                format_type = prop_schema.get('format')
                if format_type:
                    format_errors = self._check_format(value, format_type)
                    errors.extend([f"Field '{field}': {err}" for err in format_errors])
            
            elif strict:
                warnings.append(f"Unknown field '{field}'")
        
        return ValidationResult(valid=len(errors)==0, errors=errors, warnings=warnings)
    
    def _validate_array(
        self,
        data: List[Any],
        schema: Dict[str, Any],
        strict: bool
    ) -> ValidationResult:
        """Validate array against schema."""
        errors = []
        warnings = []
        
        # Min/max items
        min_items = schema.get('minItems')
        if min_items is not None and len(data) < min_items:
            errors.append(f"Array must have at least {min_items} items")
        
        max_items = schema.get('maxItems')
        if max_items is not None and len(data) > max_items:
            errors.append(f"Array must have at most {max_items} items")
        
        # Item validation
        items_schema = schema.get('items')
        if items_schema:
            for i, item in enumerate(data):
                expected_type = items_schema.get('type')
                if expected_type and not self._check_type(item, expected_type):
                    errors.append(
                        f"Item {i}: expected type '{expected_type}', "
                        f"got '{type(item).__name__}'"
                    )
        
        return ValidationResult(valid=len(errors)==0, errors=errors, warnings=warnings)
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type."""
        type_map = {
            'string': str,
            'number': (int, float),
            'integer': int,
            'boolean': bool,
            'array': list,
            'object': dict,
            'null': type(None)
        }
        
        expected_python_type = type_map.get(expected_type)
        if not expected_python_type:
            return True
        
        return isinstance(value, expected_python_type)
    
    def _check_format(self, value: str, format_type: str) -> List[str]:
        """Check if value matches format."""
        import re
        
        errors = []
        
        if format_type == 'email':
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(pattern, value):
                errors.append("invalid email format")
        
        elif format_type == 'url':
            pattern = r'^https?://[^\s/$.?#].[^\s]*$'
            if not re.match(pattern, value):
                errors.append("invalid URL format")
        
        elif format_type == 'uuid':
            pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
            if not re.match(pattern, value.lower()):
                errors.append("invalid UUID format")
        
        elif format_type == 'date':
            pattern = r'^\d{4}-\d{2}-\d{2}$'
            if not re.match(pattern, value):
                errors.append("invalid date format (expected YYYY-MM-DD)")
        
        elif format_type == 'datetime':
            pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*$'
            if not re.match(pattern, value):
                errors.append("invalid datetime format (expected ISO 8601)")
        
        return errors
    
    # Business Rules
    
    def add_rule(self, name: str, rule_fn: Callable[[Any], bool]):
        """
        Add business rule.
        
        Args:
            name: Rule name
            rule_fn: Function that returns True if valid
        """
        self._rules[name] = rule_fn
        logger.debug(f"Rule added: {name}")
    
    def validate_rules(
        self,
        rule_names: Union[str, List[str]],
        data: Any
    ) -> ValidationResult:
        """
        Validate data against business rules.
        
        Args:
            rule_names: Rule name or list of rule names
            data: Data to validate
            
        Returns:
            ValidationResult
        """
        if isinstance(rule_names, str):
            rule_names = [rule_names]
        
        errors = []
        
        for rule_name in rule_names:
            rule_fn = self._rules.get(rule_name)
            
            if not rule_fn:
                errors.append(f"Rule '{rule_name}' not found")
                continue
            
            try:
                if not rule_fn(data):
                    errors.append(f"Rule '{rule_name}' failed")
            except Exception as e:
                errors.append(f"Rule '{rule_name}' error: {str(e)}")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            data=data
        )
    
    # Connectivity Checks
    
    def add_connectivity_check(self, name: str, check_fn: Callable[[], bool]):
        """
        Add connectivity check.
        
        Args:
            name: Check name (e.g., "database", "redis", "llm")
            check_fn: Function that returns True if connected
        """
        self._connectivity_checks[name] = check_fn
        logger.debug(f"Connectivity check added: {name}")
    
    def check_connectivity(
        self,
        name: str,
        timeout: int = 5
    ) -> bool:
        """
        Check connectivity.
        
        Args:
            name: Check name
            timeout: Timeout in seconds
            
        Returns:
            True if connected
        """
        check_fn = self._connectivity_checks.get(name)
        
        if not check_fn:
            logger.warning(f"Connectivity check '{name}' not found")
            return False
        
        try:
            # TODO: Add timeout support
            result = check_fn()
            
            if result:
                logger.debug(f"Connectivity check passed: {name}")
            else:
                logger.warning(f"Connectivity check failed: {name}")
            
            return result
            
        except Exception as e:
            logger.error(f"Connectivity check error ({name}): {e}")
            return False
    
    def check_all_connectivity(self) -> Dict[str, bool]:
        """
        Check all connectivity checks.
        
        Returns:
            Dict mapping check name to result
        """
        results = {}
        
        for name in self._connectivity_checks:
            results[name] = self.check_connectivity(name)
        
        return results
    
    # Utilities
    
    def validate_all(
        self,
        data: Any,
        schema_name: Optional[str] = None,
        rule_names: Optional[List[str]] = None
    ) -> ValidationResult:
        """
        Validate data against schema and rules.
        
        Args:
            data: Data to validate
            schema_name: Optional schema name
            rule_names: Optional rule names
            
        Returns:
            Combined ValidationResult
        """
        all_errors = []
        all_warnings = []
        
        # Schema validation
        if schema_name:
            schema_result = self.validate_schema(schema_name, data)
            all_errors.extend(schema_result.errors)
            all_warnings.extend(schema_result.warnings)
        
        # Rule validation
        if rule_names:
            rule_result = self.validate_rules(rule_names, data)
            all_errors.extend(rule_result.errors)
        
        return ValidationResult(
            valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings,
            data=data
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get validator statistics.
        
        Returns:
            Dict with schema count, rule count, etc.
        """
        return {
            'schema_count': len(self._schemas),
            'rule_count': len(self._rules),
            'connectivity_check_count': len(self._connectivity_checks)
        }


# Pre-defined schemas for common types

DECISION_SCHEMA = {
    'type': 'object',
    'required': ['decision_type', 'context', 'timestamp'],
    'properties': {
        'decision_type': {'type': 'string'},
        'context': {'type': 'object'},
        'timestamp': {'type': 'string', 'format': 'datetime'},
        'confidence': {'type': 'number', 'minimum': 0.0, 'maximum': 1.0},
        'reasoning': {'type': 'string'}
    }
}

ESCALATION_SCHEMA = {
    'type': 'object',
    'required': ['agent_id', 'issue_type', 'description'],
    'properties': {
        'agent_id': {'type': 'string'},
        'issue_type': {'type': 'string', 'enum': ['technical', 'business', 'other']},
        'description': {'type': 'string'},
        'priority': {'type': 'string', 'enum': ['low', 'medium', 'high']},
        'metadata': {'type': 'object'}
    }
}

GITHUB_ISSUE_SCHEMA = {
    'type': 'object',
    'required': ['title', 'body'],
    'properties': {
        'title': {'type': 'string', 'minLength': 10, 'maxLength': 200},
        'body': {'type': 'string', 'minLength': 20},
        'labels': {'type': 'array', 'items': {'type': 'string'}},
        'assignees': {'type': 'array', 'items': {'type': 'string'}}
    }
}
