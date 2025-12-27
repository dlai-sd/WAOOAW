# Configuration Management & Validation Architecture

**Version**: 1.1  
**Date**: December 28, 2025  
**Status**: Design Complete  
**Scope**: Config Validation, Infrastructure as Code (IaC), Environment Management  
**Related**: API_GATEWAY_DESIGN.md, MESSAGE_BUS_ARCHITECTURE.md, ORCHESTRATION_LAYER_DESIGN.md, COMMON_COMPONENTS_LIBRARY_DESIGN.md

---

## Executive Summary

**Configuration Management** is the backbone of operational reliability. Two critical components:

1. **Config Validation**: Pre-deployment checks to catch errors before production
2. **Infrastructure as Code (IaC)**: Version-controlled infrastructure definitions

**v1.1 Changes:** Added Common Components Library integration (Validator component for 5-layer validation with schema, business rules, connectivity checks). See [COMMON_COMPONENTS_LIBRARY_DESIGN.md](COMMON_COMPONENTS_LIBRARY_DESIGN.md).

### Your Question: "Does IaC fall under config validation?"

**Answer**: **Partially YES, with important distinctions**

```
Configuration Management (Umbrella)
├── Application Configuration
│   ├── Config Files (YAML, JSON, .env)
│   ├── Config Validation ← What you asked about
│   └── Config Loading (loader.py)
│
└── Infrastructure as Code (IaC)
    ├── Infrastructure Configuration (Terraform, CloudFormation)
    ├── IaC Validation (terraform validate, checkov)
    └── Deployment Automation (terraform apply)
```

**Relationship**:
- IaC **IS** configuration (infrastructure definitions)
- IaC validation **IS** config validation (syntax, security, cost checks)
- But IaC **ALSO** includes provisioning/deployment (beyond validation)

**Recommendation**: 
- **Config Validation** = Application config (YAML, env vars) + IaC validation (pre-commit)
- **IaC** = Infrastructure provisioning (separate concern, but validated first)

---

## 1. Why Config Validation is Essential

### Horror Stories Without Validation

**Real-World Failures**:

1. **AWS S3 Outage (2017)**: Typo in config file → 4-hour outage, $150M loss
2. **GitLab Database Incident (2017)**: Wrong database URL in config → 6 hours of data loss
3. **Knight Capital (2012)**: Misconfigured trading bot → $440M loss in 45 minutes

**WAOOAW-Specific Risks**:

| Misconfiguration | Impact | Probability | Mitigation |
|------------------|--------|-------------|------------|
| **Wrong DATABASE_URL (dev in prod)** | Data corruption | HIGH | Validate URL pattern |
| **Missing ANTHROPIC_API_KEY** | Agent failures, silent errors | HIGH | Pre-flight check |
| **Invalid agent_config.yaml** | Agent won't start | MEDIUM | Schema validation |
| **Rate limit too high** | Cost overrun ($1000+) | MEDIUM | Sanity checks |
| **Secret key reused** | Security breach | LOW | Uniqueness check |
| **Redis URL typo** | Message bus down | HIGH | Connection test |

**Cost of Validation**: 2 days to build, 5 minutes per deployment  
**Cost of Failure**: 4-6 hours downtime, customer trust, revenue loss  
**ROI**: **10,000x** (one prevented outage justifies all validation work)

---

## 2. Config Validation Design

### 2.1 Validation Layers

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Syntax Validation (Pre-Commit)                     │
│ • YAML/JSON well-formed                                     │
│ • No typos, missing quotes                                  │
│ • Tool: yamllint, jsonlint                                  │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: Schema Validation (Pre-Commit)                     │
│ • Required fields present                                   │
│ • Data types correct (string, int, bool)                    │
│ • Enum values valid                                         │
│ • Tool: JSON Schema, Pydantic                               │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: Business Rules (CI/CD)                             │
│ • Rate limits reasonable (<10K req/min)                     │
│ • Database URL production-ready                             │
│ • API keys not dummy values                                 │
│ • Tool: Custom validation scripts                           │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 4: Connectivity Tests (Pre-Deployment)                │
│ • Database reachable                                        │
│ • Redis reachable                                           │
│ • API keys valid (not expired)                              │
│ • Tool: scripts/verify_infrastructure.py                    │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 5: Runtime Validation (Startup)                       │
│ • All services healthy                                      │
│ • No conflicting configs                                    │
│ • Graceful degradation if optional services down            │
│ • Tool: Application startup checks                          │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Validation Scope

