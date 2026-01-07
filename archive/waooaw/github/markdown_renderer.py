"""
Markdown Renderer - Story 2.4

Renders agent responses as formatted markdown for GitHub issues/comments.
Part of Epic 2: GitHub Integration.
"""
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class MarkdownRenderer:
    """
    Renders structured data as formatted markdown.
    
    Features:
    - Tables with alignment
    - Code blocks with syntax highlighting
    - Diffs with +/- formatting
    - Lists (ordered, unordered)
    - Progress bars
    - Emoji indicators
    """
    
    @staticmethod
    def render_table(
        headers: List[str],
        rows: List[List[Any]],
        alignment: Optional[List[str]] = None
    ) -> str:
        """
        Render markdown table.
        
        Args:
            headers: Column headers
            rows: Table rows
            alignment: Column alignment ('left', 'center', 'right')
            
        Returns:
            Markdown table string
        """
        if not headers or not rows:
            return ""
        
        # Default alignment: left
        if alignment is None:
            alignment = ["left"] * len(headers)
        
        # Header row
        table = "| " + " | ".join(str(h) for h in headers) + " |\n"
        
        # Alignment row
        align_chars = {
            "left": ":---",
            "center": ":---:",
            "right": "---:"
        }
        table += "| " + " | ".join(
            align_chars.get(a, ":---") for a in alignment
        ) + " |\n"
        
        # Data rows
        for row in rows:
            table += "| " + " | ".join(str(cell) for cell in row) + " |\n"
        
        return table
    
    @staticmethod
    def render_code_block(
        code: str,
        language: str = "python"
    ) -> str:
        """
        Render code block with syntax highlighting.
        
        Args:
            code: Code string
            language: Programming language (python, javascript, etc.)
            
        Returns:
            Markdown code block
        """
        return f"```{language}\n{code}\n```"
    
    @staticmethod
    def render_diff(
        old_lines: List[str],
        new_lines: List[str],
        context_lines: int = 3
    ) -> str:
        """
        Render diff between old and new content.
        
        Args:
            old_lines: Original lines
            new_lines: Modified lines
            context_lines: Number of context lines to show
            
        Returns:
            Markdown diff block
        """
        diff = "```diff\n"
        
        # Simple line-by-line diff
        max_len = max(len(old_lines), len(new_lines))
        
        for i in range(max_len):
            old_line = old_lines[i] if i < len(old_lines) else None
            new_line = new_lines[i] if i < len(new_lines) else None
            
            if old_line == new_line:
                diff += f"  {old_line}\n"
            else:
                if old_line is not None:
                    diff += f"- {old_line}\n"
                if new_line is not None:
                    diff += f"+ {new_line}\n"
        
        diff += "```"
        return diff
    
    @staticmethod
    def render_list(
        items: List[str],
        ordered: bool = False,
        indent_level: int = 0
    ) -> str:
        """
        Render list (ordered or unordered).
        
        Args:
            items: List items
            ordered: True for numbered list, False for bullets
            indent_level: Indentation level (0 = top level)
            
        Returns:
            Markdown list
        """
        list_md = ""
        indent = "  " * indent_level
        
        for i, item in enumerate(items, start=1):
            if ordered:
                list_md += f"{indent}{i}. {item}\n"
            else:
                list_md += f"{indent}- {item}\n"
        
        return list_md
    
    @staticmethod
    def render_progress_bar(
        current: int,
        total: int,
        width: int = 20,
        filled_char: str = "█",
        empty_char: str = "░"
    ) -> str:
        """
        Render progress bar.
        
        Args:
            current: Current progress value
            total: Total value
            width: Bar width in characters
            filled_char: Character for filled portion
            empty_char: Character for empty portion
            
        Returns:
            Progress bar string with percentage
        """
        if total == 0:
            pct = 0
        else:
            pct = int(100 * current / total)
        
        filled = int(width * current / total) if total > 0 else 0
        empty = width - filled
        
        bar = filled_char * filled + empty_char * empty
        
        return f"[{bar}] {pct}% ({current}/{total})"
    
    @staticmethod
    def render_severity_badge(severity: str) -> str:
        """
        Render severity badge with emoji.
        
        Args:
            severity: Severity level (critical, high, medium, low)
            
        Returns:
            Emoji badge
        """
        badges = {
            "critical": "🚨",
            "high": "🔴",
            "medium": "🟠",
            "low": "🟡",
            "info": "ℹ️"
        }
        return badges.get(severity.lower(), "❓")
    
    @staticmethod
    def render_status_indicator(status: str) -> str:
        """
        Render status indicator with emoji.
        
        Args:
            status: Status (success, warning, error, pending, in-progress)
            
        Returns:
            Emoji indicator
        """
        indicators = {
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "pending": "⏳",
            "in-progress": "🔄",
            "info": "ℹ️"
        }
        return indicators.get(status.lower(), "❓")
    
    @staticmethod
    def render_collapsible_section(
        title: str,
        content: str,
        default_open: bool = False
    ) -> str:
        """
        Render collapsible section (GitHub markdown).
        
        Args:
            title: Section title
            content: Section content
            default_open: Whether to expand by default
            
        Returns:
            Collapsible markdown
        """
        open_attr = " open" if default_open else ""
        return f"<details{open_attr}>\n<summary>{title}</summary>\n\n{content}\n\n</details>"
    
    @staticmethod
    def render_link(text: str, url: str) -> str:
        """Render markdown link."""
        return f"[{text}]({url})"
    
    @staticmethod
    def render_heading(text: str, level: int = 1) -> str:
        """
        Render markdown heading.
        
        Args:
            text: Heading text
            level: Heading level (1-6)
            
        Returns:
            Markdown heading
        """
        return f"{'#' * level} {text}"
    
    @staticmethod
    def render_blockquote(text: str) -> str:
        """Render blockquote."""
        lines = text.split("\n")
        return "\n".join(f"> {line}" for line in lines)
    
    @staticmethod
    def render_horizontal_rule() -> str:
        """Render horizontal rule."""
        return "---"


