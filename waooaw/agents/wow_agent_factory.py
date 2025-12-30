"""
WowAgentFactory - Autonomous Platform CoE Agent Generator

The factory agent that generates other Platform CoE agents! This agent:
1. Conducts interactive questionnaire to gather agent requirements
2. Validates requirements against architecture principles
3. Generates agent code from templates
4. Provisions decentralized identity (DID)
5. Creates GitHub PR for review
6. Awaits WowVision approval before deployment

Story: #77 Factory Core Logic (5 pts)
Epic: #68 WowAgentFactory Core (v0.4.1)
Theme: CONCEIVE
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from waooaw.core.waooaw_agent import WAAOOWAgent
from waooaw.factory.templates.base_coe_template import BasePlatformCoE
from waooaw.factory.interfaces.coe_interface import (
    WakeEvent,
    DecisionRequest,
    ActionContext,
    TaskDefinition,
    EventType,
    DecisionMethod,
    ActionStatus
)
from waooaw.factory.registry import AgentRegistry, AgentMetadata, AgentStatus, AgentTier

logger = logging.getLogger(__name__)


# =============================================================================
# FACTORY AGENT
# =============================================================================

class WowAgentFactory(BasePlatformCoE):
    """
    Autonomous agent generator for Platform CoE agents.
    
    Capabilities:
    - can:generate-agent-code: Generate Python code from templates
    - can:conduct-questionnaire: Interactive requirements gathering
    - can:provision-did: Create decentralized identities
    - can:create-pull-request: Submit code for review
    - can:validate-architecture: Ensure compliance with principles
    
    Constraints:
    - requires-wowvision-approval: Cannot deploy without guardian approval
    - max-10-agents-per-month: Rate limit for platform stability
    - must-use-base-template: All agents inherit from BasePlatformCoE
    
    Dependencies:
    - WowVision Prime (approval)
    - GitHub API (PR creation)
    - Agent Registry (tracking)
    """
    
    def __init__(self):
        """Initialize factory agent"""
        super().__init__(
            agent_id="WowAgentFactory",
            did="did:waooaw:factory",
            capabilities={
                "generation": [
                    "can:generate-agent-code",
                    "can:render-templates",
                    "can:write-tests"
                ],
                "validation": [
                    "can:validate-architecture",
                    "can:run-linters",
                    "can:check-compliance"
                ],
                "deployment": [
                    "can:provision-did",
                    "can:create-pull-request",
                    "can:submit-for-review"
                ],
                "interaction": [
                    "can:conduct-questionnaire",
                    "can:gather-requirements",
                    "can:clarify-specs"
                ]
            },
            constraints=[
                {
                    "rule": "requires-wowvision-approval",
                    "reason": "Quality gate before deployment",
                    "enforced_by": "WowVisionPrime"
                },
                {
                    "rule": "max-10-agents-per-month",
                    "reason": "Platform stability and review capacity",
                    "limit": 10
                },
                {
                    "rule": "must-use-base-template",
                    "reason": "Architectural consistency",
                    "template": "BasePlatformCoE"
                }
            ]
        )
        
        self.registry = AgentRegistry()
        self.generated_agents: List[str] = []
        self.pending_approvals: Dict[str, Dict[str, Any]] = {}
        
        logger.info(f"✅ {self.agent_id} initialized")
    
    # =========================================================================
    # WAKE PROTOCOL
    # =========================================================================
    
    async def should_wake(self, event: WakeEvent) -> bool:
        """
        Determine if factory should wake for event.
        
        Wakes on:
        - factory.* (direct invocations)
        - github:issue:new-agent-request (issue-based requests)
        - github:pr:approved (deployment triggers)
        
        Args:
            event: Wake event
        
        Returns:
            True if should wake
        """
        # Direct factory commands
        if event.pattern_matches("factory.*"):
            logger.info(f"🔔 Factory waking: {event.event_type} - {event.source}")
            return True
        
        # GitHub issue with "new-agent" label
        if event.event_type == EventType.GITHUB_ISSUE:
            labels = event.data.get("labels", [])
            if "new-agent" in labels:
                logger.info(f"🔔 Factory waking: New agent request from issue")
                return True
        
        # Approved PRs (for deployment)
        if event.event_type == EventType.GITHUB_PR and event.data.get("action") == "approved":
            pr_title = event.data.get("title", "")
            if pr_title.startswith("[WowAgentFactory]"):
                logger.info(f"🔔 Factory waking: PR approved for deployment")
                return True
        
        return False
    
    # =========================================================================
    # DECISION FRAMEWORK
    # =========================================================================
    
    async def make_decision(self, request: DecisionRequest) -> Dict[str, Any]:
        """
        Make decision about agent generation.
        
        Args:
            request: Decision request
        
        Returns:
            Decision with action plan
        """
        logger.info(f"🤔 Factory deciding: {request.decision_type}")
        
        # Get similar cases from memory
        similar_cases = await self._get_similar_cases(request)
        
        # Check constraints
        if len(self.generated_agents) >= 10:  # Monthly limit
            return {
                "decision": "reject",
                "reason": "Monthly agent generation limit reached (10/10)",
                "action": "wait_until_next_month",
                "confidence": 1.0
            }
        
        # Analyze requirements
        if request.decision_type == "should_generate_agent":
            spec = request.context.get("spec", {})
            
            # Validate tier
            tier = spec.get("tier")
            if not tier or tier not in [1, 2, 3, 4, 5, 6]:
                return {
                    "decision": "clarify",
                    "reason": "Invalid or missing tier (must be 1-6)",
                    "action": "request_tier_clarification"
                }
            
            # Validate dependencies
            dependencies = spec.get("dependencies", [])
            for dep in dependencies:
                if not self.registry.get_agent(dep):
                    return {
                        "decision": "defer",
                        "reason": f"Missing dependency: {dep}",
                        "action": "wait_for_dependency",
                        "blocked_by": dep
                    }
            
            # Check for duplicates
            existing = self.registry.get_agent(spec.get("agent_id"))
            if existing:
                return {
                    "decision": "reject",
                    "reason": f"Agent already exists: {spec['agent_id']}",
                    "action": "suggest_update_instead"
                }
            
            # All checks passed
            return {
                "decision": "approve",
                "reason": "Spec validated, no blockers",
                "action": "proceed_with_generation",
                "confidence": 0.9,
                "method": DecisionMethod.RULE_BASED
            }
        
        # Default: clarify
        return {
            "decision": "clarify",
            "reason": "Unknown decision type",
            "action": "request_more_context"
        }
    
    async def _get_similar_cases(self, request: DecisionRequest) -> List[Dict[str, Any]]:
        """Get similar cases from memory"""
        # TODO: Integrate with WowMemory for semantic search
        return []
    
    # =========================================================================
    # ACTION EXECUTION
    # =========================================================================
    
    async def act(self, context: ActionContext) -> Dict[str, Any]:
        """
        Execute factory action.
        
        Args:
            context: Action context
        
        Returns:
            Action result
        """
        logger.info(f"⚡ Factory acting: {context.action_type}")
        
        if context.action_type == "generate_agent_code":
            return await self._generate_agent_code(context)
        
        elif context.action_type == "provision_did":
            return await self._provision_did(context)
        
        elif context.action_type == "create_pull_request":
            return await self._create_pull_request(context)
        
        elif context.action_type == "conduct_questionnaire":
            return await self._conduct_questionnaire(context)
        
        else:
            return {
                "status": ActionStatus.FAILED,
                "error": f"Unknown action type: {context.action_type}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _generate_agent_code(self, context: ActionContext) -> Dict[str, Any]:
        """
        Generate agent code from template.
        
        Args:
            context: Action context with spec
        
        Returns:
            Generated code and metadata
        """
        spec = context.parameters.get("spec", {})
        
        # TODO: Integrate with template engine (Story 6)
        # TODO: Integrate with code generator (Story 9)
        
        logger.info(f"🏗️  Generating code for {spec.get('agent_id')}...")
        
        # Placeholder: Return template structure
        code = f'''"""
{spec.get('name')} - {spec.get('description')}

