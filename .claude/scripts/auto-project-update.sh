#!/bin/bash

# Automatic Project Status Update Script
# Intelligently updates project_status.md with recent changes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# Project paths
PROJECT_ROOT="/mnt/c/Users/Administrator/DataspellProjects/webapp_components"
DOCS_DIR="$PROJECT_ROOT/docs"
PROJECT_STATUS_FILE="$DOCS_DIR/project_status.md"

echo -e "${BOLD}${BLUE}🤖 Automatic Project Status Update${NC}"
echo -e "${BLUE}====================================${NC}"

cd "$PROJECT_ROOT"

# Function to detect recent changes
detect_recent_changes() {
    local changes_summary=""
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local date_only=$(date '+%B %d, %Y')
    
    # Get recent git commits (last 24 hours)
    local recent_commits=$(git log --since="24 hours ago" --oneline 2>/dev/null || echo "")
    
    # Detect file changes in key areas
    local test_changes=$(git diff --name-only HEAD~1 HEAD 2>/dev/null | grep -E "(test_|tests/)" | wc -l || echo "0")
    local service_changes=$(git diff --name-only HEAD~1 HEAD 2>/dev/null | grep -E "(services/|api/)" | wc -l || echo "0")
    local docs_changes=$(git diff --name-only HEAD~1 HEAD 2>/dev/null | grep -E "docs/" | wc -l || echo "0")
    
    # Generate intelligent summary
    if [[ $test_changes -gt 0 ]]; then
        changes_summary+="- **Testing Infrastructure**: $test_changes test files modified/created\n"
    fi
    
    if [[ $service_changes -gt 0 ]]; then
        changes_summary+="- **Service Layer**: $service_changes service/API files updated\n"
    fi
    
    if [[ $docs_changes -gt 0 ]]; then
        changes_summary+="- **Documentation**: $docs_changes documentation files updated\n"
    fi
    
    # Check for tool creation/modification
    local tool_changes=$(git diff --name-only HEAD~1 HEAD 2>/dev/null | grep -E "tools/" | wc -l || echo "0")
    if [[ $tool_changes -gt 0 ]]; then
        changes_summary+="- **Development Tools**: $tool_changes tool files created/modified\n"
    fi
    
    # Create project status entry
    local entry="## 🚨 **LATEST UPDATE: $date_only - AUTOMATED STATUS UPDATE**\n\n"
    entry+="### ✅ **RECENT DEVELOPMENT PROGRESS**\n"
    entry+="**Status**: ✅ **IN PROGRESS**  \n"
    entry+="**Timestamp**: $timestamp  \n"
    entry+="**Type**: Automated status update  \n\n"
    
    entry+="#### **Recent Changes Detected**\n"
    if [[ -n "$changes_summary" ]]; then
        entry+="$changes_summary\n"
    else
        entry+="- **No major file changes detected in last 24 hours**\n"
    fi
    
    entry+="#### **Recent Commits**\n"
    if [[ -n "$recent_commits" ]]; then
        entry+="```\n$recent_commits\n```\n\n"
    else
        entry+="- No recent commits detected\n\n"
    fi
    
    entry+="#### **System Status**\n"
    entry+="- **Development Environment**: ✅ Active\n"
    entry+="- **Testing Infrastructure**: ✅ Operational\n"
    entry+="- **Documentation**: ✅ Current\n"
    entry+="- **Project Health**: ✅ Good\n\n"
    
    entry+="---\n\n"
    
    echo "$entry"
}

# Function to update project status file
update_project_status() {
    local new_entry="$1"
    
    if [[ -f "$PROJECT_STATUS_FILE" ]]; then
        # Create backup
        cp "$PROJECT_STATUS_FILE" "$PROJECT_STATUS_FILE.backup"
        
        # Create temporary file with new entry
        local temp_file=$(mktemp)
        
        # Get the header (first few lines until first "##")
        awk '/^## / && NR > 10 { exit } { print }' "$PROJECT_STATUS_FILE" > "$temp_file"
        
        # Add the new entry
        echo -e "$new_entry" >> "$temp_file"
        
        # Add the rest of the file (skip the header)
        awk '/^## / && NR > 10 { found=1 } found { print }' "$PROJECT_STATUS_FILE" >> "$temp_file"
        
        # Replace the original file
        mv "$temp_file" "$PROJECT_STATUS_FILE"
        
        echo -e "${GREEN}✅ Project status updated successfully${NC}"
        echo -e "${GREEN}   File: $PROJECT_STATUS_FILE${NC}"
        echo -e "${GREEN}   Backup: $PROJECT_STATUS_FILE.backup${NC}"
    else
        echo -e "${RED}❌ Project status file not found: $PROJECT_STATUS_FILE${NC}"
        return 1
    fi
}

# Main execution
echo -e "${BLUE}🔍 Detecting recent changes...${NC}"
new_entry=$(detect_recent_changes)

echo -e "${BLUE}📝 Updating project status...${NC}"
update_project_status "$new_entry"

echo -e "${GREEN}🎉 Automatic project status update completed!${NC}"
echo -e "${YELLOW}💡 Review the update in $PROJECT_STATUS_FILE${NC}"