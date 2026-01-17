#!/bin/bash
# Environment Variables Validation Script
# Version: 1.0
# Owner: Platform Team

set -e

echo "========================================"
echo "ENVIRONMENT VARIABLES VALIDATION"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Function to check if variable is set
check_required() {
    local var_name=$1
    local var_value="${!var_name}"
    
    if [ -z "$var_value" ]; then
        echo -e "${RED}❌ FAIL${NC}: $var_name is not set"
        ((FAILED++))
        return 1
    else
        echo -e "${GREEN}✅ PASS${NC}: $var_name = ${var_value:0:20}..."
        ((PASSED++))
        return 0
    fi
}

# Function to check optional variable
check_optional() {
    local var_name=$1
    local var_value="${!var_name}"
    
    if [ -z "$var_value" ]; then
        echo -e "${YELLOW}⚠️  WARN${NC}: $var_name is not set (optional)"
        ((WARNINGS++))
    else
        echo -e "${GREEN}✅ PASS${NC}: $var_name = ${var_value:0:20}..."
        ((PASSED++))
    fi
}

# Function to validate URL format
check_url() {
    local var_name=$1
    local var_value="${!var_name}"
    
    if [ -z "$var_value" ]; then
        echo -e "${RED}❌ FAIL${NC}: $var_name is not set"
        ((FAILED++))
        return 1
    fi
    
    if [[ $var_value =~ ^https?:// ]]; then
        echo -e "${GREEN}✅ PASS${NC}: $var_name = $var_value"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}: $var_name is not a valid URL: $var_value"
        ((FAILED++))
        return 1
    fi
}

# Function to validate numeric value
check_numeric() {
    local var_name=$1
    local var_value="${!var_name}"
    local min=$2
    local max=$3
    
    if [ -z "$var_value" ]; then
        echo -e "${RED}❌ FAIL${NC}: $var_name is not set"
        ((FAILED++))
        return 1
    fi
    
    if ! [[ "$var_value" =~ ^[0-9]+\.?[0-9]*$ ]]; then
        echo -e "${RED}❌ FAIL${NC}: $var_name is not numeric: $var_value"
        ((FAILED++))
        return 1
    fi
    
    if (( $(echo "$var_value < $min" | bc -l) )) || (( $(echo "$var_value > $max" | bc -l) )); then
        echo -e "${RED}❌ FAIL${NC}: $var_name out of range [$min-$max]: $var_value"
        ((FAILED++))
        return 1
    fi
    
    echo -e "${GREEN}✅ PASS${NC}: $var_name = $var_value (valid range)"
    ((PASSED++))
    return 0
}

# Function to validate boolean
check_boolean() {
    local var_name=$1
    local var_value="${!var_name}"
    
    if [ -z "$var_value" ]; then
        echo -e "${RED}❌ FAIL${NC}: $var_name is not set"
        ((FAILED++))
        return 1
    fi
    
    if [[ "$var_value" == "true" ]] || [[ "$var_value" == "false" ]]; then
        echo -e "${GREEN}✅ PASS${NC}: $var_name = $var_value"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}: $var_name is not boolean: $var_value"
        ((FAILED++))
        return 1
    fi
}

echo "1. AUTHENTICATION & JWT"
echo "------------------------"
check_required JWT_SECRET_CP
check_required JWT_ALGORITHM
check_required JWT_ISSUER
check_numeric JWT_MAX_LIFETIME_SECONDS 3600 86400
echo ""

echo "2. SERVICE URLS"
echo "---------------"
check_url OPA_SERVICE_URL
check_url PLANT_API_URL
check_numeric PLANT_API_TIMEOUT_SECONDS 10 120
echo ""

echo "3. DATABASE & CACHE"
echo "-------------------"
check_required DATABASE_URL
check_required REDIS_HOST
check_numeric REDIS_PORT 1 65535
check_optional REDIS_PASSWORD
echo ""

echo "4. RATE LIMITING"
echo "----------------"
check_numeric RATE_LIMIT_TRIAL 10 1000
check_numeric RATE_LIMIT_PAID 100 10000
check_numeric RATE_LIMIT_ENTERPRISE 1000 100000
echo ""

echo "5. BUDGET GUARDS"
echo "----------------"
check_numeric AGENT_BUDGET_CAP_USD 0.1 100
check_numeric PLATFORM_BUDGET_CAP_USD 10 1000
check_numeric COST_GUARD_THRESHOLD_80 50 100
check_numeric COST_GUARD_THRESHOLD_95 80 100
echo ""

echo "6. TRIAL MODE"
echo "-------------"
check_numeric TRIAL_TASK_LIMIT_PER_DAY 1 100
check_numeric TRIAL_DURATION_DAYS 1 30
echo ""

echo "7. FEATURE FLAGS"
echo "----------------"
check_boolean FEATURE_FLAG_OPA_POLICY
check_boolean FEATURE_FLAG_BUDGET_GUARD
check_boolean FEATURE_FLAG_RATE_LIMITING
check_optional FEATURE_FLAG_CIRCUIT_BREAKER
check_optional FEATURE_FLAG_OPENTELEMETRY
echo ""

echo "8. LOGGING & MONITORING"
echo "-----------------------"
check_required LOG_LEVEL
check_required GCP_PROJECT_ID
check_required ENVIRONMENT
echo ""

# Summary
echo "========================================"
echo "VALIDATION SUMMARY"
echo "========================================"
echo -e "${GREEN}✅ Passed:${NC} $PASSED"
echo -e "${RED}❌ Failed:${NC} $FAILED"
echo -e "${YELLOW}⚠️  Warnings:${NC} $WARNINGS"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All required environment variables are valid!${NC}"
    exit 0
else
    echo -e "${RED}Some required environment variables are missing or invalid.${NC}"
    echo "Please check ENVIRONMENT_VARIABLES.md for reference."
    exit 1
fi
