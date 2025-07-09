#!/bin/bash

# Session End Hook for Claude Code
# Runs when main agent finishes responding

set -e

# Read JSON input from stdin (though we don't need it for this hook)
json_input=$(cat)

# Colors for output
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Project root directory
PROJECT_ROOT="/mnt/c/Users/Administrator/DataspellProjects/webapp_components"
WORKFLOW_DIR="$PROJECT_ROOT/claude_workflow"

echo -e "${BLUE}[CLAUDE HOOK]${NC} Session end documentation reminder"

# Check current time for context-aware reminders
current_hour=$(date +%H)
current_date=$(date +%Y-%m-%d)

# End of work day reminder
if [ $current_hour -ge 17 ]; then
    echo -e "${BLUE}🕐 End of day documentation reminder:${NC}"
    echo -e "${BLUE}   • Update project_status.md with today's progress${NC}"
    echo -e "${BLUE}   • Ensure all test results are documented${NC}"
    echo -e "${BLUE}   • Note any issues or blockers for tomorrow${NC}"
fi

# Start of work day reminder
if [ $current_hour -ge 8 ] && [ $current_hour -le 10 ]; then
    echo -e "${BLUE}🌅 Start of day documentation reminder:${NC}"
    echo -e "${BLUE}   • Check project_status.md for today's priorities${NC}"
    echo -e "${BLUE}   • Review any pending test failures or issues${NC}"
fi

# General session end reminder
echo -e "${YELLOW}📋 Session Summary:${NC}"
echo -e "${YELLOW}   • Remember to update project_status.md if needed${NC}"
echo -e "${YELLOW}   • Document any test results in test_reports.md${NC}"
echo -e "${YELLOW}   • Keep documentation current for next session${NC}"