#!/bin/bash

# Docker-aware WebDAV mount script for component pictures
# This script can be run on the host before starting Docker containers
# Enhanced with better stale mount cleanup and error recovery

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# WebDAV configuration
WEBDAV_URL="http://192.168.100.245:30034/webdav/components"
WEBDAV_FALLBACK_URL="http://31.182.67.115/webdav/components"
MOUNT_POINT="/components"
DOCKER_COMPOSE_FILE="docker-compose.yml"
PID_FILE="/var/run/mount.davfs/components.pid"
SECRETS_FILE="/etc/davfs2/secrets"

echo -e "${BLUE}=== Docker WebDAV Mount Setup for Component Pictures ===${NC}"

# Function to check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}Please run this script as root (use sudo)${NC}"
        exit 1
    fi
}

# Function to install davfs2
install_davfs2() {
    echo -e "${YELLOW}Installing davfs2 if needed...${NC}"
    apt-get update && apt-get install -y davfs2 fuse
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ davfs2 installed successfully${NC}"
    else
        echo -e "${RED}✗ Failed to install davfs2${NC}"
        exit 1
    fi
}

# Function to setup WebDAV credentials
setup_credentials() {
    echo -e "${YELLOW}Setting up WebDAV credentials...${NC}"
    
    # Create davfs2 directory if it doesn't exist
    mkdir -p /etc/davfs2
    
    # Check if credentials already exist
    if grep -q "$WEBDAV_URL" "$SECRETS_FILE" 2>/dev/null; then
        echo -e "${GREEN}✓ Credentials already configured${NC}"
        return 0
    fi
    
    echo -e "${YELLOW}WebDAV server requires authentication.${NC}"
    read -p "Do you want to configure credentials? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter WebDAV username (or press Enter for anonymous): " username
        if [ -n "$username" ]; then
            read -s -p "Enter WebDAV password: " password
            echo
            
            # Add credentials to secrets file
            echo "$WEBDAV_URL $username $password" >> "$SECRETS_FILE"
            echo "$WEBDAV_FALLBACK_URL $username $password" >> "$SECRETS_FILE"
            chmod 600 "$SECRETS_FILE"
            echo -e "${GREEN}✓ Credentials saved${NC}"
        else
            # Configure for anonymous access
            echo "$WEBDAV_URL \"\" \"\"" >> "$SECRETS_FILE"
            echo "$WEBDAV_FALLBACK_URL \"\" \"\"" >> "$SECRETS_FILE"
            chmod 600 "$SECRETS_FILE"
            echo -e "${GREEN}✓ Configured for anonymous access${NC}"
        fi
    else
        echo -e "${YELLOW}Skipping credential setup - you may be prompted during mount${NC}"
    fi
}

