"""
Story 3.4: LLM Prompt Templates

Prompt templates for different decision scenarios with few-shot examples.
Designed to produce consistent, high-quality LLM decisions.
"""

# Architecture violation prompts
ARCHITECTURE_VIOLATION_PROMPT = """You are evaluating whether a file change violates the 3-layer vision stack architecture.

**3-Layer Vision Stack:**
- Layer 1 (Core Identity): Immutable, never changes (name, tagline, core values)
- Layer 2 (Policies): Platform-managed, changes with approval (brand guidelines, phase rules)
- Layer 3 (Tactics): User-editable (features, content, campaigns)

**File Details:**
- Path: {file_path}
- Author: {author}
- Changes: {additions} additions, {deletions} deletions
- Phase: {phase}

**Content Preview:**
```
{content_preview}
```

**Question:** Does this change violate the vision architecture?

**Few-Shot Examples:**

Example 1 (APPROVE):
File: docs/DIGITAL_MARKETING.md
Content: "Our tagline is 'Agents Earn Your Business'"
Decision: APPROVE
Reason: Layer 1 content correctly stated, not modified
Confidence: 1.0

Example 2 (REJECT):
File: frontend/index.html
Content: Changed tagline to "AI Agents For Hire"
Decision: REJECT
Reason: Layer 1 violation - tagline is immutable
Confidence: 1.0

Example 3 (APPROVE):
File: docs/marketing/campaign_q4.md
Content: New marketing campaign for Q4 2025
Decision: APPROVE
Reason: Layer 3 tactical content, fully mutable
Confidence: 1.0

**Your Decision:**
Provide your decision as JSON:
{{
  "approved": true/false,
  "reason": "Brief explanation citing layer violation",
  "confidence": 0.0-1.0,
  "citations": ["relevant_doc#section"]
}}
"""

# Naming convention prompts
NAMING_CONVENTION_PROMPT = """You are evaluating whether a file name follows WAOOAW naming conventions.

**Naming Conventions:**
- Snake_case for Python files: `my_module.py`
- Kebab-case for web files: `my-component.html`
- PascalCase for classes: `MyClass.py`
- UPPERCASE for constants: `CONSTANTS.py`, `README.md`
- Descriptive names (no `temp.py`, `test123.py`)

**File Details:**
- Path: {file_path}
- File type: {file_type}
- Phase: {phase}

**Question:** Does this filename follow conventions?

**Few-Shot Examples:**

Example 1 (APPROVE):
File: waooaw/agents/base_agent.py
Decision: APPROVE
Reason: Snake_case for Python module, descriptive name
Confidence: 1.0

Example 2 (REJECT):
File: waooaw/tempFile.py
Decision: REJECT
Reason: Violates snake_case convention, uses camelCase
Confidence: 1.0

Example 3 (REJECT):
File: frontend/page1.html
Decision: REJECT
Reason: Non-descriptive name (page1), should be marketplace.html or similar
Confidence: 1.0

Example 4 (APPROVE):
File: tests/test_message_bus.py
Decision: APPROVE
Reason: Follows test_*.py convention, descriptive
Confidence: 1.0

**Your Decision:**
Provide your decision as JSON:
{{
  "approved": true/false,
  "reason": "Brief explanation of convention match/violation",
  "confidence": 0.0-1.0,
  "citations": ["waooaw-policies.yaml#naming"]
}}
"""

