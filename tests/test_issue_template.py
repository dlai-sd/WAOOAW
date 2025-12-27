"""
Tests for Story 2.4: Agent Violation Issue Template

Tests that the GitHub issue template exists and has the correct structure.
"""

import pytest
import os
import yaml


def test_agent_violation_template_exists():
    """Test that agent violation template file exists"""
    template_path = ".github/ISSUE_TEMPLATE/agent_violation.yml"
    assert os.path.exists(template_path), f"Template not found at {template_path}"


def test_agent_violation_template_is_valid_yaml():
    """Test that template is valid YAML"""
    template_path = ".github/ISSUE_TEMPLATE/agent_violation.yml"
    
    with open(template_path, 'r') as f:
        template_data = yaml.safe_load(f)
    
    assert template_data is not None
    assert isinstance(template_data, dict)


def test_agent_violation_template_has_required_metadata():
    """Test that template has required GitHub metadata"""
    template_path = ".github/ISSUE_TEMPLATE/agent_violation.yml"
    
    with open(template_path, 'r') as f:
        template_data = yaml.safe_load(f)
    
    # Required top-level fields
    assert "name" in template_data
    assert "description" in template_data
    assert "title" in template_data
    assert "labels" in template_data
    assert "body" in template_data
    
    # Check labels
    assert "vision-violation" in template_data["labels"]
    assert "agent-escalation" in template_data["labels"]
    
    # Check title includes emoji
    assert "🚨" in template_data["title"]


def test_agent_violation_template_has_required_fields():
    """Test that template defines all required fields from Story 2.4"""
    template_path = ".github/ISSUE_TEMPLATE/agent_violation.yml"
    
    with open(template_path, 'r') as f:
        template_data = yaml.safe_load(f)
    
    # Extract all field IDs from body
    field_ids = []
    for item in template_data["body"]:
        if "id" in item:
            field_ids.append(item["id"])
    
    # Story 2.4 required fields: file, commit, author, violation, confidence, citations
    required_fields = ["file", "commit", "author", "violation", "confidence"]
    
    for field in required_fields:
        assert field in field_ids, f"Required field '{field}' missing from template"


def test_agent_violation_template_has_decision_field():
    """Test that template has field for human decision with APPROVE/REJECT/MODIFY options"""
    template_path = ".github/ISSUE_TEMPLATE/agent_violation.yml"
    
    with open(template_path, 'r') as f:
        template_data = yaml.safe_load(f)
    
    # Find decision field
    decision_field = None
    for item in template_data["body"]:
        if item.get("id") == "decision":
            decision_field = item
            break
    
    assert decision_field is not None, "Decision field not found in template"
    
    # Check placeholder includes response options
    placeholder = decision_field["attributes"]["placeholder"]
    assert "APPROVE" in placeholder
    assert "REJECT" in placeholder
    assert "MODIFY" in placeholder


def test_agent_violation_template_has_citations_field():
    """Test that template has field for citations"""
    template_path = ".github/ISSUE_TEMPLATE/agent_violation.yml"
    
    with open(template_path, 'r') as f:
        template_data = yaml.safe_load(f)
    
    # Find citations field
    field_ids = [item.get("id") for item in template_data["body"] if "id" in item]
    
    assert "citations" in field_ids, "Citations field missing from template"


def test_agent_violation_template_has_method_field():
    """Test that template has field for decision method"""
    template_path = ".github/ISSUE_TEMPLATE/agent_violation.yml"
    
    with open(template_path, 'r') as f:
        template_data = yaml.safe_load(f)
    
    # Find method field
    field_ids = [item.get("id") for item in template_data["body"] if "id" in item]
    
    assert "method" in field_ids, "Method field missing from template"


def test_agent_violation_template_markdown_sections():
    """Test that template includes informational markdown sections"""
    template_path = ".github/ISSUE_TEMPLATE/agent_violation.yml"
    
    with open(template_path, 'r') as f:
        template_data = yaml.safe_load(f)
    
    # Count markdown sections
    markdown_sections = [item for item in template_data["body"] if item["type"] == "markdown"]
    
    # Should have at least 3: header, required action, agent learning
    assert len(markdown_sections) >= 3, "Template should have multiple markdown sections for context"


# ============================================================================
# SUMMARY
# ============================================================================

"""
Story 2.4 Test Coverage:

✅ Template file exists (1 test)
✅ Valid YAML format (1 test)
✅ Required GitHub metadata (1 test)
✅ Required fields from Story 2.4 (1 test)
✅ Decision field with response options (1 test)
✅ Citations field (1 test)
✅ Method field (1 test)
✅ Markdown sections (1 test)

Total: 8 tests ✅

Validates that the agent_violation.yml template meets all Story 2.4 requirements.
"""
