# WAOOAW Infrastructure Setup Scripts

This directory contains automated setup and verification scripts for the WAOOAW platform infrastructure.

## Scripts Overview

### 1. `setup_github_secrets.sh`

**Purpose**: Configure GitHub repository secrets for infrastructure access.

**Requirements**:
- GitHub CLI (`gh`) installed and authenticated
- Repository admin access

**Usage**:
```bash
bash scripts/setup_github_secrets.sh
```

**Secrets Configured**:
- `DATABASE_URL` - PostgreSQL connection string (Supabase)
- `PINECONE_API_KEY` - Pinecone vector database API key
- `PINECONE_INDEX_HOST` - Pinecone index host URL
- `PINECONE_INDEX_NAME` - Pinecone index name
- (Optional) `ANTHROPIC_API_KEY` - Claude API key (add later)

---

### 2. `init_database.py`

**Purpose**: Initialize PostgreSQL database with all required schemas.

**Requirements**:
- Python 3.11+
- `psycopg2-binary` package
- `DATABASE_URL` environment variable

**Usage**:
```bash
export DATABASE_URL='postgresql://postgres:PASSWORD@HOST:5432/DATABASE'
python scripts/init_database.py
```

**What It Does**:
1. Connects to PostgreSQL database
2. Creates 5 vision schema tables (from `vision/schema.sql`)
3. Creates 10 base agent schema tables (from `waooaw/database/base_agent_schema.sql`)
4. Initializes default state data
5. Verifies all tables created successfully

**Tables Created** (15 total):
- Vision: `agent_context`, `agent_decisions`, `vision_violations`, `human_escalations`, `agent_health`
- Base: `wowvision_memory`, `conversation_sessions`, `conversation_messages`, `knowledge_base`, `decision_cache`, `wowvision_state`, `agent_handoffs`, `agent_metrics`, etc.

---

### 3. `verify_infrastructure.py`

**Purpose**: Test all infrastructure components to ensure they're working correctly.

**Requirements**:
- Python 3.11+
- `psycopg2-binary`, `pinecone-client`, `anthropic` packages
- Environment variables for all services

**Usage**:
```bash
export DATABASE_URL='postgresql://...'
export PINECONE_API_KEY='pcsk_...'
export PINECONE_INDEX_HOST='...'
export PINECONE_INDEX_NAME='wowvision-memory'
export ANTHROPIC_API_KEY='sk-ant-...'  # Optional

python scripts/verify_infrastructure.py
```

**Tests Performed**:
- ✅ PostgreSQL: Connection, table queries, write/read operations
- ✅ Pinecone: Connection, vector stats, upsert/query operations
- ⏸️ Anthropic: API connection, simple completion (optional)

**Exit Codes**:
- `0` - All tests passed (or Anthropic not configured)
- `1` - One or more tests failed

---

## Quick Start Guide

### Step 1: Install Dependencies

```bash
# Install GitHub CLI (if not already installed)
# macOS
brew install gh

# Ubuntu/Debian
sudo apt install gh

# Windows
winget install GitHub.cli

# Authenticate
gh auth login
```

```bash
# Install Python dependencies
pip install psycopg2-binary pinecone-client anthropic python-dotenv
```

### Step 2: Configure GitHub Secrets

```bash
cd /path/to/WAOOAW
bash scripts/setup_github_secrets.sh
```

### Step 3: Initialize Database

```bash
export DATABASE_URL='postgresql://postgres:20251212SD*&!@db.xgxhumsivyikvxzgueho.supabase.co:5432/postgres'
python scripts/init_database.py
```

### Step 4: Verify Infrastructure

```bash
export DATABASE_URL='postgresql://...'
export PINECONE_API_KEY='pcsk_1rCgp_...'
export PINECONE_INDEX_HOST='wowvision-memory-hf97t0h.svc.aped-4627-b74a.pinecone.io'
export PINECONE_INDEX_NAME='wowvision-memory'

python scripts/verify_infrastructure.py
```

---

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `PINECONE_API_KEY` | Pinecone API key | `pcsk_1rCgp_...` |
| `PINECONE_INDEX_HOST` | Pinecone index host | `wowvision-memory-xxx.svc.aped-4627-b74a.pinecone.io` |
| `PINECONE_INDEX_NAME` | Pinecone index name | `wowvision-memory` |

### Optional

| Variable | Description | Example |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Claude API key (for full LLM capability) | `sk-ant-api03-...` |

---

## Troubleshooting

### Database Connection Issues

**Problem**: `psycopg2.OperationalError: could not connect to server`

**Solutions**:
1. Verify `DATABASE_URL` is correct
2. Check network connectivity to database host
3. Verify database credentials
4. Ensure database server is running

```bash
# Test connection directly
psql "$DATABASE_URL" -c "SELECT 1;"
```

### Pinecone Connection Issues

**Problem**: `PineconeException: Index not found`

**Solutions**:
1. Verify index name matches exactly
2. Check index exists in Pinecone dashboard
3. Verify API key has correct permissions
4. Ensure index host URL is correct

```python
# List all indexes
from pinecone import Pinecone
pc = Pinecone(api_key='YOUR_KEY')
print(pc.list_indexes())
```

### GitHub CLI Not Authenticated

**Problem**: `gh: Not authenticated with GitHub CLI`

**Solution**:
```bash
gh auth login
# Follow prompts to authenticate
```

### Module Not Found Errors

**Problem**: `ModuleNotFoundError: No module named 'psycopg2'`

**Solution**:
```bash
pip install psycopg2-binary pinecone-client anthropic
```

---

## CI/CD Integration

These scripts are used in the GitHub Actions workflow at `.github/workflows/wowvision-prime.yml`.

**Workflow Steps**:
1. Checkout repository
2. Set up Python 3.11
3. Install dependencies from `waooaw/requirements.txt`
4. Run `verify_infrastructure.py` (tests all services)
5. Run `python waooaw/main.py wake_up` (start WowVision Prime)

**Environment Variables** (from GitHub Secrets):
- All required environment variables are automatically loaded from repository secrets
- No manual configuration needed in CI/CD

---

## Security Best Practices

### Credential Handling

✅ **DO**:
- Store credentials in GitHub Secrets (encrypted)
- Use environment variables for sensitive data
- Rotate credentials regularly
- Use read-only credentials where possible

❌ **DON'T**:
- Commit credentials to repository
- Share credentials in plain text
- Use credentials in log output
- Store credentials in code

### Access Control

- Limit repository admin access
- Review GitHub Actions logs regularly
- Monitor API usage for anomalies
- Enable 2FA on all accounts

---

## Maintenance

### Regular Tasks

**Weekly**:
- Review infrastructure verification logs
- Check database storage usage
- Monitor API usage and costs

**Monthly**:
- Clean old data (use SQL cleanup functions)
- Review and rotate credentials
- Update dependencies

**Quarterly**:
- Security audit
- Performance optimization
- Cost analysis

---

## Support

**Documentation**: See `/docs/INFRASTRUCTURE_SETUP_COMPLETE.md` for detailed setup guide

**Issues**: Report problems at https://github.com/dlai-sd/WAOOAW/issues

**Questions**: Contact repository maintainers

---

## Version History

- **v1.0** (2025-12-24): Initial release
  - GitHub secrets setup script
  - Database initialization script
  - Infrastructure verification script
  - Complete documentation

---

*Last updated: December 24, 2025*
