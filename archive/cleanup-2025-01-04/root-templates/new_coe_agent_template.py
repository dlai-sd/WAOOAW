"""
New CoE Agent Template - Week 15-18 Implementation
Use this template to create new agents (13 remaining CoEs)
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from waooaw.agents.base_agent import WAAOOWAgent, AgentSpecialization, Constraint


class WowNewAgent(WAAOOWAgent):
    """
    [Agent Name] - [One-line description]
    
    Specialization: [Domain]
    Role: [Guardian/Specialist/Advisory]
    Industry: [Marketing/Education/Sales/Support]
    
    Responsibilities:
    - [Responsibility 1]
    - [Responsibility 2]
    - [Responsibility 3]
    
    INSTRUCTIONS TO DEVELOPER:
    1. Rename class to match agent (e.g., WowContentMarketing)
    2. Update docstring with agent details
    3. Fill in _load_specialization() with agent's CoE definition
    4. Implement _try_deterministic_decision() with agent-specific rules
    5. Update execute_task() with agent-specific logic
    6. Add agent to waooaw/config/coe_specs/ directory
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize agent"""
        super().__init__(
            agent_id='wow_new_agent',  # CHANGE THIS
            config=config
        )
    
    # =========================================================================
    # REQUIRED OVERRIDES
    # =========================================================================
    
    def _load_specialization(self) -> AgentSpecialization:
        """
        Define agent's CoE template.
        
        FILL IN WITH AGENT-SPECIFIC DETAILS:
        - coe_name: Agent name (e.g., "WowContent Marketing")
        - coe_type: Guardian, Specialist, or Advisory
        - domain: What domain (e.g., "Content Marketing")
        - expertise: One-liner description
        - core_responsibilities: 3-5 key responsibilities
        - capabilities: Dict of capability categories
        - constraints: What agent CANNOT do
        - skill_requirements: What skills agent needs
        """
        return AgentSpecialization(
            # IDENTITY
            coe_name="WowNewAgent",  # CHANGE THIS
            coe_type="Specialist",  # Guardian, Specialist, or Advisory
            domain="[Your Domain]",  # e.g., "Content Marketing"
            expertise="[One-line description of expertise]",
            version="1.0.0",
            
            # RESPONSIBILITIES (3-5 items)
            core_responsibilities=[
                "[Responsibility 1]",
                "[Responsibility 2]",
                "[Responsibility 3]",
            ],
            
            # CAPABILITIES (Grouped by category)
            capabilities={
                "technical": [
                    "[Technical capability 1]",
                    "[Technical capability 2]",
                ],
                "business": [
                    "[Business capability 1]",
                    "[Business capability 2]",
                ],
                "domain": [
                    "[Domain-specific capability 1]",
                    "[Domain-specific capability 2]",
                ]
            },
            
            # CONSTRAINTS (What agent CANNOT do)
            constraints=[
                Constraint(
                    action="[action agent cannot do]",
                    reason="[why this constraint exists]"
                ),
                Constraint(
                    action="[another constrained action]",
                    reason="[reason]"
                )
            ],
            
            # SKILL REQUIREMENTS (What agent needs to operate)
            skill_requirements=[
                "[Required skill 1]",
                "[Required skill 2]",
            ]
        )
    
    def _try_deterministic_decision(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Deterministic rules for this agent (85% of decisions should be here).
        
        IMPLEMENT AGENT-SPECIFIC RULES:
        - File type checks
        - Content pattern matching
        - Domain-specific validations
        - Constraint checking
        
        Return None if no deterministic rule matches (will fall back to LLM).
        """
        # Example: File type filtering
        file_path = request.get('file_path', '')
        
        # Rule 1: Only handle specific file types
        if not any(file_path.endswith(ext) for ext in ['.md', '.txt', '.html']):
            return {
                'approved': False,
                'reason': 'File type not in scope',
                'confidence': 1.0,
                'method': 'deterministic',
                'cost': 0.0
            }
        
        # Rule 2: Check constraints
        action = request.get('action', '')
        if self.specialization.is_constrained(action):
            return {
                'approved': False,
                'reason': f'Constraint violation: {self.specialization.is_constrained(action)}',
                'confidence': 1.0,
                'method': 'deterministic',
                'cost': 0.0
            }
        
        # Rule 3: Agent-specific validation
        # ADD YOUR RULES HERE
        # Example:
        # if 'keyword' in content.lower():
        #     return {'approved': False, 'reason': '...'}
        
        # No deterministic match, use LLM
        return None
    
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent-specific task.
        
        IMPLEMENT AGENT LOGIC:
        1. Extract task data
        2. Validate/process
        3. Make decision (deterministic → cached → LLM)
        4. Generate output (issue/comment/report)
        5. Return result
        """
        # Example implementation
        file_path = task.get('file_path')
        content = task.get('content', '')
        
        # 1. Try deterministic decision
        decision = self._try_deterministic_decision(task)
        if decision:
            return decision
        
        # 2. Check semantic cache (vector search)
        # cached_decision = self.vector_memory.search_similar(task)
        # if cached_decision and cached_decision.confidence > 0.9:
        #     return cached_decision
        
        # 3. Use LLM for complex reasoning
        decision = self._ask_llm(task, context=[])
        
        # 4. Generate output (issue, comment, report)
        # if not decision['approved']:
        #     self.output_generator.create_issue(...)
        
        # 5. Save decision for future caching
        self._save_decision(task, decision)
        
        return decision
    
    # =========================================================================
    # OPTIONAL: AGENT-SPECIFIC METHODS
    # =========================================================================
    
    def _validate_content(self, content: str) -> List[str]:
        """
        Agent-specific content validation.
        
        Returns list of violations.
        """
        violations = []
        
        # ADD VALIDATION LOGIC HERE
        # Example:
        # if 'banned_word' in content.lower():
        #     violations.append("Contains banned word")
        
        return violations
    
    def _get_pending_tasks(self) -> List[Dict[str, Any]]:
        """
        Get agent-specific pending tasks.
        
        Override if agent has custom task queue.
        """
        # Example: Query database for pending items
        # return self.db.execute("SELECT * FROM tasks WHERE agent_id = %s", (self.agent_id,))
        
        return []


# ============================================
# EXAMPLE: WowContent Marketing Agent
# ============================================

class WowContentMarketing(WAAOOWAgent):
    """
    Content Marketing Agent - Healthcare Specialist
    
    Specialization: Content Marketing
    Role: Specialist
    Industry: Marketing
    
    Responsibilities:
    - Create healthcare-focused blog posts
    - Validate medical content accuracy
    - SEO optimization for healthcare keywords
    - HIPAA compliance checking
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__('wow_content_marketing', config)
    
    def _load_specialization(self) -> AgentSpecialization:
        """WowContent Marketing specialization"""
        return AgentSpecialization(
            coe_name="WowContent Marketing",
            coe_type="Specialist",
            domain="Content Marketing",
            expertise="Healthcare content creation with HIPAA compliance and SEO optimization",
            version="1.0.0",
            
            core_responsibilities=[
                "Create healthcare-focused blog posts and articles",
                "Validate medical content for accuracy and compliance",
                "Optimize content for healthcare-related SEO keywords",
                "Ensure HIPAA compliance in all content",
                "Generate content calendars and topic clusters"
            ],
            
            capabilities={
                "technical": [
                    "Healthcare content writing",
                    "SEO keyword research and optimization",
                    "Content management system (CMS) integration",
                    "Analytics and performance tracking"
                ],
                "business": [
                    "Content strategy development",
                    "Audience persona creation",
                    "Competitor content analysis",
                    "ROI measurement for content"
                ],
                "domain": [
                    "HIPAA compliance verification",
                    "Medical terminology accuracy",
                    "Healthcare industry trends",
                    "Patient education content"
                ]
            },
            
            constraints=[
                Constraint(
                    action="provide medical advice",
                    reason="Not a licensed medical professional"
                ),
                Constraint(
                    action="handle protected health information (PHI)",
                    reason="HIPAA compliance - no direct PHI access"
                ),
                Constraint(
                    action="approve content without medical review",
                    reason="Medical content requires licensed professional review"
                )
            ],
            
            skill_requirements=[
                "Healthcare content writing",
                "SEO best practices",
                "HIPAA compliance knowledge",
                "Medical terminology"
            ]
        )
    
    def _try_deterministic_decision(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Healthcare content validation rules"""
        content = request.get('content', '').lower()
        
        # Rule 1: HIPAA keywords (must escalate)
        hipaa_keywords = ['patient name', 'ssn', 'medical record number', 'phi']
        if any(keyword in content for keyword in hipaa_keywords):
            return {
                'approved': False,
                'reason': 'Potential PHI detected - requires manual review',
                'confidence': 1.0,
                'method': 'deterministic',
                'cost': 0.0,
                'escalate_to_human': True
            }
        
        # Rule 2: Medical claims (require disclaimer)
        medical_claims = ['cures', 'treats', 'prevents', 'diagnoses']
        if any(claim in content for claim in medical_claims):
            return {
                'approved': False,
                'reason': 'Medical claims require disclaimer and review',
                'confidence': 1.0,
                'method': 'deterministic',
                'cost': 0.0,
                'recommendation': 'Add medical disclaimer'
            }
        
        # Rule 3: Minimum word count for SEO
        word_count = len(content.split())
        if word_count < 300:
            return {
                'approved': False,
                'reason': f'Content too short for SEO ({word_count} words, need 300+)',
                'confidence': 1.0,
                'method': 'deterministic',
                'cost': 0.0
            }
        
        # No deterministic match
        return None
    
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute content validation/creation"""
        # Implementation similar to template above
        pass


# ============================================
# DEPLOYMENT CHECKLIST
# ============================================

"""
When deploying new agent:

1. Create agent file in waooaw/agents/<industry>/<agent_name>.py
2. Define specialization (use this template)
3. Implement deterministic rules (85% of decisions)
4. Add to agent registry (waooaw/config/agents.yaml)
5. Create tests (tests/test_<agent_name>.py)
6. Add to CoE Coordinator routing logic
7. Create agent card for marketplace (frontend/data/agents/<agent_name>.json)
8. Document in docs/agents/<agent_name>.md
9. Deploy to staging for shadow mode testing
10. Monitor for 1 week before production

TESTING CHECKLIST:
- [ ] Unit tests (deterministic rules)
- [ ] Integration tests (with sibling agents)
- [ ] Shadow mode (compare with existing logic)
- [ ] Cost testing (verify <$X per day)
- [ ] Load testing (handle expected volume)
"""
