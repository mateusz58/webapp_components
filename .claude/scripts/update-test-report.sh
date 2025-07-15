#!/bin/bash

# Update Test Report Command
# Guided update of test_reports.md with proper formatting

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="/mnt/c/Users/Administrator/DataspellProjects/webapp_components"
DOCS_DIR="$PROJECT_ROOT/docs"
TEST_REPORTS_FILE="$DOCS_DIR/test_reports.md"

echo -e "${BOLD}${BLUE}🧪 Update Test Reports${NC}"
echo -e "${BLUE}======================${NC}"

# Function to add a new test report entry
add_test_report() {
    local test_type="$1"
    local total_tests="$2"
    local passed_tests="$3"
    local failed_tests="$4"
    local coverage="$5"
    local notes="$6"
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    
    # Calculate pass rate
    local pass_rate=0
    if [ $total_tests -gt 0 ]; then
        pass_rate=$(( (passed_tests * 100) / total_tests ))
    fi
    
    # Determine status icon
    local status_icon="✅"
    if [ $failed_tests -gt 0 ]; then
        status_icon="❌"
    fi
    
    # Prepare the entry
    local entry="## 📊 $timestamp - $test_type: $pass_rate% Pass Rate Achievement  \n"
    entry+="**Timestamp**: $timestamp  \n"
    entry+="**Tester**: Claude Code AI Assistant  \n"
    entry+="**Session Type**: $test_type  \n"
    entry+="**Duration**: Full testing session  \n\n"
    
    entry+="### $status_icon Test Results Summary  \n"
    entry+="- **Total Tests**: $total_tests\n"
    entry+="- **Passed**: $passed_tests\n"
    entry+="- **Failed**: $failed_tests\n"
    entry+="- **Pass Rate**: $pass_rate%\n"
    
    if [[ -n "$coverage" ]]; then
        entry+="- **Coverage**: $coverage%\n"
    fi
    
    entry+="\n"
    
    if [ $failed_tests -gt 0 ]; then
        entry+="### ❌ Issues Identified\n"
        entry+="$notes\n\n"
        entry+="### 🔧 Next Steps\n"
        entry+="- Fix failing tests\n"
        entry+="- Re-run test suite\n"
        entry+="- Update documentation\n\n"
    else
        entry+="### ✅ Success Notes\n"
        entry+="$notes\n\n"
        entry+="### 🎯 Achievements\n"
        entry+="- All tests passing\n"
        entry+="- Good test coverage maintained\n"
        entry+="- System stability confirmed\n\n"
    fi
    
    entry+="---\n\n"
    
    # Add to the beginning of the file (after the header)
    if [[ -f "$TEST_REPORTS_FILE" ]]; then
        # Create a temporary file with the new entry
        local temp_file=$(mktemp)
        
        # Get the header (first few lines until the first "##")
        awk '/^## / && NR > 10 { exit } { print }' "$TEST_REPORTS_FILE" > "$temp_file"
        
        # Add the new entry
        echo -e "$entry" >> "$temp_file"
        
        # Add the rest of the file (skip the header)
        awk '/^## / && NR > 10 { found=1 } found { print }' "$TEST_REPORTS_FILE" >> "$temp_file"
        
        # Replace the original file
        mv "$temp_file" "$TEST_REPORTS_FILE"
    else
        echo -e "${RED}❌ test_reports.md not found!${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✅ Test report entry added successfully${NC}"
}

