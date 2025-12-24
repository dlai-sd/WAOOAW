# WAOOAW Vision Stack

**Version:** 1.0  
**Status:** Production Ready  
**Purpose:** Single Source of Truth for autonomous agent coordination

---

## 🎯 Overview

The WAOOAW Vision Stack is a 3-layer system that ensures 200+ agents make consistent decisions while preserving zero context loss. It enables autonomous operation with human control via GitHub mobile.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Immutable Core (waooaw-core.yaml)                │
│  Sacred pillars - Changes require dlai-sd approval only     │
│  - 14 CoEs, Context Preservation, 2-Phase, Component Model  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Dynamic Policies (waooaw-policies.yaml)          │
│  Operational rules - WowVision manages autonomously         │
│  - Phase rules, Escalation triggers, Learned patterns       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: PostgreSQL Context Database                       │
│  Real-time agent state and decision history                 │
│  - 200+ agents, Millions of decisions, Zero context loss    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Database Setup

```bash
# Start PostgreSQL (via Docker Compose)
cd infrastructure/docker
docker-compose up -d postgres

# Initialize schema
docker exec -i waooaw-postgres psql -U waooaw -d waooaw_db < ../../vision/schema.sql

# Verify tables created
docker exec -it waooaw-postgres psql -U waooaw -d waooaw_db -c "\dt"
```

### 2. Python SDK Installation

```bash
# Install dependencies
pip install pyyaml psycopg2-binary

# Test vision stack
python scripts/vision_stack.py --validate
```

### 3. Environment Variables

```bash
# Add to .env file
DATABASE_URL=postgresql://waooaw:waooaw_dev_password@localhost:5432/waooaw_db
VISION_DIR=/home/runner/work/WAOOAW/WAOOAW/vision
GITHUB_TOKEN=<your-token>  # For escalation issues
```

---

## 📋 Files

### Core Vision Files

- **`waooaw-core.yaml`** - Immutable core vision (Layer 1)
  - 14 Centers of Excellence definitions
  - Context preservation requirements
  - 2-phase development approach
  - Component → Skill → Role → Team model
  - Brand identity and quality standards
  
- **`waooaw-policies.yaml`** - Dynamic policies (Layer 2)
  - Phase enforcement rules
  - Escalation policies
  - Learned anti-patterns
  - Agent behavior guidelines
  
- **`schema.sql`** - PostgreSQL database schema (Layer 3)
  - `agent_context` - Context storage with versioning
  - `agent_decisions` - Decision audit trail
  - `vision_violations` - Constraint violation log
  - `human_escalations` - GitHub issue integration
  - `agent_health` - Performance metrics

### Support Files

- **`escalation-template.md`** - Mobile-friendly GitHub issue template
- **`README.md`** - This file
- **`../scripts/vision_stack.py`** - Python SDK

---

## 💻 Usage

### Validating Agent Actions

```python
from scripts.vision_stack import VisionStack
import psycopg2

# Connect to database
db = psycopg2.connect(
    "postgresql://waooaw:waooaw_dev_password@localhost:5432/waooaw_db"
)

# Initialize vision stack
vision = VisionStack(db_connection=db)

# Validate an action
approved, reason, citations = vision.validate_action(
    agent_id="WowDomain",
    action={
        "type": "create_file",
        "path": "docs/marketing-domain.md"
    }
)

if approved:
    print(f"✅ Action approved: {reason}")
    print(f"   Citations: {', '.join(citations)}")
else:
    print(f"❌ Action rejected: {reason}")
    print(f"   Citations: {', '.join(citations)}")
    
    # Escalate to human if needed
    issue_number = vision.escalate_to_human(
        agent_id="WowDomain",
        action=action,
        reason=reason
    )
    print(f"   Escalated to GitHub issue #{issue_number}")
```

### Storing Context

```python
# Update agent context
version = vision.update_context(
    agent_id="WowDomain",
    context_type="domain_specification",
    context_data={
        "industry": "Healthcare",
        "components": ["GPT-4", "Claude", "FHIR API"],
        "skills_count": 18,
        "confidence": 0.97
    }
)

print(f"Context stored as version {version}")

# Retrieve latest context
context = vision.get_context(
    agent_id="WowDomain",
    context_type="domain_specification"
)

print(f"Retrieved context: {context}")

# Time-travel query (get specific version)
old_context = vision.get_context(
    agent_id="WowDomain",
    context_type="domain_specification",
    version=1
)
```