Generated by WowAgentFactory
"""

from waooaw.factory.templates.base_coe_template import BasePlatformCoE

class {spec.get('agent_id')}(BasePlatformCoE):
    """
    {spec.get('description')}
    
    Tier: {spec.get('tier')}
    Domain: {spec.get('domain')}
    """
    
    def __init__(self):
        super().__init__(
            agent_id="{spec.get('agent_id')}",
            did="{spec.get('did')}",
            capabilities={spec.get('capabilities', {})},
            constraints={spec.get('constraints', [])}
        )
    
    async def should_wake(self, event) -> bool:
        \"\"\"Wake protocol\"\"\"
        # TODO: Implement wake logic
        return False
    
    async def make_decision(self, request) -> dict:
        \"\"\"Decision framework\"\"\"
        # TODO: Implement decision logic
        return {{"decision": "approve"}}
    
    async def act(self, context) -> dict:
        \"\"\"Execute actions\"\"\"
        # TODO: Implement action logic
        return {{"status": "completed"}}
'''
        
        return {
            "status": ActionStatus.COMPLETED,
            "result": {
                "code": code,
                "agent_id": spec.get("agent_id"),
                "file_path": f"waooaw/agents/{spec.get('agent_id').lower()}.py"
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def _provision_did(self, context: ActionContext) -> Dict[str, Any]:
        """
        Provision decentralized identifier.
        
        Args:
            context: Action context
        
        Returns:
            DID document
        """
        agent_id = context.parameters.get("agent_id")
        
        # TODO: Integrate with DID registry
        did = f"did:waooaw:{agent_id.lower().replace('wow', '')}"
        
        logger.info(f"🆔 Provisioned DID: {did}")
        
        return {
            "status": ActionStatus.COMPLETED,
            "result": {
                "did": did,
                "document": {
                    "@context": "https://www.w3.org/ns/did/v1",
                    "id": did,
                    "authentication": [],
                    "service": []
                }
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def _create_pull_request(self, context: ActionContext) -> Dict[str, Any]:
        """
        Create GitHub pull request.
        
        Args:
            context: Action context
        
        Returns:
            PR details
        """
        spec = context.parameters.get("spec", {})
        code = context.parameters.get("code", "")
        
        # TODO: Integrate with GitHub API
        
        pr_title = f"[WowAgentFactory] Add {spec.get('agent_id')}"
        pr_body = f"""
