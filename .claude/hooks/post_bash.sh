#!/bin/bash

# Correct Post-Bash Hook for Claude Code
# Reads JSON input from stdin as per Claude Code documentation

set -e

# Read JSON input from stdin
json_input=$(cat)

# Extract command and exit code from JSON
bash_command=$(echo "$json_input" | jq -r '.params.command // empty')
exit_code=$(echo "$json_input" | jq -r '.result.exit_code // "0"')

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Project root directory
PROJECT_ROOT="/mnt/c/Users/Administrator/DataspellProjects/webapp_components"
WORKFLOW_DIR="$PROJECT_ROOT/claude_workflow"

echo -e "${BLUE}[CLAUDE HOOK]${NC} Post-bash check for: $bash_command (exit: $exit_code)"

# Function to check if this is a test command
is_test_command() {
    if [[ "$bash_command" == *"pytest"* ]] || [[ "$bash_command" == *"test"* ]]; then
        return 0
    fi
    return 1
}

# Enforce test report updates after test execution
if is_test_command; then
    echo -e "${YELLOW}🧪 TEST EXECUTION COMPLETED${NC}"
    
    if [ "$exit_code" -eq "0" ]; then
        echo -e "${GREEN}✅ Tests passed - remember to update test_reports.md with success details${NC}"
    else
        echo -e "${RED}❌ Tests failed - MUST update test_reports.md with failure analysis${NC}"
        echo -e "${RED}   Include: failed test details, error messages, resolution steps${NC}"
    fi
    
    echo -e "${BLUE}💡 Consider updating test documentation${NC}"
fi

# Check for deployment commands
if [[ "$bash_command" == *"start.sh"* ]] || [[ "$bash_command" == *"restart.sh"* ]] || [[ "$bash_command" == *"docker"* ]]; then
    echo -e "${GREEN}🚀 Deployment command executed${NC}"
    echo -e "${YELLOW}   Consider updating project_status.md with deployment status${NC}"
fi

# Check for migration commands
if [[ "$bash_command" == *"migrate"* ]] || [[ "$bash_command" == *"upgrade"* ]]; then
    echo -e "${GREEN}🗄️  Database operation executed${NC}"
    echo -e "${YELLOW}   Consider updating database_schema_guide.md if schema changed${NC}"
fi

# General documentation health reminder
echo -e "${BLUE}📊 Documentation Health Reminder:${NC}"
echo -e "${BLUE}   • Check project_status.md is current${NC}"
echo -e "${BLUE}   • Ensure test_reports.md reflects latest results${NC}"
echo -e "${BLUE}   • Update relevant documentation based on work done${NC}"
