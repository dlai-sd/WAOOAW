# SonarQube Code Quality Guide - WAOOAW Plant Backend

**Document:** SonarQube Setup & Code Quality Standards  
**Date:** 2026-01-14  
**Version:** 1.0 (Setup Ready)  
**Status:** Ready for Configuration (Phase 2)  

---

## Overview

SonarQube provides static code analysis to detect bugs, vulnerabilities, and code quality issues. This guide documents the planned setup and standards.

**Note:** SonarQube integration is scheduled for Phase 2 after unit tests and load tests are validated.

---

## SonarQube Architecture

### Components
```
┌────────────────────────────────────────────────────────┐
│ GitHub Repository (WAOOAW)                            │
│ ├─ Pull Request triggered                             │
│ └─ GitHub Actions CI/CD                              │
└────────────────────────────────────────────────────────┘
                      ↓
┌────────────────────────────────────────────────────────┐
│ GitHub Actions Workflow                               │
│ ├─ Run tests (unit, integration)                      │
│ ├─ Generate coverage reports (pytest-cov)            │
│ ├─ Run sonar-scanner                                 │
│ └─ Report to SonarQube                               │
└────────────────────────────────────────────────────────┘
                      ↓
┌────────────────────────────────────────────────────────┐
│ SonarQube Server                                       │
│ ├─ Code analysis (bugs, vulnerabilities)             │
│ ├─ Coverage data (from pytest-cov)                   │
│ ├─ Security hotspots review                          │
│ └─ Quality gates enforcement                         │
└────────────────────────────────────────────────────────┘
                      ↓
┌────────────────────────────────────────────────────────┐
│ GitHub Status Checks                                  │
│ ├─ Quality gate PASS/FAIL                            │
│ └─ PR merge blocked if Quality gate FAILS            │
└────────────────────────────────────────────────────────┘
```

---

## Quality Gates (Standards)

### Gate 1: Code Coverage
```yaml
coverage_targets:
  overall: "≥90%"
  new_code: "≥80%"
  modules:
    core/: "≥95%"
    models/: "≥92%"
    validators/: "≥90%"
    security/: "≥96%"
    services/: "≥85%"
    api/: "≥80%"
```

**How it works:**
- SonarQube pulls coverage data from pytest-cov
- Fails if overall coverage < 90%
- Fails if new code coverage < 80%
- Module-specific targets enforced

### Gate 2: Security (OWASP)
```yaml
security_rules:
  - "No hardcoded secrets (AWS keys, tokens)"
  - "No SQL injection vulnerabilities"
  - "No authentication/authorization bypass"
  - "No insecure cryptography (weak hash, ECB mode)"
  - "No XXE vulnerabilities"
  - "No broken access control"
  
blocker_issues: 0
critical_issues: 0
major_issues: <5
```

**Plant-specific security rules:**
- RSA-4096 encryption enforced (not weak keys)
- SHA-256 hash chains validated (not MD5)
- Constitutional L0/L1 alignment checks present
- No plaintext secrets in code

### Gate 3: Reliability (Bug Detection)
```yaml
bug_detection:
  blocker_issues: 0
  critical_issues: 0
  major_issues: <3
  
rules_enabled:
  - "Null pointer dereference detection"
  - "Resource leak detection (file/connection)"
  - "Type mismatch in comparisons"
  - "Dead code removal recommendations"
  - "Duplicate code detection"
```

### Gate 4: Maintainability (Code Smell)
```yaml
code_health:
  maintainability_rating: "A"  (highest)
  code_complexity:
    cyclomatic: "<10 per function"
    cognitive: "<15 per function"
  
  duplication: "<5%"
  lines_of_code: "<20 per function"
  
  rules_enforced:
    - "Meaningful variable names (not i, j, k)"
    - "No commented-out code"
    - "Docstrings for public methods"
    - "Type hints in function signatures"
```

---

## SonarQube Properties File

**File:** `sonar-project.properties` (in project root)

```properties
# Project identification
sonar.projectKey=WAOOAW-Plant-Backend
sonar.projectName=WAOOAW Plant Phase - Backend
sonar.projectVersion=1.0

# Source code
sonar.sources=src/Plant/BackEnd
sonar.tests=src/Plant/BackEnd/tests
sonar.python.version=3.11

# Test coverage (from pytest)
sonar.python.coverage.reportPaths=src/Plant/BackEnd/coverage.xml
sonar.coverage.exclusions=**/tests/**,**/migrations/**

# Exclude certain directories
sonar.exclusions=**/migrations/**,**/venv/**,**/node_modules/**

# Quality gates
sonar.qualitygate.wait=true
sonar.qualitygate.timeout=300

# Security rules
sonar.security.hotspots.review.priority=HIGH

# Python-specific rules
sonar.python.pylint=/usr/bin/pylint
sonar.python.mypy.reportPath=mypy-report.txt
sonar.python.flake8.reportPath=flake8-report.txt
```

---

## GitHub Actions Integration (Phase 2)

**Workflow File:** `.github/workflows/sonar-code-quality.yml`

