# Mobile Testing Standards - Docker-Only Policy

**Version**: 1.0  
**Date**: 2026-02-17  
**Applies To**: WAOOAW Mobile Application (React Native/Expo)  
**Status**: MANDATORY

---

## ⚠️ Overview: Docker-Only Testing Requirement

All testing activities for the WAOOAW mobile application **MUST** be executed inside Docker containers or the GitHub Codespaces devcontainer. The use of virtual environments (`venv`, `virtualenv`, `conda`, `pyenv`, `nvm` with local installations) is **STRICTLY PROHIBITED**.

This policy aligns with WAOOAW's established backend testing standards and ensures consistency across the entire platform.

---

## 🚫 What is Prohibited

### Absolutely Forbidden:

```bash
# ❌ NEVER DO THESE - WILL FAIL CODE REVIEW

# Python virtual environments
python -m venv venv
source venv/bin/activate
python3 -m virtualenv mobile-env

# Conda environments
conda create -n mobile-test
conda activate mobile-test

# Node version managers with local installs
nvm use 18
npm install -g jest  # Global installs outside Docker

# Running tests directly on host machine
cd mobile
npm test             # ❌ If not in Codespace
npx jest             # ❌ If not in Docker
npx detox test       # ❌ If not in Docker

# Installing dependencies locally without Docker
npm install          # ❌ Creates node_modules on host
```

### Why These Are Prohibited:

| Issue | Impact | Example |
|-------|--------|---------|
| **Dependency Drift** | Tests pass locally but fail in CI | Different Node versions (18.2 vs 18.5) |
| **Environment Inconsistency** | "Works on my machine" syndrome | Missing system libraries (libpng, etc.) |
| **Non-Reproducible Results** | Flaky tests, hard to debug | Timezone differences, locale settings |
| **Production Mismatch** | Production uses containers (Cloud Run, EAS) | File path differences (/app vs /home/user) |
| **Security Risk** | Sensitive data in host file system | JWT tokens, API keys in local storage |

---

## ✅ What is Required

### 1. Docker Compose Testing (Primary Method)

```bash
# ✅ CORRECT WAY - Run all tests via Docker Compose

# Run all tests
docker-compose -f docker-compose.mobile.yml run --rm mobile-test npm test

# Run specific test file
docker-compose -f docker-compose.mobile.yml run --rm mobile-test npm test -- auth.service.test.ts

# Run with coverage
docker-compose -f docker-compose.mobile.yml run --rm mobile-test npm test -- --coverage

# Run linting
docker-compose -f docker-compose.mobile.yml run --rm mobile-test npm run lint

# Run TypeScript check
docker-compose -f docker-compose.mobile.yml run --rm mobile-test npm run typecheck

# Run E2E tests (Detox)
docker-compose -f docker-compose.mobile.yml run --rm mobile-test npx detox test --configuration ios.sim.debug

# Interactive mode (for debugging)
docker-compose -f docker-compose.mobile.yml run --rm mobile-test /bin/sh
# Then inside container:
npm test -- --watch
```

### 2. Codespace Testing (Alternative Method)

If you're working in GitHub Codespaces, the environment is already containerized (devcontainer), so you can run tests directly:

```bash
# ✅ CORRECT - Inside Codespace (which IS a Docker container)
cd /workspaces/WAOOAW/mobile
npm test
npm run lint
npx detox test

# Verify you're in Codespace
echo $CODESPACES  # Should output "true"
```

**Important**: Codespaces ARE Docker containers. This is why direct test execution is allowed there.

---

## 📋 Docker Compose Configuration

### Required File: `docker-compose.mobile.yml`

Place this at the root of the repository:

```yaml
# /workspaces/WAOOAW/docker-compose.mobile.yml
version: '3.8'

services:
  mobile-test:
    build:
      context: ./src/mobile
      dockerfile: Dockerfile.test
    volumes:
      - ./src/mobile:/app
      - /app/node_modules  # Prevent host node_modules from being mounted
    environment:
      - NODE_ENV=test
      - CI=true
      - API_BASE_URL=http://mock-api:8020
    depends_on:
      - mock-api
    working_dir: /app
  
  mock-api:
    image: mockserver/mockserver:latest
    ports:
      - "8020:1080"
    environment:
      - MOCKSERVER_INITIALIZATION_JSON_PATH=/config/mockserver.json
    volumes:
      - ./mobile/tests/mocks:/config

  # iOS Simulator container (for Detox E2E tests)
  mobile-e2e-ios:
    build:
      context: ./src/mobile
      dockerfile: Dockerfile.e2e
    volumes:
      - ./src/mobile:/app
      - /app/node_modules
    environment:
      - DETOX_CONFIGURATION=ios.sim.debug
    privileged: true  # Required for iOS simulator

  # Android Emulator container (for Detox E2E tests)
  mobile-e2e-android:
    build:
      context: ./src/mobile
      dockerfile: Dockerfile.e2e
    volumes:
      - ./src/mobile:/app
      - /app/node_modules
    environment:
      - DETOX_CONFIGURATION=android.emu.debug
    privileged: true  # Required for Android emulator
```

