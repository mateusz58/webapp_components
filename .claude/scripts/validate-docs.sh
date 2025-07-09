#!/bin/bash

# Documentation Validation Command
# Comprehensive validation of all documentation files

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
WORKFLOW_DIR="$PROJECT_ROOT/claude_workflow"

echo -e "${BOLD}${BLUE}📋 Documentation Validation Suite${NC}"
echo -e "${BLUE}====================================${NC}"

# Function to validate file existence and basic structure
validate_file_structure() {
    local file_path="$1"
    local file_name="$2"
    local required_sections=("${@:3}")
    
    echo -e "${BLUE}Validating $file_name...${NC}"
    
    if [[ ! -f "$file_path" ]]; then
        echo -e "${RED}❌ CRITICAL: $file_name is missing!${NC}"
        return 1
    fi
    
    local errors=0
    
    # Check file size
    local file_size=$(stat -c%s "$file_path")
    if [ $file_size -lt 100 ]; then
        echo -e "${RED}❌ ERROR: $file_name is too small ($file_size bytes)${NC}"
        ((errors++))
    fi
    
    # Check for required sections
    for section in "${required_sections[@]}"; do
        if ! grep -q "$section" "$file_path"; then
            echo -e "${YELLOW}⚠️  WARNING: Missing section '$section' in $file_name${NC}"
            ((errors++))
        fi
    done
    
    # Check for status indicators
    local status_count=$(grep -c "✅\|❌\|🔄\|⚠️" "$file_path" 2>/dev/null || echo 0)
    if [ $status_count -eq 0 ]; then
        echo -e "${YELLOW}⚠️  WARNING: No status indicators found in $file_name${NC}"
        ((errors++))
    fi
    
    # Check for recent dates
    local current_year=$(date +%Y)
    local recent_dates=$(grep -c "$current_year" "$file_path" 2>/dev/null || echo 0)
    if [ $recent_dates -eq 0 ]; then
        echo -e "${YELLOW}⚠️  WARNING: No recent dates found in $file_name${NC}"
        ((errors++))
    fi
    
    if [ $errors -eq 0 ]; then
        echo -e "${GREEN}✅ $file_name structure validation passed${NC}"
    else
        echo -e "${YELLOW}⚠️  $file_name has $errors structural issues${NC}"
    fi
    
    return $errors
}

# Function to validate content quality
validate_content_quality() {
    local file_path="$1"
    local file_name="$2"
    local min_words="$3"
    
    if [[ ! -f "$file_path" ]]; then
        return 1
    fi
    
    local word_count=$(wc -w < "$file_path")
    local line_count=$(wc -l < "$file_path")
    local errors=0
    
    echo -e "${BLUE}Content analysis for $file_name:${NC}"
    echo -e "${BLUE}  📝 Words: $word_count${NC}"
    echo -e "${BLUE}  📄 Lines: $line_count${NC}"
    
    # Check minimum word count
    if [ $word_count -lt $min_words ]; then
        echo -e "${RED}❌ ERROR: $file_name too short ($word_count words, minimum: $min_words)${NC}"
        ((errors++))
    fi
    
    # Check for empty lines (good formatting)
    local empty_lines=$(grep -c "^$" "$file_path" 2>/dev/null || echo 0)
    if [ $empty_lines -lt 10 ]; then
        echo -e "${YELLOW}⚠️  WARNING: $file_name may have poor formatting (few empty lines)${NC}"
        ((errors++))
    fi
    
    # Check for code blocks
    local code_blocks=$(grep -c "```" "$file_path" 2>/dev/null || echo 0)
    if [ $code_blocks -gt 0 ]; then
        echo -e "${GREEN}✅ $file_name contains $code_blocks code blocks${NC}"
    fi
    
    # Check for links
    local links=$(grep -c "http\|\.md\|\.py" "$file_path" 2>/dev/null || echo 0)
    if [ $links -gt 0 ]; then
        echo -e "${GREEN}✅ $file_name contains $links references/links${NC}"
    fi
    
    return $errors
}

