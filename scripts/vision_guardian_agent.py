#!/usr/bin/env python3
"""Vision Guardian Agent - Constitutional Epic Review

Automatically reviews epics for constitutional alignment, brand integrity, and vision coherence.

Flow:
1. Load Foundation documents (Constitution, charters, brand strategy)
2. Score epic against constitutional principles (0-100)
3. Block (<80), Escalate (60-79), or Approve (80+)

Environment:
- OPENAI_API_KEY: Required for GPT-4o API calls
- GITHUB_TOKEN: Required for GitHub API access
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, Optional
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: requests library required. Install: pip install requests", file=sys.stderr)
    sys.exit(1)


class VisionGuardianAgent:
    """Constitutional epic reviewer"""
    
    def __init__(self, openai_api_key: str, repo_root: str = "/workspaces/WAOOAW"):
        self.api_key = openai_api_key
        self.repo_root = Path(repo_root)
        self.foundation_context = self._load_foundation_documents()
    
    def _load_foundation_documents(self) -> Dict[str, str]:
        """Load all Foundation documents for constitutional context"""
        foundation_path = self.repo_root / "main"
        
        docs = {}
        files_to_load = {
            'constitution': 'Foundation.md',
            'vg_charter': 'Foundation/vision_guardian_agent_charter.md',
            'ba_charter': 'Foundation/business_analyst_agent_charter.md',
            'ba_capabilities': 'Foundation/business_analyst_enhanced_capabilities.md',
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
    
    def review_epic(self, epic_number: int, epic_title: str, epic_body: str) -> Dict[str, Any]:
        """Review epic for constitutional alignment
        
        Returns:
            {
                'score': int (0-100),
                'decision': 'approve' | 'escalate' | 'reject',
                'breakdown': {
                    'l0_constitution': int (0-40),
                    'l1_canonical': int (0-20),
                    'brand_alignment': int (0-20),
                    'technical_excellence': int (0-20)
                },
                'feedback': str,
                'risks': List[str],
                'recommendations': List[str]
            }
        """
        prompt = self._build_review_prompt(epic_number, epic_title, epic_body)
        
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
                        'content': 'You are the Vision Guardian Agent for WAOOAW. Your role is to enforce constitutional compliance and protect the platform vision.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': 0.2,  # Low temperature for consistent scoring
                'max_tokens': 3000,
                'response_format': {'type': 'json_object'}
            },
            timeout=60
        )
        
        if response.status_code != 200:
            raise Exception(f"OpenAI API error: {response.status_code} {response.text}")
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        return json.loads(content)
    
    def _build_review_prompt(self, epic_number: int, epic_title: str, epic_body: str) -> str:
        """Build VG review prompt with full Foundation context"""
        
        return f"""You are the Vision Guardian Agent reviewing Epic #{epic_number}.

CONSTITUTIONAL CONTEXT:

{self.foundation_context['constitution'][:8000]}

YOUR CHARTER (Abridged):
{self.foundation_context['vg_charter'][:4000]}

EPIC TO REVIEW:
Title: {epic_title}
Body:
{epic_body}

YOUR TASK:
Score this epic on constitutional alignment (0-100):

1. **L0 Constitution** (40 points max):
   - "Agents Earn Your Business" philosophy preserved?
   - Deny-by-default security posture maintained?
   - Approval primitives respected?
   - Marketplace DNA (try-before-hire, agent personality)?
   - Precedent seed discipline followed?

2. **L1 Canonical Model** (20 points max):
   - Fits 13 microservice architecture?
   - Uses component reuse library?
   - Follows governance protocols?
   - Constitutional compliance path clear?

3. **Brand Alignment** (20 points max):
   - Dark theme, neon accents (#0a0a0a, #00f2fe) design system?
   - Marketplace feel (not generic SaaS)?
   - Agent personality, status, discovery?
   - "WAOOAW" brand positioning maintained?

4. **Technical Excellence** (20 points max):
   - Clear scope and success criteria?
   - Realistic implementation approach?
   - Security, performance, observability considered?
   - Avoids technical debt creation?

SCORING RULES:
- **80-100**: ✅ Approve (constitutional, proceed to BA/SA)
- **60-79**: ⚠️ Escalate (borderline, needs Governor review)
- **0-59**: ❌ Reject (constitutional violation or unclear intent)

OUTPUT (JSON only):
{{
  "score": <int 0-100>,
  "decision": "approve" | "escalate" | "reject",
  "breakdown": {{
    "l0_constitution": <int 0-40>,
    "l1_canonical": <int 0-20>,
    "brand_alignment": <int 0-20>,
    "technical_excellence": <int 0-20>
  }},
  "feedback": "<2-3 sentences explaining score>",
  "risks": ["<risk 1>", "<risk 2>"],
  "recommendations": ["<recommendation 1>", "<recommendation 2>"]
}}
"""


def main():
    parser = argparse.ArgumentParser(description='Vision Guardian Agent - Constitutional Epic Review')
    parser.add_argument('--epic-number', type=int, required=True, help='Epic issue number')
    parser.add_argument('--epic-title', required=True, help='Epic title')
    parser.add_argument('--epic-body', required=True, help='Epic description')
    parser.add_argument('--output', default='vg-review.json', help='Output JSON file')
    
    args = parser.parse_args()
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable required", file=sys.stderr)
        sys.exit(1)
    
    print(f"🛡️  Vision Guardian reviewing Epic #{args.epic_number}...")
    
    agent = VisionGuardianAgent(api_key)
    result = agent.review_epic(args.epic_number, args.epic_title, args.epic_body)
    
    # Write output
    with open(args.output, 'w') as f:
        json.dump(result, f, indent=2)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Vision Guardian Score: {result['score']}/100")
    print(f"Decision: {result['decision'].upper()}")
    print(f"{'='*60}")
    print(f"\nBreakdown:")
    print(f"  L0 Constitution:     {result['breakdown']['l0_constitution']}/40")
    print(f"  L1 Canonical Model:  {result['breakdown']['l1_canonical']}/20")
    print(f"  Brand Alignment:     {result['breakdown']['brand_alignment']}/20")
    print(f"  Technical Excellence: {result['breakdown']['technical_excellence']}/20")
    print(f"\nFeedback: {result['feedback']}")
    
    if result['risks']:
        print(f"\nRisks Identified:")
        for risk in result['risks']:
            print(f"  ⚠️  {risk}")
    
    if result['recommendations']:
        print(f"\nRecommendations:")
        for rec in result['recommendations']:
            print(f"  💡 {rec}")
    
    # Exit code based on decision
    if result['decision'] == 'reject':
        print(f"\n❌ Epic REJECTED by Vision Guardian (score {result['score']} < 80)")
        sys.exit(1)
    elif result['decision'] == 'escalate':
        print(f"\n⚠️  Epic ESCALATED to Governor (score {result['score']} 60-79)")
        sys.exit(2)
    else:
        print(f"\n✅ Epic APPROVED by Vision Guardian (score {result['score']} >= 80)")
        sys.exit(0)


if __name__ == '__main__':
    main()
