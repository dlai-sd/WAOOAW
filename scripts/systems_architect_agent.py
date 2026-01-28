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
import time
from typing import Dict, Any, List, Optional
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
    
    def __init__(self, openai_api_key: str, repo_root: Optional[str] = None):
        self.api_key = openai_api_key
        self.repo_root = Path(repo_root) if repo_root else Path(__file__).resolve().parents[1]
        self.foundation_context = self._load_foundation_documents()

    def _post_openai_with_retries(self, payload: Dict[str, Any], *, timeout: int) -> requests.Response:
        """Call OpenAI with basic retries for transient HTTP/network failures."""

        max_attempts = int(os.getenv("WAOOAW_OPENAI_MAX_ATTEMPTS", "6"))
        base_sleep = float(os.getenv("WAOOAW_OPENAI_RETRY_BASE_SLEEP", "2.0"))

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        last_error: Optional[BaseException] = None
        for attempt in range(1, max_attempts + 1):
            try:
                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=timeout,
                )

                if response.status_code == 200:
                    return response

                retryable = response.status_code in {429, 500, 502, 503, 504}
                if not retryable:
                    return response

                sleep_s = base_sleep * (2 ** (attempt - 1))
                print(
                    f"Warning: OpenAI API transient error (status={response.status_code}). "
                    f"Retrying in {sleep_s:.1f}s (attempt {attempt}/{max_attempts})",
                    file=sys.stderr,
                )
                time.sleep(sleep_s)
                continue
            except requests.RequestException as e:
                last_error = e
                sleep_s = base_sleep * (2 ** (attempt - 1))
                print(
                    f"Warning: OpenAI request failed ({type(e).__name__}: {e}). "
                    f"Retrying in {sleep_s:.1f}s (attempt {attempt}/{max_attempts})",
                    file=sys.stderr,
                )
                time.sleep(sleep_s)

        if last_error:
            raise last_error
        raise Exception("OpenAI API request failed after retries")
    
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
        
        response = self._post_openai_with_retries(
            {
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are the Systems Architect Agent for WAOOAW. You are the architecture guardian protecting system quality, preventing technical debt, and ensuring operational excellence.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,  # Lower temperature for architectural consistency
                "max_tokens": 8000,
                "response_format": {"type": "json_object"},
            },
            timeout=120,
        )
        
        if response.status_code != 200:
            raise Exception(f"OpenAI API error: {response.status_code} {response.text}")
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        data = json.loads(content)
        
        return data.get('enhanced_stories', [])
    
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