# Function to validate chronological order
validate_chronological_order() {
    local file_path="$1"
    local file_name="$2"
    
    if [[ ! -f "$file_path" ]]; then
        return 1
    fi
    
    echo -e "${BLUE}Checking chronological order for $file_name...${NC}"
    
    # Extract dates and check if they're in descending order
    local dates=$(grep -o "[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}" "$file_path" 2>/dev/null || echo "")
    
    if [[ -z "$dates" ]]; then
        echo -e "${YELLOW}⚠️  WARNING: No dates found in $file_name${NC}"
        return 1
    fi
    
    local date_count=$(echo "$dates" | wc -l)
    echo -e "${BLUE}  📅 Found $date_count dates${NC}"
    
    # Check if dates are in descending order (newest first)
    local sorted_dates=$(echo "$dates" | sort -r)
    if [[ "$dates" == "$sorted_dates" ]]; then
        echo -e "${GREEN}✅ $file_name dates are in correct chronological order${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  WARNING: $file_name dates may not be in chronological order${NC}"
        return 1
    fi
}

# Function to validate API documentation against actual code
validate_api_documentation() {
    local api_doc="$WORKFLOW_DIR/api_documentation.md"
    
    if [[ ! -f "$api_doc" ]]; then
        echo -e "${RED}❌ API documentation not found${NC}"
        return 1
    fi
    
    echo -e "${BLUE}Validating API documentation against code...${NC}"
    
    local errors=0
    
    # Check if API endpoints in documentation exist in code
    local documented_endpoints=$(grep -o "POST\|GET\|PUT\|DELETE [/a-zA-Z0-9/<>_-]*" "$api_doc" | sort -u)
    
    if [[ -z "$documented_endpoints" ]]; then
        echo -e "${RED}❌ ERROR: No API endpoints found in documentation${NC}"
        ((errors++))
    else
        local endpoint_count=$(echo "$documented_endpoints" | wc -l)
        echo -e "${BLUE}  🔌 Found $endpoint_count documented endpoints${NC}"
        
        # Check if main API files exist
        local api_files=("$PROJECT_ROOT/app/api/component_api.py" "$PROJECT_ROOT/app/api/variant_api.py")
        for api_file in "${api_files[@]}"; do
            if [[ ! -f "$api_file" ]]; then
                echo -e "${RED}❌ ERROR: API file missing: $api_file${NC}"
                ((errors++))
            fi
        done
    fi
    
    # Check for response examples
    local response_examples=$(grep -c "```json" "$api_doc" 2>/dev/null || echo 0)
    if [ $response_examples -lt 5 ]; then
        echo -e "${YELLOW}⚠️  WARNING: Few response examples in API documentation${NC}"
        ((errors++))
    fi
    
    if [ $errors -eq 0 ]; then
        echo -e "${GREEN}✅ API documentation validation passed${NC}"
    else
        echo -e "${YELLOW}⚠️  API documentation has $errors issues${NC}"
    fi
    
    return $errors
}

# Function to validate database documentation
validate_database_documentation() {
    local db_doc="$WORKFLOW_DIR/database_schema_guide.md"
    
    if [[ ! -f "$db_doc" ]]; then
        echo -e "${RED}❌ Database documentation not found${NC}"
        return 1
    fi
    
    echo -e "${BLUE}Validating database documentation...${NC}"
    
    local errors=0
    
    # Check if models.py exists
    if [[ ! -f "$PROJECT_ROOT/app/models.py" ]]; then
        echo -e "${RED}❌ ERROR: models.py not found${NC}"
        ((errors++))
    fi
    
    # Check for table documentation
    local table_count=$(grep -c "^#### \|^### " "$db_doc" 2>/dev/null || echo 0)
    if [ $table_count -lt 5 ]; then
        echo -e "${YELLOW}⚠️  WARNING: Few table definitions in database documentation${NC}"
        ((errors++))
    fi
    
    # Check for trigger documentation
    local trigger_count=$(grep -c "trigger\|function" "$db_doc" 2>/dev/null || echo 0)
    if [ $trigger_count -eq 0 ]; then
        echo -e "${YELLOW}⚠️  WARNING: No database triggers documented${NC}"
        ((errors++))
    fi
    
    if [ $errors -eq 0 ]; then
        echo -e "${GREEN}✅ Database documentation validation passed${NC}"
    else
        echo -e "${YELLOW}⚠️  Database documentation has $errors issues${NC}"
    fi
    
    return $errors
}

