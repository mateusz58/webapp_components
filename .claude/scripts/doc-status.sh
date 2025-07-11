#!/bin/bash

# Documentation Status Command
# Check the health and compliance of all documentation files

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

echo -e "${BOLD}${BLUE}📊 Documentation Status Report${NC}"
echo -e "${BLUE}======================================${NC}"

# Function to check file status
check_file_status() {
    local file_path="$1"
    local file_name="$2"
    local max_age_hours="$3"
    
    if [[ ! -f "$file_path" ]]; then
        echo -e "${RED}❌ $file_name: MISSING${NC}"
        return 1
    fi
    
    local last_modified=$(stat -c %Y "$file_path" 2>/dev/null || echo 0)
    local current_time=$(date +%s)
    local hours_since_update=$(((current_time - last_modified) / 3600))
    local last_modified_date=$(date -d "@$last_modified" "+%Y-%m-%d %H:%M")
    
    if [ $hours_since_update -le $max_age_hours ]; then
        echo -e "${GREEN}✅ $file_name: CURRENT (updated $last_modified_date)${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  $file_name: OUTDATED (updated $last_modified_date, $hours_since_update hours ago)${NC}"
        return 1
    fi
}

# Function to check content quality
check_content_quality() {
    local file_path="$1"
    local file_name="$2"
    
    if [[ ! -f "$file_path" ]]; then
        return 1
    fi
    
    local line_count=$(wc -l < "$file_path")
    local word_count=$(wc -w < "$file_path")
    
    echo -e "${BLUE}   📝 Content: $line_count lines, $word_count words${NC}"
    
    # Check for status indicators
    local status_indicators=$(grep -c "✅\|❌\|🔄\|⚠️" "$file_path" 2>/dev/null || echo 0)
    if [ $status_indicators -gt 0 ]; then
        echo -e "${BLUE}   📊 Status indicators: $status_indicators found${NC}"
    fi
    
    # Check for recent dates
    local current_year=$(date +%Y)
    local recent_dates=$(grep -c "$current_year" "$file_path" 2>/dev/null || echo 0)
    if [ $recent_dates -gt 0 ]; then
        echo -e "${BLUE}   📅 Recent dates: $recent_dates entries from $current_year${NC}"
    fi
}

# Check core documentation files
echo -e "${BOLD}Core Documentation Files:${NC}"

# Project Status (should be updated frequently)
check_file_status "$DOCS_DIR/project_status.md" "project_status.md" 4
check_content_quality "$DOCS_DIR/project_status.md" "project_status.md"
echo

# Test Reports (should be updated after test runs)
check_file_status "$DOCS_DIR/test_reports.md" "test_reports.md" 24
check_content_quality "$DOCS_DIR/test_reports.md" "test_reports.md"
echo

# Development Rules (updated less frequently)
check_file_status "$DOCS_DIR/development_rules.md" "development_rules.md" 168  # 1 week
check_content_quality "$DOCS_DIR/development_rules.md" "development_rules.md"
echo

# Testing Rules (updated less frequently)
check_file_status "$DOCS_DIR/testing_rules.md" "testing_rules.md" 168  # 1 week
check_content_quality "$DOCS_DIR/testing_rules.md" "testing_rules.md"
echo

# API Documentation (should be current with API changes)
check_file_status "$DOCS_DIR/api_documentation.md" "api_documentation.md" 72  # 3 days
check_content_quality "$DOCS_DIR/api_documentation.md" "api_documentation.md"
echo

# Database Schema Guide (updated with schema changes)
check_file_status "$DOCS_DIR/database_schema_guide.md" "database_schema_guide.md" 168  # 1 week
check_content_quality "$DOCS_DIR/database_schema_guide.md" "database_schema_guide.md"
echo

# Architecture Overview (updated with major changes)
check_file_status "$DOCS_DIR/architecture_overview.md" "architecture_overview.md" 336  # 2 weeks
check_content_quality "$DOCS_DIR/architecture_overview.md" "architecture_overview.md"
echo

# Instructions for Claude (should be stable)
check_file_status "$DOCS_DIR/instructions_for_claude.md" "instructions_for_claude.md" 720  # 1 month
check_content_quality "$DOCS_DIR/instructions_for_claude.md" "instructions_for_claude.md"
echo

# Overall compliance check
echo -e "${BOLD}${BLUE}Overall Compliance Summary:${NC}"

# Check if project_status.md has been updated today
status_file="$DOCS_DIR/project_status.md"
if [[ -f "$status_file" ]]; then
    last_modified=$(stat -c %Y "$status_file" 2>/dev/null || echo 0)
    current_time=$(date +%s)
    hours_since_update=$(((current_time - last_modified) / 3600))
    
    if [ $hours_since_update -le 8 ]; then
        echo -e "${GREEN}✅ Project status tracking: ACTIVE${NC}"
    else
        echo -e "${YELLOW}⚠️  Project status tracking: INACTIVE (update needed)${NC}"
    fi
else
    echo -e "${RED}❌ Project status tracking: MISSING${NC}"
fi

# Check test coverage
if [[ -f "$DOCS_DIR/test_reports.md" ]]; then
    coverage_info=$(grep -i "coverage" "$DOCS_DIR/test_reports.md" | tail -1 || echo "")
    if [[ -n "$coverage_info" ]]; then
        echo -e "${BLUE}📊 Latest test coverage info: $coverage_info${NC}"
    fi
fi

# Recommendations
echo -e "${BOLD}${BLUE}Recommendations:${NC}"

# Check which files need immediate attention
if [[ ! -f "$DOCS_DIR/project_status.md" ]] || [[ $((($(date +%s) - $(stat -c %Y "$DOCS_DIR/project_status.md" 2>/dev/null || echo 0)) / 3600)) -gt 4 ]]; then
    echo -e "${YELLOW}📝 Update project_status.md with current task progress${NC}"
fi

if [[ ! -f "$DOCS_DIR/test_reports.md" ]] || [[ $((($(date +%s) - $(stat -c %Y "$DOCS_DIR/test_reports.md" 2>/dev/null || echo 0)) / 3600)) -gt 24 ]]; then
    echo -e "${YELLOW}🧪 Run tests and update test_reports.md${NC}"
fi

# Check for API files that might need documentation updates
api_files_modified=$(find "$PROJECT_ROOT/app/api" -name "*.py" -mtime -1 2>/dev/null | wc -l)
if [ $api_files_modified -gt 0 ]; then
    echo -e "${YELLOW}🔌 $api_files_modified API files modified recently - consider updating api_documentation.md${NC}"
fi

echo -e "${BLUE}======================================${NC}"
echo -e "${BOLD}${BLUE}Documentation Status Check Complete${NC}"