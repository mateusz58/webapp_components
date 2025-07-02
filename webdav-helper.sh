#!/bin/bash

# WebDAV Mount Management Helper Script
# Provides easy commands for managing the WebDAV mount

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

MOUNT_POINT="/components"
PID_FILE="/var/run/mount.davfs/components.pid"

show_usage() {
    echo -e "${BLUE}WebDAV Mount Management Helper${NC}"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  status    - Show current mount status"
    echo "  mount     - Mount WebDAV (runs full setup script)"
    echo "  unmount   - Unmount WebDAV"
    echo "  cleanup   - Clean up stale mounts and processes"
    echo "  test      - Test WebDAV connectivity"
    echo "  restart   - Unmount and remount"
    echo "  logs      - Show davfs2 logs"
    echo "  help      - Show this help message"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}This command requires root privileges. Use: sudo $0 $1${NC}"
        exit 1
    fi
}

show_status() {
    echo -e "${BLUE}=== WebDAV Mount Status ===${NC}"
    
    # Check if mounted
    if mountpoint -q "$MOUNT_POINT" 2>/dev/null; then
        echo -e "${GREEN}✓ WebDAV is mounted at $MOUNT_POINT${NC}"
        
        # Show mount details
        echo -e "${YELLOW}Mount details:${NC}"
        mount | grep "$MOUNT_POINT"
        
        # Test accessibility
        if ls "$MOUNT_POINT" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ Mount point is accessible${NC}"
            
            # Show disk usage
            echo -e "${YELLOW}Disk usage:${NC}"
            df -h "$MOUNT_POINT" 2>/dev/null || echo "  (Unable to get disk usage)"
            
            # Show file count
            file_count=$(find "$MOUNT_POINT" -type f 2>/dev/null | wc -l)
            echo -e "${YELLOW}Files in mount: $file_count${NC}"
        else
            echo -e "${RED}✗ Mount point is not accessible${NC}"
        fi
    else
        echo -e "${RED}✗ WebDAV is not mounted${NC}"
    fi
    
    # Check for PID file
    if [ -f "$PID_FILE" ]; then
        echo -e "${YELLOW}! PID file exists: $PID_FILE${NC}"
        if [ -r "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE" 2>/dev/null)
            if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
                echo -e "${YELLOW}  davfs process running (PID: $PID)${NC}"
            else
                echo -e "${RED}  Stale PID file (process not running)${NC}"
            fi
        fi
    fi
    
    # Check for davfs processes
    davfs_processes=$(pgrep -f "mount.davfs.*$MOUNT_POINT" 2>/dev/null | wc -l)
    if [ "$davfs_processes" -gt 0 ]; then
        echo -e "${YELLOW}Active davfs processes: $davfs_processes${NC}"
    fi
}

do_mount() {
    echo -e "${YELLOW}Running full WebDAV setup...${NC}"
    if [ -f "./docker-mount-webdav.sh" ]; then
        ./docker-mount-webdav.sh
    else
        echo -e "${RED}docker-mount-webdav.sh not found in current directory${NC}"
        exit 1
    fi
}

do_unmount() {
    check_root
    echo -e "${YELLOW}Unmounting WebDAV...${NC}"
    
    if mountpoint -q "$MOUNT_POINT"; then
        umount "$MOUNT_POINT"
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ WebDAV unmounted successfully${NC}"
        else
            echo -e "${YELLOW}Trying force unmount...${NC}"
            umount -f "$MOUNT_POINT" 2>/dev/null || umount -l "$MOUNT_POINT" 2>/dev/null
            echo -e "${GREEN}✓ Force unmount completed${NC}"
        fi
    else
        echo -e "${YELLOW}WebDAV is not mounted${NC}"
    fi
    
    # Clean up PID file
    if [ -f "$PID_FILE" ]; then
        rm -f "$PID_FILE"
        echo -e "${GREEN}✓ Cleaned up PID file${NC}"
    fi
}

do_cleanup() {
    check_root
    echo -e "${YELLOW}Cleaning up stale mounts and processes...${NC}"
    
    # Kill any davfs processes
    pkill -f "mount.davfs.*$MOUNT_POINT" 2>/dev/null && echo -e "${GREEN}✓ Killed davfs processes${NC}"
    
    # Remove PID file
    if [ -f "$PID_FILE" ]; then
        rm -f "$PID_FILE"
        echo -e "${GREEN}✓ Removed PID file${NC}"
    fi
    
    # Force unmount
    if mountpoint -q "$MOUNT_POINT"; then
        umount -f "$MOUNT_POINT" 2>/dev/null || umount -l "$MOUNT_POINT" 2>/dev/null
        echo -e "${GREEN}✓ Force unmounted${NC}"
    fi
    
    echo -e "${GREEN}Cleanup completed${NC}"
}

test_connectivity() {
    echo -e "${YELLOW}Testing WebDAV connectivity...${NC}"
    
    urls=(
        "http://192.168.100.245:30034/webdav/components"
        "http://31.182.67.115/webdav/components"
    )
    
    for url in "${urls[@]}"; do
        echo -e "${YELLOW}Testing: $url${NC}"
        if curl -s --connect-timeout 5 -I "$url" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ $url is accessible${NC}"
        else
            echo -e "${RED}✗ $url is not accessible${NC}"
        fi
    done
}

do_restart() {
    echo -e "${YELLOW}Restarting WebDAV mount...${NC}"
    do_unmount
    sleep 2
    do_cleanup
    sleep 1
    do_mount
}

show_logs() {
    echo -e "${YELLOW}Recent davfs2 logs:${NC}"
    journalctl -u davfs2 --no-pager -n 20 2>/dev/null || echo "No systemd logs available"
    
    echo -e "${YELLOW}System logs related to davfs:${NC}"
    dmesg | grep -i davfs | tail -10 2>/dev/null || echo "No kernel logs available"
}

# Main command handling
case "${1:-status}" in
    "status"|"s")
        show_status
        ;;
    "mount"|"m")
        do_mount
        ;;
    "unmount"|"u")
        do_unmount
        ;;
    "cleanup"|"c")
        do_cleanup
        ;;
    "test"|"t")
        test_connectivity
        ;;
    "restart"|"r")
        do_restart
        ;;
    "logs"|"l")
        show_logs
        ;;
    "help"|"h"|"-h"|"--help")
        show_usage
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        show_usage
        exit 1
        ;;
esac