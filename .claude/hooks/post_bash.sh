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
DOCS_DIR="$PROJECT_ROOT/docs"

echo ""
echo -e "${BOLD}${YELLOW}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${YELLOW}⚡ CLAUDE ENFORCEMENT HOOK EXECUTING: POST-BASH AUTOMATION${NC}"
echo -e "${BOLD}${YELLOW}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Command: $bash_command${NC}"
echo -e "${YELLOW}Exit Code: $exit_code${NC}"
echo ""

# Function to check if this is a test command
is_test_command() {
    if [[ "$bash_command" == *"pytest"* ]] || [[ "$bash_command" == *"test"* ]]; then
        return 0
    fi
    return 1
}

# AUTOMATIC TEST REPORT GENERATION after test execution
if is_test_command; then
    echo -e "${YELLOW}🧪 TEST EXECUTION COMPLETED - TRIGGERING AUTOMATIC REPORT GENERATION${NC}"
    
    # Automatic test report generation
    echo -e "${BLUE}🤖 AUTO-GENERATING TEST REPORT...${NC}"
    
    # Run the automated test report generator
    cd "$PROJECT_ROOT"
    if python tools/scripts/generate_test_reports.py --unit-only > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Automated test report generated successfully${NC}"
        echo -e "${GREEN}   Location: docs/test_reports_generated/test_summary_[timestamp].md${NC}"
    else
        echo -e "${YELLOW}⚠️  Automated report generation failed, manual update required${NC}"
    fi
    
    # MANDATORY test report documentation update
    if [ "$exit_code" -eq "0" ]; then
        echo -e "${GREEN}✅ Tests passed - automated report generated${NC}"
        echo -e "${RED}🚨 MANDATORY: Claude must update docs/test_reports_generated/test_reports.md${NC}"
        echo -e "${RED}   REQUIREMENT: Add chronological entry with test results summary${NC}"
    else
        echo -e "${RED}❌ Tests failed - CRITICAL ACTION REQUIRED${NC}"
        echo -e "${RED}🚨 MANDATORY: Claude must immediately update test documentation${NC}"
        echo -e "${RED}   REQUIREMENTS:${NC}"
        echo -e "${RED}   1. Update docs/test_reports_generated/test_reports.md with failure analysis${NC}"
        echo -e "${RED}   2. Include: failed test details, error messages, resolution steps${NC}"
        echo -e "${RED}   3. Document debugging approach and next steps${NC}"
        echo -e "${RED}   This is ENFORCED by testing_rules.md!${NC}"
    fi
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
echo ""
echo -e "${BOLD}${YELLOW}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${GREEN}✅ POST-BASH HOOK COMPLETED - AUTOMATION EXECUTED${NC}"
echo -e "${BOLD}${YELLOW}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}📊 Documentation Health Reminder:${NC}"
echo -e "${BLUE}   • Check project_status.md is current${NC}"
echo -e "${BLUE}   • Ensure test_reports.md reflects latest results${NC}"
echo -e "${BLUE}   • Update relevant documentation based on work done${NC}"
echo ""