### Handling Escalations

```python
# Escalate high-risk action to human
issue_number = vision.escalate_to_human(
    agent_id="WowOperation",
    action={
        "type": "update_infrastructure",
        "path": "infrastructure/k8s/production.yaml"
    },
    reason="Production infrastructure change requires approval",
    priority="critical"
)

# Check escalation status in database
cursor = db.cursor()
cursor.execute(
    "SELECT * FROM pending_escalations WHERE github_issue_number = %s",
    (issue_number,)
)
escalation = cursor.fetchone()
```

---

## 🗄️ Database Queries

### Common Queries

```sql
-- Get all pending human escalations
SELECT * FROM pending_escalations 
ORDER BY hours_pending DESC;

-- Get agent health summary (last 24 hours)
SELECT * FROM agent_health_summary 
WHERE agent_id = 'WowDomain';

-- Get decision history for an agent
SELECT 
    action_type,
    approved,
    reasoning,
    vision_layer,
    created_at
FROM agent_decisions
WHERE agent_id = 'WowDomain'
ORDER BY created_at DESC
LIMIT 20;

-- Find patterns in violations
SELECT 
    violation_type,
    COUNT(*) as count,
    array_agg(DISTINCT agent_id) as agents
FROM vision_violations
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY violation_type
ORDER BY count DESC;

-- Get latest context for all agents
SELECT 
    agent_id,
    context_type,
    version,
    updated_at
FROM active_agent_contexts
ORDER BY agent_id, context_type;
```

### Time-Travel Queries

```sql
-- Get context at specific point in time
SELECT * FROM agent_context
WHERE agent_id = 'WowDomain'
  AND context_type = 'domain_specification'
  AND created_at <= '2025-12-01 10:00:00'
ORDER BY version DESC
LIMIT 1;

-- Compare context versions
SELECT 
    version,
    context_data->>'industry' as industry,
    context_data->>'confidence' as confidence,
    created_at
FROM agent_context
WHERE agent_id = 'WowDomain'
  AND context_type = 'domain_specification'
ORDER BY version;
```

---

## 🔧 Workflow Integration

The vision stack is integrated into `.github/workflows/continuous-development.yml`:

```yaml
- name: Load Vision Stack
  run: |
    python -c "
    from scripts.vision_stack import VisionStack
    vision = VisionStack()
    print('✅ Vision stack loaded')
    "

- name: Validate Action
  env:
    AGENT_ID: ${{ env.AGENT_ID }}
    ACTION_TYPE: ${{ env.ACTION_TYPE }}
    FILE_PATH: ${{ env.FILE_PATH }}
  run: |
    python -c "
    import os
    from scripts.vision_stack import VisionStack
    
    vision = VisionStack()
    approved, reason, citations = vision.validate_action(
        os.environ['AGENT_ID'],
        {
            'type': os.environ['ACTION_TYPE'],
            'path': os.environ['FILE_PATH']
        }
    )
    
    if not approved:
        print(f'❌ {reason}')
        exit(1)
    "
```

---

## 📱 Mobile Escalation Workflow

1. **Agent triggers escalation** → GitHub issue created using `escalation-template.md`
2. **dlai-sd receives notification** on GitHub mobile app
3. **Quick response** → Comment "APPROVED" or "REJECTED"
4. **Workflow monitors** issue for response
5. **Action proceeds** or is blocked based on response
6. **All captured** in `human_escalations` table

---

## 🧪 Testing

### Unit Tests

```bash
# Test vision stack validation
pytest tests/test_vision_stack.py -v

# Test database schema
pytest tests/test_schema.py -v
```

### Integration Tests

```bash
# Test 100 concurrent agent decisions
python scripts/load_test_vision.py --agents 100 --decisions 1000

# Test escalation workflow
python scripts/test_escalation.py
```

### Manual Testing

```bash
# Validate vision files
python scripts/vision_stack.py --validate

# Test file creation approval (should pass)
python -c "
from scripts.vision_stack import VisionStack
vision = VisionStack()
result = vision.validate_action('WowDomain', {
    'type': 'create_file',
    'path': 'vision/test.sql'
})
print(f'Result: {result}')
"

# Test file creation rejection (should fail)
python -c "
from scripts.vision_stack import VisionStack
vision = VisionStack()
result = vision.validate_action('WowDomain', {
    'type': 'create_file',
    'path': 'backend/test.py'
})
print(f'Result: {result}')
"
```

---

## 📊 Monitoring

