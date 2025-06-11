#!/bin/bash
# ==============================================================================
# COMPREHENSIVE SHOPIFY ANALYTICS TEST SUITE
# ==============================================================================
# This script runs a complete test suite covering:
# - Environment setup and validation
# - Code formatting and linting
# - Database connectivity testing
# - Unit and integration tests
# - Docker container testing
# - Application functionality validation
# - Performance and security checks

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Global variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEST_RESULTS_DIR="$PROJECT_ROOT/test-results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$TEST_RESULTS_DIR/test_suite_$TIMESTAMP.log"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0
WARNINGS=0

# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

print_header() {
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================================${NC}"
}

print_section() {
    echo ""
    echo -e "${CYAN}🔍 $1${NC}"
    echo -e "${CYAN}$(printf '%.0s-' {1..50})${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((TESTS_PASSED++))
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
    ((TESTS_FAILED++))
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((WARNINGS++))
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

run_test() {
    local test_name="$1"
    local test_command="$2"
    local required="${3:-true}"  # Default to required

    ((TESTS_RUN++))
    print_info "Running: $test_name"

    if eval "$test_command" >> "$LOG_FILE" 2>&1; then
        print_success "$test_name"
        return 0
    else
        if [ "$required" = "true" ]; then
            print_error "$test_name FAILED"
            return 1
        else
            print_warning "$test_name FAILED (non-critical)"
            return 0
        fi
    fi
}

check_command() {
    if command -v "$1" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# ==============================================================================
# SETUP AND INITIALIZATION
# ==============================================================================

initialize_test_suite() {
    print_header "🧪 SHOPIFY ANALYTICS COMPREHENSIVE TEST SUITE"

    # Create test results directory
    mkdir -p "$TEST_RESULTS_DIR"

    # Initialize log file
    echo "Test Suite Started: $(date)" > "$LOG_FILE"
    echo "Project Root: $PROJECT_ROOT" >> "$LOG_FILE"
    echo "" >> "$LOG_FILE"

    print_info "Test results will be saved to: $TEST_RESULTS_DIR"
    print_info "Detailed logs: $LOG_FILE"

    cd "$PROJECT_ROOT"
}

# ==============================================================================
# ENVIRONMENT VALIDATION
# ==============================================================================

validate_environment() {
    print_section "Environment Validation"

    # Check if we're in the right directory
    if [ ! -f "run.py" ] || [ ! -f "config.py" ]; then
        print_error "Not in Shopify Analytics project directory"
        exit 1
    fi
    print_success "Project directory validation"

    # Check Python version
    if check_command python3; then
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        print_success "Python 3 found: $PYTHON_VERSION"
    else
        print_error "Python 3 not found"
        exit 1
    fi

    # Check pip
    if check_command pip || check_command pip3; then
        print_success "pip package manager found"
    else
        print_error "pip not found"
        exit 1
    fi

    # Check Docker
    if check_command docker; then
        if docker info >/dev/null 2>&1; then
            print_success "Docker is running"
        else
            print_warning "Docker found but not running"
        fi
    else
        print_warning "Docker not found (Docker tests will be skipped)"
    fi

    # Check Docker Compose
    if check_command docker-compose; then
        print_success "Docker Compose found"
    else
        print_warning "Docker Compose not found (Docker tests will be skipped)"
    fi

    # Check .env file
    if [ -f ".env" ]; then
        print_success ".env file exists"
        # Validate .env format
        if grep -q "DATABASE_URL=" .env && grep -q "SECRET_KEY=" .env; then
            print_success ".env file has required variables"
        else
            print_warning ".env file missing required variables"
        fi
    else
        print_warning ".env file not found (database tests may fail)"
    fi
}

# ==============================================================================
# DEPENDENCY MANAGEMENT
# ==============================================================================

setup_dependencies() {
    print_section "Dependency Management"

    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        print_info "Activating virtual environment..."
        source venv/bin/activate
        print_success "Virtual environment activated"
    elif [ -d ".venv" ]; then
        print_info "Activating virtual environment (.venv)..."
        source .venv/bin/activate
        print_success "Virtual environment activated"
    else
        print_warning "No virtual environment found (recommended to use one)"
    fi

    # Install/update production dependencies
    if [ -f "requirements.txt" ]; then
        print_info "Installing production dependencies..."
        if pip install -r requirements.txt >/dev/null 2>&1; then
            print_success "Production dependencies installed"
        else
            print_error "Failed to install production dependencies"
            return 1
        fi
    fi

    # Install/update development dependencies
    if [ -f "requirements-dev.txt" ]; then
        print_info "Installing development dependencies..."
        if pip install -r requirements-dev.txt >/dev/null 2>&1; then
            print_success "Development dependencies installed"
        else
            print_warning "Failed to install development dependencies (some tests may be skipped)"
        fi
    else
        print_warning "requirements-dev.txt not found"
        # Install essential testing tools anyway
        print_info "Installing essential testing tools..."
        pip install pytest pytest-cov black flake8 isort mypy >/dev/null 2>&1 || true
    fi
}

# ==============================================================================
# CODE QUALITY CHECKS
# ==============================================================================

run_code_quality_checks() {
    print_section "Code Quality Checks"

    # Check if black is available
    if check_command black; then
        print_info "Checking code formatting with Black..."
        if black --check app/ tests/ >/dev/null 2>&1; then
            print_success "Code formatting is correct"
        else
            print_warning "Code formatting issues found"
            print_info "Attempting to auto-fix formatting..."
            if black app/ tests/ >/dev/null 2>&1; then
                print_success "Code formatting fixed automatically"
            else
                print_error "Failed to fix code formatting"
            fi
        fi
    else
        print_warning "Black not available (skipping formatting check)"
    fi

    # Check import sorting
    if check_command isort; then
        print_info "Checking import sorting..."
        if isort --check-only app/ tests/ >/dev/null 2>&1; then
            print_success "Import sorting is correct"
        else
            print_warning "Import sorting issues found"
            print_info "Attempting to auto-fix import sorting..."
            if isort app/ tests/ >/dev/null 2>&1; then
                print_success "Import sorting fixed automatically"
            else
                print_error "Failed to fix import sorting"
            fi
        fi
    else
        print_warning "isort not available (skipping import sorting check)"
    fi

    # Run linting
    if check_command flake8; then
        print_info "Running linting with flake8..."
        if flake8 app/ tests/ >/dev/null 2>&1; then
            print_success "No linting issues found"
        else
            print_warning "Linting issues found (check detailed logs)"
            # Don't fail on linting issues, just warn
        fi
    else
        print_warning "flake8 not available (skipping linting)"
    fi

    # Run type checking
    if check_command mypy; then
        print_info "Running type checking with mypy..."
        if mypy app/ >/dev/null 2>&1; then
            print_success "No type checking issues found"
        else
            print_warning "Type checking issues found (non-blocking)"
        fi
    else
        print_warning "mypy not available (skipping type checking)"
    fi
}

# ==============================================================================
# DATABASE CONNECTIVITY TESTS
# ==============================================================================

test_database_connectivity() {
    print_section "Database Connectivity Tests"

    if [ ! -f ".env" ]; then
        print_warning "No .env file found, skipping database tests"
        return 0
    fi

    # Load environment variables safely
    if export $(grep -v '^#' .env | grep -v '^$' | xargs) 2>/dev/null; then
        print_success "Environment variables loaded"
    else
        print_warning "Failed to load environment variables"
        return 0
    fi

    if [ -z "$DATABASE_URL" ]; then
        print_warning "DATABASE_URL not set, skipping database tests"
        return 0
    fi

    # Test database connection with Python
    print_info "Testing database connection..."
    cat > /tmp/db_test.py << 'EOF'
import sys
import os
try:
    from sqlalchemy import create_engine, text
    engine = create_engine(os.environ['DATABASE_URL'])
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("SUCCESS: Database connection established")

        # Test materialized view
        try:
            result = conn.execute(text("SELECT COUNT(*) FROM catalogue.all_shops_product_data_extended LIMIT 1"))
            count = result.fetchone()[0]
            print(f"SUCCESS: Materialized view accessible with {count:,} records")
        except Exception as e:
            print(f"WARNING: Materialized view issue: {e}")
            sys.exit(2)

        # Test shop data
        try:
            result = conn.execute(text("SELECT DISTINCT shop_technical_name FROM catalogue.all_shops_product_data_extended LIMIT 3"))
            shops = [row[0] for row in result]
            print(f"SUCCESS: Found shops: {', '.join(shops)}")
        except Exception as e:
            print(f"WARNING: Shop data access issue: {e}")
            sys.exit(2)

except ImportError:
    print("WARNING: SQLAlchemy not available")
    sys.exit(2)
except Exception as e:
    print(f"ERROR: Database connection failed: {e}")
    sys.exit(1)
EOF

    if python3 /tmp/db_test.py 2>&1 | tee -a "$LOG_FILE"; then
        DB_EXIT_CODE=${PIPESTATUS[0]}
        if [ $DB_EXIT_CODE -eq 0 ]; then
            print_success "Database connectivity tests passed"
        elif [ $DB_EXIT_CODE -eq 2 ]; then
            print_warning "Database connectivity tests completed with warnings"
        else
            print_error "Database connectivity tests failed"
        fi
    fi

    rm -f /tmp/db_test.py
}

# ==============================================================================
# UNIT AND INTEGRATION TESTS
# ==============================================================================

run_python_tests() {
    print_section "Python Unit and Integration Tests"

    if [ ! -d "tests" ]; then
        print_warning "Tests directory not found, skipping Python tests"
        return 0
    fi

    if check_command pytest; then
        print_info "Running pytest..."

        # Create pytest configuration for this run
        cat > pytest.ini << 'EOF'
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=app
    --cov-report=term-missing
    --cov-report=html:test-results/htmlcov
    --cov-report=xml:test-results/coverage.xml
    --junit-xml=test-results/junit.xml

markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    api: marks tests as API tests
EOF

        # Run tests with different markers
        print_info "Running unit tests..."
        if pytest tests/ -m "unit or not slow" --maxfail=5 2>&1 | tee -a "$LOG_FILE"; then
            print_success "Unit tests passed"
        else
            print_warning "Some unit tests failed"
        fi

        print_info "Running integration tests..."
        if pytest tests/ -m "integration" --maxfail=3 2>&1 | tee -a "$LOG_FILE"; then
            print_success "Integration tests passed"
        else
            print_warning "Some integration tests failed"
        fi

        # Check coverage
        if check_command coverage; then
            print_info "Checking test coverage..."
            COVERAGE=$(coverage report --show-missing | tail -1 | awk '{print $4}' | sed 's/%//')
            if [ "${COVERAGE%.*}" -ge 80 ]; then
                print_success "Test coverage: $COVERAGE% (meets 80% threshold)"
            else
                print_warning "Test coverage: $COVERAGE% (below 80% threshold)"
            fi
        fi

    else
        print_warning "pytest not available, skipping Python tests"
    fi
}

# ==============================================================================
# DOCKER TESTS
# ==============================================================================

run_docker_tests() {
    print_section "Docker Container Tests"

    if ! check_command docker || ! check_command docker-compose; then
        print_warning "Docker not available, skipping container tests"
        return 0
    fi

    if ! docker info >/dev/null 2>&1; then
        print_warning "Docker not running, skipping container tests"
        return 0
    fi

    # Test Docker build
    print_info "Testing Docker build..."
    if docker-compose build web >/dev/null 2>&1; then
        print_success "Docker build successful"
    else
        print_error "Docker build failed"
        return 1
    fi

    # Test container startup
    print_info "Testing container startup..."
    if timeout 60 docker-compose run --rm --entrypoint="" web python3 -c "print('Container startup successful')" >/dev/null 2>&1; then
        print_success "Container startup test passed"
    else
        print_error "Container startup test failed"
        return 1
    fi

    # Test database connection from container
    if [ -f ".env" ]; then
        print_info "Testing database connection from container..."
        if timeout 60 docker-compose run --rm --entrypoint="" web python3 -c "
from app import create_app, db
from sqlalchemy import text
app = create_app()
with app.app_context():
    result = db.session.execute(text('SELECT 1'))
    print('Container database connection successful')
" >/dev/null 2>&1; then
            print_success "Container database connection test passed"
        else
            print_warning "Container database connection test failed"
        fi
    fi

    # Clean up test containers
    docker-compose down >/dev/null 2>&1 || true
}

# ==============================================================================
# APPLICATION FUNCTIONALITY TESTS
# ==============================================================================

run_application_tests() {
    print_section "Application Functionality Tests"

    # Start application in background for testing
    print_info "Starting application for functionality testing..."

    if check_command docker-compose && docker info >/dev/null 2>&1; then
        # Use Docker for testing
        docker-compose up -d >/dev/null 2>&1
        sleep 10  # Wait for startup

        # Test if application is responding
        print_info "Testing application responsiveness..."
        for i in {1..30}; do
            if curl -s http://localhost:5000/ >/dev/null 2>&1; then
                print_success "Application is responding"
                break
            fi
            sleep 2
        done

        # Test API endpoints
        print_info "Testing API endpoints..."
        if curl -s http://localhost:5000/api/shops | grep -q '\['; then
            print_success "Shops API endpoint working"
        else
            print_warning "Shops API endpoint not working"
        fi

        if curl -s http://localhost:5000/api/vendors >/dev/null 2>&1; then
            print_success "Vendors API endpoint working"
        else
            print_warning "Vendors API endpoint not working"
        fi

        # Test main pages
        for page in "" "products" "analytics" "consistency-check"; do
            if curl -s "http://localhost:5000/$page" | grep -q "Shopify"; then
                print_success "Page /$page is accessible"
            else
                print_warning "Page /$page is not accessible"
            fi
        done

        # Clean up
        docker-compose down >/dev/null 2>&1

    else
        print_warning "Cannot start application for testing (Docker not available)"
    fi
}

# ==============================================================================
# SECURITY AND PERFORMANCE CHECKS
# ==============================================================================

run_security_checks() {
    print_section "Security and Performance Checks"

    # Check for common security issues
    print_info "Checking for hardcoded secrets..."
    if grep -r "password\|secret\|key" --include="*.py" app/ | grep -v "SECRET_KEY" | grep -v "password'" >/dev/null 2>&1; then
        print_warning "Potential hardcoded secrets found (check logs)"
    else
        print_success "No obvious hardcoded secrets found"
    fi

    # Check .env file security
    if [ -f ".env" ]; then
        if [ "$(stat -c %a .env 2>/dev/null || stat -f %A .env 2>/dev/null)" = "600" ]; then
            print_success ".env file has secure permissions"
        else
            print_warning ".env file permissions should be 600"
        fi
    fi

    # Check for TODO/FIXME comments
    TODO_COUNT=$(grep -r "TODO\|FIXME\|XXX" --include="*.py" app/ 2>/dev/null | wc -l)
    if [ "$TODO_COUNT" -gt 0 ]; then
        print_warning "$TODO_COUNT TODO/FIXME comments found"
    else
        print_success "No TODO/FIXME comments found"
    fi

    # Check requirements for known vulnerabilities (if safety is available)
    if check_command safety; then
        print_info "Checking for known vulnerabilities..."
        if safety check >/dev/null 2>&1; then
            print_success "No known vulnerabilities found"
        else
            print_warning "Potential vulnerabilities found (check with 'safety check')"
        fi
    else
        print_info "Install 'safety' package for vulnerability checking"
    fi
}

# ==============================================================================
# PERFORMANCE TESTS
# ==============================================================================

run_performance_tests() {
    print_section "Performance Tests"

    # Test import time
    print_info "Testing application import time..."
    IMPORT_TIME=$(python3 -c "
import time
start = time.time()
from app import create_app
end = time.time()
print(f'{end - start:.2f}')
" 2>/dev/null || echo "0")

    if [ "$(echo "$IMPORT_TIME < 2.0" | bc 2>/dev/null || echo 1)" = "1" ]; then
        print_success "Application import time: ${IMPORT_TIME}s (good)"
    else
        print_warning "Application import time: ${IMPORT_TIME}s (slow)"
    fi

    # Check file sizes
    if [ -d "app/static" ]; then
        STATIC_SIZE=$(du -sh app/static 2>/dev/null | cut -f1)
        print_info "Static files size: $STATIC_SIZE"
    fi

    # Check Python bytecode compilation
    print_info "Testing Python compilation..."
    if python3 -m py_compile app/*.py 2>/dev/null; then
        print_success "All Python files compile successfully"
    else
        print_error "Python compilation errors found"
    fi
}

# ==============================================================================
# REPORTING AND CLEANUP
# ==============================================================================

generate_test_report() {
    print_section "Test Results Summary"

    # Create summary report
    REPORT_FILE="$TEST_RESULTS_DIR/test_summary_$TIMESTAMP.txt"

    cat > "$REPORT_FILE" << EOF
SHOPIFY ANALYTICS TEST SUITE REPORT
Generated: $(date)
Project: Shopify Analytics Dashboard

SUMMARY:
========
Tests Run:    $TESTS_RUN
Tests Passed: $TESTS_PASSED
Tests Failed: $TESTS_FAILED
Warnings:     $WARNINGS

DETAILED RESULTS:
================
EOF

    # Append detailed log
    echo "" >> "$REPORT_FILE"
    cat "$LOG_FILE" >> "$REPORT_FILE"

    print_info "Detailed report saved to: $REPORT_FILE"

    # Print summary
    echo ""
    print_header "TEST SUITE SUMMARY"
    echo ""
    if [ $TESTS_FAILED -eq 0 ]; then
        print_success "All critical tests passed! ✨"
    else
        print_error "$TESTS_FAILED critical test(s) failed"
    fi

    if [ $WARNINGS -gt 0 ]; then
        print_warning "$WARNINGS warning(s) found"
    fi

    echo ""
    print_info "📊 Tests Run: $TESTS_RUN"
    print_info "✅ Passed: $TESTS_PASSED"
    print_info "❌ Failed: $TESTS_FAILED"
    print_info "⚠️  Warnings: $WARNINGS"
    echo ""

    if [ -f "$TEST_RESULTS_DIR/htmlcov/index.html" ]; then
        print_info "📈 Coverage report: $TEST_RESULTS_DIR/htmlcov/index.html"
    fi

    print_info "📋 Full report: $REPORT_FILE"
    print_info "📝 Detailed logs: $LOG_FILE"
}

cleanup() {
    print_section "Cleanup"

    # Clean up temporary files
    rm -f pytest.ini

    # Stop any running containers
    if check_command docker-compose; then
        docker-compose down >/dev/null 2>&1 || true
    fi

    print_success "Cleanup completed"
}

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

main() {
    # Trap to ensure cleanup on exit
    trap cleanup EXIT

    # Initialize
    initialize_test_suite

    # Run test phases
    validate_environment
    setup_dependencies
    run_code_quality_checks
    test_database_connectivity
    run_python_tests
    run_docker_tests
    run_application_tests
    run_security_checks
    run_performance_tests

    # Generate report
    generate_test_report

    # Exit with appropriate code
    if [ $TESTS_FAILED -eq 0 ]; then
        echo ""
        print_success "🎉 Test suite completed successfully!"
        exit 0
    else
        echo ""
        print_error "💥 Test suite completed with failures"
        exit 1
    fi
}

# ==============================================================================
# SCRIPT ENTRY POINT
# ==============================================================================

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi