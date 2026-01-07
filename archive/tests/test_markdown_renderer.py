"""
Unit Tests for Markdown Renderer - Story 2.4
"""
import pytest

import sys
sys.path.insert(0, '/workspaces/WAOOAW')

from waooaw.github.markdown_renderer import (
    MarkdownRenderer,
    render_violation_summary,
    render_pr_review_summary
)


class TestMarkdownRenderer:
    """Test markdown renderer."""
    
    def test_render_table(self):
        """Should render markdown table."""
        headers = ["Name", "Age", "City"]
        rows = [
            ["Alice", 30, "NYC"],
            ["Bob", 25, "SF"]
        ]
        
        table = MarkdownRenderer.render_table(headers, rows)
        
        assert "| Name | Age | City |" in table
        assert "| Alice | 30 | NYC |" in table
        assert ":---" in table
    
    def test_render_table_with_alignment(self):
        """Should render table with custom alignment."""
        headers = ["Left", "Center", "Right"]
        rows = [["A", "B", "C"]]
        alignment = ["left", "center", "right"]
        
        table = MarkdownRenderer.render_table(headers, rows, alignment)
        
        assert ":---" in table
        assert ":---:" in table
        assert "---:" in table
    
    def test_render_code_block(self):
        """Should render code block with syntax highlighting."""
        code = "def hello():\n    print('Hello')"
        
        block = MarkdownRenderer.render_code_block(code, "python")
        
        assert block.startswith("```python")
        assert "def hello()" in block
        assert block.endswith("```")
    
    def test_render_diff(self):
        """Should render diff."""
        old_lines = ["line 1", "line 2", "line 3"]
        new_lines = ["line 1", "line 2 modified", "line 3"]
        
        diff = MarkdownRenderer.render_diff(old_lines, new_lines)
        
        assert "```diff" in diff
        assert "- line 2" in diff
        assert "+ line 2 modified" in diff
        assert "  line 1" in diff
    
    def test_render_list_unordered(self):
        """Should render unordered list."""
        items = ["First", "Second", "Third"]
        
        list_md = MarkdownRenderer.render_list(items, ordered=False)
        
        assert "- First" in list_md
        assert "- Second" in list_md
    
    def test_render_list_ordered(self):
        """Should render ordered list."""
        items = ["First", "Second", "Third"]
        
        list_md = MarkdownRenderer.render_list(items, ordered=True)
        
        assert "1. First" in list_md
        assert "2. Second" in list_md
        assert "3. Third" in list_md
    
    def test_render_progress_bar(self):
        """Should render progress bar."""
        bar = MarkdownRenderer.render_progress_bar(7, 10, width=10)
        
        assert "70%" in bar
        assert "(7/10)" in bar
        assert "█" in bar
        assert "░" in bar
    
    def test_render_severity_badge(self):
        """Should render severity badges."""
        assert MarkdownRenderer.render_severity_badge("critical") == "🚨"
        assert MarkdownRenderer.render_severity_badge("high") == "🔴"
        assert MarkdownRenderer.render_severity_badge("medium") == "🟠"
        assert MarkdownRenderer.render_severity_badge("low") == "🟡"
    
    def test_render_status_indicator(self):
        """Should render status indicators."""
        assert MarkdownRenderer.render_status_indicator("success") == "✅"
        assert MarkdownRenderer.render_status_indicator("error") == "❌"
        assert MarkdownRenderer.render_status_indicator("warning") == "⚠️"
    
    def test_render_collapsible_section(self):
        """Should render collapsible section."""
        section = MarkdownRenderer.render_collapsible_section(
            "Details",
            "Hidden content"
        )
        
        assert "<details>" in section
        assert "<summary>Details</summary>" in section
        assert "Hidden content" in section
        assert "</details>" in section
    
    def test_render_heading(self):
        """Should render headings."""
        assert MarkdownRenderer.render_heading("Title", 1) == "# Title"
        assert MarkdownRenderer.render_heading("Subtitle", 2) == "## Subtitle"
    
    def test_render_blockquote(self):
        """Should render blockquote."""
        quote = MarkdownRenderer.render_blockquote("Line 1\nLine 2")
        
        assert "> Line 1" in quote
        assert "> Line 2" in quote


class TestConvenienceFunctions:
    """Test convenience rendering functions."""
    
    def test_render_violation_summary_empty(self):
        """Should handle empty violations."""
        summary = render_violation_summary([])
        
        assert "No violations" in summary
    
    def test_render_violation_summary_with_violations(self):
        """Should render violation table."""
        violations = [
            {
                "severity": "high",
                "violation_type": "Security",
                "file_path": "src/auth.py",
                "description": "SQL injection vulnerability"
            },
            {
                "severity": "low",
                "violation_type": "Style",
                "file_path": "src/utils.py",
                "description": "Line too long"
            }
        ]
        
        summary = render_violation_summary(violations)
        
        assert "Security" in summary
        assert "src/auth.py" in summary
        assert "🔴" in summary  # High severity
        assert "🟡" in summary  # Low severity
    
    def test_render_pr_review_summary_approved(self):
        """Should render approved PR summary."""
        summary = render_pr_review_summary(
            files_count=5,
            violations=[],
            approved=True
        )
        
        assert "APPROVED" in summary
        assert "5" in summary  # Files count
        assert "✅" in summary
    
    def test_render_pr_review_summary_rejected(self):
        """Should render rejected PR summary."""
        violations = [
            {"severity": "high", "violation_type": "Bug", "file_path": "test.py", "description": "Test"}
        ]
        
        summary = render_pr_review_summary(
            files_count=3,
            violations=violations,
            approved=False
        )
        
        assert "CHANGES REQUESTED" in summary
        assert "⚠️" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