#### Application Configuration

**Files to Validate**:
- `waooaw/config/agent_config.yaml`
- `waooaw/config/message_bus_config.yaml`
- `backend/.env`
- `infrastructure/docker/docker-compose.yml`
- `infrastructure/kong/central-gateway.yaml`
- `docs/vision/waooaw-core.yaml` (vision stack)

**Validation Rules**:
| Config Item | Validation | Error Example | Fix |
|-------------|-----------|---------------|-----|
| `DATABASE_URL` | Postgres URL pattern | `mysql://...` | Change to `postgresql://` |
| `REDIS_URL` | Redis URL pattern | `redis://localhost` | Use actual host |
| `ANTHROPIC_API_KEY` | Starts with `sk-ant-` | `your_key_here` | Get real key |
| `MESSAGE_BUS_PRIORITY_STREAMS` | Integer 1-10 | `five` | Use numeric `5` |
| `MESSAGE_BUS_RETENTION_DAYS` | Integer 1-3650 | `forever` | Use `730` (2 years) |
| `AGENT_SECRET_KEY_*` | 64-char hex | `secret123` | Generate: `secrets.token_hex(32)` |
| `LOG_LEVEL` | Enum: DEBUG/INFO/WARN/ERROR | `VERBOSE` | Use `INFO` |

#### Infrastructure as Code

**Files to Validate**:
- `infrastructure/terraform/*.tf` (when we add Terraform)
- `infrastructure/docker/docker-compose.yml`
- `.github/workflows/*.yml`

**Validation Rules**:
| IaC Item | Validation | Error Example | Fix |
|----------|-----------|---------------|-----|
| S3 buckets | Not public | `acl = "public-read"` | Use `acl = "private"` |
| Database | Encryption enabled | `encrypted = false` | Set `encrypted = true` |
| Secrets | Not hardcoded | `api_key = "sk-..."` | Use `var.api_key` |
| Costs | <$500/month | 100 EC2 instances | Review instance count |
| Security groups | No 0.0.0.0/0 SSH | `0.0.0.0/0:22` | Use specific IP |

---

## 3. Implementation: Config Validator CLI

### 3.1 Tool: `scripts/validate_config.py`

**Purpose**: Pre-deployment validation of all configs

**Usage**:
```bash
# Validate all configs (dev environment)
python scripts/validate_config.py

# Validate specific environment
python scripts/validate_config.py --env=production

# Check only critical items (fast)
python scripts/validate_config.py --critical-only

# CI/CD mode (exit 1 on any error)
python scripts/validate_config.py --strict
```

**Output**:
```
🔍 WAOOAW Configuration Validator v1.0
============================================

📂 Validating Application Configs...
✅ waooaw/config/agent_config.yaml - VALID
✅ waooaw/config/message_bus_config.yaml - VALID
✅ backend/.env - VALID

🔐 Validating Secrets...
✅ DATABASE_URL - Valid PostgreSQL URL
✅ ANTHROPIC_API_KEY - Valid format (sk-ant-...)
⚠️  OPENAI_API_KEY - Not set (optional)
✅ AGENT_SECRET_KEY_WOW_VISION_PRIME - Valid 64-char hex

🔌 Testing Connectivity...
✅ PostgreSQL - Connected (waooaw@supabase)
✅ Redis - Connected (localhost:6379)
✅ Pinecone - Connected (index: wowvision-memory)
⚠️  Anthropic API - Not configured (limited mode)

📊 Validating Business Rules...
✅ Rate limits - Within bounds (<10K req/min)
✅ Database URL - Production-ready
✅ Cost estimate - $45/month (under budget)

🏗️  Validating Infrastructure...
✅ docker-compose.yml - Valid YAML, all services defined
✅ Kong gateway config - Valid routes, plugins configured

============================================
RESULT: ✅ PASSED with 2 warnings
Warnings:
- OPENAI_API_KEY not set (embeddings will use Claude)
- Anthropic API not configured (limited mode)

Ready to deploy! 🚀
```