# Enhanced function to clean up stale mounts and processes
cleanup_stale_mount() {
    echo -e "${YELLOW}Cleaning up any stale mounts...${NC}"
    
    # Check if PID file exists and handle stale PID
    if [ -f "$PID_FILE" ]; then
        echo -e "${YELLOW}Found PID file: $PID_FILE${NC}"
        
        # Check if the process is actually running
        if [ -r "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE" 2>/dev/null)
            if [ -n "$PID" ]; then
                if kill -0 "$PID" 2>/dev/null; then
                    echo -e "${YELLOW}Killing active davfs process (PID: $PID)${NC}"
                    kill -TERM "$PID" 2>/dev/null
                    sleep 3
                    # Force kill if still running
                    if kill -0 "$PID" 2>/dev/null; then
                        echo -e "${YELLOW}Force killing stubborn process...${NC}"
                        kill -KILL "$PID" 2>/dev/null
                        sleep 1
                    fi
                else
                    echo -e "${YELLOW}PID $PID is stale (process not running)${NC}"
                fi
            fi
        fi
        
        # Remove the PID file
        rm -f "$PID_FILE"
        echo -e "${GREEN}✓ Cleaned up PID file${NC}"
    fi
    
    # Clean up any remaining davfs processes for this mount point
    echo -e "${YELLOW}Checking for remaining davfs processes...${NC}"
    local remaining_pids=$(pgrep -f "mount.davfs.*$MOUNT_POINT" 2>/dev/null)
    if [ -n "$remaining_pids" ]; then
        echo -e "${YELLOW}Found remaining davfs processes: $remaining_pids${NC}"
        pkill -f "mount.davfs.*$MOUNT_POINT" 2>/dev/null || true
        sleep 2
        # Force kill any stubborn processes
        pkill -9 -f "mount.davfs.*$MOUNT_POINT" 2>/dev/null || true
        echo -e "${GREEN}✓ Cleaned up remaining processes${NC}"
    fi
    
    # Force unmount if still mounted (try multiple methods)
    if mountpoint -q "$MOUNT_POINT" 2>/dev/null; then
        echo -e "${YELLOW}Mount point is still active, attempting unmount...${NC}"
        
        # Try force unmount first
        if umount -f "$MOUNT_POINT" 2>/dev/null; then
            echo -e "${GREEN}✓ Force unmount successful${NC}"
        else
            echo -e "${YELLOW}Force unmount failed, trying lazy unmount...${NC}"
            if umount -l "$MOUNT_POINT" 2>/dev/null; then
                echo -e "${GREEN}✓ Lazy unmount successful${NC}"
            else
                echo -e "${YELLOW}Lazy unmount failed, but continuing...${NC}"
            fi
        fi
        sleep 2
    fi
    
    # Clean up davfs cache to prevent stale data issues
    echo -e "${YELLOW}Cleaning davfs cache...${NC}"
    rm -rf /var/cache/davfs2/* 2>/dev/null || true
    rm -rf ~/.davfs2/cache/* 2>/dev/null || true
    
    echo -e "${GREEN}✓ Cleanup completed${NC}"
}

# Function to create mount point
create_mount_point() {
    echo -e "${YELLOW}Creating mount point: $MOUNT_POINT${NC}"
    mkdir -p "$MOUNT_POINT"
    echo -e "${GREEN}✓ Mount point created${NC}"
}

# Function to test WebDAV connectivity
test_webdav_connectivity() {
    echo -e "${YELLOW}Testing WebDAV server connectivity...${NC}"
    
    # Test primary URL
    if curl -s --connect-timeout 10 -I "$WEBDAV_URL" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Primary WebDAV server is accessible${NC}"
        return 0
    else
        echo -e "${YELLOW}! Primary WebDAV server not accessible, trying fallback...${NC}"
        
        # Test fallback URL
        if curl -s --connect-timeout 10 -I "$WEBDAV_FALLBACK_URL" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ Fallback WebDAV server is accessible${NC}"
            WEBDAV_URL="$WEBDAV_FALLBACK_URL"
            return 0
        else
            echo -e "${RED}✗ Both WebDAV servers are unreachable${NC}"
            return 1
        fi
    fi
}

# Enhanced function to mount WebDAV with better error handling
mount_webdav() {
    # Check if already mounted and working
    if mountpoint -q "$MOUNT_POINT" && [ -d "$MOUNT_POINT" ] && ls "$MOUNT_POINT" >/dev/null 2>&1; then
        echo -e "${YELLOW}WebDAV already mounted at $MOUNT_POINT${NC}"
        
        # Test if it's actually working (not just mounted)
        local test_file="$MOUNT_POINT/.connection_test_$$"
        if echo "connection test" > "$test_file" 2>/dev/null; then
            rm -f "$test_file" 2>/dev/null
            echo -e "${GREEN}✓ Existing mount is working properly${NC}"
            read -p "Unmount and remount anyway? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo -e "${GREEN}Using existing mount${NC}"
                return 0
            fi
        else
            echo -e "${YELLOW}Existing mount appears broken (transport endpoint issue)${NC}"
        fi
        
        cleanup_stale_mount
    else
        # Clean up any stale mounts
        cleanup_stale_mount
    fi

    echo -e "${YELLOW}Mounting WebDAV: $WEBDAV_URL -> $MOUNT_POINT${NC}"
    
    # Configure davfs2 for better stability
    echo -e "${YELLOW}Configuring davfs2 for stability...${NC}"
    mkdir -p /etc/davfs2
    
    # Create or update davfs2.conf with stable settings
    if ! grep -q "use_locks.*0" /etc/davfs2/davfs2.conf 2>/dev/null; then
        echo "use_locks 0" >> /etc/davfs2/davfs2.conf
        echo -e "${GREEN}✓ Disabled file locking for compatibility${NC}"
    fi
    
    # Try mounting with progressively simpler options
    local mount_attempts=(
        "rw,uid=1000,gid=1000,file_mode=0644,dir_mode=0755,nolock,_netdev"
        "rw,uid=1000,gid=1000,nolock,_netdev"
        "rw,nolock,_netdev"
        "rw,nolock"
        "rw"
    )
    
    for i in "${!mount_attempts[@]}"; do
        local options="${mount_attempts[$i]}"
        echo -e "${YELLOW}Attempt $((i+1)): Mounting with options: $options${NC}"
        
        if mount -t davfs "$WEBDAV_URL" "$MOUNT_POINT" -o "$options" 2>/dev/null; then
            echo -e "${GREEN}✓ WebDAV mounted successfully${NC}"
            # Give davfs a moment to initialize
            sleep 2
            return 0
        else
            echo -e "${YELLOW}Failed with options: $options${NC}"
            if [ $i -lt $((${#mount_attempts[@]} - 1)) ]; then
                echo -e "${YELLOW}Retrying with simpler options...${NC}"
                sleep 1
            fi
        fi
    done
    
    echo -e "${RED}✗ Failed to mount WebDAV after all attempts${NC}"
    return 1
}

# Enhanced function to verify mount with write test
verify_mount() {
    echo -e "${YELLOW}Verifying mount...${NC}"
    
    # Check if mount point is accessible
    if ! mountpoint -q "$MOUNT_POINT"; then
        echo -e "${RED}✗ Mount point is not mounted${NC}"
        return 1
    fi
    
    # Check if we can list directory contents
    if ! ls "$MOUNT_POINT" >/dev/null 2>&1; then
        echo -e "${RED}✗ Cannot access mount point contents${NC}"
        echo -e "${YELLOW}This might be a 'transport endpoint is not connected' issue${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✓ Mount verified successfully${NC}"
    return 0
}

# Function to set permissions
set_permissions() {
    echo -e "${YELLOW}Setting permissions...${NC}"
    
    # Set ownership (1000:1000 is typical for Docker containers)
    chown -R 1000:1000 "$MOUNT_POINT" 2>/dev/null || true
    chmod -R 755 "$MOUNT_POINT" 2>/dev/null || true
    
    echo -e "${GREEN}✓ Permissions set${NC}"
}

# Function to add to fstab
add_to_fstab() {
    read -p "Add to /etc/fstab for automatic mounting on boot? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Check if entry already exists
        if grep -q "$WEBDAV_URL" /etc/fstab; then
            echo -e "${YELLOW}Entry already exists in /etc/fstab${NC}"
        else
            echo "$WEBDAV_URL $MOUNT_POINT davfs rw,user,noauto,uid=1000,gid=1000,nolock 0 0" >> /etc/fstab
            echo -e "${GREEN}✓ Added to /etc/fstab${NC}"
        fi
    fi
}

# Function to show mount info
show_mount_info() {
    echo -e "${BLUE}=== Mount Information ===${NC}"
    echo -e "${YELLOW}Mount point: $MOUNT_POINT${NC}"
    echo -e "${YELLOW}WebDAV URL: $WEBDAV_URL${NC}"
    echo -e "${YELLOW}External URL: http://31.182.67.115/webdav/components${NC}"
    
    echo -e "${YELLOW}Mount details:${NC}"
    mount | grep "$MOUNT_POINT" || echo "  (No mount information available)"
    
    echo -e "${YELLOW}Disk usage:${NC}"
    df -h "$MOUNT_POINT" 2>/dev/null || echo "  (Unable to get disk usage info)"
    
    echo -e "${YELLOW}Directory contents (first 10 items):${NC}"
    ls -la "$MOUNT_POINT" 2>/dev/null | head -10 || echo "  (Unable to list contents)"
}

# Enhanced function to test Docker integration with better write testing
test_docker_integration() {
    echo -e "${BLUE}=== Testing Docker Integration ===${NC}"
    
    if [ -f "$DOCKER_COMPOSE_FILE" ]; then
        echo -e "${GREEN}✓ Docker Compose file found${NC}"
        echo -e "${YELLOW}You can now run: docker-compose up --build${NC}"
    else
        echo -e "${YELLOW}! Docker Compose file not found in current directory${NC}"
        echo -e "${YELLOW}  Make sure you're in the project root directory${NC}"
    fi
    
    # Enhanced write access test
    echo -e "${YELLOW}Testing write access to mount point...${NC}"
    local test_file="$MOUNT_POINT/.test_write_access_$$"
    
    # Try writing a test file
    if echo "test write at $(date)" > "$test_file" 2>/dev/null; then
        echo -e "${GREEN}✓ Write access confirmed${NC}"
        
        # Try reading it back
        if cat "$test_file" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ Read-back successful${NC}"
            rm -f "$test_file" 2>/dev/null
        else
            echo -e "${YELLOW}! Write succeeded but read-back failed${NC}"
            rm -f "$test_file" 2>/dev/null || true
        fi
    else
        echo -e "${RED}✗ Write access failed${NC}"
        local error_msg=$(echo "test write" > "$test_file" 2>&1)
        echo -e "${YELLOW}Error details: $error_msg${NC}"
        
        if [[ "$error_msg" == *"Transport endpoint is not connected"* ]]; then
            echo -e "${YELLOW}This is a davfs connection issue. Attempting to fix...${NC}"
            
            # Try to fix the transport endpoint issue
            echo -e "${YELLOW}Attempting to remount to fix transport endpoint issue...${NC}"
            cleanup_stale_mount
            if mount_webdav && verify_mount; then
                echo -e "${YELLOW}Retesting write access after remount...${NC}"
                if echo "test write after fix" > "$test_file" 2>/dev/null; then
                    echo -e "${GREEN}✓ Write access fixed!${NC}"
                    rm -f "$test_file" 2>/dev/null
                else
                    echo -e "${RED}✗ Write access still not working after remount${NC}"
                fi
            fi
        fi
    fi
}

# Function to show troubleshooting info
show_troubleshooting() {
    echo -e "${BLUE}=== Troubleshooting Information ===${NC}"
    echo -e "${YELLOW}If you encounter issues:${NC}"
    echo -e "  1. Check WebDAV server status: curl -I $WEBDAV_URL"
    echo -e "  2. Check mount status: mountpoint $MOUNT_POINT"
    echo -e "  3. Check davfs logs: journalctl -u davfs2"
    echo -e "  4. Manual unmount: sudo umount $MOUNT_POINT"
    echo -e "  5. Clean PID file: sudo rm -f $PID_FILE"
    echo -e "  6. Kill davfs processes: sudo pkill -f mount.davfs"
    echo -e "  7. Clean cache: sudo rm -rf /var/cache/davfs2/*"
    echo -e "  8. Re-run this script: sudo $0"
}

# Main execution
main() {
    check_root
    install_davfs2
    setup_credentials
    
    if ! test_webdav_connectivity; then
        echo -e "${RED}Cannot proceed - WebDAV server is not accessible${NC}"
        show_troubleshooting
        exit 1
    fi
    
    create_mount_point
    
    if mount_webdav && verify_mount; then
        set_permissions
        add_to_fstab
        show_mount_info
        test_docker_integration
        
        echo -e "${GREEN}=== WebDAV Setup Complete! ===${NC}"
        echo -e "${YELLOW}Next steps:${NC}"
        echo -e "  1. Run: docker-compose up --build"
        echo -e "  2. Test file uploads in the application"
        echo -e "  3. Verify URLs use: http://31.182.67.115/webdav/components/..."
    else
        echo -e "${RED}Setup failed. Please check the error messages above.${NC}"
        show_troubleshooting
        exit 1
    fi
}

# Handle script arguments
case "${1:-}" in
    "cleanup")
        check_root
        cleanup_stale_mount
        echo -e "${GREEN}Cleanup completed${NC}"
        ;;
    "test")
        test_webdav_connectivity
        ;;
    "unmount")
        check_root
        cleanup_stale_mount
        echo -e "${GREEN}Unmount completed${NC}"
        ;;
    "fix")
        check_root
        echo -e "${BLUE}=== Attempting to Fix Transport Endpoint Issues ===${NC}"
        cleanup_stale_mount
        create_mount_point
        if mount_webdav && verify_mount; then
            set_permissions
            test_docker_integration
            echo -e "${GREEN}✓ Fix completed successfully${NC}"
        else
            echo -e "${RED}✗ Fix attempt failed${NC}"
            show_troubleshooting
        fi
        ;;
    *)
        main "$@"
        ;;
esac