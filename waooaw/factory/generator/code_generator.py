"""
Code Generator - Combines template + config + questionnaire

Orchestrates the full code generation pipeline:
1. Gather requirements (questionnaire)
2. Validate spec (config system)
3. Render code (template engine)
4. Write files (agent, tests, docs)

Story: #82 Code Generator (5 pts)
Epic: #68 WowAgentFactory Core (v0.4.1)
Theme: CONCEIVE
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional, List

from waooaw.factory.config.schema import AgentSpecConfig, validate_agent_spec
from waooaw.factory.config.parser import ConfigParser
from waooaw.factory.engine.template_engine import TemplateEngine
from waooaw.factory.questionnaire.questionnaire import Questionnaire

logger = logging.getLogger(__name__)


# =============================================================================
# CODE GENERATOR
# =============================================================================

class CodeGenerator:
    """
    Orchestrates full agent code generation pipeline.
    
    Pipeline:
    1. Requirements: Gather via questionnaire or load from YAML
    2. Validation: Validate spec against schema
    3. Rendering: Render code from Jinja2 templates
    4. Output: Write agent file, test file, config file
    
    Features:
    - Multiple input sources (questionnaire, YAML, dict)
    - Template-based generation
    - Automatic test generation
    - Config file export
    - Dry-run mode
    """
    
    def __init__(
        self,
        output_dir: Optional[Path] = None,
        template_dir: Optional[Path] = None
    ):
        """
        Initialize code generator.
        
        Args:
            output_dir: Directory for generated files
            template_dir: Directory containing templates
        """
        self.output_dir = output_dir or Path("waooaw/agents")
        self.template_dir = template_dir
        
        self.config_parser = ConfigParser()
        self.template_engine = TemplateEngine(template_dir)
        self.questionnaire = Questionnaire()
        
        logger.info(f"✅ CodeGenerator initialized (output: {self.output_dir})")
    
    # =========================================================================
    # GENERATION
    # =========================================================================
    
    def generate_from_questionnaire(
        self,
        initial_spec: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Generate agent from questionnaire.
        
        Args:
            initial_spec: Optional initial values
        
        Returns:
            dict: Generated files {filepath: content}
        """
        logger.info("📋 Generating from questionnaire...")
        
        # Run questionnaire
        if initial_spec:
            spec = self.questionnaire.run_with_initial(initial_spec)
        else:
            spec = self.questionnaire.run()
        
        # Generate code
        return self._generate_files(spec)
    
    def generate_from_yaml(self, yaml_path: Path) -> Dict[str, str]:
        """
        Generate agent from YAML config.
        
        Args:
            yaml_path: Path to YAML config file
        
        Returns:
            dict: Generated files {filepath: content}
        """
        logger.info(f"📄 Generating from YAML: {yaml_path}")
        
        # Load spec
        spec = self.config_parser.load_spec(yaml_path)
        if not spec:
            raise ValueError(f"Failed to load spec from {yaml_path}")
        
        # Generate code
        return self._generate_files(spec)
    
    def generate_from_dict(self, spec_dict: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate agent from dictionary.
        
        Args:
            spec_dict: Agent specification as dict
        
        Returns:
            dict: Generated files {filepath: content}
        """
        logger.info("📦 Generating from dict...")
        
        # Validate
        is_valid, error = validate_agent_spec(spec_dict)
        if not is_valid:
            raise ValueError(f"Invalid spec: {error}")
        
        # Create spec object
        spec = AgentSpecConfig.from_dict(spec_dict)
        
        # Generate code
        return self._generate_files(spec)
    
    def _generate_files(self, spec: AgentSpecConfig) -> Dict[str, str]:
        """
        Generate all files for agent.
        
        Args:
            spec: Agent specification
        
        Returns:
            dict: Generated files {filepath: content}
        """
        logger.info(f"🏗️  Generating files for {spec.coe_name}...")
        
        files = {}
        
        # 1. Agent code
        agent_code = self.template_engine.render_agent(spec)
        if agent_code:
            agent_file = f"{spec.coe_name.lower()}.py"
            files[agent_file] = agent_code
            logger.info(f"  ✅ Generated agent: {agent_file}")
        else:
            logger.error(f"  ❌ Failed to generate agent code")
        
        # 2. Test code
        test_code = self.template_engine.render_tests(spec)
        if test_code:
            test_file = f"test_{spec.coe_name.lower()}.py"
            files[test_file] = test_code
            logger.info(f"  ✅ Generated tests: {test_file}")
        
        # 3. Config YAML
        config_yaml = self._generate_config_yaml(spec)
        config_file = f"{spec.coe_name.lower()}_config.yaml"
        files[config_file] = config_yaml
        logger.info(f"  ✅ Generated config: {config_file}")
        
        # 4. README
        readme_md = self._generate_readme(spec)
        readme_file = f"{spec.coe_name}_README.md"
        files[readme_file] = readme_md
        logger.info(f"  ✅ Generated README: {readme_file}")
        
        logger.info(f"✅ Generated {len(files)} files for {spec.coe_name}")
        return files
    
    def _generate_config_yaml(self, spec: AgentSpecConfig) -> str:
        """Generate YAML config file"""
        import yaml
        spec_dict = spec.to_dict()
        return yaml.dump(spec_dict, default_flow_style=False, sort_keys=False)
    
    def _generate_readme(self, spec: AgentSpecConfig) -> str:
        """Generate README file"""
        return f"""# {spec.display_name}

{spec.description}

## Agent Details

- **Tier**: {spec.tier}
- **Domain**: {spec.domain.value}
- **Version**: {spec.version}
- **DID**: {spec.did if hasattr(spec, 'did') else 'TBD'}

## Capabilities

{self._format_capabilities(spec.capabilities)}

## Constraints

{self._format_constraints(spec.constraints)}

## Dependencies

{', '.join(spec.dependencies) if spec.dependencies else 'None'}

## Wake Patterns

{self._format_list(spec.wake_patterns)}

## Resource Budget

${spec.resource_budget:.2f}/month

## Generated

Generated by WowAgentFactory  
Theme: CONCEIVE  
Epic: Platform CoE
"""
    
    def _format_capabilities(self, capabilities: Dict[str, List[str]]) -> str:
        """Format capabilities for markdown"""
        if not capabilities:
            return "None"
        lines = []
        for category, caps in capabilities.items():
            lines.append(f"### {category.title()}")
            for cap in caps:
                lines.append(f"- {cap}")
        return "\n".join(lines)
    
    def _format_constraints(self, constraints: List[Dict[str, str]]) -> str:
        """Format constraints for markdown"""
        if not constraints:
            return "None"
        lines = []
        for constraint in constraints:
            lines.append(f"- **{constraint['rule']}**: {constraint['reason']}")
        return "\n".join(lines)
    
    def _format_list(self, items: List[str]) -> str:
        """Format list for markdown"""
        if not items:
            return "None"
        return "\n".join(f"- `{item}`" for item in items)
    
    # =========================================================================
    # OUTPUT
    # =========================================================================
    
    def write_files(
        self,
        files: Dict[str, str],
        dry_run: bool = False
    ) -> List[Path]:
        """
        Write generated files to disk.
        
        Args:
            files: Files to write {filename: content}
            dry_run: If True, don't write files
        
        Returns:
            List of written file paths
        """
        written_paths = []
        
        for filename, content in files.items():
            # Determine output path
            if filename.startswith("test_"):
                output_path = Path("tests/factory") / filename
            elif filename.endswith("_config.yaml"):
                output_path = Path("waooaw/factory/config/specs") / filename
            elif filename.endswith("_README.md"):
                output_path = Path("docs/agents") / filename
            else:
                output_path = self.output_dir / filename
            
            if dry_run:
                logger.info(f"  [DRY RUN] Would write: {output_path}")
                continue
            
            # Create parent directories
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            output_path.write_text(content, encoding="utf-8")
            written_paths.append(output_path)
            logger.info(f"  💾 Wrote: {output_path}")
        
        return written_paths
    
    def generate_and_write(
        self,
        spec_source: Any,
        source_type: str = "dict",
        dry_run: bool = False
    ) -> List[Path]:
        """
        Generate and write files in one call.
        
        Args:
            spec_source: Spec source (dict, Path, or None for questionnaire)
            source_type: "dict", "yaml", or "questionnaire"
            dry_run: If True, don't write files
        
        Returns:
            List of written file paths
        """
        # Generate files
        if source_type == "dict":
            files = self.generate_from_dict(spec_source)
        elif source_type == "yaml":
            files = self.generate_from_yaml(spec_source)
        elif source_type == "questionnaire":
            files = self.generate_from_questionnaire(spec_source)
        else:
            raise ValueError(f"Unknown source type: {source_type}")
        
        # Write files
        return self.write_files(files, dry_run=dry_run)


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def generate_agent(
    spec: Dict[str, Any],
    output_dir: Optional[Path] = None,
    dry_run: bool = False
) -> List[Path]:
    """
    Convenience function to generate agent from spec dict.
    
    Args:
        spec: Agent specification as dict
        output_dir: Output directory
        dry_run: If True, don't write files
    
    Returns:
        List of written file paths
    """
    generator = CodeGenerator(output_dir=output_dir)
    return generator.generate_and_write(spec, source_type="dict", dry_run=dry_run)


# =============================================================================
# USAGE EXAMPLES
# =============================================================================

"""
Example: Using CodeGenerator

```python
from waooaw.factory.generator import CodeGenerator, generate_agent
from pathlib import Path

# Example 1: Generate from dict
spec = {
    "coe_name": "WowExample",
    "display_name": "WowExample",
    "tier": 3,
    "domain": "communication",
    "version": "0.4.2",
    "description": "Example agent for testing",
    "capabilities": {"messaging": ["can:send", "can:receive"]},
    "constraints": [],
    "dependencies": ["WowAgentFactory"],
    "wake_patterns": ["example.*"],
    "resource_budget": 30.0
}

files = generate_agent(spec, dry_run=True)
print(f"Generated {len(files)} files")

# Example 2: Generate from YAML
generator = CodeGenerator()
files = generator.generate_from_yaml(Path("config/specs/wowdomain.yaml"))

# Example 3: Generate from questionnaire
generator = CodeGenerator()
initial = {"coe_name": "WowExample", "tier": 3}
files = generator.generate_from_questionnaire(initial_spec=initial)

# Example 4: Generate and write
generator = CodeGenerator(output_dir=Path("generated"))
paths = generator.generate_and_write(spec, source_type="dict")
print(f"Written: {paths}")
```
"""
