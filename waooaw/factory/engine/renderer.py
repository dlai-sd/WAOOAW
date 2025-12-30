"""
Helper functions for template rendering

Story: #79 Template Engine (3 pts)
Epic: #68 WowAgentFactory Core (v0.4.1)
Theme: CONCEIVE
"""

from typing import Any, Dict, Optional
from waooaw.factory.config.schema import AgentSpecConfig
from waooaw.factory.engine.template_engine import TemplateEngine


def render_agent_code(spec: AgentSpecConfig, template_dir: Optional[str] = None) -> Optional[str]:
    """
    Render agent code from specification.
    
    Args:
        spec: Agent specification
        template_dir: Optional template directory
    
    Returns:
        Rendered Python code
    """
    engine = TemplateEngine(template_dir)
    return engine.render_agent(spec)


def render_test_code(spec: AgentSpecConfig, template_dir: Optional[str] = None) -> Optional[str]:
    """
    Render test code from specification.
    
    Args:
        spec: Agent specification
        template_dir: Optional template directory
    
    Returns:
        Rendered test code
    """
    engine = TemplateEngine(template_dir)
    return engine.render_tests(spec)


def render_from_template(
    template_name: str,
    context: Dict[str, Any],
    template_dir: Optional[str] = None
) -> Optional[str]:
    """
    Render arbitrary template with context.
    
    Args:
        template_name: Template file name
        context: Template variables
        template_dir: Optional template directory
    
    Returns:
        Rendered output
    """
    engine = TemplateEngine(template_dir)
    return engine.render(template_name, context)
