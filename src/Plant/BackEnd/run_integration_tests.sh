#!/bin/bash
# Integration Test Runner for WAOOAW Plant Backend
# Handles environment setup and test execution with proper error handling

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV_PATH="$PROJECT_ROOT/.venv"

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

check_venv() {
    if [ ! -d "$VENV_PATH" ]; then
        print_error "Virtual environment not found at $VENV_PATH"
        echo "Create it with: python3 -m venv $VENV_PATH"
        exit 1
    fi
    print_success "Virtual environment found"
}

check_dependencies() {
    print_header "Checking Dependencies"
    
    # Activate venv
    source "$VENV_PATH/bin/activate"
    
    # Check pytest
    if ! python -m pytest --version > /dev/null 2>&1; then
        print_error "pytest not installed"
        echo "Installing: pip install -r requirements.txt"
        pip install -r "$SCRIPT_DIR/requirements.txt"
    else
        print_success "pytest $(python -m pytest --version 2>&1 | cut -d' ' -f2)"
    fi
    
    # Check pytest-asyncio
    if ! python -c "import pytest_asyncio" 2>/dev/null; then
        print_error "pytest-asyncio not installed"
        pip install pytest-asyncio
    else
        print_success "pytest-asyncio installed"
    fi
    
    # Check testcontainers
    if ! python -c "import testcontainers" 2>/dev/null; then
        print_error "testcontainers not installed"
        pip install testcontainers
    else
        print_success "testcontainers installed"
    fi
    
    # Check sqlalchemy
    if ! python -c "from sqlalchemy import __version__; print(__version__)" 2>/dev/null; then
        print_error "SQLAlchemy not installed"
        pip install "sqlalchemy>=2.0"
    else
        print_success "SQLAlchemy $(python -c "from sqlalchemy import __version__; print(__version__)")"
    fi
}

run_tests() {
    local test_type="${1:-all}"
    
    print_header "Running Integration Tests"
    
    source "$VENV_PATH/bin/activate"
    
    case "$test_type" in
        all)
            echo "Running all integration tests with coverage..."
            python -m pytest tests/integration/ -v \
                --cov=core,models,validators \
                --cov-report=html \
                --cov-report=term-missing \
                --tb=short
            ;;
        database)
            echo "Running database connection tests..."
            python -m pytest tests/integration/test_database_connection.py -v
            ;;
        migrations)
            echo "Running migration tests..."
            python -m pytest tests/integration/test_alembic_migrations.py -v
            ;;
        security)
            echo "Running security tests (RLS + Audit)..."
            python -m pytest \
                tests/integration/test_rls_policies.py \
                tests/integration/test_audit_trail.py \
                -v
            ;;
        performance)
            echo "Running performance tests (pooling + transactions)..."
            python -m pytest \
                tests/integration/test_connector_pooling.py \
                tests/integration/test_transactions.py \
                -v
            ;;
        vectors)
            echo "Running vector tests..."
            python -m pytest tests/integration/test_pgvector_functionality.py -v
            ;;
        coverage)
            echo "Generating coverage report..."
            python -m pytest tests/integration/ \
                --cov=core,models,validators,security \
                --cov-report=html \
                --cov-report=term-missing \
                --cov-fail-under=90
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
    
    source "$VENV_PATH/bin/activate"
    
    python -m pytest tests/integration/ \
        -v \
        --cov=core,models,validators,security \
        --cov-report=html \
        --cov-report=term \
        --html=test_report.html \
        --self-contained-html
    
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
  VENV: $VENV_PATH
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
        check_venv
        check_dependencies
        run_tests "${2:-all}"
        ;;
    coverage)
        check_venv
        check_dependencies
        run_tests "coverage"
        ;;
    report)
        check_venv
        check_dependencies
        generate_report
        ;;
    check)
        check_venv
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
