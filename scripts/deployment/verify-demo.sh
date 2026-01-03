#!/bin/bash

# WAOOAW v2 Deployment Verification Script
# Validates demo environment deployment

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT="demo"
BACKEND_URL="https://demo-api.waooaw.com"
WAOOAW_PORTAL_URL="https://demo-www.waooaw.com"
PLATFORM_PORTAL_URL="https://demo-pp.waooaw.com"

echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  WAOOAW v2 Deployment Verification${NC}"
echo -e "${CYAN}  Environment: ${ENVIRONMENT}${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local expected=$3
    
    echo -n "Testing ${name}... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "${url}" 2>&1)
    
    if [ "$response" == "$expected" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $response)"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (Expected $expected, got $response)"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Function to test JSON endpoint
test_json_endpoint() {
    local name=$1
    local url=$2
    local json_field=$3
    local expected_value=$4
    
    echo -n "Testing ${name}... "
    
    response=$(curl -s "${url}" 2>&1)
    http_code=$?
    
    if [ $http_code -ne 0 ]; then
        echo -e "${RED}✗ FAIL${NC} (Connection failed)"
        ((TESTS_FAILED++))
        return 1
    fi
    
    actual_value=$(echo "$response" | jq -r ".$json_field" 2>/dev/null)
    
    if [ "$actual_value" == "$expected_value" ]; then
        echo -e "${GREEN}✓ PASS${NC} ($json_field = $expected_value)"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (Expected $expected_value, got $actual_value)"
        echo -e "${YELLOW}Response: $response${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Function to test HTML content
test_html_content() {
    local name=$1
    local url=$2
    local search_string=$3
    
    echo -n "Testing ${name}... "
    
    response=$(curl -s "${url}" 2>&1)
    http_code=$?
    
    if [ $http_code -ne 0 ]; then
        echo -e "${RED}✗ FAIL${NC} (Connection failed)"
        ((TESTS_FAILED++))
        return 1
    fi
    
    if echo "$response" | grep -q "$search_string"; then
        echo -e "${GREEN}✓ PASS${NC} (Found: $search_string)"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (String not found: $search_string)"
        ((TESTS_FAILED++))
        return 1
    fi
}

echo -e "${YELLOW}1. Backend API Tests${NC}"
echo "─────────────────────────"
test_endpoint "Backend Health Check" "${BACKEND_URL}/health" "200"
test_json_endpoint "Backend Environment" "${BACKEND_URL}/config" "environment" "demo"
test_endpoint "Backend Root" "${BACKEND_URL}/" "200"
test_endpoint "Backend OAuth Login Endpoint" "${BACKEND_URL}/auth/login?frontend=www" "302"
echo ""

echo -e "${YELLOW}2. WaooawPortal Tests${NC}"
echo "─────────────────────────"
test_endpoint "WaooawPortal Homepage" "${WAOOAW_PORTAL_URL}/" "200"
test_html_content "WaooawPortal Title" "${WAOOAW_PORTAL_URL}/" "WAOOAW"
test_html_content "WaooawPortal Marketplace Link" "${WAOOAW_PORTAL_URL}/" "marketplace"
test_endpoint "WaooawPortal Marketplace Page" "${WAOOAW_PORTAL_URL}/marketplace" "200"
echo ""

echo -e "${YELLOW}3. PlatformPortal Tests${NC}"
echo "─────────────────────────"
test_endpoint "PlatformPortal Homepage" "${PLATFORM_PORTAL_URL}/" "200"
test_html_content "PlatformPortal Title" "${PLATFORM_PORTAL_URL}/" "Platform Portal"
echo ""

echo -e "${YELLOW}4. SSL Certificate Tests${NC}"
echo "─────────────────────────"
echo -n "Testing SSL Certificate... "
ssl_output=$(echo | openssl s_client -connect demo-api.waooaw.com:443 -servername demo-api.waooaw.com 2>&1)
if echo "$ssl_output" | grep -q "Verify return code: 0"; then
    echo -e "${GREEN}✓ PASS${NC} (Valid SSL)"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} (SSL validation failed)"
    ((TESTS_FAILED++))
fi
echo ""

echo -e "${YELLOW}5. DNS Resolution Tests${NC}"
echo "─────────────────────────"
for domain in "demo-api.waooaw.com" "demo-www.waooaw.com" "demo-pp.waooaw.com"; do
    echo -n "Testing DNS for ${domain}... "
    ip=$(dig +short $domain | tail -n1)
    if [ -n "$ip" ]; then
        echo -e "${GREEN}✓ PASS${NC} (Resolves to $ip)"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC} (No DNS record)"
        ((TESTS_FAILED++))
    fi
done
echo ""

echo -e "${YELLOW}6. CORS Tests${NC}"
echo "─────────────────────────"
echo -n "Testing CORS headers... "
cors_response=$(curl -s -H "Origin: https://demo-www.waooaw.com" -I "${BACKEND_URL}/health" 2>&1)
if echo "$cors_response" | grep -q "access-control-allow-origin"; then
    echo -e "${GREEN}✓ PASS${NC} (CORS headers present)"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} (CORS headers missing)"
    ((TESTS_FAILED++))
fi
echo ""

echo -e "${YELLOW}7. Performance Tests${NC}"
echo "─────────────────────────"
for service in "Backend" "WaooawPortal" "PlatformPortal"; do
    case $service in
        "Backend") url=$BACKEND_URL/health ;;
        "WaooawPortal") url=$WAOOAW_PORTAL_URL/ ;;
        "PlatformPortal") url=$PLATFORM_PORTAL_URL/ ;;
    esac
    
    echo -n "Testing ${service} response time... "
    response_time=$(curl -o /dev/null -s -w '%{time_total}' $url)
    response_time_ms=$(echo "$response_time * 1000" | bc)
    
    if (( $(echo "$response_time < 2.0" | bc -l) )); then
        echo -e "${GREEN}✓ PASS${NC} (${response_time_ms}ms)"
        ((TESTS_PASSED++))
    else
        echo -e "${YELLOW}⚠ SLOW${NC} (${response_time_ms}ms)"
        ((TESTS_PASSED++))
    fi
done
echo ""

# Summary
echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  Test Summary${NC}"
echo -e "${CYAN}============================================${NC}"
echo -e "${GREEN}Passed: ${TESTS_PASSED}${NC}"
echo -e "${RED}Failed: ${TESTS_FAILED}${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed! Demo environment is ready.${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Please review the logs.${NC}"
    exit 1
fi