## New Platform CoE Agent: {spec.get('name')}

**Tier:** {spec.get('tier')}  
**Domain:** {spec.get('domain')}  
**DID:** {spec.get('did')}

### Description
{spec.get('description')}

### Capabilities
{', '.join(sum(spec.get('capabilities', {}).values(), []))}

### Dependencies
{', '.join(spec.get('dependencies', []))}

---

🤖 Generated by WowAgentFactory  
⏰ {datetime.now().isoformat()}  
🔍 Awaiting WowVision Prime approval
"""
        
        logger.info(f"📝 Created PR: {pr_title}")
        
        return {
            "status": ActionStatus.COMPLETED,
            "result": {
                "pr_number": 999,  # Placeholder
                "pr_url": f"https://github.com/waooaw/platform/pull/999",
                "title": pr_title,
                "body": pr_body
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def _conduct_questionnaire(self, context: ActionContext) -> Dict[str, Any]:
        """
        Conduct interactive questionnaire.
        
        Args:
            context: Action context
        
        Returns:
            Collected spec
        """
        # TODO: Integrate with questionnaire system (Story 8)
        
        logger.info(f"📋 Starting questionnaire...")
        
        return {
            "status": ActionStatus.COMPLETED,
            "result": {
                "spec": {
                    "agent_id": "WowExample",
                    "name": "WowExample",
                    "tier": 3,
                    "domain": "example",
                    "capabilities": {},
                    "dependencies": []
                }
            },
            "timestamp": datetime.now().isoformat()
        }
    
    # =========================================================================
    # TASK EXECUTION
    # =========================================================================
    
    async def execute_task(self, task: TaskDefinition) -> Dict[str, Any]:
        """
        Execute factory task.
        
        Args:
            task: Task definition
        
        Returns:
            Task result
        """
        logger.info(f"📋 Factory executing task: {task.task_id} - {task.description}")
        
        if task.task_type == "create_new_agent":
            return await self._task_create_new_agent(task)
        
        elif task.task_type == "update_existing_agent":
            return await self._task_update_existing_agent(task)
        
        elif task.task_type == "deploy_agent":
            return await self._task_deploy_agent(task)
        
        else:
            return {
                "task_id": task.task_id,
                "status": "failed",
                "error": f"Unknown task type: {task.task_type}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _task_create_new_agent(self, task: TaskDefinition) -> Dict[str, Any]:
        """
        Full agent creation workflow.
        
        Steps:
        1. Conduct questionnaire
        2. Make decision (approve/reject)
        3. Generate code
        4. Provision DID
        5. Create PR
        6. Register in agent registry
        7. Wait for approval
        
        Args:
            task: Task definition
        
        Returns:
            Creation result
        """
        logger.info(f"🏭 Creating new agent...")
        
        # Step 1: Questionnaire
        questionnaire_context = ActionContext(
            action_type="conduct_questionnaire",
            parameters=task.parameters,
            timeout=300
        )
        questionnaire_result = await self.act(questionnaire_context)
        spec = questionnaire_result["result"]["spec"]
        
        # Step 2: Decision
        decision_request = DecisionRequest(
            decision_type="should_generate_agent",
            context={"spec": spec},
            constraints=[]
        )
        decision = await self.make_decision(decision_request)
        
        if decision["decision"] != "approve":
            return {
                "task_id": task.task_id,
                "status": "rejected",
                "reason": decision["reason"],
                "timestamp": datetime.now().isoformat()
            }
        
        # Step 3: Generate code
        code_context = ActionContext(
            action_type="generate_agent_code",
            parameters={"spec": spec},
            timeout=60
        )
        code_result = await self.act(code_context)
        
        # Step 4: Provision DID
        did_context = ActionContext(
            action_type="provision_did",
            parameters={"agent_id": spec["agent_id"]},
            timeout=30
        )
        did_result = await self.act(did_context)
        spec["did"] = did_result["result"]["did"]
        
        # Step 5: Create PR
        pr_context = ActionContext(
            action_type="create_pull_request",
            parameters={"spec": spec, "code": code_result["result"]["code"]},
            timeout=60
        )
        pr_result = await self.act(pr_context)
        
        # Step 6: Register in agent registry
        metadata = AgentMetadata(
            agent_id=spec["agent_id"],
            did=spec["did"],
            name=spec.get("name", spec["agent_id"]),
            tier=AgentTier(spec["tier"]),
            version="0.4.2",
            status=AgentStatus.PROVISIONED,
            capabilities=spec.get("capabilities", {}),
            dependencies=spec.get("dependencies", []),
            description=spec.get("description", "")
        )
        self.registry.register_agent(metadata)
        
        # Track generation
        self.generated_agents.append(spec["agent_id"])
        self.pending_approvals[spec["agent_id"]] = {
            "pr_number": pr_result["result"]["pr_number"],
            "created_at": datetime.now(),
            "spec": spec
        }
        
        logger.info(f"✅ Agent creation complete: {spec['agent_id']}")
        logger.info(f"📝 PR #{pr_result['result']['pr_number']} awaiting approval")
        
        return {
            "task_id": task.task_id,
            "status": "completed",
            "result": {
                "agent_id": spec["agent_id"],
                "did": spec["did"],
                "pr_number": pr_result["result"]["pr_number"],
                "pr_url": pr_result["result"]["pr_url"],
                "status": "awaiting_approval"
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def _task_update_existing_agent(self, task: TaskDefinition) -> Dict[str, Any]:
        """Update existing agent"""
        # TODO: Implement update logic
        return {
            "task_id": task.task_id,
            "status": "not_implemented",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _task_deploy_agent(self, task: TaskDefinition) -> Dict[str, Any]:
        """Deploy approved agent"""
        # TODO: Integrate with deployment system (Story 10)
        agent_id = task.parameters.get("agent_id")
        self.registry.mark_deployed(agent_id)
        
        return {
            "task_id": task.task_id,
            "status": "completed",
            "result": {
                "agent_id": agent_id,
                "status": "deployed"
            },
            "timestamp": datetime.now().isoformat()
        }


# =============================================================================
# USAGE EXAMPLES
# =============================================================================

"""
Example: Using WowAgentFactory

```python
import asyncio
from waooaw.agents.wow_agent_factory import WowAgentFactory
from waooaw.factory.interfaces.coe_interface import WakeEvent, EventType, TaskDefinition

async def main():
    # Initialize factory
    factory = WowAgentFactory()
    
    # Example 1: Create new agent via task
    task = TaskDefinition(
        task_id="create-wow-example",
        task_type="create_new_agent",
        description="Create WowExample agent for testing",
        parameters={
            "initial_spec": {
                "agent_id": "WowExample",
                "tier": 3,
                "domain": "example"
            }
        },
        priority=1
    )
    
    result = await factory.execute_task(task)
    print(f"Task result: {result}")
    
    # Example 2: Wake factory for event
    event = WakeEvent(
        event_id="evt_001",
        event_type=EventType.CUSTOM,
        source="user",
        timestamp=datetime.now(),
        data={"action": "create_agent"},
        pattern="factory.create"
    )
    
    if await factory.should_wake(event):
        print("Factory woke up!")
    
    # Example 3: Check registry stats
    registry = factory.registry
    stats = registry.get_statistics()
    print(f"Platform stats: {stats}")

if __name__ == "__main__":
    asyncio.run(main())
```
"""
