# WAOOAW Agent System

**Base Agent Core Architecture + WowVision Prime**

---

## Overview

This directory contains the foundational agent system for the WAOOAW platform:

- **Base Agent Class** (`WAAOOWAgent`): Common capabilities for all 14 CoEs
- **WowVision Prime**: First production agent (Vision Guardian)
- **Memory System**: PostgreSQL + Pinecone vector storage
- **Decision Framework**: Hybrid deterministic + LLM reasoning
- **GitHub Integration**: Autonomous operation and escalation

---

## Directory Structure

```
waooaw/
├── agents/                  # Agent implementations
│   ├── base_agent.py       # WAAOOWAgent base class
│   └── wowvision_prime.py  # Vision Guardian agent
├── memory/                  # Memory system
│   └── vector_memory.py    # Pinecone integration
├── vision/                  # Vision stack
│   └── vision_stack.py     # 3-layer vision management
├── database/                # Database schemas
│   └── base_agent_schema.sql
├── config/                  # Configuration
│   ├── agent_config.yaml   # Config template
│   └── loader.py           # Config loader
├── logs/                    # Log files (gitignored)
├── main.py                  # Entry point
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

---

## Quick Start

### 1. Install Dependencies

```bash
cd waooaw
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file:

```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/waooaw
GITHUB_TOKEN=ghp_xxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxx
PINECONE_API_KEY=xxxxx  # Optional
```

### 3. Initialize Database

```bash
psql $DATABASE_URL < database/base_agent_schema.sql
```

### 4. Run WowVision Prime

```bash
# Single wake cycle
python main.py wake_up

# Watch mode (continuous)
python main.py watch --interval 300

# Dry run (no actual changes)
python main.py --dry-run wake_up
```

---

## Architecture

See [`docs/BASE_AGENT_CORE_ARCHITECTURE.md`](../docs/BASE_AGENT_CORE_ARCHITECTURE.md) for complete architecture documentation.

### Key Components

**1. WAAOOWAgent (Base Class)**
- 6-step wake-up protocol
- Hybrid decision framework
- Persistent memory
- GitHub integration
- Learning & improvement

**2. WowVision Prime (First Agent)**
- Enforces vision stack
- Validates file creations
- Reviews PRs
- Processes escalations
- Learns violation patterns

**3. Memory System**
- PostgreSQL: Structured data
- Pinecone: Vector embeddings
- Redis: Decision cache (planned)

**4. Decision Framework**
- Tier 1: Decision cache (free, instant)
- Tier 2: Deterministic logic (free, <1ms)
- Tier 3: Vector memory (~$0.0001)
- Tier 4: LLM reasoning (~$0.05-0.15)

---

## Usage Examples

### Single Wake Cycle

```bash
python main.py wake_up
```

Output:
```
🌅 WowVision-Prime waking up (wake #0)
✅ Identity: WowVision Prime - Phase phase1_foundation
📚 Loaded context version 0
🤝 0 pending handoffs
🧠 Applied 3 learnings
📋 Found 2 pending tasks
🔨 Executing task: validate_file_creation
✅ Validated: docs/example.md (method=deterministic)
💾 Saved context (version 0)
💤 WowVision-Prime sleeping (wake #1)
```

### Watch Mode

```bash
python main.py watch --interval 60
```

Runs continuously, waking every 60 seconds.

### Dry Run

```bash
python main.py --dry-run wake_up
```

Simulates execution without making actual changes (GitHub issues, database writes).

---

## Configuration

Edit `config/agent_config.yaml` or create `config/agent_config.local.yaml`:

```yaml
agent:
  id: "WowVision-Prime"
  version: "1.0.0"

database:
  url: "${DATABASE_URL}"

github:
  token: "${GITHUB_TOKEN}"
  repo: "dlai-sd/WAOOAW"

anthropic:
  api_key: "${ANTHROPIC_API_KEY}"
  model: "claude-sonnet-4.5-20250514"

logging:
  level: "INFO"
  file: "logs/wowvision-prime.log"

wake_schedule:
  type: "cron"
  schedule: "*/5 * * * *"  # Every 5 minutes
```

