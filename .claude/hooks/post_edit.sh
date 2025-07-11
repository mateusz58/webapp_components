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
DOCS_DIR="$PROJECT_ROOT/docs"

echo ""
echo -e "${BOLD}${BLUE}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${BLUE}🔧 CLAUDE ENFORCEMENT HOOK EXECUTING: POST-EDIT VALIDATION${NC}"
echo -e "${BOLD}${BLUE}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Tool: $tool_name | File: $(basename "$file_path")${NC}"
echo ""

# Function to check documentation reminders based on file type
check_documentation_reminder() {
    local file="$1"
    local RED='\033[0;31m'
    local GREEN='\033[0;32m'
    
    # API file modifications
    if [[ "$file" == *"/api/"* ]] && [[ "$file" == *.py ]]; then
        echo -e "${RED}📝 CRITICAL: API file modified - MUST update api_documentation.md${NC}"
        echo -e "${YELLOW}   File: $file${NC}"
        echo -e "${BLUE}   Command: Use '/project:doc-status' to check documentation health${NC}"
    fi
    
    # Database model modifications
    if [[ "$file" == *"models.py"* ]] || [[ "$file" == *"migration"* ]]; then
        echo -e "${RED}🗄️  CRITICAL: Database file modified - MUST update database_schema_guide.md${NC}"
        echo -e "${YELLOW}   File: $file${NC}"
        echo -e "${BLUE}   Action: Document any new columns, tables, or relationships${NC}"
    fi
    
    # Test file modifications
    if [[ "$file" == *"test_"* ]] || [[ "$file" == *"/tests/"* ]]; then
        echo -e "${YELLOW}🧪 REMINDER: Test file modified - remember to update test_reports.md after running tests${NC}"
        echo -e "${YELLOW}   File: $file${NC}"
        echo -e "${RED}   WARNING: Tests in root directory violate testing_rules.md!${NC}" if [[ "$file" != *"/tests/"* ]]
    fi
    
    # Service/utility modifications
    if [[ "$file" == *"/services/"* ]] || [[ "$file" == *"/utils/"* ]]; then
        echo -e "${YELLOW}🔧 REMINDER: Service/utility modified - check if architecture_overview.md needs updates${NC}"
        echo -e "${YELLOW}   File: $file${NC}"
        echo -e "${BLUE}   Consider: New services, changed interfaces, or architectural patterns${NC}"
    fi
    
    # Component service specific checks
    if [[ "$file" == *"component_service.py"* ]]; then
        echo -e "${RED}🚨 CRITICAL: ComponentService modified - Check these documents:${NC}"
        echo -e "${YELLOW}   1. architecture_overview.md - Update service layer description${NC}"
        echo -e "${YELLOW}   2. api_documentation.md - Update affected endpoints${NC}"
        echo -e "${YELLOW}   3. database_schema_guide.md - Update if DB operations changed${NC}"
        echo -e "${BLUE}   Command: '/project:doc-status' for comprehensive check${NC}"
    fi
    
    # WebDAV related changes
    if [[ "$file" == *"webdav"* ]] || [[ "$file" == *"picture"* ]]; then
        echo -e "${YELLOW}📸 REMINDER: Picture/WebDAV functionality modified${NC}"
        echo -e "${YELLOW}   Update architecture_overview.md section on File Management & WebDAV${NC}"
    fi
}

# Main logic
if [[ -n "$file_path" ]]; then
    check_documentation_reminder "$file_path"
fi

# STRICT ENFORCEMENT: Testing Rules Compliance
check_testing_rules_compliance() {
    local file="$1"
    
    # Test file organization enforcement
    if [[ "$file" == *"test_"* ]]; then
        # Check if test is in proper directory structure
        if [[ "$file" != *"/tests/"* ]]; then
            echo -e "${RED}🚨 CRITICAL VIOLATION: Test file outside /tests/ directory!${NC}"
            echo -e "${RED}   File: $file${NC}"
            echo -e "${RED}   RULE: All test files must be in tests/ directory (testing_rules.md)${NC}"
            echo -e "${YELLOW}   ACTION REQUIRED: Move this file to proper tests/ subdirectory${NC}"
        fi
        
        # Check for test file consolidation compliance
        local service_name=""
        if [[ "$file" == *"component_service"* ]]; then
            service_name="ComponentService"
        elif [[ "$file" == *"webdav"* ]]; then
            service_name="WebDAV"
        fi
        
        if [[ -n "$service_name" ]]; then
            echo -e "${YELLOW}📋 TEST CONSOLIDATION CHECK: $service_name test file modified${NC}"
            echo -e "${YELLOW}   RULE: One test file per service (testing_rules.md)${NC}"
            echo -e "${YELLOW}   VERIFY: Ensure all $service_name tests are in single consolidated file${NC}"
        fi
    fi
    
    # No comments policy enforcement
    if [[ "$file" == *.py ]] || [[ "$file" == *.js ]]; then
        echo -e "${RED}🚫 REMINDER: NO COMMENTS POLICY ACTIVE${NC}"
        echo -e "${RED}   File: $file${NC}"
        echo -e "${RED}   RULE: Self-documenting code only, no comments/docstrings (development_rules.md)${NC}"
    fi
}

# Check project status update frequency with STRICT enforcement
if [[ -f "$DOCS_DIR/project_status.md" ]]; then
    last_modified=$(stat -c %Y "$DOCS_DIR/project_status.md" 2>/dev/null || echo 0)
    current_time=$(date +%s)
    hours_since_update=$(((current_time - last_modified) / 3600))
    
    if [ $hours_since_update -gt 1 ]; then
        echo -e "${RED}🚨 CRITICAL: project_status.md hasn't been updated in $hours_since_update hours${NC}"
        echo -e "${RED}   ENFORCEMENT RULE: Update required within 1 hour of significant changes${NC}"
        echo -e "${YELLOW}   IMMEDIATE ACTION: Use '/project:update-project-status' command${NC}"
        echo -e "${RED}   This violates project documentation standards!${NC}"
    fi
fi

# ENFORCE testing rules compliance
if [[ -n "$file_path" ]]; then
    check_testing_rules_compliance "$file_path"
fi

# Final enforcement summary
echo ""
echo -e "${BOLD}${BLUE}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${GREEN}✅ POST-EDIT HOOK COMPLETED - CLAUDE ENFORCEMENT ACTIVE${NC}"
echo -e "${BOLD}${BLUE}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}💡 TIP: Run '/project:doc-status' regularly to ensure documentation is current${NC}"
echo ""