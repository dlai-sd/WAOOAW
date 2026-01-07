"""
Validation Pipeline - Quality checks before deployment

Runs multiple validation checks:
1. Architecture compliance (WowVision integration placeholder)
2. Pytest tests
3. Code linting (black, flake8, mypy)
4. Schema validation
5. Dependency checks

Story: #84 Validation Pipeline (3 pts)
Epic: #68 WowAgentFactory Core (v0.4.1)
Theme: CONCEIVE
"""

import logging
import subprocess
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

from waooaw.factory.config.schema import AgentSpecConfig, validate_agent_spec
from waooaw.factory.registry import AgentRegistry

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class ValidationLevel(Enum):
    """Validation severity level"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ValidationIssue:
    """Single validation issue"""
    level: ValidationLevel
    check: str
    message: str
    file: Optional[str] = None
    line: Optional[int] = None


@dataclass
class ValidationResult:
    """
    Result of validation pipeline.
    
    Attributes:
        passed: Whether validation passed
        agent_id: Agent identifier
        checks_run: Number of checks executed
        errors: List of error issues
        warnings: List of warning issues
        infos: List of info issues
    """
    passed: bool
    agent_id: str
    checks_run: int = 0
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    infos: List[ValidationIssue] = field(default_factory=list)
    
    @property
    def error_count(self) -> int:
        return len(self.errors)
    
    @property
    def warning_count(self) -> int:
        return len(self.warnings)
    
    @property
    def info_count(self) -> int:
        return len(self.infos)
    
    def add_issue(self, issue: ValidationIssue):
        """Add issue to result"""
        if issue.level == ValidationLevel.ERROR:
            self.errors.append(issue)
        elif issue.level == ValidationLevel.WARNING:
            self.warnings.append(issue)
        else:
            self.infos.append(issue)


# =============================================================================
# VALIDATOR
# =============================================================================

class Validator:
    """
    Validation pipeline for generated agents.
    
    Runs comprehensive quality checks before deployment.
    """
    
    def __init__(self):
        """Initialize validator"""
        self.registry = AgentRegistry()
        logger.info("✅ Validator initialized")
    
    # =========================================================================
    # VALIDATION CHECKS
    # =========================================================================
    
    def validate_spec(
        self,
        spec: AgentSpecConfig,
        result: ValidationResult
    ) -> None:
        """
        Validate agent specification.
        
        Args:
            spec: Agent specification
            result: Validation result to update
        """
        logger.info("  📋 Validating spec...")
        result.checks_run += 1
        
        spec_dict = spec.to_dict()
        is_valid, error = validate_agent_spec(spec_dict)
        
        if not is_valid:
            result.add_issue(ValidationIssue(
                level=ValidationLevel.ERROR,
                check="spec_validation",
                message=f"Invalid spec: {error}"
            ))
        else:
            result.add_issue(ValidationIssue(
                level=ValidationLevel.INFO,
                check="spec_validation",
                message="Spec validation passed"
            ))
    
    def validate_dependencies(
        self,
        spec: AgentSpecConfig,
        result: ValidationResult
    ) -> None:
        """
        Validate agent dependencies.
        
        Args:
            spec: Agent specification
            result: Validation result to update
        """
        logger.info("  🔗 Validating dependencies...")
        result.checks_run += 1
        
        for dep in spec.dependencies:
            agent = self.registry.get_agent(dep)
            if not agent:
                result.add_issue(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    check="dependency_check",
                    message=f"Missing dependency: {dep}"
                ))
            else:
                result.add_issue(ValidationIssue(
                    level=ValidationLevel.INFO,
                    check="dependency_check",
                    message=f"Dependency available: {dep}"
                ))
    
    def validate_pytest(
        self,
        test_file: Path,
        result: ValidationResult
    ) -> None:
        """
        Run pytest on test file.
        
        Args:
            test_file: Path to test file
            result: Validation result to update
        """
        logger.info("  🧪 Running pytest...")
        result.checks_run += 1
        
        if not test_file.exists():
            result.add_issue(ValidationIssue(
                level=ValidationLevel.WARNING,
                check="pytest",
                message=f"Test file not found: {test_file}",
                file=str(test_file)
            ))
            return
        
        try:
            proc = subprocess.run(
                ["pytest", str(test_file), "-v"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if proc.returncode == 0:
                result.add_issue(ValidationIssue(
                    level=ValidationLevel.INFO,
                    check="pytest",
                    message="All tests passed",
                    file=str(test_file)
                ))
            else:
                result.add_issue(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    check="pytest",
                    message=f"Tests failed:\n{proc.stdout}",
                    file=str(test_file)
                ))
                
        except FileNotFoundError:
            result.add_issue(ValidationIssue(
                level=ValidationLevel.WARNING,
                check="pytest",
                message="pytest not installed"
            ))
        except subprocess.TimeoutExpired:
            result.add_issue(ValidationIssue(
                level=ValidationLevel.ERROR,
                check="pytest",
                message="Tests timed out (>60s)"
            ))
        except Exception as e:
            result.add_issue(ValidationIssue(
                level=ValidationLevel.ERROR,
                check="pytest",
                message=f"pytest error: {e}"
            ))
    
    def validate_black(
        self,
        agent_file: Path,
        result: ValidationResult
    ) -> None:
        """
        Check code formatting with black.
        
        Args:
            agent_file: Path to agent file
            result: Validation result to update
        """
        logger.info("  🎨 Checking formatting (black)...")
        result.checks_run += 1
        
        if not agent_file.exists():
            result.add_issue(ValidationIssue(
                level=ValidationLevel.WARNING,
                check="black",
                message=f"Agent file not found: {agent_file}",
                file=str(agent_file)
            ))
            return
        
        try:
            proc = subprocess.run(
                ["black", "--check", str(agent_file)],
                capture_output=True,
                text=True
            )
            
            if proc.returncode == 0:
                result.add_issue(ValidationIssue(
                    level=ValidationLevel.INFO,
                    check="black",
                    message="Code formatting OK",
                    file=str(agent_file)
                ))
            else:
                result.add_issue(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    check="black",
                    message="Code needs formatting (run: black <file>)",
                    file=str(agent_file)
                ))
                
        except FileNotFoundError:
            result.add_issue(ValidationIssue(
                level=ValidationLevel.INFO,
                check="black",
                message="black not installed (optional)"
            ))
    
    def validate_flake8(
        self,
        agent_file: Path,
        result: ValidationResult
    ) -> None:
        """
        Check code style with flake8.
        
        Args:
            agent_file: Path to agent file
            result: Validation result to update
        """
        logger.info("  📏 Checking style (flake8)...")
        result.checks_run += 1
        
        if not agent_file.exists():
            return
        
        try:
            proc = subprocess.run(
                ["flake8", str(agent_file), "--max-line-length=100"],
                capture_output=True,
                text=True
            )
            
            if proc.returncode == 0:
                result.add_issue(ValidationIssue(
                    level=ValidationLevel.INFO,
                    check="flake8",
                    message="Code style OK",
                    file=str(agent_file)
                ))
            else:
                result.add_issue(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    check="flake8",
                    message=f"Style issues:\n{proc.stdout}",
                    file=str(agent_file)
                ))
                
        except FileNotFoundError:
            result.add_issue(ValidationIssue(
                level=ValidationLevel.INFO,
                check="flake8",
                message="flake8 not installed (optional)"
            ))
    
    def validate_wowvision(
        self,
        spec: AgentSpecConfig,
        agent_file: Path,
        result: ValidationResult
    ) -> None:
        """
        Run WowVision architecture validation (placeholder).
        
        Args:
            spec: Agent specification
            agent_file: Path to agent file
            result: Validation result to update
        """
        logger.info("  👁️  Running WowVision checks...")
        result.checks_run += 1
        
        # TODO: Integrate with actual WowVision Prime agent
        # For now, perform basic checks
        
        # Check 1: Tier consistency
        if spec.tier < 1 or spec.tier > 6:
            result.add_issue(ValidationIssue(
                level=ValidationLevel.ERROR,
                check="wowvision_tier",
                message=f"Invalid tier: {spec.tier} (must be 1-6)"
            ))
        
        # Check 2: Dependency order (higher tiers depend on lower)
        for dep in spec.dependencies:
            dep_agent = self.registry.get_agent(dep)
            if dep_agent and dep_agent.tier.value > spec.tier:
                result.add_issue(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    check="wowvision_dependency_order",
                    message=f"Tier violation: {spec.coe_name} (tier {spec.tier}) depends on {dep} (tier {dep_agent.tier.value})"
                ))
        
        # Check 3: Base template inheritance
        if agent_file.exists():
            content = agent_file.read_text()
            if "BasePlatformCoE" not in content:
                result.add_issue(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    check="wowvision_inheritance",
                    message="Must inherit from BasePlatformCoE",
                    file=str(agent_file)
                ))
        
        result.add_issue(ValidationIssue(
            level=ValidationLevel.INFO,
            check="wowvision",
            message="Basic architecture checks passed"
        ))
    
    # =========================================================================
    # PIPELINE
    # =========================================================================
    
    def validate(
        self,
        spec: AgentSpecConfig,
        agent_file: Path,
        test_file: Optional[Path] = None
    ) -> ValidationResult:
        """
        Run full validation pipeline.
        
        Args:
            spec: Agent specification
            agent_file: Path to generated agent file
            test_file: Path to test file (optional)
        
        Returns:
            Validation result
        """
        logger.info(f"🔍 Validating {spec.coe_name}...")
        
        result = ValidationResult(
            passed=True,  # Assume pass, set to False if errors
            agent_id=spec.coe_name
        )
        
        # Run checks
        self.validate_spec(spec, result)
        self.validate_dependencies(spec, result)
        self.validate_wowvision(spec, agent_file, result)
        
        if agent_file.exists():
            self.validate_black(agent_file, result)
            self.validate_flake8(agent_file, result)
        
        if test_file and test_file.exists():
            self.validate_pytest(test_file, result)
        
        # Determine pass/fail
        result.passed = (result.error_count == 0)
        
        # Log summary
        if result.passed:
            logger.info(f"✅ Validation passed: {spec.coe_name} ({result.checks_run} checks, {result.warning_count} warnings)")
        else:
            logger.error(f"❌ Validation failed: {spec.coe_name} ({result.error_count} errors, {result.warning_count} warnings)")
        
        return result
    
    def print_result(self, result: ValidationResult) -> None:
        """Print validation result to console"""
        print(f"\n{'='*60}")
        print(f"Validation Result: {result.agent_id}")
        print(f"{'='*60}")
        print(f"Status: {'✅ PASS' if result.passed else '❌ FAIL'}")
        print(f"Checks Run: {result.checks_run}")
        print(f"Errors: {result.error_count}")
        print(f"Warnings: {result.warning_count}")
        print(f"Info: {result.info_count}")
        
        if result.errors:
            print(f"\n{'─'*60}")
            print("ERRORS:")
            for issue in result.errors:
                print(f"  ❌ [{issue.check}] {issue.message}")
                if issue.file:
                    print(f"     File: {issue.file}")
        
        if result.warnings:
            print(f"\n{'─'*60}")
            print("WARNINGS:")
            for issue in result.warnings:
                print(f"  ⚠️  [{issue.check}] {issue.message}")
        
        print(f"{'='*60}\n")


# =============================================================================
# USAGE EXAMPLES
# =============================================================================

"""
Example: Using Validator

```python
from waooaw.factory.validation import Validator
from waooaw.factory.config.schema import AgentSpecConfig, AgentDomain
from pathlib import Path

# Create spec
spec = AgentSpecConfig(
    coe_name="WowExample",
    display_name="WowExample",
    tier=3,
    domain=AgentDomain.COMMUNICATION,
    version="0.4.2",
    description="Example agent",
    capabilities={"messaging": ["send", "receive"]},
    dependencies=["WowAgentFactory"],
    wake_patterns=["example.*"],
    resource_budget=30.0
)

# Validate
validator = Validator()
result = validator.validate(
    spec=spec,
    agent_file=Path("waooaw/agents/wowexample.py"),
    test_file=Path("tests/factory/test_wowexample.py")
)

# Print result
validator.print_result(result)

# Check result
if result.passed:
    print("✅ Ready for deployment")
else:
    print(f"❌ Fix {result.error_count} errors before deploying")
```
"""