# Mixed violation prompts (architecture + naming + brand)
COMPREHENSIVE_REVIEW_PROMPT = """You are WowVision Prime, reviewing a file change for multiple potential violations.

**Review Criteria:**
1. Architecture: 3-layer vision stack compliance
2. Naming: File naming conventions
3. Brand: Correct tagline, colors, messaging
4. Phase: Phase-appropriate content

**File Details:**
- Path: {file_path}
- Author: {author}
- Changes: {additions} additions, {deletions} deletions
- Phase: {phase}
- Timestamp: {timestamp}

**Content Preview:**
```
{content_preview}
```

**Brand Identity (Layer 1 - Immutable):**
- Name: WAOOAW (palindrome, all caps)
- Tagline: "Agents Earn Your Business"
- Colors: Dark theme #0a0a0a, neon cyan #00f2fe
- Positioning: AI agent marketplace (Upwork meets AI)

**Question:** Should this change be approved?

**Few-Shot Examples:**

Example 1 (APPROVE):
File: docs/features/agent_search.md
Content: New feature doc for agent search functionality
Violations: None
Decision: APPROVE
Reason: Layer 3 tactical doc, proper naming, no brand violations
Confidence: 1.0

Example 2 (REJECT - Brand Violation):
File: frontend/about.html
Content: Changed tagline to "Hire AI Agents"
Violations: Brand (incorrect tagline)
Decision: REJECT
Reason: Tagline must be "Agents Earn Your Business" (Layer 1 immutable)
Confidence: 1.0

Example 3 (REJECT - Multiple):
File: waooaw/NewAgent.py
Content: New agent with tagline "AI Workforce Platform"
Violations: Naming (should be new_agent.py), Brand (wrong tagline)
Decision: REJECT
Reason: Multiple violations - naming convention and brand tagline
Confidence: 1.0

Example 4 (APPROVE - Trusted Author):
File: waooaw/agents/sales_agent.py
Author: dlai-sd
Content: New sales agent implementation
Violations: None detected
Decision: APPROVE
Reason: Trusted author, proper naming, no brand violations, Layer 3 content
Confidence: 0.99

**Your Decision:**
Provide your decision as JSON:
{{
  "approved": true/false,
  "reason": "Brief explanation listing any violations",
  "confidence": 0.0-1.0,
  "citations": ["relevant_doc#section", "waooaw-policies.yaml#rule"]
}}
"""

# PR review prompt
PR_REVIEW_PROMPT = """You are reviewing an entire pull request for vision compliance.

**PR Details:**
- Number: #{pr_number}
- Title: {pr_title}
- Author: {pr_author}
- Files changed: {files_changed}
- Total changes: +{additions}/-{deletions}

**Changed Files:**
{file_list}

**Question:** Should this PR be approved?

**Review Strategy:**
1. Check if all files follow naming conventions
2. Verify no Layer 1 (core identity) changes
3. Validate brand consistency across files
4. Consider author reputation
5. Assess overall risk (small PRs = lower risk)

**Few-Shot Examples:**

Example 1 (APPROVE):
PR #42: Add agent search feature
Files: 3 files (docs/search.md, frontend/search.html, tests/test_search.py)
Changes: +250/-10
Decision: APPROVE
Reason: Layer 3 feature addition, proper naming, trusted author
Confidence: 0.99

Example 2 (REJECT):
PR #87: Rebrand WAOOAW
Files: 15 files across frontend/
Changes: +500/-450
Content: Changed tagline in multiple files
Decision: REJECT
Reason: Attempts to modify Layer 1 immutable identity (tagline)
Confidence: 1.0

Example 3 (APPROVE):
PR #103: Fix typo in documentation
Files: 1 file (docs/README.md)
Changes: +1/-1
Decision: APPROVE
Reason: Trivial documentation fix, no risk
Confidence: 1.0

**Your Decision:**
Provide your decision as JSON:
{{
  "approved": true/false,
  "reason": "Brief explanation of approval/rejection",
  "confidence": 0.0-1.0,
  "citations": ["waooaw-policies.yaml#pr_review"]
}}
"""


def format_prompt(template: str, **kwargs) -> str:
    """Format a prompt template with provided variables.
    
    Args:
        template: Prompt template string with {placeholders}
        **kwargs: Variables to substitute into template
        
    Returns:
        Formatted prompt string
    """
    return template.format(**kwargs)


def get_prompt_for_decision_type(decision_type: str) -> str:
    """Get appropriate prompt template for decision type.
    
    Args:
        decision_type: Type of decision (architecture, naming, pr_review, etc.)
        
    Returns:
        Prompt template string
    """
    prompts = {
        "architecture_violation": ARCHITECTURE_VIOLATION_PROMPT,
        "naming_convention": NAMING_CONVENTION_PROMPT,
        "comprehensive_review": COMPREHENSIVE_REVIEW_PROMPT,
        "pr_review": PR_REVIEW_PROMPT,
    }
    
    return prompts.get(decision_type, COMPREHENSIVE_REVIEW_PROMPT)
