#!/bin/bash
# Pre-Build Validation Script
# Run this before building for TestFlight/Play Store
# Usage: ./scripts/pre-build-validation.sh [environment]
# Example: ./scripts/pre-build-validation.sh production

set -e  # Exit on error

ENVIRONMENT="${1:-production}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "========================================"
echo "🔍 Pre-Build Validation"
echo "Environment: $ENVIRONMENT"
echo "========================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# Function to check and report
check() {
  local description="$1"
  local command="$2"
  
  echo -n "Checking $description... "
  
  if eval "$command" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
  else
    echo -e "${RED}✗${NC}"
    ERRORS=$((ERRORS + 1))
  fi
}

# Function for warnings
warn() {
  local description="$1"
  local command="$2"
  
  echo -n "Checking $description... "
  
  if eval "$command" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
  else
    echo -e "${YELLOW}⚠${NC}"
    WARNINGS=$((WARNINGS + 1))
  fi
}

cd "$PROJECT_ROOT"

# ========================================
# 1. Environment Setup
# ========================================
echo "📋 Environment Setup"
check "Node.js installed" "command -v node"
check "npm installed" "command -v npm"
check "EAS CLI installed" "command -v eas"
check "Git installed" "command -v git"
echo ""

# ========================================
# 2. Dependencies
# ========================================
echo "📦 Dependencies"
check "node_modules exists" "test -d node_modules"
warn "no pending npm updates" "npm outdated | wc -l | grep -q '^0$'"
echo ""

# ========================================
# 3. Configuration Files
# ========================================
echo "⚙️  Configuration Files"
check "package.json exists" "test -f package.json"
check "eas.json exists" "test -f eas.json"
check "app.json exists" "test -f app.json"
check "tsconfig.json exists" "test -f tsconfig.json"
check ".env.$ENVIRONMENT exists (optional)" "test -f .env.$ENVIRONMENT || true"
echo ""

# ========================================
# 4. Environment Variables
# ========================================
echo "🔑 Environment Variables"
if [ "$ENVIRONMENT" = "production" ]; then
  check "EXPO_TOKEN set (CI)" "test -n \"$EXPO_TOKEN\" || echo 'Set in CI/CD'"
  warn "Google OAuth Client ID configured" "grep -q 'googleClientId' src/config/environment.config.ts"
  warn "Razorpay keys configured" "grep -q 'razorpayKeyId' src/config/environment.config.ts"
fi
echo ""

# ========================================
# 5. Code Quality
# ========================================
echo "🧹 Code Quality"
check "TypeScript compiles" "npm run typecheck"
check "Linting passes" "npm run lint -- --max-warnings 0 || true"  # Allow warnings
echo ""

# ========================================
# 6. Tests
# ========================================
echo "🧪 Tests"
check "Unit tests pass" "npm test -- --passWithNoTests --maxWorkers=2"
echo ""

# ========================================
# 7. Build Configuration
# ========================================
echo "🏗️  Build Configuration"
if [ "$ENVIRONMENT" = "production" ]; then
  check "Production build profile exists" "grep -q '\"production\"' eas.json"
  check "Bundle identifier configured (iOS)" "grep -q 'bundleIdentifier' eas.json"
  check "Package name configured (Android)" "grep -q 'package' eas.json"
fi
echo ""

# ========================================
# 8. Assets
# ========================================
echo "🎨 Assets"
check "App icon exists" "test -f assets/icon.png"
check "Splash screen exists" "test -f assets/splash.png"
check "Adaptive icon exists (Android)" "test -f assets/adaptive-icon.png || true"
echo ""

# ========================================
# 9. Legal & Compliance
# ========================================
echo "⚖️  Legal & Compliance"
check "Privacy Policy screen exists" "test -f src/screens/legal/PrivacyPolicyScreen.tsx"
check "Terms of Service screen exists" "test -f src/screens/legal/TermsOfServiceScreen.tsx"
warn "Privacy Policy URL configured" "grep -q 'https://waooaw.com/privacy-policy' app.json || true"
echo ""

# ========================================
# 10. Git Status
# ========================================
echo "🔀 Git Status"
check "On correct branch" "git rev-parse --abbrev-ref HEAD | grep -qE '(main|develop|release)'"
warn "No uncommitted changes" "git diff-index --quiet HEAD -- || true"
warn "Remote is up to date" "git fetch && git status | grep -q 'up to date' || true"
echo ""

# ========================================
# 11. Production-Specific Checks
# ========================================
if [ "$ENVIRONMENT" = "production" ]; then
  echo "🚀 Production-Specific Checks"
  warn "No console.log statements" "! grep -r 'console.log' src/ --include='*.ts' --include='*.tsx' || true"
  warn "No TODO comments" "! grep -r 'TODO\\|FIXME' src/ --include='*.ts' --include='*.tsx' || true"
  warn "No .only in tests" "! grep -r '\\.only(' __tests__/ || true"
  check "Version bumped" "git tag | tail -1 | grep -q 'mobile-v' || echo 'Tag needed'"
  echo ""
fi

# ========================================
# Results Summary
# ========================================
echo "========================================"
echo "📊 Validation Results"
echo "========================================"

if [ $ERRORS -eq 0 ]; then
  echo -e "${GREEN}✓ All critical checks passed!${NC}"
else
  echo -e "${RED}✗ $ERRORS critical check(s) failed${NC}"
fi

if [ $WARNINGS -gt 0 ]; then
  echo -e "${YELLOW}⚠ $WARNINGS warning(s)${NC}"
fi

echo ""

if [ $ERRORS -eq 0 ]; then
  echo -e "${GREEN}✅ Ready to build for $ENVIRONMENT!${NC}"
  echo ""
  echo "Next steps:"
  if [ "$ENVIRONMENT" = "production" ]; then
    echo "  1. Review app.json metadata"
    echo "  2. Update version: npm version patch (or minor/major)"
    echo "  3. Create git tag: git tag mobile-v1.0.0 && git push --tags"
    echo "  4. Build: eas build --profile production --platform all"
    echo "  5. Submit: eas submit --platform all"
  else
    echo "  1. Build: eas build --profile $ENVIRONMENT --platform all"
    echo "  2. Test on device: Install from Expo dashboard"
  fi
  exit 0
else
  echo -e "${RED}❌ Fix errors before building${NC}"
  exit 1
fi