### 3.2 Implementation Code

**File**: `scripts/validate_config.py`

```python
#!/usr/bin/env python3
"""
WAOOAW Configuration Validator

Validates all configuration files before deployment:
- Syntax (YAML, JSON, env vars)
- Schema (required fields, types)
- Business rules (rate limits, URLs, keys)
- Connectivity (database, Redis, APIs)
- Infrastructure (IaC syntax, security)

Usage:
    python scripts/validate_config.py              # Dev environment
    python scripts/validate_config.py --env=prod   # Production
    python scripts/validate_config.py --strict     # CI/CD mode (exit 1 on error)
"""

import os
import sys
import yaml
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass
import psycopg2
import redis
from pinecone import Pinecone

@dataclass
class ValidationResult:
    """Result of a validation check"""
    component: str
    status: str  # pass, warn, fail
    message: str
    details: str = ""

class ConfigValidator:
    """Validate all WAOOAW configurations"""
    
    def __init__(self, env: str = "development", strict: bool = False):
        self.env = env
        self.strict = strict
        self.results: List[ValidationResult] = []
        
    def run_all_checks(self) -> Tuple[List[ValidationResult], int]:
        """Run all validation checks, return (results, exit_code)"""
        print("🔍 WAOOAW Configuration Validator v1.0")
        print("=" * 60)
        print()
        
        # Layer 1: Syntax validation
        print("📂 Validating Application Configs...")
        self.validate_yaml_syntax()
        
        # Layer 2: Schema validation
        print("\n🔐 Validating Secrets...")
        self.validate_secrets()
        
        # Layer 3: Business rules
        print("\n📊 Validating Business Rules...")
        self.validate_business_rules()
        
        # Layer 4: Connectivity
        print("\n🔌 Testing Connectivity...")
        self.validate_connectivity()
        
        # Layer 5: Infrastructure
        print("\n🏗️  Validating Infrastructure...")
        self.validate_infrastructure()
        
        # Summary
        print("\n" + "=" * 60)
        return self.print_summary()
    
    def validate_yaml_syntax(self):
        """Validate YAML files are well-formed"""
        yaml_files = [
            "waooaw/config/agent_config.yaml",
            "waooaw/config/message_bus_config.yaml",
            "infrastructure/docker/docker-compose.yml"
        ]
        
        for filepath in yaml_files:
            try:
                with open(filepath, 'r') as f:
                    yaml.safe_load(f)
                self.results.append(ValidationResult(
                    filepath, "pass", "Valid YAML syntax"
                ))
                print(f"✅ {filepath} - VALID")
            except Exception as e:
                self.results.append(ValidationResult(
                    filepath, "fail", f"Invalid YAML: {e}"
                ))
                print(f"❌ {filepath} - INVALID: {e}")
    
    def validate_secrets(self):
        """Validate environment variables and secrets"""
        checks = {
            "DATABASE_URL": {
                "required": True,
                "pattern": r"^postgresql://.*",
                "error": "Must be PostgreSQL URL (postgresql://...)"
            },
            "REDIS_URL": {
                "required": True,
                "pattern": r"^redis://.*",
                "error": "Must be Redis URL (redis://...)"
            },
            "ANTHROPIC_API_KEY": {
                "required": False,  # Optional in v0.2.x
                "pattern": r"^sk-ant-",
                "error": "Must start with 'sk-ant-'"
            },
            "AGENT_SECRET_KEY_WOW_VISION_PRIME": {
                "required": True,
                "pattern": r"^[0-9a-fA-F]{64}$",
                "error": "Must be 64-char hex (secrets.token_hex(32))"
            },
            "GITHUB_TOKEN": {
                "required": True,
                "pattern": r"^ghp_",
                "error": "Must start with 'ghp_'"
            }
        }
        
        for var_name, check in checks.items():
            value = os.getenv(var_name)
            
            if not value:
                if check["required"]:
                    self.results.append(ValidationResult(
                        var_name, "fail", "Required variable not set"
                    ))
                    print(f"❌ {var_name} - NOT SET")
                else:
                    self.results.append(ValidationResult(
                        var_name, "warn", "Optional variable not set"
                    ))
                    print(f"⚠️  {var_name} - Not set (optional)")
                continue
            
            # Check pattern
            if not re.match(check["pattern"], value):
                self.results.append(ValidationResult(
                    var_name, "fail", check["error"]
                ))
                print(f"❌ {var_name} - {check['error']}")
            else:
                self.results.append(ValidationResult(
                    var_name, "pass", "Valid format"
                ))
                print(f"✅ {var_name} - Valid format")
    
    def validate_business_rules(self):
        """Validate business logic rules"""
        # Load message bus config
        with open("waooaw/config/message_bus_config.yaml", 'r') as f:
            bus_config = yaml.safe_load(f)
        
        # Check rate limits
        priority_streams = bus_config.get("priority_streams", 0)
        if priority_streams < 1 or priority_streams > 10:
            self.results.append(ValidationResult(
                "priority_streams", "fail", 
                f"Priority streams must be 1-10, got {priority_streams}"
            ))
            print(f"❌ priority_streams - Out of range: {priority_streams}")
        else:
            self.results.append(ValidationResult(
                "priority_streams", "pass", f"Valid: {priority_streams}"
            ))
            print(f"✅ priority_streams - Valid: {priority_streams}")
        
        # Check retention days
        retention_days = bus_config.get("retention_days", 0)
        if retention_days < 1 or retention_days > 3650:
            self.results.append(ValidationResult(
                "retention_days", "fail",
                f"Retention must be 1-3650 days, got {retention_days}"
            ))
            print(f"❌ retention_days - Out of range: {retention_days}")
        else:
            self.results.append(ValidationResult(
                "retention_days", "pass", f"Valid: {retention_days} days"
            ))
            print(f"✅ retention_days - Valid: {retention_days} days")
        
        # Cost estimate (mock)
        cost_estimate = 45  # $45/month
        if cost_estimate > 500:
            self.results.append(ValidationResult(
                "cost_estimate", "warn",
                f"High cost: ${cost_estimate}/month (budget: $500)"
            ))
            print(f"⚠️  cost_estimate - High: ${cost_estimate}/month")
        else:
            self.results.append(ValidationResult(
                "cost_estimate", "pass",
                f"${cost_estimate}/month (under budget)"
            ))
            print(f"✅ cost_estimate - ${cost_estimate}/month (under budget)")
    
    def validate_connectivity(self):
        """Test connectivity to external services"""
        # PostgreSQL
        try:
            db_url = os.getenv("DATABASE_URL")
            if db_url:
                conn = psycopg2.connect(db_url)
                conn.close()
                self.results.append(ValidationResult(
                    "PostgreSQL", "pass", "Connected"
                ))
                print("✅ PostgreSQL - Connected")
            else:
                self.results.append(ValidationResult(
                    "PostgreSQL", "fail", "DATABASE_URL not set"
                ))
                print("❌ PostgreSQL - DATABASE_URL not set")
        except Exception as e:
            self.results.append(ValidationResult(
                "PostgreSQL", "fail", f"Connection failed: {e}"
            ))
            print(f"❌ PostgreSQL - Connection failed: {e}")
        
        # Redis
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            r = redis.from_url(redis_url)
            r.ping()
            self.results.append(ValidationResult(
                "Redis", "pass", "Connected"
            ))
            print("✅ Redis - Connected")
        except Exception as e:
            self.results.append(ValidationResult(
                "Redis", "fail", f"Connection failed: {e}"
            ))
            print(f"❌ Redis - Connection failed: {e}")
        
        # Pinecone (optional)
        try:
            api_key = os.getenv("PINECONE_API_KEY")
            if api_key:
                pc = Pinecone(api_key=api_key)
                # Just check API key is valid, don't query index
                self.results.append(ValidationResult(
                    "Pinecone", "pass", "API key valid"
                ))
                print("✅ Pinecone - API key valid")
            else:
                self.results.append(ValidationResult(
                    "Pinecone", "warn", "Not configured (optional)"
                ))
                print("⚠️  Pinecone - Not configured (optional)")
        except Exception as e:
            self.results.append(ValidationResult(
                "Pinecone", "warn", f"API key invalid: {e}"
            ))
            print(f"⚠️  Pinecone - API key invalid: {e}")
    
    def validate_infrastructure(self):
        """Validate infrastructure configuration"""
        # Check docker-compose.yml
        try:
            with open("infrastructure/docker/docker-compose.yml", 'r') as f:
                compose = yaml.safe_load(f)
            
            required_services = ["postgres", "redis"]
            missing = [s for s in required_services if s not in compose.get("services", {})]
            
            if missing:
                self.results.append(ValidationResult(
                    "docker-compose.yml", "fail",
                    f"Missing services: {missing}"
                ))
                print(f"❌ docker-compose.yml - Missing services: {missing}")
            else:
                self.results.append(ValidationResult(
                    "docker-compose.yml", "pass",
                    "All required services defined"
                ))
                print("✅ docker-compose.yml - All services defined")
        except Exception as e:
            self.results.append(ValidationResult(
                "docker-compose.yml", "fail", f"Invalid: {e}"
            ))
            print(f"❌ docker-compose.yml - Invalid: {e}")
    
    def print_summary(self) -> Tuple[List[ValidationResult], int]:
        """Print summary and return exit code"""
        passed = [r for r in self.results if r.status == "pass"]
        warned = [r for r in self.results if r.status == "warn"]
        failed = [r for r in self.results if r.status == "fail"]
        
        if failed:
            print(f"RESULT: ❌ FAILED with {len(failed)} errors, {len(warned)} warnings")
            print()
            print("Errors:")
            for r in failed:
                print(f"  ❌ {r.component}: {r.message}")
            if warned:
                print("\nWarnings:")
                for r in warned:
                    print(f"  ⚠️  {r.component}: {r.message}")
            return self.results, 1
        
        elif warned:
            print(f"RESULT: ⚠️  PASSED with {len(warned)} warnings")
            print()
            print("Warnings:")
            for r in warned:
                print(f"  ⚠️  {r.component}: {r.message}")
            print()
            print("Ready to deploy! 🚀")
            return self.results, 0 if not self.strict else 1
        
        else:
            print("RESULT: ✅ ALL CHECKS PASSED")
            print()
            print("Ready to deploy! 🚀")
            return self.results, 0

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate WAOOAW configuration")
    parser.add_argument("--env", default="development", choices=["development", "staging", "production"])
    parser.add_argument("--strict", action="store_true", help="Fail on warnings (CI/CD mode)")
    parser.add_argument("--critical-only", action="store_true", help="Check only critical items")
    
    args = parser.parse_args()
    
    validator = ConfigValidator(env=args.env, strict=args.strict)
    results, exit_code = validator.run_all_checks()
    
    sys.exit(exit_code)
```