```yaml
name: SonarQube Code Quality Analysis

on:
  push:
    branches:
      - main
      - develop
  pull_request:
    branches:
      - main
      - develop

jobs:
  sonarqube:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0  # Full history for better analysis
      
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r src/Plant/BackEnd/requirements.txt
          pip install coverage pylint mypy flake8
      
      - name: Run unit tests with coverage
        run: |
          cd src/Plant/BackEnd
          pytest tests/unit/ \
            --cov=core,models,validators,security \
            --cov-report=xml \
            --cov-report=html
      
      - name: Run linting
        run: |
          cd src/Plant/BackEnd
          pylint core/ models/ validators/ security/ > pylint-report.txt || true
          flake8 core/ models/ validators/ security/ > flake8-report.txt || true
          mypy core/ models/ validators/ security/ > mypy-report.txt || true
      
      - name: SonarQube analysis
        uses: SonarSource/sonarcloud-github-action@master
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
        with:
          args: >
            -Dsonar.projectKey=WAOOAW-Plant-Backend
            -Dsonar.organization=dlai-sd
            -Dsonar.python.coverage.reportPaths=src/Plant/BackEnd/coverage.xml
```

---

## Local SonarQube Analysis

### Option 1: SonarCloud (Cloud-based, Recommended)

**Setup:**
```bash
# 1. Create account at https://sonarcloud.io
# 2. Add GitHub organization: dlai-sd
# 3. Authorize repository: WAOOAW
# 4. Get SONAR_TOKEN from account settings
# 5. Add to GitHub Secrets: Settings → Secrets → SONAR_TOKEN
```

**Run locally:**
```bash
# Install sonar-scanner
brew install sonarcloud  # macOS
# or download from https://docs.sonarcloud.io/advanced-setup/ci-cd-integrations/github-actions-for-sonarcloud/

# Run analysis
sonar-scanner \
  -Dsonar.projectKey=WAOOAW-Plant-Backend \
  -Dsonar.organization=dlai-sd \
  -Dsonar.sources=src/Plant/BackEnd \
  -Dsonar.tests=src/Plant/BackEnd/tests \
  -Dsonar.python.coverage.reportPaths=src/Plant/BackEnd/coverage.xml \
  -Dsonar.login=$SONAR_TOKEN
```

### Option 2: Self-Hosted SonarQube (Enterprise)

**Docker Compose:**
```yaml
version: '3.8'
services:
  sonarqube:
    image: sonarqube:latest
    ports:
      - "9000:9000"
    environment:
      SONARQUBE_JDBC_URL: jdbc:postgresql://postgres:5432/sonarqube
      SONARQUBE_JDBC_USERNAME: sonar
      SONARQUBE_JDBC_PASSWORD: sonarpass
    volumes:
      - sonarqube_data:/opt/sonarqube/data
      - sonarqube_logs:/opt/sonarqube/logs
  
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: sonar
      POSTGRES_PASSWORD: sonarpass
      POSTGRES_DB: sonarqube
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  sonarqube_data:
  sonarqube_logs:
  postgres_data:
```

**Run locally:**
```bash
# Start SonarQube
docker-compose up -d

# Access at http://localhost:9000
# Default: admin / admin

# Run analysis
sonar-scanner \
  -Dsonar.projectKey=plant-backend \
  -Dsonar.sources=src/Plant/BackEnd \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.login=admin \
  -Dsonar.password=admin
```

---

## Quality Gate Rules (Plant-Specific)

### Constitutional Alignment (Custom Rule)
```
Rule ID: PLANT-001
Name: Constitutional L0/L1 Compliance Check
Description: All entities must include L0/L1 validation
Severity: BLOCKER
Applies to: models/, services/
Check: BaseEntity methods contain validate_l0() calls
```

### Cryptography Standards
```
Rule ID: PLANT-002
Name: Secure Cryptography Usage
Description: Enforce RSA-4096, SHA-256, no weak keys
Severity: CRITICAL
Applies to: security/
Checks:
  - RSA key size >= 4096
  - Hash algorithm in {SHA-256, SHA-512}
  - No use of MD5, SHA1, DES
  - No hardcoded keys in code
```

### Hash Chain Integrity
```
Rule ID: PLANT-003
Name: Hash Chain Immutability
Description: Audit trails must use append-only pattern
Severity: CRITICAL
Applies to: security/, models/
Checks:
  - No UPDATE/DELETE on audit_trail table
  - Hash chain validation present
  - Tamper detection implemented
```

---

## Code Quality Metrics

### Baseline Targets (Phase 1)
```
Overall Coverage:        90%+
New Code Coverage:       80%+
Duplicated Lines:        <5%
Code Smells:            <50 (info only)
Bugs:                   0 (blocker/critical)
Vulnerabilities:        0 (blocker/critical)
Security Hotspots:      0 unreviewed
Maintainability Rating: A
Reliability Rating:     A
Security Rating:        A
```