# Function to run tests and capture results
run_and_capture_tests() {
    local test_command="$1"
    local test_type="$2"
    
    echo -e "${BLUE}Running tests: $test_command${NC}"
    
    # Run the test command and capture output
    local output_file=$(mktemp)
    local exit_code=0
    
    cd "$PROJECT_ROOT"
    
    # Run the test command
    if eval "$test_command" > "$output_file" 2>&1; then
        exit_code=0
    else
        exit_code=$?
    fi
    
    # Parse the output for test results
    local total_tests=0
    local passed_tests=0
    local failed_tests=0
    local coverage=""
    
    # Try to parse pytest output
    if grep -q "failed" "$output_file"; then
        failed_tests=$(grep -o "[0-9]* failed" "$output_file" | grep -o "[0-9]*" | head -1)
    fi
    
    if grep -q "passed" "$output_file"; then
        passed_tests=$(grep -o "[0-9]* passed" "$output_file" | grep -o "[0-9]*" | head -1)
    fi
    
    # Calculate total
    total_tests=$((passed_tests + failed_tests))
    
    # Try to extract coverage
    if grep -q "coverage" "$output_file"; then
        coverage=$(grep -o "[0-9]*%" "$output_file" | head -1 | grep -o "[0-9]*")
    fi
    
    # Prepare notes from output
    local notes=""
    if [ $exit_code -eq 0 ]; then
        notes="All tests completed successfully. System is stable and ready for deployment."
    else
        notes="Test failures detected. See output below for details:\n\n\`\`\`\n$(tail -20 "$output_file")\n\`\`\`"
    fi
    
    # Add the test report
    add_test_report "$test_type" "$total_tests" "$passed_tests" "$failed_tests" "$coverage" "$notes"
    
    # Show results
    echo -e "${BLUE}Test Results:${NC}"
    echo -e "${BLUE}  Total: $total_tests${NC}"
    echo -e "${BLUE}  Passed: $passed_tests${NC}"
    echo -e "${BLUE}  Failed: $failed_tests${NC}"
    if [[ -n "$coverage" ]]; then
        echo -e "${BLUE}  Coverage: $coverage%${NC}"
    fi
    
    # Clean up
    rm -f "$output_file"
    
    return $exit_code
}

# Interactive menu
show_menu() {
    echo -e "${BOLD}Choose an action:${NC}"
    echo -e "${BLUE}1.${NC} Run and record unit tests"
    echo -e "${BLUE}2.${NC} Run and record API tests"
    echo -e "${BLUE}3.${NC} Run and record Selenium tests"
    echo -e "${BLUE}4.${NC} Run and record all tests"
    echo -e "${BLUE}5.${NC} Manual test report entry"
    echo -e "${BLUE}6.${NC} View recent test reports"
    echo -e "${BLUE}7.${NC} Exit"
    echo -n "Enter your choice [1-7]: "
}

# Function to view recent test reports
view_recent_reports() {
    if [[ -f "$TEST_REPORTS_FILE" ]]; then
        echo -e "${BOLD}${BLUE}Recent Test Reports (last 3 entries):${NC}"
        head -100 "$TEST_REPORTS_FILE"
    else
        echo -e "${RED}❌ test_reports.md not found!${NC}"
    fi
}

# Function for manual test report entry
manual_test_entry() {
    echo -e "${BLUE}Manual test report entry:${NC}"
    echo -n "Enter test type (e.g., 'Unit Tests', 'API Tests', 'Selenium E2E'): "
    read -r test_type
    echo -n "Enter total tests: "
    read -r total_tests
    echo -n "Enter passed tests: "
    read -r passed_tests
    echo -n "Enter failed tests: "
    read -r failed_tests
    echo -n "Enter coverage percentage (optional): "
    read -r coverage
    echo -n "Enter notes/comments: "
    read -r notes
    
    add_test_report "$test_type" "$total_tests" "$passed_tests" "$failed_tests" "$coverage" "$notes"
}

# Main interactive loop
main() {
    while true; do
        show_menu
        read -r choice
        
        case $choice in
            1)
                echo -e "${BLUE}Running unit tests...${NC}"
                run_and_capture_tests "python -m pytest tests/unit/ -v" "Unit Tests"
                ;;
            2)
                echo -e "${BLUE}Running API tests...${NC}"
                run_and_capture_tests "python -m pytest tests/api/ -v" "API Tests"
                ;;
            3)
                echo -e "${BLUE}Running Selenium tests...${NC}"
                run_and_capture_tests "python -m pytest tests/selenium/ -v" "Selenium E2E Tests"
                ;;
            4)
                echo -e "${BLUE}Running all tests...${NC}"
                run_and_capture_tests "python -m pytest tests/ -v --cov=app" "Complete Test Suite"
                ;;
            5)
                manual_test_entry
                ;;
            6)
                view_recent_reports
                ;;
            7)
                echo -e "${GREEN}✅ Test report update completed${NC}"
                break
                ;;
            *)
                echo -e "${RED}❌ Invalid choice. Please try again.${NC}"
                ;;
        esac
        
        echo
        echo -e "${YELLOW}Press Enter to continue...${NC}"
        read -r
        clear
    done
}

# Check if test reports file exists
if [[ ! -f "$TEST_REPORTS_FILE" ]]; then
    echo -e "${RED}❌ test_reports.md not found at $TEST_REPORTS_FILE${NC}"
    echo -e "${YELLOW}Please ensure the file exists before running this command${NC}"
    exit 1
fi

# Start the interactive process
main