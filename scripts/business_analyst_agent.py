#!/usr/bin/env python3
"""Business Analyst Agent - User Story Generation

Generates relevant user stories from epics using Foundation context and INVEST principles.

Flow:
1. Load Foundation documents (BA charter, design system, best practices)
2. Generate N user stories matching epic intent
3. Apply INVEST principles, acceptance criteria, platform context

Environment:
- OPENAI_API_KEY: Required for GPT-4o API calls
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, List
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: requests library required. Install: pip install requests", file=sys.stderr)
    sys.exit(1)


class BusinessAnalystAgent:
    """User story generation from epics"""
    
    def __init__(self, openai_api_key: str, repo_root: str = "/workspaces/WAOOAW"):
        self.api_key = openai_api_key
        self.repo_root = Path(repo_root)
        self.foundation_context = self._load_foundation_documents()
    
    def _load_foundation_documents(self) -> Dict[str, str]:
        """Load Foundation documents for BA context"""
        foundation_path = self.repo_root / "main"
        
        docs = {}
        files_to_load = {
            'constitution': 'Foundation.md',
            'ba_charter': 'Foundation/business_analyst_agent_charter.md',
            'ba_capabilities': 'Foundation/business_analyst_enhanced_capabilities.md',
        }
        
        for key, file_path in files_to_load.items():
            full_path = foundation_path / file_path
            if full_path.exists():
                docs[key] = full_path.read_text(encoding='utf-8')
            else:
                print(f"Warning: {full_path} not found", file=sys.stderr)
                docs[key] = ""
        
        # Load docs for brand context
        docs_path = self.repo_root / "docs"
        if (docs_path / "BRAND_STRATEGY.md").exists():
            docs['brand_strategy'] = (docs_path / "BRAND_STRATEGY.md").read_text(encoding='utf-8')
        
        return docs
    
    def generate_stories(self, epic_number: int, epic_title: str, epic_body: str, 
                        story_count: int) -> List[Dict[str, Any]]:
        """Generate user stories from epic
        
        Returns:
            List of stories with structure:
            {
                'index': int,
                'title': str,
                'labels': List[str],
                'body': str (markdown),
                'story_points': int,
                'rice_score': Dict,
                'platform': str
            }
        """
        prompt = self._build_generation_prompt(epic_number, epic_title, epic_body, story_count)
        
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
                        'content': 'You are the Business Analyst Agent for WAOOAW. You create user stories following INVEST principles with deep understanding of the constitutional design.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': 0.7,  # Balance creativity with consistency
                'max_tokens': 6000,
                'response_format': {'type': 'json_object'}
            },
            timeout=90
        )
        
        if response.status_code != 200:
            raise Exception(f"OpenAI API error: {response.status_code} {response.text}")
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        data = json.loads(content)
        
        return data.get('stories', [])
    
    def _build_generation_prompt(self, epic_number: int, epic_title: str, 
                                 epic_body: str, story_count: int) -> str:
        """Build BA story generation prompt"""
        
        return f"""You are the Business Analyst Agent for WAOOAW AI Agent Marketplace.

CONSTITUTIONAL CONTEXT (Foundation.md - Key Principles):
{self.foundation_context['constitution'][:6000]}

YOUR CHARTER (business_analyst_agent_charter.md):
{self.foundation_context['ba_charter'][:4000]}

DESIGN SYSTEM (business_analyst_enhanced_capabilities.md):
{self.foundation_context['ba_capabilities'][:3000]}

EPIC TO ANALYZE:
Epic #{epic_number}: {epic_title}

Description:
{epic_body}

YOUR TASK:
Generate exactly {story_count} user stories following INVEST principles:

**INVEST Principles** (MANDATORY):
- **Independent**: Can be developed separately without dependencies on other stories
- **Negotiable**: Details can be refined with stakeholders
- **Valuable**: Clear business value to users/platform
- **Estimable**: Team can estimate effort (1-13 story points)
- **Small**: Completable in 1-2 sprints
- **Testable**: Clear acceptance criteria (Given/When/Then)

**CRITICAL REQUIREMENTS**:
1. Stories MUST match epic intent (not generic templates!)
2. User-centric language: "As a [role], I want [capability], So that [value]"
3. Clear acceptance criteria in Given/When/Then format
4. Platform-specific context (PP/CP/Plant)
5. Identify code reuse opportunities (existing microservices, components)
6. Constitutional alignment (marketplace DNA, security, approval primitives)