### Health Metrics

```sql
-- Agent decision rate (per hour)
SELECT 
    date_trunc('hour', created_at) as hour,
    COUNT(*) as decisions
FROM agent_decisions
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY hour
ORDER BY hour;

-- Approval rate by agent
SELECT 
    agent_id,
    COUNT(*) as total_decisions,
    SUM(CASE WHEN approved THEN 1 ELSE 0 END) as approved,
    ROUND(100.0 * SUM(CASE WHEN approved THEN 1 ELSE 0 END) / COUNT(*), 2) as approval_rate
FROM agent_decisions
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY agent_id
ORDER BY approval_rate DESC;

-- Escalation response time
SELECT 
    AVG(EXTRACT(EPOCH FROM (responded_at - created_at))/3600) as avg_hours,
    MIN(EXTRACT(EPOCH FROM (responded_at - created_at))/3600) as min_hours,
    MAX(EXTRACT(EPOCH FROM (responded_at - created_at))/3600) as max_hours
FROM human_escalations
WHERE status != 'pending'
  AND responded_at IS NOT NULL;
```

### Alerts

Set up alerts for:
- Pending escalations > 12 hours
- Violation rate > 15% for any agent
- Context update failures
- Database connection issues

---

## 🔒 Security

### Access Control

- Vision core file is **read-only** for all agents
- Policies file updated only by WowVision with approval
- Database uses row-level security
- All changes logged and auditable

### Data Protection

- Context data encrypted at rest (PostgreSQL encryption)
- Audit trail immutable (no DELETE operations)
- Secrets not stored in context
- GitHub token secured via environment variables

---

## 🐛 Troubleshooting

### Vision Stack Won't Load

```bash
# Check file existence
ls -l vision/waooaw-core.yaml vision/waooaw-policies.yaml

# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('vision/waooaw-core.yaml'))"
python -c "import yaml; yaml.safe_load(open('vision/waooaw-policies.yaml'))"
```

### Database Connection Failed

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Test connection
docker exec -it waooaw-postgres psql -U waooaw -d waooaw_db -c "SELECT version();"

# Verify schema loaded
docker exec -it waooaw-postgres psql -U waooaw -d waooaw_db -c "\dt"
```

### Actions Always Rejected

```bash
# Check phase settings
python -c "
from scripts.vision_stack import VisionStack
vision = VisionStack()
phase1_active = vision.policies['phase_rules']['phase1_restrictions']['active']
print(f'Phase 1 active: {phase1_active}')
"

# View recent violations
docker exec -it waooaw-postgres psql -U waooaw -d waooaw_db -c "
SELECT violation_type, COUNT(*) 
FROM vision_violations 
WHERE created_at >= NOW() - INTERVAL '1 hour'
GROUP BY violation_type;
"
```

---

## 📚 Reference

### Vision Layers

| Layer | File | Authority | Purpose |
|-------|------|-----------|---------|
| 1 | `waooaw-core.yaml` | dlai-sd only | Immutable sacred pillars |
| 2 | `waooaw-policies.yaml` | WowVision CoE | Dynamic operational rules |
| 3 | PostgreSQL | System | Real-time state & history |

### Phase Rules

| Phase | Status | Python Files | Documentation |
|-------|--------|--------------|---------------|
| 1 | Active | ❌ Rejected | ✅ Allowed |
| 2 | Pending | ✅ Allowed | ✅ Required |

### CoEs (Centers of Excellence)

14 CoEs across 3 tiers:
- **Tier 1 (7):** WowDomain, WowAgentFactory, WowMarketplace, WowCustomer, WowLearning, WowAnalytics, WowCompliance
- **Tier 2 (4):** WowSubscription, WowFinance, WowOperation, WowIntegration
- **Tier 3 (3):** WowSecurity, WowTesting, WowEngineering

---

## 🎯 Success Criteria

- ✅ All 3 vision layers operational
- ✅ PostgreSQL schema deployed
- ✅ Python SDK validates actions
- ✅ Workflow integration complete
- ✅ GitHub escalations mobile-friendly
- ✅ Zero hard-coded vision in code
- ✅ All agents use vision stack

---

## 📞 Support

For issues or questions:
1. Check this README
2. Review vision files (`waooaw-core.yaml`, `waooaw-policies.yaml`)
3. Query database for context
4. Create GitHub issue with escalation template

---

**Powered by WAOOAW Vision Stack v1.0**  
*Enabling autonomous agent coordination at scale*