### Required File: `mobile/Dockerfile.test`

```dockerfile
# mobile/Dockerfile.test
FROM node:18-alpine

# Install system dependencies
RUN apk add --no-cache \
    git \
    bash \
    curl

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci --prefer-offline --no-audit

# Copy source code
COPY . .

# Default command
CMD ["npm", "test"]
```

### Required File: `mobile/Dockerfile.e2e`

```dockerfile
# mobile/Dockerfile.e2e (for Detox E2E tests)
FROM node:18

# Install Detox dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3 \
    openjdk-11-jdk \
    android-sdk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Build Detox
RUN npx detox build --configuration ios.sim.debug

CMD ["npx", "detox", "test", "--configuration", "ios.sim.debug"]
```

---

## 🔄 CI/CD Workflow Integration

### GitHub Actions Workflow with Docker

```yaml
# .github/workflows/mobile-ci.yml
name: Mobile CI - Docker-Only Testing

on:
  push:
    branches: [main, develop]
    paths:
      - 'mobile/**'
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      # ✅ All tests run via Docker Compose
      - name: Run linting
        run: docker-compose -f docker-compose.mobile.yml run --rm mobile-test npm run lint
      
      - name: Run TypeScript check
        run: docker-compose -f docker-compose.mobile.yml run --rm mobile-test npm run typecheck
      
      - name: Run unit tests
        run: docker-compose -f docker-compose.mobile.yml run --rm mobile-test npm test -- --coverage --ci
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./mobile/coverage/lcov.info
      
      - name: Run E2E tests (iOS)
        run: docker-compose -f docker-compose.mobile.yml run --rm mobile-e2e-ios
      
      - name: Run E2E tests (Android)
        run: docker-compose -f docker-compose.mobile.yml run --rm mobile-e2e-android
      
      # ❌ Fail if virtual environments detected
      - name: Check for prohibited virtual environments
        run: |
          if [ -d "src/mobile/venv" ] || [ -d "src/mobile/.venv" ] || [ -f "src/mobile/pyvenv.cfg" ]; then
            echo "❌ ERROR: Virtual environment detected in mobile directory!"
            echo "This violates WAOOAW testing standards."
            exit 1
          fi
          if [ -d "src/mobile/node_modules" ] && [ ! -f "src/mobile/.dockerignore" ]; then
            echo "⚠️  WARNING: node_modules exists on host without .dockerignore"
            echo "Ensure tests are run in Docker, not on host."
          fi
```

---

## 🛡️ Enforcement Mechanisms

### 1. Pre-commit Hook

Install this hook to prevent accidental venv usage:

```bash
# .git/hooks/pre-commit (or via husky)
#!/bin/bash

echo "🔍 Checking for WAOOAW testing standards compliance..."

# Check for virtual environments
if [ -d "src/mobile/venv" ] || [ -d "src/mobile/.venv" ] || [ -d "src/mobile/virtualenv" ]; then
  echo ""
  echo "❌ ERROR: Virtual environment detected!"
  echo ""
  echo "WAOOAW Policy: All mobile tests MUST run via Docker."
  echo "Remove virtual environment and use:"
  echo "  docker-compose -f docker-compose.mobile.yml run --rm mobile-test npm test"
  echo ""
  echo "Reference: docs/mobile/TESTING_STANDARDS.md"
  echo ""
  exit 1
fi

# Check for node_modules on host (suspicious)
if [ -d "src/mobile/node_modules" ] && ! git diff --cached --name-only | grep -q 'docker-compose'; then
  echo ""
  echo "⚠️  WARNING: node_modules exists on host machine."
  echo "Ensure you're running tests via Docker Compose, not directly on host."
  echo ""
  echo "If you need to run tests, use:"
  echo "  docker-compose -f docker-compose.mobile.yml run --rm mobile-test npm test"
  echo ""
fi

echo "✅ Testing standards check passed."
exit 0
```

Make it executable:

```bash
chmod +x .git/hooks/pre-commit
```

### 2. Code Review Checklist

**Reviewers MUST verify** for every PR touching `mobile/**`:

- [ ] **All tests run via Docker Compose or Codespace**
- [ ] No `venv`, `virtualenv`, or `.venv` directories in changes
- [ ] No instructions to run tests directly on host machine
- [ ] CI/CD workflow uses Docker for all test commands
- [ ] Developer confirmed tests pass via: `docker-compose -f docker-compose.mobile.yml run --rm mobile-test npm test`
- [ ] Coverage report generated from Docker run
- [ ] No global npm installs (`npm install -g`) in documentation

### 3. Story Definition of Done

Every story's Definition of Done MUST include:

```markdown
- [ ] **Unit tests written and passing via Docker**
  - Command used: `docker-compose -f docker-compose.mobile.yml run --rm mobile-test npm test`
  - Screenshot/log of Docker test run attached to PR
- [ ] **Integration tests written and passing via Docker**
- [ ] **E2E tests written and passing via Docker (if applicable)**
- [ ] **❌ NO virtual environments used for testing**
```