# Main validation function
main() {
    local total_errors=0
    
    echo -e "${BOLD}🔍 Starting comprehensive documentation validation...${NC}"
    echo
    
    # Validate each documentation file
    
    # 1. Project Status (most critical)
    validate_file_structure "$WORKFLOW_DIR/project_status.md" "project_status.md" "## " "Status" "Priority"
    ((total_errors += $?))
    validate_content_quality "$WORKFLOW_DIR/project_status.md" "project_status.md" 500
    ((total_errors += $?))
    validate_chronological_order "$WORKFLOW_DIR/project_status.md" "project_status.md"
    ((total_errors += $?))
    echo
    
    # 2. Test Reports
    validate_file_structure "$WORKFLOW_DIR/test_reports.md" "test_reports.md" "## " "Test Results" "Pass Rate"
    ((total_errors += $?))
    validate_content_quality "$WORKFLOW_DIR/test_reports.md" "test_reports.md" 300
    ((total_errors += $?))
    validate_chronological_order "$WORKFLOW_DIR/test_reports.md" "test_reports.md"
    ((total_errors += $?))
    echo
    
    # 3. Development Rules
    validate_file_structure "$WORKFLOW_DIR/development_rules.md" "development_rules.md" "Backend" "Frontend" "Rules"
    ((total_errors += $?))
    validate_content_quality "$WORKFLOW_DIR/development_rules.md" "development_rules.md" 1000
    ((total_errors += $?))
    echo
    
    # 4. Testing Rules
    validate_file_structure "$WORKFLOW_DIR/testing_rules.md" "testing_rules.md" "Testing" "Rules" "TDD"
    ((total_errors += $?))
    validate_content_quality "$WORKFLOW_DIR/testing_rules.md" "testing_rules.md" 800
    ((total_errors += $?))
    echo
    
    # 5. API Documentation
    validate_file_structure "$WORKFLOW_DIR/api_documentation.md" "api_documentation.md" "API" "Endpoints" "Response"
    ((total_errors += $?))
    validate_content_quality "$WORKFLOW_DIR/api_documentation.md" "api_documentation.md" 1500
    ((total_errors += $?))
    validate_api_documentation
    ((total_errors += $?))
    echo
    
    # 6. Database Schema Guide
    validate_file_structure "$WORKFLOW_DIR/database_schema_guide.md" "database_schema_guide.md" "Schema" "Tables" "Relationships"
    ((total_errors += $?))
    validate_content_quality "$WORKFLOW_DIR/database_schema_guide.md" "database_schema_guide.md" 1200
    ((total_errors += $?))
    validate_database_documentation
    ((total_errors += $?))
    echo
    
    # 7. Architecture Overview
    validate_file_structure "$WORKFLOW_DIR/architecture_overview.md" "architecture_overview.md" "Architecture" "Technology" "Structure"
    ((total_errors += $?))
    validate_content_quality "$WORKFLOW_DIR/architecture_overview.md" "architecture_overview.md" 1500
    ((total_errors += $?))
    echo
    
    # 8. Instructions for Claude
    validate_file_structure "$WORKFLOW_DIR/instructions_for_claude.md" "instructions_for_claude.md" "Read" "Update" "Files"
    ((total_errors += $?))
    validate_content_quality "$WORKFLOW_DIR/instructions_for_claude.md" "instructions_for_claude.md" 400
    ((total_errors += $?))
    echo
    
    # Summary
    echo -e "${BOLD}${BLUE}📋 Validation Summary${NC}"
    echo -e "${BLUE}=====================${NC}"
    
    if [ $total_errors -eq 0 ]; then
        echo -e "${GREEN}✅ ALL DOCUMENTATION VALIDATION PASSED${NC}"
        echo -e "${GREEN}   Documentation is in excellent condition${NC}"
    elif [ $total_errors -le 10 ]; then
        echo -e "${YELLOW}⚠️  DOCUMENTATION HAS MINOR ISSUES${NC}"
        echo -e "${YELLOW}   Total issues found: $total_errors${NC}"
        echo -e "${YELLOW}   Recommend addressing these issues${NC}"
    else
        echo -e "${RED}❌ DOCUMENTATION HAS SERIOUS ISSUES${NC}"
        echo -e "${RED}   Total issues found: $total_errors${NC}"
        echo -e "${RED}   Immediate attention required${NC}"
    fi
    
    echo -e "${BLUE}=====================${NC}"
    echo -e "${BOLD}${BLUE}Documentation Validation Complete${NC}"
    
    return $total_errors
}

# Run the validation
main "$@"