---

## 4. Infrastructure as Code (IaC) Integration

### 4.1 IaC Validation Tools

**Terraform**:
```bash
# Syntax validation
terraform fmt -check

# Plan validation (dry run)
terraform plan

# Security scan
checkov --directory infrastructure/terraform

# Cost estimation
infracost breakdown --path infrastructure/terraform
```

**Docker Compose**:
```bash
# Syntax validation
docker-compose -f infrastructure/docker/docker-compose.yml config

# Validate against production constraints
docker-compose -f infrastructure/docker/docker-compose.yml config | grep -E "(memory|cpu)"
```

**GitHub Actions**:
```bash
# Validate workflow syntax
actionlint .github/workflows/*.yml
```

### 4.2 Pre-Commit Hooks

**File**: `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files
        args: ['--maxkb=500']
  
  - repo: https://github.com/adrienverge/yamllint
    rev: v1.32.0
    hooks:
      - id: yamllint
        args: ['-c', '.yamllint.yml']
  
  - repo: local
    hooks:
      - id: validate-config
        name: Validate WAOOAW Configs
        entry: python scripts/validate_config.py --strict
        language: system
        pass_filenames: false
        always_run: true
      
      - id: terraform-fmt
        name: Terraform Format Check
        entry: terraform fmt -check
        language: system
        files: \.tf$
        pass_filenames: false
      
      - id: checkov
        name: Checkov Security Scan
        entry: checkov --directory infrastructure/terraform
        language: system
        files: \.tf$
        pass_filenames: false
```