### Module Breakdown
```
core/
  ├─ Coverage: 95%
  ├─ Complexity: Low
  └─ Issues: 0 blocker, 0 critical

models/
  ├─ Coverage: 92%
  ├─ Complexity: Medium (BaseEntity is complex)
  └─ Issues: 0 blocker, <2 critical (allowed)

validators/
  ├─ Coverage: 90%
  ├─ Complexity: Medium
  └─ Issues: 0 blocker, 0 critical

security/
  ├─ Coverage: 96%
  ├─ Complexity: High (cryptography)
  └─ Issues: 0 blocker, 0 critical

services/
  ├─ Coverage: 85%
  ├─ Complexity: Medium
  └─ Issues: 0 blocker, <3 critical

api/
  ├─ Coverage: 80%
  ├─ Complexity: Low
  └─ Issues: 0 blocker, 0 critical
```

---

## Trend Analysis (Over Time)

**Metrics to Track:**
```
Week 1: Baseline (current state)
Week 2: After bug fixes
Week 4: After security audit
Week 8: After code refactoring (maintainability)
Month 3: Post-launch stability
```

**Expected Trend:**
```
Coverage:       90% → 92% → 94% → 95% (steady increase)
Bugs:           0  → 0  → 0  → 0   (stable)
Vulnerabilities: 0  → 0  → 0  → 0   (stable)
Code Smells:    30 → 20 → 10 → 5   (decreasing)
Debt Ratio:     2% → 1% → 0.5% → 0.3% (improving)
```

---

## SonarQube Dashboard

**Widgets to Add:**
1. **Quality Gate Status** - Current gate pass/fail
2. **Coverage Trend** - Coverage % over time
3. **Bugs & Vulnerabilities** - Blocker/critical/major counts
4. **Code Smells** - Maintainability issues
5. **Duplication** - Duplicate code percentage
6. **Complexity** - Cyclomatic & cognitive complexity
7. **Security Hotspots** - Unreviewed security issues
8. **Ratings** - Reliability, Security, Maintainability (A-E)

---

## Integration Points

### 1. GitHub Status Checks
```
Branch Protection Rule:
✓ Require status checks to pass before merging
✓ SonarQube/Quality Gate: PASS required
✗ If Quality Gate FAILS: Cannot merge PR
```

### 2. Pull Request Comments
```
SonarQube bot comments on PR:
- New bugs/vulnerabilities
- Coverage change
- Code quality suggestions
- Link to full report
```

### 3. Slack Notifications
```
#plant-engineering channel:
"🔴 SonarQube Quality Gate FAILED
  Project: WAOOAW Plant Backend
  Coverage: 85% (target: 90%)
  Bugs: 2 CRITICAL
  PR: #123 by @user
  Fix: https://sonarcloud.io/..."
```

---

## Phase 2 Setup Checklist

- [ ] Create SonarCloud account (https://sonarcloud.io)
- [ ] Add GitHub organization (dlai-sd)
- [ ] Authorize WAOOAW repository
- [ ] Get SONAR_TOKEN
- [ ] Add to GitHub Secrets
- [ ] Create sonar-project.properties
- [ ] Create `.github/workflows/sonar-code-quality.yml`
- [ ] Add branch protection rule for SonarQube
- [ ] Configure Slack notifications
- [ ] Test with first PR
- [ ] Tune quality gates based on results
- [ ] Document team standards

---

## Expected Timeline

**Phase 1 (Current):** Unit tests + Load tests ✓  
**Phase 2 (Next Sprint):** SonarQube integration  
- Week 1: Setup SonarCloud account, GitHub Actions
- Week 2: Analyze baseline code quality
- Week 3: Fix blocker/critical issues
- Week 4: Tune quality gates, integrate with branch protection

**Phase 3:** Sonar dashboard, trending reports  
**Phase 4:** Security hotspot reviews, refactoring plan  

---

## SonarQube vs Alternatives

| Tool | Type | Cost | Setup Time | Plant Fit |
|------|------|------|-----------|-----------|
| **SonarCloud** | Cloud | Free (open source) | 5 min | ✅ Best |
| **SonarQube** | Self-hosted | $2k-10k | 1 hour | ✅ Enterprise |
| **CodeClimate** | Cloud | $100-300/mo | 10 min | ⚠️ Limited Python |
| **Snyk** | Cloud | $50-500/mo | 10 min | ⚠️ Dependency only |
| **DeepSource** | Cloud | Free (limited) | 5 min | ⚠️ No Python focus |

**Recommendation:** SonarCloud (free, excellent Python support, GitHub integration)

---

## Next Steps

1. **Phase 1 Complete:** Unit tests (DONE) + Load tests (DONE)
2. **Phase 2 Setup:** SonarCloud account creation (next sprint)
3. **Phase 2 Integration:** GitHub Actions + branch protection
4. **Phase 3 Optimization:** Quality gate tuning + dashboard
5. **Phase 4 Security:** Hotspot reviews + security audit

---

**Last Updated:** 2026-01-14  
**Status:** Ready for Phase 2 Setup (Next Sprint)  
**Recommendation:** SonarCloud (free, cloud-based)  
**Phase 1 Result:** Unit Tests + Load Tests Complete ✓
