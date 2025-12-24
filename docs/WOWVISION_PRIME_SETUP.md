# WowVision Prime - Setup & Deployment Guide

**WAOOAW Platform Vision Guardian**

*Complete setup guide for deploying WowVision Prime agent*

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Infrastructure Setup](#infrastructure-setup)
3. [Environment Configuration](#environment-configuration)
4. [Database Initialization](#database-initialization)
5. [Local Testing](#local-testing)
6. [GitHub Actions Deployment](#github-actions-deployment)
7. [Monitoring & Observability](#monitoring--observability)
8. [Troubleshooting](#troubleshooting)
9. [Maintenance](#maintenance)

---

## Prerequisites

### Required Accounts & Access

- **GitHub**: Repository access with admin permissions
- **PostgreSQL**: Database server (v14+)
- **Pinecone**: Vector database account (free tier works)
- **Anthropic**: Claude API access (pay-as-you-go)

### Local Development Tools

```bash
# Required
Python 3.11+
PostgreSQL 14+
Git

# Optional (for development)
Docker Desktop
VS Code / PyCharm
pgAdmin / DBeaver
```

### Cost Estimate

**Monthly operational costs**:
- PostgreSQL: $0 (shared with platform)
- Pinecone: ~$5 (shared across agents)
- Claude API: ~$20 (200 decisions/day)
- GitHub Actions: $0 (within free tier)

**Total**: ~$25/month

---

## Infrastructure Setup

### 1. PostgreSQL Database

#### Option A: Local PostgreSQL

```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql
```

```sql
CREATE DATABASE waooaw;
CREATE USER waooaw_agent WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE waooaw TO waooaw_agent;
\q
```

#### Option B: Managed PostgreSQL (Recommended for Production)

**AWS RDS**:
```bash
# Create RDS PostgreSQL instance via AWS Console
# - Engine: PostgreSQL 14+
# - Instance class: db.t3.micro (free tier)
# - Storage: 20GB SSD
# - Public access: Yes (with security group)
# - Database name: waooaw
```

**Supabase** (Free tier):
```bash
# 1. Create project at https://supabase.com
# 2. Get connection string from project settings
# 3. Connection string format:
#    postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
```

**Neon** (Free tier):
```bash
# 1. Create project at https://neon.tech
# 2. Get connection string
# 3. Format: postgresql://[USER]:[PASSWORD]@[HOST]/[DATABASE]
```

---

### 2. Pinecone Vector Database

```bash
# 1. Sign up at https://www.pinecone.io (free tier: 1M vectors)
# 2. Create index via dashboard:

Name: waooaw-memory
Dimensions: 1536  # OpenAI text-embedding-3-small
Metric: cosine
Region: us-west1-gcp (or nearest)

# 3. Get API key from dashboard → API Keys
```

**Via Pinecone CLI** (optional):
```bash
pip install pinecone-client

python -c "
import pinecone
pinecone.init(api_key='YOUR_API_KEY')
pinecone.create_index(
    'waooaw-memory',
    dimension=1536,
    metric='cosine'
)
"
```

---

### 3. Anthropic Claude API

```bash
# 1. Sign up at https://console.anthropic.com
# 2. Navigate to API Keys
# 3. Create new API key
# 4. Save key securely (starts with 'sk-ant-')

# Test API key
curl https://api.anthropic.com/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-sonnet-4.5-20250514",
    "max_tokens": 100,
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

---

### 4. GitHub Token

```bash
# Create Personal Access Token (classic)
# Settings → Developer settings → Personal access tokens → Tokens (classic)

# Required scopes:
# - repo (full control)
# - workflow (update workflows)

# Or use GitHub CLI
gh auth login
gh auth token  # Get token
```

---

## Environment Configuration

### 1. Create Environment File

**File**: `waooaw/.env`

```bash
# Database
DATABASE_URL=postgresql://waooaw_agent:secure_password@localhost:5432/waooaw
DB_HOST=localhost
DB_PORT=5432
DB_NAME=waooaw
DB_USER=waooaw_agent
DB_PASSWORD=secure_password

# GitHub
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GITHUB_REPO=dlai-sd/WAOOAW

# Pinecone
PINECONE_API_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX=waooaw-memory

# Anthropic
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Agent Configuration
AGENT_ID=WowVision-Prime
ENVIRONMENT=development
LOG_LEVEL=INFO

# Optional: OpenAI (for embeddings)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 2. Secure Environment Variables

**Never commit `.env` to Git**:
```bash
# Add to .gitignore
echo "waooaw/.env" >> .gitignore
echo "*.env" >> .gitignore
echo ".env.local" >> .gitignore
```

**For GitHub Actions**, add secrets:
```bash
gh secret set DATABASE_URL --body "postgresql://user:pass@host/db"
gh secret set GITHUB_TOKEN --body "ghp_xxxxx"
gh secret set PINECONE_API_KEY --body "xxxxx"
gh secret set ANTHROPIC_API_KEY --body "sk-ant-xxxxx"
```

---

## Database Initialization

### 1. Install Database Schema

```bash
# Navigate to repository
cd /path/to/WAOOAW

# Connect to database
psql -h localhost -U waooaw_agent -d waooaw

# Run schema
\i waooaw/database/base_agent_schema.sql

# Verify tables
\dt
```

Expected tables:
- `agent_context`
- `wowvision_memory`
- `conversation_sessions`
- `conversation_messages`
- `knowledge_base`
- `decision_cache`
- `human_escalations`
- `agent_handoffs`
- `wowvision_state`

### 2. Initialize Agent State

```sql
-- Set initial platform phase
INSERT INTO wowvision_state (state_key, state_value)
VALUES ('current_phase', '{"phase": "phase1_foundation", "started_at": "2024-12-24T00:00:00Z"}');

-- Create initial agent context
INSERT INTO agent_context (agent_id, context_type, context_data, version)
VALUES (
    'WowVision-Prime',
    'initialization',
    '{"initialized_at": "2024-12-24T00:00:00Z", "version": "1.0.0"}',
    0
);

-- Verify
SELECT * FROM wowvision_state;
SELECT * FROM agent_context;
```

### 3. Seed Knowledge Base (Optional)

```sql
-- Add initial learnings
INSERT INTO knowledge_base (category, title, content, confidence, source)
VALUES
(
    'WowVision-Prime-core-constraints',
    'Phase 1: No Python Code Generation',
    '{"rule": "NEVER generate Python code in Phase 1", "reason": "Foundation phase focuses on architecture"}',
    1.0,
    'waooaw-core.yaml'
),
(
    'WowVision-Prime-policies',
    'Markdown files always allowed',
    '{"rule": "Markdown files (.md) are always allowed", "file_types": [".md", ".markdown"]}',
    1.0,
    'waooaw-policies.yaml'
);
```

---

## Local Testing

### 1. Install Dependencies

```bash
cd /path/to/WAOOAW/waooaw

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Verify Installation

```bash
# Test imports
python -c "
from agents.base_agent import WAAOOWAgent
from agents.wowvision_prime import WowVisionPrime
from memory.vector_memory import VectorMemory
from vision.vision_stack import VisionStack
print('✅ All imports successful')
"
```

### 3. Test Database Connection

```bash
python -c "
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()
cur.execute('SELECT version();')
print('✅ Database connected:', cur.fetchone()[0])
conn.close()
"
```

### 4. Test API Connections

```bash
# Test GitHub
python -c "
from github import Github
import os
from dotenv import load_dotenv

load_dotenv()
g = Github(os.getenv('GITHUB_TOKEN'))
repo = g.get_repo(os.getenv('GITHUB_REPO'))
print('✅ GitHub connected:', repo.full_name)
"

# Test Anthropic
python -c "
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
print('✅ Anthropic connected')
"

# Test Pinecone
python -c "
from pinecone import Pinecone
import os
from dotenv import load_dotenv

load_dotenv()
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
print('✅ Pinecone connected')
print('Indexes:', pc.list_indexes())
"
```

### 5. Run WowVision Prime Locally

```bash
# Single wake cycle
python waooaw/main.py wake_up

# Watch mode (continuous)
python waooaw/main.py watch --interval 300  # Every 5 minutes

# Dry run (no actual changes)
python waooaw/main.py wake_up --dry-run

# Verbose logging
LOG_LEVEL=DEBUG python waooaw/main.py wake_up
```

### 6. Test Specific Functionality

```bash
# Test decision making
python -c "
from agents.wowvision_prime import WowVisionPrime
from config.loader import load_config

config = load_config()
agent = WowVisionPrime(config)

decision = agent.make_decision({
    'type': 'create_file',
    'path': 'test.py',
    'agent_id': 'test',
    'commit_sha': 'abc123'
})

print(f'Decision: {decision.approved}')
print(f'Reason: {decision.reason}')
print(f'Method: {decision.method}')
"

# Test memory storage
python -c "
from agents.wowvision_prime import WowVisionPrime
from config.loader import load_config

config = load_config()
agent = WowVisionPrime(config)

agent.store_memory(
    'test',
    'test_memory',
    {'content': 'This is a test memory', 'importance': 0.8}
)

memories = agent.recall_memory('test memory')
print(f'Recalled {len(memories)} memories')
"
```

---

## GitHub Actions Deployment

### 1. Create Workflow File

**File**: `.github/workflows/wowvision-prime.yml`

```yaml
name: WowVision Prime Agent

on:
  schedule:
    # Run every 5 minutes
    - cron: '*/5 * * * *'
  
  # Manual trigger
  workflow_dispatch:
    inputs:
      dry_run:
        description: 'Dry run (no actual changes)'
        required: false
        default: 'false'
  
  # Webhook trigger
  repository_dispatch:
    types: [vision-check, file-created, pr-opened]

jobs:
  run-wowvision-prime:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          cd waooaw
          pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Run WowVision Prime
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITHUB_REPO: ${{ github.repository }}
          PINECONE_API_KEY: ${{ secrets.PINECONE_API_KEY }}
          PINECONE_ENVIRONMENT: ${{ secrets.PINECONE_ENVIRONMENT }}
          PINECONE_INDEX: ${{ secrets.PINECONE_INDEX }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          AGENT_ID: WowVision-Prime
          ENVIRONMENT: production
          LOG_LEVEL: INFO
        run: |
          cd waooaw
          if [ "${{ github.event.inputs.dry_run }}" = "true" ]; then
            python main.py wake_up --dry-run
          else
            python main.py wake_up
          fi
      
      - name: Upload logs
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: wowvision-logs-${{ github.run_number }}
          path: waooaw/logs/
          retention-days: 7
```

### 2. Set GitHub Secrets

```bash
# Via GitHub CLI
gh secret set DATABASE_URL
gh secret set PINECONE_API_KEY
gh secret set PINECONE_ENVIRONMENT
gh secret set PINECONE_INDEX
gh secret set ANTHROPIC_API_KEY

# Or via GitHub UI:
# Settings → Secrets and variables → Actions → New repository secret
```

### 3. Enable Workflow

```bash
# Push workflow file
git add .github/workflows/wowvision-prime.yml
git commit -m "Add WowVision Prime workflow"
git push

# Verify workflow
gh workflow list
gh workflow view "WowVision Prime Agent"

# Manual trigger
gh workflow run "WowVision Prime Agent"

# Check status
gh run list --workflow="WowVision Prime Agent"
```

### 4. Monitor Workflow

```bash
# Watch logs in real-time
gh run watch

# View specific run
gh run view [RUN_ID]

# Download artifacts
gh run download [RUN_ID]
```

---

## Monitoring & Observability

### 1. Logging

**Log locations**:
- Local: `waooaw/logs/wowvision-prime.log`
- GitHub Actions: Workflow artifacts

**Log format** (JSON):
```json
{
  "timestamp": "2024-12-24T10:00:00Z",
  "level": "INFO",
  "agent_id": "WowVision-Prime",
  "wake_count": 42,
  "message": "Decision made",
  "context": {
    "decision_type": "create_file",
    "method": "deterministic",
    "approved": false
  }
}
```

### 2. Metrics

**Track in database**:
```sql
-- Create metrics table
CREATE TABLE agent_metrics (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Query metrics
SELECT 
    agent_id,
    metric_name,
    AVG(metric_value) as avg_value,
    COUNT(*) as count
FROM agent_metrics
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY agent_id, metric_name;
```

**Key metrics**:
- Wake cycles per day
- Decisions made (by method: cache/deterministic/vector/llm)
- LLM cost per day
- Escalations created
- Tasks executed
- Average wake duration

### 3. Dashboards

**PostgreSQL queries for dashboard**:

```sql
-- Daily activity summary
SELECT 
    DATE(created_at) as date,
    COUNT(*) as wake_cycles,
    COUNT(DISTINCT agent_id) as active_agents
FROM agent_context
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Decision method distribution
SELECT 
    method,
    COUNT(*) as count,
    ROUND(AVG(CASE WHEN approved THEN 1 ELSE 0 END) * 100, 2) as approval_rate
FROM decision_cache
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY method;

-- Top escalation reasons
SELECT 
    escalation_reason,
    COUNT(*) as count,
    status
FROM human_escalations
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY escalation_reason, status
ORDER BY count DESC
LIMIT 10;
```

### 4. Alerts

**Set up alerts for**:
- Agent failures (wake cycle errors)
- High LLM costs (>$5/day)
- Escalation backlog (>10 pending)
- Database connection issues

**Example: Email alert script**:
```python
# alerts/check_escalations.py
import psycopg2
import smtplib
from email.mime.text import MIMEText

def check_escalation_backlog():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT COUNT(*) FROM human_escalations 
        WHERE status = 'pending' 
        AND created_at < NOW() - INTERVAL '1 hour'
    """)
    
    count = cur.fetchone()[0]
    
    if count > 10:
        send_alert(f"High escalation backlog: {count} pending")
    
    conn.close()
```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed

```bash
# Error: psycopg2.OperationalError: could not connect

# Check connection string
echo $DATABASE_URL

# Test connection
psql "$DATABASE_URL"

# Check PostgreSQL is running
sudo systemctl status postgresql

# Check firewall/security group
# Ensure port 5432 is accessible
```

#### 2. Pinecone Index Not Found

```bash
# Error: Index 'waooaw-memory' not found

# List indexes
python -c "
from pinecone import Pinecone
import os
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
print(pc.list_indexes())
"

# Create index if missing
python -c "
from pinecone import Pinecone
import os
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
pc.create_index('waooaw-memory', dimension=1536, metric='cosine')
"
```

#### 3. GitHub API Rate Limit

```bash
# Error: RateLimitExceededException

# Check rate limit status
gh api rate_limit

# Solution: Use GitHub token (higher limits)
# Ensure GITHUB_TOKEN is set correctly
```

#### 4. LLM API Errors

```bash
# Error: AuthenticationError / InsufficientQuotaError

# Check API key
python -c "
import anthropic
import os
client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
print('API key valid')
"

# Check usage/billing
# Visit: https://console.anthropic.com/settings/billing
```

#### 5. Vision Stack Not Loaded

```bash
# Error: VisionStack initialization failed

# Check if vision files exist
ls -la waooaw/vision/
ls -la docs/waooaw-*.yaml 2>/dev/null || echo "Vision YAML files not found"

# Create placeholder vision stack
# (Will be implemented in future)
```

### Debug Mode

```bash
# Enable verbose logging
export LOG_LEVEL=DEBUG

# Run with Python debugger
python -m pdb waooaw/main.py wake_up

# Check recent errors
tail -f waooaw/logs/wowvision-prime.log

# Database query logs
# Add to PostgreSQL config: log_statement = 'all'
```

---

## Maintenance

### Daily Tasks

```bash
# Check agent health
gh run list --workflow="WowVision Prime Agent" --limit 5

# Review escalations
psql "$DATABASE_URL" -c "
SELECT * FROM human_escalations 
WHERE status = 'pending' 
ORDER BY created_at DESC;
"

# Check LLM costs
psql "$DATABASE_URL" -c "
SELECT 
    DATE(created_at) as date,
    COUNT(*) as llm_calls,
    SUM(CAST(context_data->>'cost' AS NUMERIC)) as total_cost
FROM decision_cache
WHERE method = 'llm'
  AND created_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at);
"
```

### Weekly Tasks

```bash
# Clean old decision cache
psql "$DATABASE_URL" -c "
DELETE FROM decision_cache 
WHERE created_at < NOW() - INTERVAL '7 days';
"

# Archive old context snapshots
psql "$DATABASE_URL" -c "
DELETE FROM agent_context 
WHERE created_at < NOW() - INTERVAL '30 days'
  AND context_type = 'wake_cycle';
"

# Review learning effectiveness
psql "$DATABASE_URL" -c "
SELECT 
    category,
    COUNT(*) as learnings,
    AVG(confidence) as avg_confidence
FROM knowledge_base
GROUP BY category;
"
```

### Monthly Tasks

```bash
# Database optimization
psql "$DATABASE_URL" -c "VACUUM ANALYZE;"

# Review and update agent config
vim waooaw/config/agent_config.yaml

# Update dependencies
cd waooaw
pip list --outdated
pip install --upgrade -r requirements.txt

# Security audit
pip-audit
```

### Backup & Recovery

```bash
# Backup database
pg_dump "$DATABASE_URL" > backups/waooaw_$(date +%Y%m%d).sql

# Backup Pinecone index (export vectors)
python -c "
from pinecone import Pinecone
import os
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index('waooaw-memory')
# Fetch and save vectors
# (Implementation depends on vector count)
"

# Restore database
psql "$DATABASE_URL" < backups/waooaw_20241224.sql
```

---

## Next Steps

After successful setup:

1. ✅ **Monitor first 24 hours**: Ensure agent wakes up regularly
2. ✅ **Review first escalations**: Check if vision validation works correctly
3. ✅ **Tune wake schedule**: Adjust based on activity levels
4. ✅ **Optimize costs**: Review LLM usage, improve deterministic rules
5. ✅ **Build WowDomain**: Next CoE inheriting from base

---

## Support

**Documentation**:
- [Base Agent Architecture](BASE_AGENT_CORE_ARCHITECTURE.md)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Pinecone Docs](https://docs.pinecone.io)
- [Anthropic API Docs](https://docs.anthropic.com)

**Issues**:
- Create issue: `gh issue create --label wowvision-prime`
- Check logs: `gh run view --log`

**Community**:
- Slack: `#wowvision-prime`
- Email: agents@waooaw.ai

---

*Last Updated: December 2024*  
*Version: 1.0*
