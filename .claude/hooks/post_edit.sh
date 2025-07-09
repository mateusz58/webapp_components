#!/bin/bash

# Correct Post-Edit Hook for Claude Code
# Reads JSON input from stdin as per Claude Code documentation

set -e

# Read JSON input from stdin
json_input=$(cat)

# Extract tool name and file path from JSON
tool_name=$(echo "$json_input" | jq -r '.tool // empty')
file_path=$(echo "$json_input" | jq -r '.params.file_path // .params.path // empty')

# Colors for output
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Project root directory
PROJECT_ROOT="/mnt/c/Users/Administrator/DataspellProjects/webapp_components"
WORKFLOW_DIR="$PROJECT_ROOT/claude_workflow"

echo -e "${BLUE}[CLAUDE HOOK]${NC} Post-edit check for tool: $tool_name"

# Function to check documentation reminders based on file type
check_documentation_reminder() {
    local file="$1"
    
    # API file modifications
    if [[ "$file" == *"/api/"* ]] && [[ "$file" == *.py ]]; then
        echo -e "${YELLOW}📝 REMINDER: API file modified - consider updating api_documentation.md${NC}"
        echo -e "${YELLOW}   File: $file${NC}"
    fi
    
    # Database model modifications
    if [[ "$file" == *"models.py"* ]] || [[ "$file" == *"migration"* ]]; then
        echo -e "${YELLOW}🗄️  REMINDER: Database file modified - consider updating database_schema_guide.md${NC}"
        echo -e "${YELLOW}   File: $file${NC}"
    fi
    
    # Test file modifications
    if [[ "$file" == *"test_"* ]] || [[ "$file" == *"/tests/"* ]]; then
        echo -e "${YELLOW}🧪 REMINDER: Test file modified - remember to update test_reports.md after running tests${NC}"
        echo -e "${YELLOW}   File: $file${NC}"
    fi
    
    # Service/utility modifications
    if [[ "$file" == *"/services/"* ]] || [[ "$file" == *"/utils/"* ]]; then
        echo -e "${YELLOW}🔧 REMINDER: Service/utility modified - consider if development_rules.md needs updates${NC}"
        echo -e "${YELLOW}   File: $file${NC}"
    fi
}

# Main logic
if [[ -n "$file_path" ]]; then
    check_documentation_reminder "$file_path"
fi

# Check project status update frequency
if [[ -f "$WORKFLOW_DIR/project_status.md" ]]; then
    last_modified=$(stat -c %Y "$WORKFLOW_DIR/project_status.md" 2>/dev/null || echo 0)
    current_time=$(date +%s)
    hours_since_update=$(((current_time - last_modified) / 3600))
    
    if [ $hours_since_update -gt 2 ]; then
        echo -e "${YELLOW}⚠️  project_status.md hasn't been updated in $hours_since_update hours${NC}"
        echo -e "${YELLOW}   Consider updating the project dashboard${NC}"
    fi
fi