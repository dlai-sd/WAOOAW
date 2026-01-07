# WowVision Prime - Vision Guardian CoE

**CoE Type**: Guardian  
**Domain**: Architecture & Vision Validation  
**Status**: ✅ Active (First Production Agent)

---

## Overview

WowVision Prime is WAOOAW's first production agent, serving as the Vision Guardian for the platform. It validates that all architectural decisions, code, and documentation align with WAOOAW's core vision and principles.

**Key Responsibilities:**
- Validate architectural decisions against vision documents
- Review code for vision compliance
- Ensure documentation reflects platform philosophy
- Guard against scope creep and vision drift

---

## Documentation in This Folder

| Document | Purpose | Audience |
|----------|---------|----------|
| [WOWVISION_PRIME_SETUP.md](./WOWVISION_PRIME_SETUP.md) | Complete setup & deployment guide | Developers, DevOps |
| [schema.sql](./schema.sql) | Database schema for WowVision tables | Database admins |

---

## Quick Links

**Implementation:**
- Agent Code: [waooaw/agents/wowvision_prime.py](../../waooaw/agents/wowvision_prime.py)
- Vision Stack: [waooaw/vision/vision_stack.py](../../waooaw/vision/vision_stack.py)
- Base Agent: [waooaw/agents/base_agent.py](../../waooaw/agents/base_agent.py)

**Related Documentation:**
- [Base Agent Architecture](../BASE_AGENT_CORE_ARCHITECTURE.md)
- [Data Dictionary](../DATA_DICTIONARY.md)
- [Product Spec](../PRODUCT_SPEC.md)

**Templates:**
- [New CoE Agent Template](../../templates/new_coe_agent_template.py) - Use this to create similar agents

---

## Agent Characteristics

**Specialization:**
- **Domain**: Vision & Architecture Validation
- **Expertise**: WAOOAW platform vision, architectural principles
- **Type**: Guardian (protects platform integrity)

**Personality:**
- Precise and principle-driven
- Proactive in spotting vision drift
- Collaborative with other CoEs

**Constraints:**
- Cannot modify core vision (read-only on vision docs)
- Cannot make business decisions (escalates to human)
- Cannot approve changes that violate constraints

---

## Status & Metrics

**Current Version**: v0.2  
**Implementation Status**: 80% complete
- ✅ Dual-identity framework
- ✅ Specialization defined
- ✅ Decision framework (deterministic + LLM)
- ✅ Database schema
- 🟡 Output generation (needs GitHub integration)
- ⏳ Event-driven wake (Week 1-2)

**Performance (Target):**
- Wake frequency: On-demand (event-driven)
- Decision latency: <500ms (95th percentile)
- Cost: <$3/month
- Accuracy: 95%+ vision compliance detection

---

## Usage Examples

### As First Production Agent
```python
from waooaw.agents.wowvision_prime import WowVisionPrime

# Initialize
agent = WowVisionPrime({
    'db_config': {...},
    'github_token': '...',
    'llm_api_key': '...'
})

# Wake and execute
agent.wake_up()
```

### As Template for New CoEs
WowVision Prime serves as the reference implementation for all 14 CoEs. See [new_coe_agent_template.py](../../templates/new_coe_agent_template.py) for guidance.

---

## Development Roadmap

### ✅ Completed (v0.1 - v0.2)
- Specialization definition
- Database schema
- Decision framework
- Base integration

### 🔄 In Progress (v0.3)
- Event-driven wake (Week 1-2)
- GitHub issue creation (Week 3-4)
- PR commenting (Week 3-4)

### 📅 Planned
- v0.4: Daily reports
- v0.5: Resource budgets
- v0.8: Learning from feedback
- v1.0: Full 15-dimension compliance

---

## Related CoEs

**Coordination:**
- Reports to: Platform Coordinator (Week 13-14)
- Collaborates with: All 14 CoEs
- Escalates to: Human architects

**Similar CoEs (To Be Created):**
- WowSecurity Guardian (Security validation)
- WowQuality Guardian (Code quality)
- WowCompliance Guardian (Regulatory compliance)

---

## Getting Help

**Setup Issues:** See [WOWVISION_PRIME_SETUP.md](./WOWVISION_PRIME_SETUP.md)  
**Architecture Questions:** See [BASE_AGENT_CORE_ARCHITECTURE.md](../BASE_AGENT_CORE_ARCHITECTURE.md)  
**General Questions:** See [DOC_INDEX.md](../../DOC_INDEX.md)

---

_WowVision Prime: The first agent that makes you say "WOW" at architecture quality_ 🚀