**GUARDRAILS / LIFETIME CONSTRAINTS (MANDATORY)**:
- Every story MUST include a **Constraints (Do Not Break)** section in the story body.
- Treat constraints as lifetime constraints that SA and Coding must enforce.
- Default constraints to include (tailor per story):
    - Avoid refactors unrelated to story scope; prefer minimal, reversible edits.
    - Do not rename or remove public API paths under `/api/*` unless explicitly required; if required, update all tests and clients.
    - Do not change import surfaces used by tests (e.g., patch/mocking targets) without updating tests.
    - For auth/OAuth/JWT work: tests must not make real network calls; preserve stable mocking/patch points.
    - Preflight requirement: changes must pass `pytest --collect-only` for impacted service test suites to prevent import/collection failures.

**REUSABLE COMPONENTS** (prefer over building new):
- Audit Service (Port 8010): System-wide audit logging
- AI Explorer (Port 8008): Prompt templates, token tracking
- Integrations (Port 8009): CRM, payment, communication
- OPA Policy (Port 8013): Trial mode enforcement, RBAC
- PP Gateway (Port 8015): OAuth, RBAC, rate limiting
- Mobile Push (Port 8017): FCM notifications
- Stripe Webhook (Port 8018): Payment events
- Health Aggregator (Port 8019): Service health monitoring
- Finance Service (Port 8007): Subscription tracking, cost monitoring

**OUTPUT FORMAT** (JSON only):
{{
  "stories": [
    {{
      "index": 1,
      "title": "[US-{epic_number}-1] Specific Descriptive Title",
      "labels": ["user-story", "epic-{epic_number}", "priority-must-have"],
    "body": "**As a** [specific role]\\n**I want** [specific capability]\\n**So that** [specific value]\\n\\n**Platform**: PP | CP | Plant\\n**Priority**: P0 (Critical) | P1 (High) | P2 (Medium)\\n\\n**Constraints (Do Not Break)**:\\n- [Constraint 1]\\n- [Constraint 2]\\n- [Constraint 3]\\n\\n**Acceptance Criteria**:\\n1. **Given** [context] **When** [action] **Then** [outcome]\\n2. **Given** [context] **When** [action] **Then** [outcome]\\n3. [4-6 criteria total]\\n\\n**Code Reuse Opportunities**:\\n- Use [existing component] for [capability]\\n- Leverage [pattern/library]\\n\\n**Constitutional Alignment**:\\n- Maintains [principle]\\n- Follows [pattern]\\n\\n**Test Strategy**:\\n- Unit tests: [what to test]\\n- Integration: [what to test]\\n- Performance: [target metric]",
      "story_points": 5,
      "rice_score": {{
        "reach": 80,
        "impact": 90,
        "confidence": 85,
        "effort": 5
      }},
      "platform": "CP"
    }}
  ]
}}

Generate {story_count} stories that actually match the epic intent!
"""


def main():
    parser = argparse.ArgumentParser(description='Business Analyst Agent - User Story Generation')
    parser.add_argument('--epic-number', type=int, required=True, help='Epic issue number')
    parser.add_argument('--epic-title', required=True, help='Epic title')
    parser.add_argument('--epic-body', required=True, help='Epic description')
    parser.add_argument('--story-count', type=int, required=True, help='Number of stories to generate')
    parser.add_argument('--output', default='ba-stories.json', help='Output JSON file')
    
    args = parser.parse_args()
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable required", file=sys.stderr)
        sys.exit(1)
    
    print(f"📝 Business Analyst generating {args.story_count} stories for Epic #{args.epic_number}...")
    
    agent = BusinessAnalystAgent(api_key)
    stories = agent.generate_stories(args.epic_number, args.epic_title, args.epic_body, args.story_count)
    
    # Write output
    output_data = {'stories': stories}
    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Generated {len(stories)} user stories")
    print(f"{'='*60}\n")
    
    for story in stories:
        print(f"{story['index']}. {story['title']}")
        print(f"   Platform: {story.get('platform', 'N/A')} | Points: {story.get('story_points', '?')}")
        print()
    
    print(f"✅ Stories saved to {args.output}")
    sys.exit(0)


if __name__ == '__main__':
    main()