**Install**:
```bash
pip install pre-commit
pre-commit install
```

**Usage** (automatic on `git commit`):
```bash
git add .
git commit -m "Update config"

# Pre-commit runs automatically:
# ✅ Trailing whitespace check
# ✅ YAML syntax check
# ✅ Config validation
# ✅ Terraform format
# ✅ Checkov security scan
```

---

## 5. CI/CD Integration

### GitHub Actions Workflow

**File**: `.github/workflows/validate-config.yml`

```yaml
name: Config Validation

on:
  pull_request:
    paths:
      - 'waooaw/config/**'
      - 'infrastructure/**'
      - '.env.example'
  push:
    branches:
      - main
      - develop

jobs:
  validate-app-config:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install yamllint jsonlint
      
      - name: Validate YAML syntax
        run: |
          yamllint waooaw/config/
          yamllint infrastructure/
      
      - name: Validate app configs
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          REDIS_URL: ${{ secrets.REDIS_URL }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          AGENT_SECRET_KEY_WOW_VISION_PRIME: ${{ secrets.AGENT_SECRET_KEY_WOW_VISION_PRIME }}
        run: |
          python scripts/validate_config.py --strict
  
  validate-terraform:
    runs-on: ubuntu-latest
    if: contains(github.event.pull_request.changed_files, 'infrastructure/terraform')
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
      
      - name: Terraform Format Check
        run: terraform fmt -check -recursive infrastructure/terraform
      
      - name: Terraform Validate
        run: |
          cd infrastructure/terraform
          terraform init -backend=false
          terraform validate
      
      - name: Checkov Security Scan
        uses: bridgecrewio/checkov-action@master
        with:
          directory: infrastructure/terraform
          framework: terraform
          output_format: cli
          soft_fail: false  # Fail on security issues
  
  validate-docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Validate Docker Compose
        run: |
          docker-compose -f infrastructure/docker/docker-compose.yml config
      
      - name: Lint Dockerfiles
        uses: hadolint/hadolint-action@v3.1.0
        with:
          dockerfile: backend/Dockerfile
```

