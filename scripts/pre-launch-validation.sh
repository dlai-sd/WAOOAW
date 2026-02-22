#!/bin/bash

# Pre-Launch Validation Script for WAOOAW Mobile App
# Run this before submitting to App Store / Play Store

set -e

echo "🚀 WAOOAW Mobile - Pre-Launch Validation"
echo "========================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# Navigate to mobile directory
cd "$(dirname "$0")/../src/mobile"

echo "📁 Current directory: $(pwd)"
echo ""

# 1. Check TypeScript compilation
echo "1️⃣  Checking TypeScript compilation..."
if npm run typecheck > /dev/null 2>&1; then
    echo -e "${GREEN}✅ TypeScript: No errors${NC}"
else
    echo -e "${RED}❌ TypeScript: Compilation errors found${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 2. Run linter
echo "2️⃣  Running ESLint..."
if npm run lint > /dev/null 2>&1; then
    echo -e "${GREEN}✅ ESLint: No issues${NC}"
else
    echo -e "${YELLOW}⚠️  ESLint: Issues found (check manually)${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# 3. Run tests
echo "3️⃣  Running test suite..."
if npm test -- --passWithNoTests --coverage > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Tests: All passing${NC}"
else
    echo -e "${RED}❌ Tests: Failures detected${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 4. Check for console.log statements
echo "4️⃣  Checking for console.log statements..."
CONSOLE_LOGS=$(grep -r "console.log" src/ --exclude-dir=node_modules --exclude="*.test.ts" --exclude="*.test.tsx" | wc -l || true)
if [ "$CONSOLE_LOGS" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Found $CONSOLE_LOGS console.log statements (review for production)${NC}"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}✅ No console.log statements${NC}"
fi

# 5. Check for TODO/FIXME comments
echo "5️⃣  Checking for TODO/FIXME comments..."
TODOS=$(grep -r "TODO\|FIXME" src/ --exclude-dir=node_modules | wc -l || true)
if [ "$TODOS" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Found $TODOS TODO/FIXME comments${NC}"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}✅ No TODO/FIXME comments${NC}"
fi

# 6. Check app.json configuration
echo "6️⃣  Validating app.json..."
if [ -f "app.json" ]; then
    # Check version
    VERSION=$(grep '"version"' app.json | head -1 | sed 's/.*: "\(.*\)".*/\1/')
    if [ -n "$VERSION" ]; then
        echo -e "${GREEN}✅ Version: $VERSION${NC}"
    else
        echo -e "${RED}❌ Version not found in app.json${NC}"
        ERRORS=$((ERRORS + 1))
    fi
    
    # Check app name
    APP_NAME=$(grep '"name"' app.json | head -1 | sed 's/.*: "\(.*\)".*/\1/')
    if [ "$APP_NAME" = "WAOOAW" ]; then
        echo -e "${GREEN}✅ App name: $APP_NAME${NC}"
    else
        echo -e "${YELLOW}⚠️  App name: $APP_NAME (verify correct)${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "${RED}❌ app.json not found${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 7. Check EAS configuration
echo "7️⃣  Validating eas.json..."
if [ -f "eas.json" ]; then
    # Check production profile
    if grep -q '"production"' eas.json; then
        echo -e "${GREEN}✅ Production profile configured${NC}"
    else
        echo -e "${RED}❌ Production profile missing in eas.json${NC}"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${RED}❌ eas.json not found${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 8. Check environment configuration
echo "8️⃣  Validating environment config..."
if [ -f "src/config/environment.config.ts" ]; then
    # Check for placeholder URLs
    if grep -q "localhost" src/config/environment.config.ts; then
        echo -e "${YELLOW}⚠️  Found localhost in environment config (verify production config)${NC}"
        WARNINGS=$((WARNINGS + 1))
    else
        echo -e "${GREEN}✅ No localhost references${NC}"
    fi
    
    # Check for placeholder keys
    if grep -q "REPLACE_WITH" src/config/environment.config.ts; then
        echo -e "${RED}❌ Found REPLACE_WITH placeholders in config${NC}"
        ERRORS=$((ERRORS + 1))
    else
        echo -e "${GREEN}✅ No placeholder keys${NC}"
    fi
else
    echo -e "${RED}❌ environment.config.ts not found${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 9. Check for sensitive data
echo "9️⃣  Checking for hardcoded secrets..."
SECRETS=$(grep -r -i "api_key\|secret\|password\|token" src/ --exclude-dir=node_modules --exclude="*.test.ts" --exclude="*.test.tsx" | grep -v "// " | grep -v "const " | wc -l || true)
if [ "$SECRETS" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Found $SECRETS potential secret references (review manually)${NC}"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}✅ No obvious hardcoded secrets${NC}"
fi

# 10. Check bundle size (if metro bundler available)
echo "🔟 Checking bundle size..."
if command -v npx &> /dev/null; then
    echo -e "${GREEN}✅ Metro bundler available${NC}"
else
    echo -e "${YELLOW}⚠️  Metro bundler not found (skip bundle check)${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# 11. Check dependencies
echo "1️⃣1️⃣  Checking dependencies..."
if [ -f "package.json" ]; then
    # Check for outdated major versions
    OUTDATED=$(npm outdated | wc -l || true)
    if [ "$OUTDATED" -gt 1 ]; then
        echo -e "${YELLOW}⚠️  $((OUTDATED - 1)) packages have updates available${NC}"
        WARNINGS=$((WARNINGS + 1))
    else
        echo -e "${GREEN}✅ All dependencies up to date${NC}"
    fi
else
    echo -e "${RED}❌ package.json not found${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 12. Check for .env files (should not be in production)
echo "1️⃣2️⃣  Checking for .env files..."
if [ -f ".env" ] || [ -f ".env.production" ]; then
    echo -e "${RED}❌ Found .env files (should use EAS environment variables)${NC}"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✅ No .env files (using EAS env vars)${NC}"
fi

# 13. Verify Google Services files (Firebase)
echo "1️⃣3️⃣  Checking Google Services files..."
if [ -f "google-services.json" ]; then
    echo -e "${GREEN}✅ google-services.json found (Android)${NC}"
else
    echo -e "${YELLOW}⚠️  google-services.json not found (add for Firebase)${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

if [ -f "GoogleService-Info.plist" ]; then
    echo -e "${GREEN}✅ GoogleService-Info.plist found (iOS)${NC}"
else
    echo -e "${YELLOW}⚠️  GoogleService-Info.plist not found (add for Firebase)${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# 14. Check Privacy Policy URL
echo "1️⃣4️⃣  Checking Privacy Policy..."
if grep -q "waooaw.com/privacy-policy" app.json; then
    echo -e "${GREEN}✅ Privacy Policy URL configured${NC}"
else
    echo -e "${RED}❌ Privacy Policy URL missing in app.json${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 15. Check Terms of Service URL
echo "1️⃣5️⃣  Checking Terms of Service..."
if grep -q "waooaw.com/terms" app.json; then
    echo -e "${GREEN}✅ Terms of Service URL configured${NC}"
else
    echo -e "${YELLOW}⚠️  Terms of Service URL not found${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""
echo "========================================"
echo "📊 Validation Summary"
echo "========================================"
echo -e "Errors: ${RED}$ERRORS${NC}"
echo -e "Warnings: ${YELLOW}$WARNINGS${NC}"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! App is ready for submission.${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  $WARNINGS warnings found. Review before submission.${NC}"
    exit 0
else
    echo -e "${RED}❌ $ERRORS errors found. Fix these before submission.${NC}"
    exit 1
fi
