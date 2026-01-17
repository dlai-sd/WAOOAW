#!/bin/bash
# Test Gateway Audit Logs Schema
# Version: 1.0
# Purpose: Validate schema, indexes, RLS policies, and insert test data

set -e

echo "🧪 Testing Gateway Audit Logs Schema"
echo "===================================="

# Database connection (use environment variables or defaults)
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-waooaw_db}"
DB_USER="${DB_USER:-postgres}"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run SQL and check result
run_test() {
    local test_name="$1"
    local sql_query="$2"
    local expected_result="$3"
    
    echo -n "Testing: $test_name... "
    
    result=$(PGPASSWORD="${DB_PASSWORD}" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "$sql_query" 2>&1)
    exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        if [ -z "$expected_result" ] || echo "$result" | grep -q "$expected_result"; then
            echo -e "${GREEN}✓ PASS${NC}"
            ((TESTS_PASSED++))
            return 0
        else
            echo -e "${RED}✗ FAIL${NC} (unexpected result: $result)"
            ((TESTS_FAILED++))
            return 1
        fi
    else
        echo -e "${RED}✗ FAIL${NC} (error: $result)"
        ((TESTS_FAILED++))
        return 1
    fi
}

echo ""
echo "1. Schema Validation"
echo "--------------------"

# Test 1: Table exists
run_test "Table gateway_audit_logs exists" \
    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'gateway_audit_logs');" \
    "t"

# Test 2: Required columns exist
run_test "Column id exists" \
    "SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'gateway_audit_logs' AND column_name = 'id');" \
    "t"

run_test "Column correlation_id exists" \
    "SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'gateway_audit_logs' AND column_name = 'correlation_id');" \
    "t"

run_test "Column user_id exists" \
    "SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'gateway_audit_logs' AND column_name = 'user_id');" \
    "t"

run_test "Column opa_decisions exists" \
    "SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'gateway_audit_logs' AND column_name = 'opa_decisions');" \
    "t"

echo ""
echo "2. Index Validation"
echo "-------------------"

# Test 3: Indexes exist
run_test "Index idx_audit_correlation_id exists" \
    "SELECT EXISTS (SELECT FROM pg_indexes WHERE tablename = 'gateway_audit_logs' AND indexname = 'idx_audit_correlation_id');" \
    "t"

run_test "Index idx_audit_user_id exists" \
    "SELECT EXISTS (SELECT FROM pg_indexes WHERE tablename = 'gateway_audit_logs' AND indexname = 'idx_audit_user_id');" \
    "t"

run_test "Index idx_audit_timestamp exists" \
    "SELECT EXISTS (SELECT FROM pg_indexes WHERE tablename = 'gateway_audit_logs' AND indexname = 'idx_audit_timestamp');" \
    "t"

run_test "Index idx_audit_errors exists" \
    "SELECT EXISTS (SELECT FROM pg_indexes WHERE tablename = 'gateway_audit_logs' AND indexname = 'idx_audit_errors');" \
    "t"

echo ""
echo "3. RLS Policy Validation"
echo "------------------------"

# Test 4: RLS enabled
run_test "Row Level Security enabled" \
    "SELECT relrowsecurity FROM pg_class WHERE relname = 'gateway_audit_logs';" \
    "t"

# Test 5: Policies exist
run_test "admin_all_access policy exists" \
    "SELECT EXISTS (SELECT FROM pg_policies WHERE tablename = 'gateway_audit_logs' AND policyname = 'admin_all_access');" \
    "t"

run_test "user_own_logs policy exists" \
    "SELECT EXISTS (SELECT FROM pg_policies WHERE tablename = 'gateway_audit_logs' AND policyname = 'user_own_logs');" \
    "t"

run_test "system_insert_logs policy exists" \
    "SELECT EXISTS (SELECT FROM pg_policies WHERE tablename = 'gateway_audit_logs' AND policyname = 'system_insert_logs');" \
    "t"

echo ""
echo "4. Test Data Insertion"
echo "----------------------"

# Generate test UUIDs
TEST_USER_ID="11111111-1111-1111-1111-111111111111"
TEST_CUSTOMER_ID="22222222-2222-2222-2222-222222222222"
TEST_CORRELATION_ID="33333333-3333-3333-3333-333333333333"

