#!/bin/bash

# Simple WebDAV mount script for component pictures
# Run this script to mount WebDAV before using the application

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# WebDAV configuration
WEBDAV_URL="http://192.168.100.245:30034/webdav/components"
MOUNT_POINT="/components"

echo -e "${BLUE}=== Quick WebDAV Mount for Component Pictures ===${NC}"

# Function to check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}Please run this script as root (use sudo)${NC}"
        echo -e "${YELLOW}Example: sudo ./mount-webdav-simple.sh${NC}"
        exit 1
    fi
}

# Function to check if davfs2 is installed
check_davfs2() {
    if ! command -v mount.davfs &> /dev/null; then
        echo -e "${YELLOW}Installing davfs2...${NC}"
        apt-get update && apt-get install -y davfs2 fuse
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ davfs2 installed successfully${NC}"
        else
            echo -e "${RED}✗ Failed to install davfs2${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}✓ davfs2 is already installed${NC}"
    fi
}

# Function to mount WebDAV
mount_webdav() {
    # Check if already mounted
    if mountpoint -q "$MOUNT_POINT"; then
        echo -e "${GREEN}✓ WebDAV already mounted at $MOUNT_POINT${NC}"
        return 0
    fi

    # Create mount point
    echo -e "${YELLOW}Creating mount point: $MOUNT_POINT${NC}"
    mkdir -p "$MOUNT_POINT"

    echo -e "${YELLOW}Mounting WebDAV: $WEBDAV_URL -> $MOUNT_POINT${NC}"
    mount -t davfs "$WEBDAV_URL" "$MOUNT_POINT"

    # Check if mount was successful
    if mountpoint -q "$MOUNT_POINT"; then
        echo -e "${GREEN}✓ WebDAV mounted successfully at $MOUNT_POINT${NC}"
        
        # Set permissions
        chown -R 1000:1000 "$MOUNT_POINT"
        chmod -R 755 "$MOUNT_POINT"
        echo -e "${GREEN}✓ Permissions set${NC}"
        
        # Test write access
        if touch "$MOUNT_POINT/test_write_access" 2>/dev/null; then
            rm -f "$MOUNT_POINT/test_write_access"
            echo -e "${GREEN}✓ Write access confirmed${NC}"
        else
            echo -e "${YELLOW}⚠ Warning: Limited write access${NC}"
        fi
        
        return 0
    else
        echo -e "${RED}✗ Failed to mount WebDAV${NC}"
        echo -e "${YELLOW}Possible issues:${NC}"
        echo -e "  - Network connection to $WEBDAV_URL"
        echo -e "  - WebDAV server not accessible"
        echo -e "  - Authentication required"
        return 1
    fi
}

# Function to show status
show_status() {
    echo -e "${BLUE}=== Current Status ===${NC}"
    echo -e "${YELLOW}Mount point: $MOUNT_POINT${NC}"
    echo -e "${YELLOW}WebDAV URL: $WEBDAV_URL${NC}"
    
    if mountpoint -q "$MOUNT_POINT"; then
        echo -e "${GREEN}Status: MOUNTED${NC}"
        echo -e "${YELLOW}Files in mount:${NC}"
        ls -la "$MOUNT_POINT" | head -10
        if [ $(ls -1 "$MOUNT_POINT" | wc -l) -gt 10 ]; then
            echo "... and more"
        fi
    else
        echo -e "${RED}Status: NOT MOUNTED${NC}"
    fi
}

# Main execution
main() {
    check_root
    check_davfs2
    
    if mount_webdav; then
        show_status
        
        echo -e "${GREEN}=== WebDAV Mount Complete! ===${NC}"
        echo -e "${YELLOW}You can now start the application with:${NC}"
        echo -e "  docker-compose up --build"
        echo -e ""
        echo -e "${YELLOW}To unmount later, run:${NC}"
        echo -e "  sudo umount $MOUNT_POINT"
    else
        echo -e "${RED}Mount failed. Please check the issues above.${NC}"
        exit 1
    fi
}

# Handle command line arguments
case "${1:-mount}" in
    "mount")
        main
        ;;
    "status")
        show_status
        ;;
    "unmount")
        if mountpoint -q "$MOUNT_POINT"; then
            echo -e "${YELLOW}Unmounting $MOUNT_POINT...${NC}"
            umount "$MOUNT_POINT"
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✓ WebDAV unmounted successfully${NC}"
            else
                echo -e "${RED}✗ Failed to unmount WebDAV${NC}"
            fi
        else
            echo -e "${YELLOW}WebDAV is not mounted at $MOUNT_POINT${NC}"
        fi
        ;;
    *)
        echo -e "${BLUE}Usage: $0 [mount|unmount|status]${NC}"
        echo -e "  mount   - Mount WebDAV (default)"
        echo -e "  unmount - Unmount WebDAV"
        echo -e "  status  - Show current mount status"
        ;;
esac