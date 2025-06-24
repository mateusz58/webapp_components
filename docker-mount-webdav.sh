#!/bin/bash

# Docker-aware WebDAV mount script for component pictures
# This script can be run on the host before starting Docker containers

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# WebDAV configuration
WEBDAV_URL="http://192.168.100.245:30034/webdav/components"
MOUNT_POINT="/components"
DOCKER_COMPOSE_FILE="docker-compose.yml"

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

# Function to create mount point
create_mount_point() {
    echo -e "${YELLOW}Creating mount point: $MOUNT_POINT${NC}"
    mkdir -p "$MOUNT_POINT"
    echo -e "${GREEN}✓ Mount point created${NC}"
}

# Function to mount WebDAV
mount_webdav() {
    # Check if already mounted
    if mountpoint -q "$MOUNT_POINT"; then
        echo -e "${YELLOW}WebDAV already mounted at $MOUNT_POINT${NC}"
        read -p "Unmount and remount? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            umount "$MOUNT_POINT"
            echo -e "${YELLOW}Unmounted existing mount${NC}"
        else
            echo -e "${GREEN}Using existing mount${NC}"
            return 0
        fi
    fi

    echo -e "${YELLOW}Mounting WebDAV: $WEBDAV_URL -> $MOUNT_POINT${NC}"
    mount -t davfs "$WEBDAV_URL" "$MOUNT_POINT"

    # Check if mount was successful
    if mountpoint -q "$MOUNT_POINT"; then
        echo -e "${GREEN}✓ WebDAV mounted successfully at $MOUNT_POINT${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed to mount WebDAV${NC}"
        return 1
    fi
}

# Function to set permissions
set_permissions() {
    echo -e "${YELLOW}Setting permissions and creating directory structure...${NC}"
    
    # Set ownership (1000:1000 is typical for Docker containers)
    chown -R 1000:1000 "$MOUNT_POINT"
    chmod -R 755 "$MOUNT_POINT"
    
    # Files will be stored directly in WebDAV root
    # No subdirectories needed for the new URL structure
    
    echo -e "${GREEN}✓ Permissions and directory structure set${NC}"
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
            echo "$WEBDAV_URL $MOUNT_POINT davfs rw,user,noauto 0 0" >> /etc/fstab
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
    echo -e "${YELLOW}Disk usage:${NC}"
    df -h "$MOUNT_POINT" 2>/dev/null || echo "  (Unable to get disk usage info)"
}

# Function to test Docker integration
test_docker_integration() {
    echo -e "${BLUE}=== Testing Docker Integration ===${NC}"
    
    if [ -f "$DOCKER_COMPOSE_FILE" ]; then
        echo -e "${GREEN}✓ Docker Compose file found${NC}"
        echo -e "${YELLOW}You can now run: docker-compose up --build${NC}"
    else
        echo -e "${YELLOW}! Docker Compose file not found in current directory${NC}"
        echo -e "${YELLOW}  Make sure you're in the project root directory${NC}"
    fi
    
    # Test write access
    echo -e "${YELLOW}Testing write access to mount point...${NC}"
    if touch "$MOUNT_POINT/test_write_access" 2>/dev/null; then
        rm -f "$MOUNT_POINT/test_write_access"
        echo -e "${GREEN}✓ Write access confirmed${NC}"
    else
        echo -e "${RED}✗ No write access to mount point${NC}"
        echo -e "${YELLOW}This may cause issues with file uploads${NC}"
    fi
}

# Main execution
main() {
    check_root
    install_davfs2
    create_mount_point
    
    if mount_webdav; then
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
        exit 1
    fi
}

# Run main function
main "$@"