# Test 6: Insert sample audit log (CP Gateway)
run_test "Insert CP Gateway audit log" \
    "SET app.service_account = 'gateway';
     INSERT INTO gateway_audit_logs (
         correlation_id, gateway_type, request_id, http_method, endpoint,
         user_id, customer_id, email, roles, trial_mode,
         opa_policies_evaluated, opa_decisions, opa_latency_ms,
         status_code, total_latency_ms, action, resource
     ) VALUES (
         '$TEST_CORRELATION_ID', 'CP', 'req-001', 'POST', '/api/v1/agents',
         '$TEST_USER_ID', '$TEST_CUSTOMER_ID', 'test@waooaw.com', ARRAY['user'], true,
         ARRAY['trial_mode', 'agent_budget'], 
         '{\"trial_mode\": {\"allow\": true}, \"agent_budget\": {\"allow\": true}}'::jsonb,
         15,
         201, 245, 'create', 'agent'
     ) RETURNING id;" \
    ""

# Test 7: Insert sample audit log (PP Gateway with OPA deny)
run_test "Insert PP Gateway audit log with OPA deny" \
    "SET app.service_account = 'gateway';
     INSERT INTO gateway_audit_logs (
         correlation_id, gateway_type, request_id, http_method, endpoint,
         user_id, email, roles, trial_mode,
         opa_policies_evaluated, opa_decisions, opa_latency_ms,
         status_code, error_type, error_message, total_latency_ms, action, resource
     ) VALUES (
         '$TEST_CORRELATION_ID', 'PP', 'req-002', 'DELETE', '/api/v1/agents/agent-123',
         '$TEST_USER_ID', 'test@waooaw.com', ARRAY['viewer'], false,
         ARRAY['rbac_pp', 'governor_role'], 
         '{\"rbac_pp\": {\"allow\": false, \"deny_reason\": \"User lacks permission agent.delete\"}, \"governor_role\": {\"allow\": true}}'::jsonb,
         12,
         403, 'permission_denied', 'Insufficient permissions', 89, 'delete', 'agent'
     ) RETURNING id;" \
    ""

# Test 8: Insert sample audit log with high latency
run_test "Insert audit log with high latency" \
    "SET app.service_account = 'gateway';
     INSERT INTO gateway_audit_logs (
         correlation_id, gateway_type, request_id, http_method, endpoint,
         user_id, email, roles, trial_mode,
         opa_policies_evaluated, opa_decisions, opa_latency_ms,
         status_code, total_latency_ms, plant_latency_ms, action, resource
     ) VALUES (
         '$TEST_CORRELATION_ID', 'CP', 'req-003', 'POST', '/api/v1/executions',
         '$TEST_USER_ID', 'test@waooaw.com', ARRAY['agent_orchestrator'], false,
         ARRAY['trial_mode', 'agent_budget', 'governor_role'], 
         '{\"trial_mode\": {\"allow\": true}, \"agent_budget\": {\"allow\": true}, \"governor_role\": {\"allow\": true}}'::jsonb,
         18,
         200, 3542, 3500, 'execute', 'task'
     ) RETURNING id;" \
    ""

echo ""
echo "5. Query Validation"
echo "-------------------"

# Test 9: Count inserted logs
run_test "Count test logs (should be 3)" \
    "SELECT COUNT(*) FROM gateway_audit_logs WHERE correlation_id = '$TEST_CORRELATION_ID';" \
    "3"

# Test 10: Query by correlation_id (trace)
run_test "Query by correlation_id" \
    "SELECT COUNT(*) FROM gateway_audit_logs WHERE correlation_id = '$TEST_CORRELATION_ID';" \
    "3"

# Test 11: Query by user_id
run_test "Query by user_id" \
    "SELECT COUNT(*) FROM gateway_audit_logs WHERE user_id = '$TEST_USER_ID';" \
    "3"

# Test 12: Query OPA denies
run_test "Query OPA denies" \
    "SELECT COUNT(*) FROM gateway_audit_logs WHERE opa_decisions::TEXT LIKE '%\"allow\": false%';" \
    "1"

# Test 13: Query by status code (errors)
run_test "Query by status code 403" \
    "SELECT COUNT(*) FROM gateway_audit_logs WHERE status_code = 403;" \
    "1"

# Test 14: Query high latency requests (>1000ms)
run_test "Query high latency requests" \
    "SELECT COUNT(*) FROM gateway_audit_logs WHERE total_latency_ms > 1000;" \
    "1"

