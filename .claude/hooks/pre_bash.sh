#!/bin/bash

# Correct Pre-Bash Hook for Claude Code
# Reads JSON input from stdin as per Claude Code documentation

set -e

# Read JSON input from stdin
json_input=$(cat)

# Extract command from JSON
bash_command=$(echo "$json_input" | jq -r '.params.command // empty')

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Project root directory
PROJECT_ROOT="/mnt/c/Users/Administrator/DataspellProjects/webapp_components"
WORKFLOW_DIR="$PROJECT_ROOT/claude_workflow"

echo -e "${BLUE}[CLAUDE HOOK]${NC} Pre-bash check for: $bash_command"

# Function to check if this is a git commit
is_git_commit() {
    if [[ "$bash_command" == *"git commit"* ]]; then
        return 0
    fi
    return 1
}

# Function to check if this is a test command
is_test_command() {
    if [[ "$bash_command" == *"pytest"* ]] || [[ "$bash_command" == *"test"* ]]; then
        return 0
    fi
    return 1
}

# Check for git commits and enforce project status updates
if is_git_commit; then
    echo -e "${YELLOW}📝 GIT COMMIT DETECTED${NC}"
    
    # Check if project_status.md has recent updates
    if [[ -f "$WORKFLOW_DIR/project_status.md" ]]; then
        last_modified=$(stat -c %Y "$WORKFLOW_DIR/project_status.md" 2>/dev/null || echo 0)
        current_time=$(date +%s)
        hours_since_update=$(((current_time - last_modified) / 3600))
        
        if [ $hours_since_update -gt 1 ]; then
            echo -e "${RED}⚠️  WARNING: project_status.md not updated in $hours_since_update hours${NC}"
            echo -e "${RED}   Consider updating project status before committing${NC}"
            # Note: Can't actually block in Claude Code hooks - just warn
        fi
    fi
fi

# Remind about test reporting
if is_test_command; then
    echo -e "${YELLOW}🧪 TEST COMMAND DETECTED${NC}"
    echo -e "${YELLOW}   Remember to update test_reports.md after test completion${NC}"
fi