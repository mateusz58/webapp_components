#!/bin/bash

# Update Project Status Command
# Guided update of project_status.md with proper formatting

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
STATUS_FILE="$WORKFLOW_DIR/project_status.md"

echo -e "${BOLD}${BLUE}📊 Update Project Status Dashboard${NC}"
echo -e "${BLUE}====================================${NC}"

# Function to add a new status entry
add_status_entry() {
    local title="$1"
    local description="$2"
    local status="$3"
    local priority="$4"
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    
    # Prepare the entry
    local entry="## 🚨 $timestamp - $title\n"
    entry+="**Status**: $status  \n"
    entry+="**Priority**: $priority  \n"
    entry+="**Impact**: $description\n\n"
    
    # Add to the beginning of the file (after the header)
    if [[ -f "$STATUS_FILE" ]]; then
        # Create a temporary file with the new entry
        local temp_file=$(mktemp)
        
        # Get the header (first few lines until the first "##")
        awk '/^## / && NR > 10 { exit } { print }' "$STATUS_FILE" > "$temp_file"
        
        # Add the new entry
        echo -e "$entry" >> "$temp_file"
        
        # Add a separator
        echo "---" >> "$temp_file"
        echo "" >> "$temp_file"
        
        # Add the rest of the file (skip the header)
        awk '/^## / && NR > 10 { found=1 } found { print }' "$STATUS_FILE" >> "$temp_file"
        
        # Replace the original file
        mv "$temp_file" "$STATUS_FILE"
    else
        echo -e "${RED}❌ project_status.md not found!${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✅ Status entry added successfully${NC}"
}

# Function to mark a task as completed
mark_task_completed() {
    local task_pattern="$1"
    local completion_note="$2"
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    
    # Search for the task and mark it as completed
    if [[ -f "$STATUS_FILE" ]]; then
        sed -i "s/🔄 PENDING/✅ COMPLETED/g; s/❌ BLOCKED/✅ COMPLETED/g" "$STATUS_FILE"
        
        # Add completion note
        local completion_entry="## ✅ $timestamp - TASK COMPLETED\n"
        completion_entry+="**Task**: $task_pattern\n"
        completion_entry+="**Completion Note**: $completion_note\n\n"
        
        # Add to the beginning of the file
        local temp_file=$(mktemp)
        awk '/^## / && NR > 10 { exit } { print }' "$STATUS_FILE" > "$temp_file"
        echo -e "$completion_entry" >> "$temp_file"
        echo "---" >> "$temp_file"
        echo "" >> "$temp_file"
        awk '/^## / && NR > 10 { found=1 } found { print }' "$STATUS_FILE" >> "$temp_file"
        mv "$temp_file" "$STATUS_FILE"
        
        echo -e "${GREEN}✅ Task marked as completed${NC}"
    else
        echo -e "${RED}❌ project_status.md not found!${NC}"
        return 1
    fi
}

# Function to add a new active task
add_active_task() {
    local task_title="$1"
    local task_description="$2"
    local priority="$3"
    local estimated_time="$4"
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    
    local task_entry="## 🔄 $timestamp - $task_title\n"
    task_entry+="**Status**: 🔄 IN PROGRESS  \n"
    task_entry+="**Priority**: $priority  \n"
    task_entry+="**Estimated Time**: $estimated_time  \n"
    task_entry+="**Description**: $task_description\n\n"
    
    # Add to the beginning of the file
    if [[ -f "$STATUS_FILE" ]]; then
        local temp_file=$(mktemp)
        awk '/^## / && NR > 10 { exit } { print }' "$STATUS_FILE" > "$temp_file"
        echo -e "$task_entry" >> "$temp_file"
        echo "---" >> "$temp_file"
        echo "" >> "$temp_file"
        awk '/^## / && NR > 10 { found=1 } found { print }' "$STATUS_FILE" >> "$temp_file"
        mv "$temp_file" "$STATUS_FILE"
        
        echo -e "${GREEN}✅ Active task added successfully${NC}"
    else
        echo -e "${RED}❌ project_status.md not found!${NC}"
        return 1
    fi
}

# Interactive menu
show_menu() {
    echo -e "${BOLD}Choose an action:${NC}"
    echo -e "${BLUE}1.${NC} Add new status update"
    echo -e "${BLUE}2.${NC} Mark task as completed"
    echo -e "${BLUE}3.${NC} Add new active task"
    echo -e "${BLUE}4.${NC} View current status"
    echo -e "${BLUE}5.${NC} Exit"
    echo -n "Enter your choice [1-5]: "
}

# Function to view current status
view_current_status() {
    if [[ -f "$STATUS_FILE" ]]; then
        echo -e "${BOLD}${BLUE}Current Project Status (last 10 entries):${NC}"
        head -50 "$STATUS_FILE"
    else
        echo -e "${RED}❌ project_status.md not found!${NC}"
    fi
}

# Main interactive loop
main() {
    while true; do
        show_menu
        read -r choice
        
        case $choice in
            1)
                echo -e "${BLUE}Adding new status update:${NC}"
                echo -n "Enter title: "
                read -r title
                echo -n "Enter description: "
                read -r description
                echo -n "Enter status (✅ COMPLETE/🔄 IN PROGRESS/❌ BLOCKED): "
                read -r status
                echo -n "Enter priority (HIGH/MEDIUM/LOW): "
                read -r priority
                
                add_status_entry "$title" "$description" "$status" "$priority"
                ;;
            2)
                echo -e "${BLUE}Marking task as completed:${NC}"
                echo -n "Enter task pattern to search for: "
                read -r task_pattern
                echo -n "Enter completion note: "
                read -r completion_note
                
                mark_task_completed "$task_pattern" "$completion_note"
                ;;
            3)
                echo -e "${BLUE}Adding new active task:${NC}"
                echo -n "Enter task title: "
                read -r task_title
                echo -n "Enter task description: "
                read -r task_description
                echo -n "Enter priority (HIGH/MEDIUM/LOW): "
                read -r priority
                echo -n "Enter estimated time: "
                read -r estimated_time
                
                add_active_task "$task_title" "$task_description" "$priority" "$estimated_time"
                ;;
            4)
                view_current_status
                ;;
            5)
                echo -e "${GREEN}✅ Project status update completed${NC}"
                break
                ;;
            *)
                echo -e "${RED}❌ Invalid choice. Please try again.${NC}"
                ;;
        esac
        
        echo
        echo -e "${YELLOW}Press Enter to continue...${NC}"
        read -r
        clear
    done
}

# Check if status file exists
if [[ ! -f "$STATUS_FILE" ]]; then
    echo -e "${RED}❌ project_status.md not found at $STATUS_FILE${NC}"
    echo -e "${YELLOW}Please ensure the file exists before running this command${NC}"
    exit 1
fi

# Start the interactive process
main