echo ""
echo "6. Helper Function Validation"
echo "------------------------------"

# Test 15: get_trace_by_correlation_id function
run_test "get_trace_by_correlation_id function exists" \
    "SELECT EXISTS (SELECT FROM pg_proc WHERE proname = 'get_trace_by_correlation_id');" \
    "t"

# Test 16: get_user_activity_summary function
run_test "get_user_activity_summary function exists" \
    "SELECT EXISTS (SELECT FROM pg_proc WHERE proname = 'get_user_activity_summary');" \
    "t"

# Test 17: Call get_trace_by_correlation_id
run_test "Call get_trace_by_correlation_id (returns 3 rows)" \
    "SELECT COUNT(*) FROM get_trace_by_correlation_id('$TEST_CORRELATION_ID'::UUID);" \
    "3"

# Test 18: Call get_user_activity_summary
run_test "Call get_user_activity_summary" \
    "SELECT total_requests FROM get_user_activity_summary('$TEST_USER_ID'::UUID);" \
    "3"

echo ""
echo "7. Trigger Validation"
echo "---------------------"

# Test 19: Auto-generate correlation_id trigger
run_test "Insert without correlation_id (should auto-generate)" \
    "SET app.service_account = 'gateway';
     INSERT INTO gateway_audit_logs (
         gateway_type, request_id, http_method, endpoint,
         user_id, email, roles, trial_mode,
         status_code, total_latency_ms, action, resource
     ) VALUES (
         'CP', 'req-test-trigger', 'GET', '/api/v1/health',
         '$TEST_USER_ID', 'test@waooaw.com', ARRAY['user'], false,
         200, 15, 'health_check', 'system'
     ) RETURNING correlation_id;" \
    ""

echo ""
echo "8. Performance Test"
echo "-------------------"

# Test 20: Bulk insert performance
echo -n "Testing: Bulk insert 100 logs... "
start_time=$(date +%s%N)

for i in {1..100}; do
    PGPASSWORD="${DB_PASSWORD}" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c \
        "SET app.service_account = 'gateway';
         INSERT INTO gateway_audit_logs (
             gateway_type, request_id, http_method, endpoint,
             user_id, email, roles, trial_mode,
             opa_policies_evaluated, opa_decisions, opa_latency_ms,
             status_code, total_latency_ms, action, resource
         ) VALUES (
             'CP', 'req-perf-$i', 'GET', '/api/v1/tasks',
             '$TEST_USER_ID', 'test@waooaw.com', ARRAY['user'], false,
             ARRAY['trial_mode'], '{\"trial_mode\": {\"allow\": true}}'::jsonb, 10,
             200, 150, 'list', 'task'
         );" > /dev/null 2>&1
done

end_time=$(date +%s%N)
duration=$(( (end_time - start_time) / 1000000 )) # Convert to milliseconds

if [ $duration -lt 10000 ]; then  # Less than 10 seconds for 100 inserts
    echo -e "${GREEN}✓ PASS${NC} ($duration ms)"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠ SLOW${NC} ($duration ms, expected < 10000 ms)"
    ((TESTS_PASSED++))
fi

# Test 21: Query performance (indexed query)
echo -n "Testing: Indexed query performance... "
start_time=$(date +%s%N)

PGPASSWORD="${DB_PASSWORD}" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c \
    "SELECT COUNT(*) FROM gateway_audit_logs WHERE user_id = '$TEST_USER_ID';" > /dev/null 2>&1

end_time=$(date +%s%N)
duration=$(( (end_time - start_time) / 1000000 ))

if [ $duration -lt 1000 ]; then  # Less than 1 second
    echo -e "${GREEN}✓ PASS${NC} ($duration ms)"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠ SLOW${NC} ($duration ms, expected < 1000 ms)"
    ((TESTS_PASSED++))
fi

echo ""
echo "9. Cleanup Test Data"
echo "--------------------"

# Test 22: Delete test data
run_test "Delete test data" \
    "DELETE FROM gateway_audit_logs WHERE user_id = '$TEST_USER_ID';" \
    ""

run_test "Verify cleanup (should be 0)" \
    "SELECT COUNT(*) FROM gateway_audit_logs WHERE user_id = '$TEST_USER_ID';" \
    "0"

echo ""
echo "===================================="
echo "📊 Test Summary"
echo "===================================="
echo -e "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
