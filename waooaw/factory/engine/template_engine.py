"""
Template Engine - Jinja2-based code generation

Renders agent code from templates using configuration data.

Story: #79 Template Engine (3 pts)
Epic: #68 WowAgentFactory Core (v0.4.1)
Theme: CONCEIVE
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional
from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound

from waooaw.factory.config.schema import AgentSpecConfig

logger = logging.getLogger(__name__)


class TemplateEngine:
    """
    Jinja2-based template engine for agent code generation.
    
    Features:
    - Template inheritance
    - Custom filters and functions
    - Macro support
    - Auto-escaping disabled (Python code generation)
    """
    
    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize template engine.
        
        Args:
            template_dir: Directory containing Jinja2 templates
        """
        self.template_dir = template_dir or Path(__file__).parent / "templates"
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=False,  # Generating Python code, not HTML
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Register custom filters
        self.env.filters['camel_case'] = self._camel_case
        self.env.filters['snake_case'] = self._snake_case
        self.env.filters['title_case'] = self._title_case
        self.env.filters['list_join'] = self._list_join
        
        logger.info(f"✅ TemplateEngine initialized with dir: {self.template_dir}")
    
    # =========================================================================
    # CUSTOM FILTERS
    # =========================================================================
    
    @staticmethod
    def _camel_case(text: str) -> str:
        """Convert to CamelCase"""
        return ''.join(word.capitalize() for word in text.split('_'))
    
    @staticmethod
    def _snake_case(text: str) -> str:
        """Convert to snake_case"""
        import re
        text = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', text).lower()
    
    @staticmethod
    def _title_case(text: str) -> str:
        """Convert to Title Case"""
        return text.replace('_', ' ').title()
    
    @staticmethod
    def _list_join(items: list, separator: str = ', ') -> str:
        """Join list items"""
        return separator.join(str(item) for item in items)
    
    # =========================================================================
    # RENDERING
    # =========================================================================
    
    def render(self, template_name: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Render template with context.
        
        Args:
            template_name: Name of template file (e.g., "agent.py.j2")
            context: Template context variables
        
        Returns:
            Rendered output or None if error
        """
        try:
            template = self.env.get_template(template_name)
            output = template.render(**context)
            logger.info(f"✅ Rendered template: {template_name}")
            return output
            
        except TemplateNotFound:
            logger.error(f"❌ Template not found: {template_name}")
            return None
        except Exception as e:
            logger.error(f"❌ Error rendering {template_name}: {e}")
            return None
    
    def render_from_string(self, template_string: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Render template from string.
        
        Args:
            template_string: Template as string
            context: Template context variables
        
        Returns:
            Rendered output or None if error
        """
        try:
            template = self.env.from_string(template_string)
            output = template.render(**context)
            return output
        except Exception as e:
            logger.error(f"❌ Error rendering template string: {e}")
            return None
    
    def render_agent(self, spec: AgentSpecConfig) -> Optional[str]:
        """
        Render agent code from spec.
        
        Args:
            spec: Agent specification
        
        Returns:
            Rendered Python code or None if error
        """
        context = {
            "spec": spec,
            "coe_name": spec.coe_name,
            "display_name": spec.display_name,
            "tier": spec.tier,
            "domain": spec.domain.value,
            "version": spec.version,
            "description": spec.description,
            "capabilities": spec.capabilities,
            "constraints": spec.constraints,
            "dependencies": spec.dependencies,
            "wake_patterns": spec.wake_patterns,
            "resource_budget": spec.resource_budget,
            "specialization": spec.specialization
        }
        
        return self.render("agent.py.j2", context)
    
    def render_tests(self, spec: AgentSpecConfig) -> Optional[str]:
        """
        Render test file from spec.
        
        Args:
            spec: Agent specification
        
        Returns:
            Rendered test code or None if error
        """
        context = {
            "spec": spec,
            "coe_name": spec.coe_name,
            "agent_file": f"{spec.coe_name.lower()}.py"
        }
        
        return self.render("test_agent.py.j2", context)
    
    # =========================================================================
    # TEMPLATE MANAGEMENT
    # =========================================================================
    
    def list_templates(self) -> list[str]:
        """List available templates"""
        return self.env.list_templates()
    
    def template_exists(self, template_name: str) -> bool:
        """Check if template exists"""
        try:
            self.env.get_template(template_name)
            return True
        except TemplateNotFound:
            return False


def render_agent_code(spec: AgentSpecConfig, template_dir: Optional[Path] = None) -> Optional[str]:
    """
    Convenience function to render agent code.
    
    Args:
        spec: Agent specification
        template_dir: Optional template directory
    
    Returns:
        Rendered Python code
    """
    engine = TemplateEngine(template_dir)
    return engine.render_agent(spec)


# =============================================================================
# USAGE EXAMPLES  
# =============================================================================

# Example usage (commented out - uncomment to test):
#
# from waooaw.factory.engine import TemplateEngine, render_agent_code
# from waooaw.factory.config.schema import AgentSpecConfig, AgentDomain
#
# # Example 1: Render agent from spec
# spec = AgentSpecConfig(
#     coe_name="WowExample",
#     display_name="WowExample",
#     tier=3,
#     domain=AgentDomain.COMMUNICATION,
#     version="0.4.2",
#     description="Example agent for testing",
#     capabilities={
#         "messaging": ["send", "receive"],
#         "validation": ["schema_check"]
#     },
#     dependencies=["WowAgentFactory"],
#     wake_patterns=["example.*"]
# )
#
# code = render_agent_code(spec)
# if code:
#     print(code)
#
# # Example 2: Render with custom template
# engine = TemplateEngine()
# context = {
#     "agent_name": "WowCustom",
#     "methods": ["wake", "decide", "act"]
# }
# output = engine.render("custom_template.j2", context)
#
# # Example 3: List available templates
# engine = TemplateEngine()
# templates = engine.list_templates()
# print(f"Available templates: {templates}")
