#!/bin/bash

# Mount WebDAV script for component pictures
# This script mounts the WebDAV share to /components directory

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# WebDAV configuration
WEBDAV_URL="http://192.168.100.245:30034/webdav/components"
MOUNT_POINT="/components"

echo -e "${YELLOW}Setting up WebDAV mount for component pictures...${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run this script as root (use sudo)${NC}"
    exit 1
fi

# Install davfs2 if not already installed
echo -e "${YELLOW}Installing davfs2 if needed...${NC}"
apt-get update && apt-get install -y davfs2

# Create mount point
echo -e "${YELLOW}Creating mount point: $MOUNT_POINT${NC}"
mkdir -p "$MOUNT_POINT"

# Check if already mounted
if mountpoint -q "$MOUNT_POINT"; then
    echo -e "${YELLOW}WebDAV already mounted at $MOUNT_POINT${NC}"
    umount "$MOUNT_POINT"
    echo -e "${YELLOW}Unmounted existing mount${NC}"
fi

# Mount the WebDAV
echo -e "${YELLOW}Mounting WebDAV: $WEBDAV_URL -> $MOUNT_POINT${NC}"
mount -t davfs "$WEBDAV_URL" "$MOUNT_POINT"

# Check if mount was successful
if mountpoint -q "$MOUNT_POINT"; then
    echo -e "${GREEN}✓ WebDAV mounted successfully at $MOUNT_POINT${NC}"
    
    # Set permissions for the application
    chown -R 1000:1000 "$MOUNT_POINT"
    chmod -R 755 "$MOUNT_POINT"
    
    # Files will be stored directly in WebDAV root (no subfolders needed)
    
    echo -e "${GREEN}✓ Directory structure created${NC}"
    echo -e "${GREEN}✓ Permissions set${NC}"
    
    # Show mount info
    echo -e "${YELLOW}Mount information:${NC}"
    df -h "$MOUNT_POINT"
    
else
    echo -e "${RED}✗ Failed to mount WebDAV${NC}"
    exit 1
fi

# Add to fstab for persistent mounting (optional)
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

echo -e "${GREEN}WebDAV setup complete!${NC}"
echo -e "${YELLOW}Mount point: $MOUNT_POINT${NC}"
echo -e "${YELLOW}WebDAV URL: $WEBDAV_URL${NC}"
echo -e "${YELLOW}External URL: http://31.182.67.115/webdav/components${NC}"