---

## 🤔 Common Questions

### Q: Why can't I just run `npm test` on my Mac/Windows machine?

**A**: While it might work locally, it creates three major problems:
1. **Inconsistency**: Your Mac has different system libraries, Node version, and environment variables than CI/CD and production
2. **Non-reproducibility**: When tests fail in CI but pass locally, debugging becomes a nightmare
3. **Standard violation**: WAOOAW's backend (Plant, CP, PP) all use Docker-only testing. Mobile must follow the same standard.

### Q: Is Codespace really a Docker container?

**A**: Yes! GitHub Codespaces run inside a devcontainer (Docker). When you run `npm test` in Codespace, you're already inside a container. Verify with:

```bash
# Inside Codespace
echo $CODESPACES  # Outputs: true
cat /proc/1/cgroup  # Shows Docker cgroup
```

This is why direct test execution is allowed in Codespaces but not on your host machine.

### Q: Docker is slow on my M1 Mac. Can I use a virtual environment instead?

**A**: No. Docker performance issues should be addressed (use Rosetta 2, increase Docker resources), not bypassed. Alternatively:
- Use GitHub Codespaces (free for open source, fast cloud environment)
- Use native ARM64 Docker images where possible
- Optimize Docker layer caching

### Q: What if I need to debug a specific test interactively?

**A**: Run Docker in interactive mode:

```bash
# Start interactive shell in container
docker-compose -f docker-compose.mobile.yml run --rm mobile-test /bin/sh

# Inside container, run tests in watch mode
npm test -- --watch

# Or run specific test with debugger
node --inspect-brk=0.0.0.0:9229 node_modules/.bin/jest auth.service.test.ts
```

Then attach your IDE debugger to `localhost:9229`.

### Q: How do I set up my IDE (VS Code) to work with Docker tests?

**A**: Use the Dev Container extension:

1. Install "Dev Containers" extension in VS Code
2. Open project in dev container: `Cmd+Shift+P` → "Dev Containers: Reopen in Container"
3. Now VS Code runs inside the container, and `npm test` works directly

Or use Remote-Containers with `docker-compose.mobile.yml`.

### Q: What about Expo Go testing on my physical device?

**A**: Manual testing on physical devices is allowed and encouraged:

```bash
# Start Expo dev server (can be on host or in Docker)
cd src/mobile
npm start

# Scan QR code with Expo Go app
```

However, **automated tests** (unit, integration, E2E) must still run via Docker.

---

## 📊 Testing Workflow Comparison

### ❌ Wrong Way (Prohibited)

```bash
# On your Mac/Windows machine
cd /Users/you/waooaw/mobile
python -m venv venv
source venv/bin/activate
npm install
npm test  # ❌ WRONG - runs on host, not in Docker
```

**Problems**:
- ❌ Tests run with your system's Node/Python/libraries
- ❌ Results not reproducible in CI/CD
- ❌ Violates WAOOAW standards
- ❌ Will fail code review

### ✅ Correct Way (Docker Compose)

```bash
# At repository root
cd /workspaces/WAOOAW
docker-compose -f docker-compose.mobile.yml run --rm mobile-test npm test
```

**Benefits**:
- ✅ Runs in identical environment to CI/CD
- ✅ Results 100% reproducible
- ✅ Follows WAOOAW standards
- ✅ Passes code review

### ✅ Correct Way (Codespace)

```bash
# Inside GitHub Codespace (already a container)
cd /workspaces/WAOOAW/mobile
npm test
```

**Benefits**:
- ✅ Already in Docker container (devcontainer)
- ✅ Same benefits as Docker Compose
- ✅ Faster iteration (no docker-compose overhead)

---

## 📚 References

### WAOOAW Documentation
- [CONTEXT_AND_INDEX.md - Section 11: Testing Strategy](../CONTEXT_AND_INDEX.md#11-testing-strategy)
- [Mobile Approach - Section 12: Testing Strategy](./mobile_approach.md#12-testing-strategy)
- [Implementation Plan - Definition of Done](./implementation_plan.md#definition-of-done-story-level)

### External Resources
- [Docker Best Practices for Node.js](https://github.com/nodejs/docker-node/blob/main/docs/BestPractices.md)
- [Detox Docker Setup](https://wix.github.io/Detox/docs/guide/docker)
- [GitHub Actions with Docker Compose](https://docs.docker.com/compose/ci-cd/)

---

## 🔄 Change Log

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | WAOOAW Tech Team | Initial Docker-only testing standards created |

---

## ✅ Acknowledgment

By contributing to the WAOOAW mobile application, you acknowledge and agree to follow these Docker-only testing standards. Violations will result in PR rejection and rework requirements.

**For questions or exceptions**, contact:
- Tech Lead: [TBD]
- DevOps Lead: [TBD]

---

**Document Status**: ✅ MANDATORY - Must be followed by all contributors  
**Last Review**: 2026-02-17  
**Next Review**: Before EPIC-1 completion