Environment variables can be referenced with `${VAR}` or `${VAR:-default}`.

---

## Development

### Create New Agent

```python
from waooaw.agents.base_agent import WAAOOWAgent, Decision

class MyAgent(WAAOOWAgent):
    def __init__(self, config):
        super().__init__(agent_id="MyAgent", config=config)
    
    def _restore_identity(self):
        self.role = "My Custom Role"
    
    def execute_task(self, task):
        # Implement task execution
        pass
    
    def _get_pending_tasks(self):
        # Return list of tasks
        return []
```

### Run Tests

```bash
pytest
pytest --cov=waooaw
```

### Lint Code

```bash
black waooaw/
flake8 waooaw/
mypy waooaw/
```

---

## Deployment

### GitHub Actions

See [`.github/workflows/wowvision-prime.yml`](../.github/workflows/wowvision-prime.yml) for automated deployment.

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY waooaw/ ./waooaw/
RUN pip install -r waooaw/requirements.txt
CMD ["python", "waooaw/main.py", "watch", "--interval", "300"]
```

### Kubernetes

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: wowvision-prime
spec:
  schedule: "*/5 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: agent
            image: waooaw/wowvision-prime:latest
            command: ["python", "waooaw/main.py", "wake_up"]
```

---

## Monitoring

### Logs

```bash
# Follow logs
tail -f logs/wowvision-prime.log

# Search logs
grep "Violation" logs/wowvision-prime.log
```

### Database Queries

```sql
-- Recent wake cycles
SELECT agent_id, version, created_at 
FROM agent_context 
WHERE agent_id = 'WowVision-Prime'
ORDER BY version DESC LIMIT 10;

-- Pending escalations
SELECT * FROM human_escalations 
WHERE status = 'pending';

-- Decision method distribution
SELECT method, COUNT(*) 
FROM decision_cache 
GROUP BY method;

-- LLM costs
SELECT DATE(created_at), COUNT(*), SUM(CAST(decision_data->>'cost' AS NUMERIC))
FROM decision_cache
WHERE method = 'llm'
GROUP BY DATE(created_at);
```

---

## Troubleshooting

### Agent won't start

```bash
# Check database connection
psql $DATABASE_URL -c "SELECT 1"

# Check GitHub token
gh auth status

# Enable debug logging
LOG_LEVEL=DEBUG python main.py wake_up
```

### No tasks found

Ensure GitHub repository has recent activity (commits, PRs).

### LLM errors

Check Anthropic API key and billing:
```bash
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01"
```

---

## Cost Optimization

**Expected monthly cost per agent**: ~$25

- PostgreSQL: $0 (shared)
- Pinecone: ~$5 (shared across agents)
- Claude API: ~$20 (200 decisions/day)

**Cost reduction strategies**:
1. Decision caching (60% cache hits = $0)
2. Deterministic logic (30% = $0)
3. Vector memory (8% = ~$0.08)
4. LLM only when needed (2% = ~$20)

---

## Next Steps

1. ✅ Deploy WowVision Prime
2. ⏳ Build WowDomain (second CoE)
3. ⏳ Implement remaining 12 CoEs
4. ⏳ Add telemetry & dashboards
5. ⏳ Optimize costs based on usage

---

## Documentation

- [Base Agent Architecture](../docs/BASE_AGENT_CORE_ARCHITECTURE.md)
- [Setup Guide](../docs/WOWVISION_PRIME_SETUP.md)
- [Product Spec](../docs/PRODUCT_SPEC.md)
- [Data Dictionary](../docs/DATA_DICTIONARY.md)

---

## Support

- **Issues**: Create GitHub issue with label `wowvision-prime`
- **Email**: agents@waooaw.ai
- **Slack**: `#wowvision-prime`

---

*Last Updated: December 2024*  
*Version: 1.0.0*
