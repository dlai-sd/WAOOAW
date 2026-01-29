#!/bin/bash
# Integration Test Runner for WAOOAW Plant Backend
# Docker-first test execution (no local Python environment required).

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Functions
print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC} $1"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}!${NC} $1"
}

check_dependencies() {
    print_header "Checking Dependencies"

    if ! command -v docker >/dev/null 2>&1; then
        print_error "docker is required"
        exit 1
    fi

    if ! docker version >/dev/null 2>&1; then
        print_error "docker daemon is not available"
        exit 1
    fi

    if ! docker compose version >/dev/null 2>&1; then
        print_error "docker compose is required"
        exit 1
    fi

    print_success "Docker + Docker Compose available"
}

start_test_services() {
    print_header "Starting Test Services"

    docker compose -f "$PROJECT_ROOT/tests/docker-compose.test.yml" up -d

    print_success "Test services started (postgres:5433, redis:6380)"
}

_run_pytest_in_docker() {
    local cmd="$1"

    docker run --rm \
        --network host \
        -v "$PROJECT_ROOT:/repo" \
        -w "/repo/src/Plant/BackEnd" \
        -e "ENVIRONMENT=${ENVIRONMENT:-test}" \
        -e "DATABASE_URL=${DATABASE_URL:-postgresql+asyncpg://waooaw_test:waooaw_test_password@localhost:5433/waooaw_test_db}" \
        -e "REDIS_URL=${REDIS_URL:-redis://localhost:6380/0}" \
        python:3.11-slim \
        bash -lc "python -m pip install -q --disable-pip-version-check -r requirements.txt pytest pytest-asyncio pytest-cov pytest-mock pytest-timeout && ${cmd}"
}

run_tests() {
    local test_type="${1:-all}"
    
    print_header "Running Integration Tests"

    start_test_services
    
    case "$test_type" in
        all)
            echo "Running all integration tests with coverage..."
            _run_pytest_in_docker "python -m pytest tests/integration/ -v \
                --cov=core,models,validators \
                --cov-report=html \
                --cov-report=term-missing \
                --tb=short"
            ;;
        database)
            echo "Running database connection tests..."
            _run_pytest_in_docker "python -m pytest tests/integration/test_database_connection.py -v"
            ;;
        migrations)
            echo "Running migration tests..."
            _run_pytest_in_docker "python -m pytest tests/integration/test_alembic_migrations.py -v"
            ;;
        security)
            echo "Running security tests (RLS + Audit)..."
            _run_pytest_in_docker "python -m pytest \
                tests/integration/test_rls_policies.py \
                tests/integration/test_audit_trail.py \
                -v"
            ;;
        performance)
            echo "Running performance tests (pooling + transactions)..."
            _run_pytest_in_docker "python -m pytest \
                tests/integration/test_connector_pooling.py \
                tests/integration/test_transactions.py \
                -v"
            ;;
        vectors)
            echo "Running vector tests..."
            _run_pytest_in_docker "python -m pytest tests/integration/test_pgvector_functionality.py -v"
            ;;
        coverage)
            echo "Generating coverage report..."
            _run_pytest_in_docker "python -m pytest tests/integration/ \
                --cov=core,models,validators,security \
                --cov-report=html \
                --cov-report=term-missing \
                --cov-fail-under=90"
            echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"
            ;;
        *)
            print_error "Unknown test type: $test_type"
            echo "Valid options: all, database, migrations, security, performance, vectors, coverage"
            exit 1
            ;;
    esac
}

generate_report() {
    print_header "Generating Test Report"

    start_test_services

    _run_pytest_in_docker "python -m pytest tests/integration/ \
        -v \
        --cov=core,models,validators,security \
        --cov-report=html \
        --cov-report=term \
        --html=test_report.html \
        --self-contained-html"
    
    print_success "Reports generated:"
    echo "  - htmlcov/index.html (coverage)"
    echo "  - test_report.html (test results)"
}

show_help() {
    cat << EOF
${BLUE}Integration Test Runner - WAOOAW Plant Backend${NC}

Usage: $(basename "$0") [command] [options]

Commands:
  run [type]         Run integration tests
                     Types: all, database, migrations, security, performance, vectors
  
  coverage           Generate coverage report with ≥90% threshold
  report             Generate HTML test report and coverage
  check              Check dependencies only
  help               Show this help message

Examples:
  $(basename "$0") run all              # Run all tests with coverage
  $(basename "$0") run database         # Run database connection tests
  $(basename "$0") run security         # Run RLS + audit tests
  $(basename "$0") coverage             # Generate coverage report
  $(basename "$0") report               # Generate full HTML report

Environment:
  PROJECT: $PROJECT_ROOT

${BLUE}Test Files:${NC}
  - test_database_connection.py    (12 tests - async engine, extensions, pooling)
  - test_alembic_migrations.py     (11 tests - schema evolution)
  - test_rls_policies.py           (11 tests - constraints, append-only)
  - test_pgvector_functionality.py (9 tests - vector operations)
  - test_audit_trail.py            (10 tests - immutability, tamper detection)
  - test_connector_pooling.py      (11 tests - connection management)
  - test_transactions.py           (10 tests - ACID compliance)

${BLUE}Total: 74 async integration tests${NC}
Target Coverage: ≥90%

EOF
}

# Main execution
if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

case "$1" in
    run)
        check_dependencies
        run_tests "${2:-all}"
        ;;
    coverage)
        check_dependencies
        run_tests "coverage"
        ;;
    report)
        check_dependencies
        generate_report
        ;;
    check)
        check_dependencies
        print_success "All dependencies satisfied"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
