#!/bin/bash

# Pre-Edit Hook for Claude Code - STRICT RULE ENFORCEMENT
# Prevents rule violations BEFORE they happen

set -e

# Read JSON input from stdin
json_input=$(cat)

# Extract tool name and file path from JSON
tool_name=$(echo "$json_input" | jq -r '.tool // empty')
file_path=$(echo "$json_input" | jq -r '.params.file_path // .params.path // empty')

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
GREEN='\033[0;32m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo -e "${BOLD}${RED}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${RED}🛡️  CLAUDE ENFORCEMENT HOOK EXECUTING: PRE-EDIT VALIDATION${NC}"
echo -e "${BOLD}${RED}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${RED}Tool: $tool_name | Target: $(basename "$file_path")${NC}"
echo -e "${RED}CHECKING RULES COMPLIANCE BEFORE EDIT...${NC}"
echo ""

# STRICT ENFORCEMENT: Check for rule violations BEFORE editing
check_pre_edit_rules() {
    local file="$1"
    
    # Check if creating test files in wrong location
    if [[ "$file" == *"test_"* ]] && [[ "$file" != *"/tests/"* ]]; then
        echo -e "${RED}🚨 BLOCKED: Cannot create test file outside /tests/ directory!${NC}"
        echo -e "${RED}   Attempted file: $file${NC}"
        echo -e "${RED}   RULE VIOLATION: testing_rules.md requires all tests in /tests/ directory${NC}"
        echo -e "${YELLOW}   CORRECTIVE ACTION: Use proper path like tests/unit/ or tests/integration/${NC}"
        return 1
    fi
    
    # Check for duplicate test file creation (anti-consolidation)
    if [[ "$file" == *"/tests/"* ]] && [[ "$file" == *"component_service"* ]]; then
        echo -e "${YELLOW}⚠️  WARNING: ComponentService test file modification${NC}"
        echo -e "${YELLOW}   CONSOLIDATION RULE: Only ONE test file per service allowed${NC}"
        echo -e "${YELLOW}   Check: Are you adding to existing test_component_service.py?${NC}"
        echo -e "${YELLOW}   Or creating duplicate file violating testing_rules.md?${NC}"
    fi
    
    # Check for comment addition attempts
    if [[ "$file" == *.py ]] || [[ "$file" == *.js ]]; then
        echo -e "${RED}🚫 STRICT REMINDER: NO COMMENTS POLICY ACTIVE${NC}"
        echo -e "${RED}   Target file: $file${NC}"
        echo -e "${RED}   ABSOLUTE RULE: No comments, docstrings, or explanatory text${NC}"
        echo -e "${RED}   Use self-documenting code ONLY (development_rules.md)${NC}"
    fi
    
    return 0
}

# ENFORCE TODOWRITE USAGE
if [[ "$tool_name" == "Write" ]] || [[ "$tool_name" == "Edit" ]] || [[ "$tool_name" == "MultiEdit" ]]; then
    echo -e "${BLUE}📋 RULE REMINDER: Use TodoWrite tool for task management${NC}"
    echo -e "${BLUE}   REQUIREMENT: Track all development tasks in todo list${NC}"
fi

# Run pre-edit rule checks
if [[ -n "$file_path" ]]; then
    if ! check_pre_edit_rules "$file_path"; then
        echo -e "${RED}🛑 RULE VIOLATION DETECTED - EDIT BLOCKED${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${BOLD}${GREEN}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${GREEN}✅ PRE-EDIT HOOK COMPLETED - RULES VALIDATED - EDIT AUTHORIZED${NC}"
echo -e "${BOLD}${GREEN}════════════════════════════════════════════════════════════════════${NC}"
echo ""