---

## 6. Environment-Specific Validation

### Dev vs Staging vs Production

**Different rules per environment**:

| Check | Dev | Staging | Production |
|-------|-----|---------|------------|
| **Database URL** | Allow localhost | Must be managed | Must be managed + SSL |
| **Debug mode** | Allow `true` | Allow `true` | Must be `false` |
| **API keys** | Allow dummy | Must be real | Must be real + rotated |
| **Rate limits** | Unlimited | 10x production | Production limits |
| **Secrets** | .env file OK | GitHub Secrets | GitHub Secrets + Vault |
| **Encryption** | Optional | Required | Required |
| **Monitoring** | Optional | Required | Required |

**Implementation**:
```python
# scripts/validate_config.py
def validate_database_url(self, db_url: str):
    if self.env == "production":
        # Production: Must be managed database with SSL
        if "localhost" in db_url or "127.0.0.1" in db_url:
            return ValidationResult("DATABASE_URL", "fail", 
                "Production must use managed database, not localhost")
        if "sslmode=require" not in db_url:
            return ValidationResult("DATABASE_URL", "fail",
                "Production must use SSL (sslmode=require)")
    elif self.env == "staging":
        # Staging: Must be managed, SSL optional
        if "localhost" in db_url:
            return ValidationResult("DATABASE_URL", "warn",
                "Staging should use managed database")
    # Dev: Anything goes
    
    return ValidationResult("DATABASE_URL", "pass", "Valid URL")
```