# Convenience functions

def render_violation_summary(violations: List[Dict[str, Any]]) -> str:
    """
    Render violation summary table.
    
    Args:
        violations: List of violation dicts
        
    Returns:
        Markdown table
    """
    if not violations:
        return "✅ No violations detected!"
    
    rows = []
    for v in violations:
        severity_badge = MarkdownRenderer.render_severity_badge(v.get("severity", ""))
        rows.append([
            severity_badge,
            v.get("violation_type", "Unknown"),
            v.get("file_path", "N/A"),
            v.get("description", "")[:50] + "..."  # Truncate
        ])
    
    return MarkdownRenderer.render_table(
        headers=["Severity", "Type", "File", "Description"],
        rows=rows,
        alignment=["center", "left", "left", "left"]
    )


def render_pr_review_summary(
    files_count: int,
    violations: List[Dict[str, Any]],
    approved: bool
) -> str:
    """
    Render PR review summary.
    
    Args:
        files_count: Number of files reviewed
        violations: List of violations
        approved: Whether approved
        
    Returns:
        Markdown summary
    """
    md = MarkdownRenderer.render_heading("🤖 WowVision Prime Review", 2)
    md += "\n\n"
    
    # Status indicator
    status = "success" if approved else "warning"
    md += f"{MarkdownRenderer.render_status_indicator(status)} **Status**: "
    md += "APPROVED ✅\n\n" if approved else "CHANGES REQUESTED ⚠️\n\n"
    
    # Stats
    md += f"**Files Reviewed**: {files_count}\n"
    md += f"**Violations**: {len(violations)}\n\n"
    
    # Violations table
    if violations:
        md += MarkdownRenderer.render_heading("Violations Found", 3)
        md += "\n\n"
        md += render_violation_summary(violations)
    
    return md
