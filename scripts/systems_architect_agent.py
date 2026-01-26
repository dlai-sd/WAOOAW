#!/usr/bin/env python3
"""Systems Architect Agent - Architecture Guardian & Story Enhancement

Reviews BA stories and adds:
- STRIDE security analysis
- Performance budgets
- API contracts
- Blast radius analysis
- Cost impact
- Deployment strategy
- Observability requirements
- Rollback plans
- Architecture Decision Records (ADRs)
- Technical debt prevention

Environment:
- OPENAI_API_KEY: Required for GPT-4o API calls
"""

import os
import sys
import json
import argparse
import re
from typing import Dict, Any, List
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: requests library required. Install: pip install requests", file=sys.stderr)
    sys.exit(1)


class SystemsArchitectAgent:
    """Architecture guardian - enhances stories with quality attributes"""
    
    # Platform-wide standards
    PERFORMANCE_BUDGETS = {
        'api_response': '300ms',
        'page_load': '2s',
        'db_query': '100ms'
    }
    
    COST_THRESHOLD = 20  # Escalate if monthly cost > $20 (20% of $100 budget)
    
    def __init__(self, openai_api_key: str, repo_root: str = "/workspaces/WAOOAW"):
        self.api_key = openai_api_key
        self.repo_root = Path(repo_root)
        self.foundation_context = self._load_foundation_documents()
    
    def _load_foundation_documents(self) -> Dict[str, str]:
        """Load Foundation documents for SA context"""
        foundation_path = self.repo_root / "main"
        
        docs = {}
        files_to_load = {
            'constitution': 'Foundation.md',
            'sa_charter': 'Foundation/systems_architect_foundational_governance_agent.md',
            'sa_capabilities': 'Foundation/systems_architect_enhanced_capabilities.md',
        }
        
        for key, file_path in files_to_load.items():
            full_path = foundation_path / file_path
            if full_path.exists():
                docs[key] = full_path.read_text(encoding='utf-8')
            else:
                print(f"Warning: {full_path} not found", file=sys.stderr)
                docs[key] = ""
        
        return docs
    
    def review_stories(self, epic_number: int, stories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance stories with architecture guardian analysis
        
        Returns:
            Enhanced stories with additional fields:
            - architectural_notes
            - security_stride
            - performance_requirements
            - observability
            - deployment_strategy
            - rollback_plan
            - cost_impact
            - blast_radius
            - debt_prevention
        """
        prompt = self._build_review_prompt(epic_number, stories)
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'gpt-4o',
                'messages': [
                    {
                        'role': 'system',
                        'content': 'You are the Systems Architect Agent for WAOOAW. You are the architecture guardian protecting system quality, preventing technical debt, and ensuring operational excellence.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': 0.3,  # Lower temperature for architectural consistency
                'max_tokens': 8000,
                'response_format': {'type': 'json_object'}
            },
            timeout=120
        )
        
        if response.status_code != 200:
            raise Exception(f"OpenAI API error: {response.status_code} {response.text}")
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        data = json.loads(content)

        enhanced = data.get('enhanced_stories', [])
        return self._enforce_lifetime_constraints(stories, enhanced)

    @staticmethod
    def _default_lifetime_constraints() -> List[str]:
        return [
            "Avoid refactors unrelated to story scope; prefer minimal, reversible edits.",
            "Do not rename or remove public API paths under /api/* unless explicitly required; if required, update all tests and clients.",
            "Do not change import surfaces used by tests (e.g., patch/mocking targets) without updating tests.",
            "For auth/OAuth/JWT work: tests must not make real network calls; preserve stable mocking/patch points.",
            "Changes must pass pytest --collect-only for impacted service test suites to prevent import/collection failures.",
        ]

    @staticmethod
    def _extract_constraints_from_body(body: str) -> List[str]:
        if not body:
            return []

        # Match a section header like **Constraints (Do Not Break)**
        header = re.compile(r"^\*\*Constraints \(Do Not Break\)\*\*\s*$", re.IGNORECASE)
        lines = body.splitlines()

        start_idx: int | None = None
        for idx, line in enumerate(lines):
            if header.match(line.strip()):
                start_idx = idx + 1
                break

        if start_idx is None:
            return []

        constraints: List[str] = []
        for line in lines[start_idx:]:
            stripped = line.strip()
            if not stripped:
                # Stop at first blank line after bullets.
                if constraints:
                    break
                continue
            # Stop when the next bold section starts.
            if stripped.startswith("**") and stripped.endswith("**"):
                break
            if stripped.startswith("-"):
                item = stripped.lstrip("-").strip()
                if item:
                    constraints.append(item)
                continue
            # If we encounter non-bullet content after collecting some bullets, stop.
            if constraints:
                break

        return constraints

    @classmethod
    def _ensure_constraints_in_body(cls, body: str, constraints: List[str]) -> str:
        constraints = [c.strip() for c in constraints if c and c.strip()]
        if not constraints:
            constraints = cls._default_lifetime_constraints()

        section = "**Constraints (Do Not Break)**\n" + "\n".join(f"- {c}" for c in constraints) + "\n"

        if not body:
            return section

        # If a Constraints section exists, replace its bullet list.
        header_re = re.compile(r"^\*\*Constraints \(Do Not Break\)\*\*\s*$", re.IGNORECASE | re.MULTILINE)
        m = header_re.search(body)
        if m:
            lines = body.splitlines(True)  # keepends
            # Find the line index containing the header match.
            header_line_idx = 0
            running = 0
            for i, line in enumerate(lines):
                running += len(line)
                if running >= m.end():
                    header_line_idx = i
                    break

            # Rebuild: keep content up to header line, then inject section, then skip old bullets.
            prefix = "".join(lines[:header_line_idx])
            # Skip header line itself
            remainder_lines = lines[header_line_idx + 1 :]
            trimmed: List[str] = []
            skipping = True
            for line in remainder_lines:
                stripped = line.strip()
                if skipping:
                    if not stripped:
                        continue
                    # Stop skipping once we hit the next section header or any non-bullet content.
                    if stripped.startswith("**") and stripped.endswith("**"):
                        skipping = False
                        trimmed.append(line)
                        continue
                    if stripped.startswith("-"):
                        continue
                    skipping = False
                    trimmed.append(line)
                    continue
                trimmed.append(line)

            return prefix + section + "\n" + "".join(trimmed).lstrip("\n")

        # Otherwise, insert after Priority line if present.
        priority_re = re.compile(r"^\*\*Priority\*\*:.*$", re.IGNORECASE | re.MULTILINE)
        pm = priority_re.search(body)
        if pm:
            insert_at = pm.end()
            return body[:insert_at] + "\n\n" + section + "\n" + body[insert_at:].lstrip("\n")

        # Fallback: prepend.
        return section + "\n" + body

    @classmethod
    def _enforce_lifetime_constraints(
        cls,
        original_stories: List[Dict[str, Any]],
        enhanced_stories: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        original_by_index: Dict[int, Dict[str, Any]] = {}
        for s in original_stories or []:
            try:
                original_by_index[int(s.get("index"))] = s
            except Exception:
                continue

        enforced: List[Dict[str, Any]] = []
        for story in enhanced_stories or []:
            # Copy so we can mutate safely.
            out = dict(story)
            idx = out.get("index")

            original = None
            try:
                original = original_by_index.get(int(idx))
            except Exception:
                original = None

            original_body = (original or {}).get("body") or ""
            enhanced_body = out.get("body") or ""

            original_constraints = cls._extract_constraints_from_body(original_body)
            enhanced_constraints = cls._extract_constraints_from_body(enhanced_body)

            chosen = original_constraints or enhanced_constraints or cls._default_lifetime_constraints()

            # Ensure body contains the Constraints section (and preserve verbatim BA constraints).
            out["body"] = cls._ensure_constraints_in_body(enhanced_body, chosen)

            # Ensure machine-readable list exists.
            arch = out.get("architectural_enhancements")
            if not isinstance(arch, dict):
                arch = {}
            arch["lifetime_constraints"] = chosen
            out["architectural_enhancements"] = arch

            enforced.append(out)

        return enforced
    
    def _build_review_prompt(self, epic_number: int, stories: List[Dict[str, Any]]) -> str:
        """Build SA review prompt"""
        
        stories_json = json.dumps(stories, indent=2)
        
        return f"""You are the Systems Architect Agent for WAOOAW - the architecture guardian.

CONSTITUTIONAL CONTEXT (Foundation.md - 13 Microservices):
{self.foundation_context['constitution'][:6000]}

YOUR CHARTER (systems_architect_foundational_governance_agent.md):
{self.foundation_context['sa_charter'][:5000]}

ENHANCED CAPABILITIES (systems_architect_enhanced_capabilities.md):
{self.foundation_context['sa_capabilities'][:4000]}

PLATFORM-WIDE STANDARDS:
- Performance: API <{self.PERFORMANCE_BUDGETS['api_response']}, Page <{self.PERFORMANCE_BUDGETS['page_load']}, DB <{self.PERFORMANCE_BUDGETS['db_query']}
- Security: STRIDE analysis mandatory for all stories
- Cost: Escalate to Governor if monthly cost >${self.COST_THRESHOLD} (20% of budget)
- Observability: Metrics + logs + alerts required for all features
- Rollback: Required for all database/config changes

STORIES TO ENHANCE:
{stories_json}

YOUR TASK:
For EACH story, add architecture guardian analysis:

0. **Lifetime Constraints Enforcement** (mandatory, non-negotiable):
    - Ensure the story `body` contains a section titled **Constraints (Do Not Break)**.
    - Preserve any BA-provided constraints verbatim; do NOT rewrite them.
    - If the story involves auth/OAuth/JWT, add constraints that keep tests hermetic (no real network calls) and keep mocking/patch points stable.
    - Add a machine-readable `lifetime_constraints` list under `architectural_enhancements` that mirrors the constraints in the body.

1. **STRIDE Security Analysis** (mandatory):
   - Spoofing: Identity/authentication threats
   - Tampering: Data integrity threats
   - Repudiation: Audit/non-repudiation gaps
   - Information Disclosure: Data leak risks
   - Denial of Service: Resource exhaustion
   - Elevation of Privilege: Permission bypass
   Format: "T1: [threat] → Mitigation: [solution]"

2. **Performance Requirements** (specific targets):
   - API response time budget
   - Database query limits
   - Caching strategy (TTL, invalidation)
   - Pagination/rate limiting

3. **API Contracts** (if integration story):
   - Endpoint specification
   - Request/response schemas
   - Error codes
   - Versioning strategy

4. **Blast Radius Analysis**:
   - What systems affected if this fails?
   - Cascading failure scenarios
   - Circuit breaker/fallback needed?

5. **Cost Impact** (monthly $):
   - Cloud Run requests
   - Database storage
   - External API calls
   - Total estimated cost

6. **Deployment Strategy**:
   - Feature flag needed?
   - Canary rollout %?
   - Rollback trigger conditions

7. **Observability** (metrics, logs, alerts):
   - Key metrics to track
   - Log entries needed
   - Alert thresholds

8. **Rollback Plan**:
   - How to undo this change?
   - Database migration reversibility?
   - Configuration rollback steps

9. **Code Reuse Opportunities**:
   - Which existing microservices to use?
   - Reusable components/libraries
   - Avoid duplication notes

10. **Technical Debt Prevention**:
    - Design decisions that will cause pain later
    - Recommended alternatives
    - "This will break when X reaches Y scale"

OUTPUT FORMAT (JSON only):
{{
  "enhanced_stories": [
    {{
      ...original_story_fields,
      "architectural_enhancements": {{
                "lifetime_constraints": [
                    "Avoid refactors unrelated to story scope; prefer minimal, reversible edits.",
                    "Do not rename or remove public API paths under /api/* unless explicitly required; if required, update all tests and clients.",
                    "Changes must pass pytest --collect-only for impacted service test suites."
                ],
        "security_stride": [
          "T1 (Spoofing): [threat description] → Mitigation: [solution]",
          "T5 (Info Disclosure): [threat] → Mitigation: [solution]"
        ],
        "performance_requirements": {{
          "api_response_budget": "200ms",
          "cache_strategy": "5min TTL, invalidate on update",
          "pagination": "20 items/page"
        }},
        "api_contract": {{
          "endpoint": "GET /api/v1/resource",
          "request_schema": {{}},
          "response_schema": {{}},
          "error_codes": ["400", "401", "429"]
        }},
        "blast_radius": "Plant API down → Show cached results + stale warning. Circuit breaker after 5 failures.",
        "cost_impact": {{
          "monthly_estimate": "$2",
          "breakdown": "Cloud Run: $1, Redis cache: $1",
          "budget_percent": "2%"
        }},
        "deployment_strategy": {{
          "feature_flag": "feature_xyz_enabled",
          "canary_rollout": "10% → 6hrs → 50% → 12hrs → 100%",
          "rollback_trigger": ">5% error rate OR >500ms p95 latency"
        }},
        "observability": {{
          "metrics": ["api_latency", "cache_hit_rate", "error_count"],
          "logs": ["API call duration", "cache misses", "errors"],
          "alerts": ["p95 latency >500ms for 5min", "error rate >5%"]
        }},
        "rollback_plan": "Disable feature flag. No DB changes (read-only). Revert to previous behavior.",
        "code_reuse": [
          "Use Health Aggregator (Port 8019) for monitoring",
          "Use OPA Policy (Port 8013) for access control",
          "Leverage existing OAuth middleware"
        ],
        "debt_prevention": [
          "⚠️ Storing JSON in text field will make querying slow >10K records. Use JSONB.",
          "✅ API versioned (/v1/) - can evolve safely"
        ]
      }}
    }}
  ]
}}

Enhance all {len(stories)} stories with complete architecture guardian analysis!
"""


def main():
    parser = argparse.ArgumentParser(description='Systems Architect Agent - Architecture Guardian')
    parser.add_argument('--epic-number', type=int, required=True, help='Epic issue number')
    parser.add_argument('--stories-file', required=True, help='Input JSON file with BA stories')
    parser.add_argument('--output', default='sa-enhanced-stories.json', help='Output JSON file')
    
    args = parser.parse_args()
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable required", file=sys.stderr)
        sys.exit(1)
    
    # Load BA stories
    with open(args.stories_file) as f:
        ba_data = json.load(f)
        stories = ba_data.get('stories', [])
    
    print(f"🏗️  Systems Architect reviewing {len(stories)} stories for Epic #{args.epic_number}...")
    
    agent = SystemsArchitectAgent(api_key)
    enhanced_stories = agent.review_stories(args.epic_number, stories)
    
    # Write output
    output_data = {'enhanced_stories': enhanced_stories}
    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Enhanced {len(enhanced_stories)} stories with architecture guardian analysis")
    print(f"{'='*60}\n")
    
    for story in enhanced_stories:
        enhancements = story.get('architectural_enhancements', {})
        print(f"{story['index']}. {story['title']}")
        
        if 'security_stride' in enhancements:
            print(f"   Security: {len(enhancements['security_stride'])} STRIDE threats analyzed")
        
        if 'cost_impact' in enhancements:
            cost = enhancements['cost_impact'].get('monthly_estimate', 'N/A')
            print(f"   Cost Impact: {cost}/month")
        
        if 'code_reuse' in enhancements:
            print(f"   Code Reuse: {len(enhancements['code_reuse'])} opportunities identified")
        
        print()
    
    print(f"✅ Enhanced stories saved to {args.output}")
    sys.exit(0)


if __name__ == '__main__':
    main()
