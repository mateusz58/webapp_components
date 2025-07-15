#!/bin/bash

# Post-TodoWrite Hook for Claude Code - Intelligent Task Management Automation
# Automatically handles project status updates based on todo completion patterns

set -e

# Read JSON input from stdin
json_input=$(cat)

# Extract todo information from JSON
todos_json=$(echo "$json_input" | jq -r '.params.todos // empty' 2>/dev/null || echo "")

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

# Project paths
PROJECT_ROOT="/mnt/c/Users/Administrator/DataspellProjects/webapp_components"
DOCS_DIR="$PROJECT_ROOT/docs"

echo ""
echo -e "${BOLD}${BLUE}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${BLUE}🔧 CLAUDE AUTOMATION: INTELLIGENT TODO TRACKING SYSTEM${NC}"
echo -e "${BOLD}${BLUE}════════════════════════════════════════════════════════════════════${NC}"

# Function to analyze todo completion patterns
analyze_todo_completion() {
    if [[ -n "$todos_json" ]]; then
        # Count completed vs total todos
        local total_todos=$(echo "$todos_json" | jq '. | length' 2>/dev/null || echo "0")
        local completed_todos=$(echo "$todos_json" | jq '[.[] | select(.status == "completed")] | length' 2>/dev/null || echo "0")
        local in_progress_todos=$(echo "$todos_json" | jq '[.[] | select(.status == "in_progress")] | length' 2>/dev/null || echo "0")
        local high_priority_completed=$(echo "$todos_json" | jq '[.[] | select(.status == "completed" and .priority == "high")] | length' 2>/dev/null || echo "0")
        
        echo -e "${BLUE}📊 TODO ANALYSIS:${NC}"
        echo -e "${BLUE}   Total tasks: $total_todos${NC}"
        echo -e "${BLUE}   Completed: $completed_todos${NC}"
        echo -e "${BLUE}   In progress: $in_progress_todos${NC}"
        echo -e "${BLUE}   High priority completed: $high_priority_completed${NC}"
        
        # Intelligent automation triggers
        if [[ $completed_todos -gt 0 ]]; then
            echo -e "${GREEN}✅ TASK COMPLETION DETECTED - TRIGGERING AUTOMATION${NC}"
            
            # Auto-trigger project status update for significant completions
            if [[ $high_priority_completed -gt 0 ]] || [[ $completed_todos -ge 3 ]]; then
                echo -e "${YELLOW}🤖 AUTO-TRIGGERING: Project status update (significant task completion)${NC}"
                echo -e "${BLUE}   Reason: $high_priority_completed high-priority tasks or $completed_todos total tasks completed${NC}"
                
                # Run automatic project status update
                cd "$PROJECT_ROOT"
                if [[ -f ".claude/scripts/auto-project-update.sh" ]]; then
                    echo -e "${BLUE}🔄 Running automatic project status update...${NC}"
                    bash .claude/scripts/auto-project-update.sh 2>/dev/null || echo -e "${YELLOW}⚠️  Auto-update script encountered issues${NC}"
                fi
            fi
            
            # Check for testing-related completions
            local test_related=$(echo "$todos_json" | jq -r '[.[] | select(.status == "completed" and (.content | test("test|Test|TEST")))] | length' 2>/dev/null || echo "0")
            if [[ $test_related -gt 0 ]]; then
                echo -e "${GREEN}🧪 TEST-RELATED TASK COMPLETION DETECTED${NC}"
                echo -e "${YELLOW}📋 AUTOMATED REMINDER: Update test_reports.md with results${NC}"
                echo -e "${BLUE}   Command: '/project:update-test-report' for guided test documentation${NC}"
            fi
            
            # Check for component service related completions
            local component_service_related=$(echo "$todos_json" | jq -r '[.[] | select(.status == "completed" and (.content | test("component.*service|ComponentService")))] | length' 2>/dev/null || echo "0")
            if [[ $component_service_related -gt 0 ]]; then
                echo -e "${GREEN}⚙️  COMPONENT SERVICE TASK COMPLETION DETECTED${NC}"
                echo -e "${YELLOW}📋 AUTOMATED REMINDER: Update architecture_overview.md if service changes made${NC}"
            fi
            
        elif [[ $in_progress_todos -gt 0 ]]; then
            echo -e "${BLUE}🔄 ACTIVE DEVELOPMENT DETECTED${NC}"
            echo -e "${YELLOW}💡 TIP: Use TodoWrite frequently to track progress${NC}"
        fi
        
        # Progress completion percentage
        if [[ $total_todos -gt 0 ]]; then
            local completion_percentage=$(( (completed_todos * 100) / total_todos ))
            if [[ $completion_percentage -ge 80 ]]; then
                echo -e "${GREEN}🎯 HIGH COMPLETION RATE: $completion_percentage% tasks completed${NC}"
                echo -e "${GREEN}   Consider running '/project:update-project-status' to document milestone${NC}"
            elif [[ $completion_percentage -ge 50 ]]; then
                echo -e "${YELLOW}📈 GOOD PROGRESS: $completion_percentage% tasks completed${NC}"
            fi
        fi
    fi
}

# Function to provide intelligent recommendations
provide_intelligent_recommendations() {
    echo -e "${BOLD}${YELLOW}🤖 INTELLIGENT AUTOMATION RECOMMENDATIONS:${NC}"
    
    # Check last project status update
    if [[ -f "$DOCS_DIR/project_status.md" ]]; then
        local last_modified=$(stat -c %Y "$DOCS_DIR/project_status.md" 2>/dev/null || echo 0)
        local current_time=$(date +%s)
        local hours_since_update=$(((current_time - last_modified) / 3600))
        
        if [[ $hours_since_update -gt 2 ]]; then
            echo -e "${YELLOW}⏰ Project status last updated $hours_since_update hours ago${NC}"
            echo -e "${YELLOW}   AUTO-SUGGESTION: Consider running '/project:auto-project-update'${NC}"
        fi
    fi
    
    # Check for frequent TodoWrite usage (good practice)
    echo -e "${GREEN}✅ TodoWrite usage detected - excellent task management!${NC}"
    echo -e "${BLUE}💡 OPTIMIZATION TIP: Let automation handle project status updates${NC}"
    echo -e "${BLUE}   • High-priority completions → Auto-trigger project updates${NC}"
    echo -e "${BLUE}   • Test completions → Auto-remind for test documentation${NC}"
    echo -e "${BLUE}   • Service changes → Auto-suggest architecture docs update${NC}"
}

# Main execution
analyze_todo_completion
echo ""
provide_intelligent_recommendations

echo ""
echo -e "${BOLD}${BLUE}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${GREEN}✅ INTELLIGENT TODO TRACKING COMPLETED${NC}"
echo -e "${BOLD}${BLUE}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}💡 The system learns from your todo patterns to automate documentation${NC}"
echo ""