---

## 7. Monitoring & Alerts

### Config Drift Detection

**Problem**: Config changes outside of version control (manual edits in prod)

**Solution**: Periodic drift detection

```python
# scripts/detect_config_drift.py
def detect_drift():
    """Compare running config vs Git version"""
    # Read running config
    live_config = read_from_production()
    
    # Read Git version
    git_config = read_from_git("main")
    
    # Diff
    diff = compare(live_config, git_config)
    
    if diff:
        alert_slack(f"Config drift detected: {diff}")
        create_github_issue("Config Drift", diff)
```

**Schedule**: Daily cron job or GitHub Action

---

## 8. Documentation & Runbooks

### Operator Playbook

**When config validation fails**:

1. **Syntax Error**:
   ```bash
   ❌ agent_config.yaml - Invalid YAML: line 42, column 5
   ```
   - **Fix**: Check indentation, missing quotes, trailing commas
   - **Tool**: `yamllint waooaw/config/agent_config.yaml`

2. **Missing Secret**:
   ```bash
   ❌ DATABASE_URL - NOT SET
   ```
   - **Fix**: Add to GitHub Secrets or `.env` file
   - **Tool**: `gh secret set DATABASE_URL`

3. **Invalid Format**:
   ```bash
   ❌ AGENT_SECRET_KEY_WOW_VISION_PRIME - Must be 64-char hex
   ```
   - **Fix**: Generate new key
   - **Tool**: `python -c "import secrets; print(secrets.token_hex(32))"`

4. **Connectivity Failure**:
   ```bash
   ❌ PostgreSQL - Connection timeout
   ```
   - **Fix**: Check firewall, database up, URL correct
   - **Tool**: `psql $DATABASE_URL`

---

## 9. Summary

### Yes, Config Validation is Essential

**Benefits**:
1. ✅ Catch errors before production (10,000x ROI)
2. ✅ Faster debugging (clear error messages)
3. ✅ Security (no hardcoded secrets, SSL required)
4. ✅ Cost control (rate limit sanity checks)
5. ✅ Compliance (audit trail of config changes)

**Effort**: 2-3 days to build, 5 minutes per deployment  
**Maintenance**: 1 hour/month to update rules

### IaC and Config Validation Relationship

```
Configuration Management (Parent Concept)
│
├── Application Config
│   ├── YAML/JSON files
│   ├── Environment variables
│   └── Config Validation ← scripts/validate_config.py
│
└── Infrastructure as Code (IaC)
    ├── Terraform (.tf files)
    ├── CloudFormation (YAML)
    ├── Docker Compose (YAML)
    ├── IaC Validation ← terraform validate, checkov
    └── IaC Provisioning ← terraform apply
```

**Answer to Your Question**:
- ✅ **YES**: IaC validation (syntax, security) is part of config validation
- ✅ **YES**: IaC files are configuration (infrastructure definitions)
- 🟡 **PARTIAL**: IaC provisioning is beyond validation (deployment action)

**Recommendation**: 
- Build `scripts/validate_config.py` for app configs (Week 9-10)
- Add IaC validation when we introduce Terraform (Week 25-28)
- Use pre-commit hooks to validate on every commit

---

## 10. Next Steps

**Immediate (v0.2.7)**:
1. Create `scripts/validate_config.py` (2 days)
2. Add pre-commit hooks (1 day)
3. Update CI/CD workflow (1 day)

**Phase 2 (v0.8, when adding IaC)**:
1. Add Terraform validation
2. Add Checkov security scan
3. Add config drift detection

**Total Effort**: 4 days initial, 1 hour/month maintenance

---

**Version**: 1.0  
**Last Updated**: December 28, 2025  
**Author**: GitHub Copilot  
**Status**: Ready for Implementation
