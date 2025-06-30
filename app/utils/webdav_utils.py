"""WebDAV utilities for mount detection and management."""

import os
import subprocess
import logging
from flask import current_app


def is_webdav_mounted(mount_point='/components'):
    """Check if WebDAV is properly mounted at the given mount point."""
    try:
        # Method 1: Check if it's a mount point
        result = subprocess.run(['mountpoint', '-q', mount_point], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            return True
        
        # Method 2: Check mount output for davfs
        result = subprocess.run(['mount'], capture_output=True, text=True)
        if result.returncode == 0:
            mount_output = result.stdout
            # Look for davfs mount on our mount point
            for line in mount_output.split('\n'):
                if mount_point in line and 'davfs' in line:
                    return True
        
        return False
    except Exception as e:
        current_app.logger.error(f"Error checking WebDAV mount status: {e}")
        return False


def get_webdav_config():
    """Get WebDAV configuration from environment or config."""
    return {
        'internal_url': os.environ.get('WEBDAV_INTERNAL_URL', 'http://192.168.100.245:30034/webdav/components'),
        'external_url': os.environ.get('WEBDAV_EXTERNAL_URL', 'http://31.182.67.115/webdav/components'),
        'mount_point': os.environ.get('WEBDAV_MOUNT_POINT', '/components'),
        'username': os.environ.get('WEBDAV_USERNAME', ''),
        'password': os.environ.get('WEBDAV_PASSWORD', '')
    }


def mount_webdav_if_needed(mount_point='/components'):
    """Attempt to mount WebDAV if not already mounted."""
    if is_webdav_mounted(mount_point):
        current_app.logger.info(f"WebDAV already mounted at {mount_point}")
        return True
    
    try:
        config = get_webdav_config()
        internal_url = config['internal_url']
        
        current_app.logger.info(f"Attempting to mount WebDAV: {internal_url} -> {mount_point}")
        
        # Create mount point if it doesn't exist
        os.makedirs(mount_point, exist_ok=True)
        
        # Try to mount using davfs
        mount_cmd = ['mount', '-t', 'davfs', internal_url, mount_point]
        result = subprocess.run(mount_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            current_app.logger.info(f"Successfully mounted WebDAV at {mount_point}")
            return True
        else:
            current_app.logger.error(f"Failed to mount WebDAV: {result.stderr}")
            return False
            
    except Exception as e:
        current_app.logger.error(f"Error mounting WebDAV: {e}")
        return False


def check_webdav_write_access(mount_point='/components'):
    """Check if we have write access to the WebDAV mount."""
    if not is_webdav_mounted(mount_point):
        return False
    
    try:
        test_file = os.path.join(mount_point, '.write_test')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        return True
    except Exception as e:
        current_app.logger.warning(f"No write access to WebDAV mount: {e}")
        return False


def get_webdav_status():
    """Get comprehensive WebDAV status information."""
    mount_point = '/components'
    config = get_webdav_config()
    
    status = {
        'mount_point': mount_point,
        'is_mounted': is_webdav_mounted(mount_point),
        'mount_exists': os.path.exists(mount_point),
        'has_write_access': False,
        'internal_url': config['internal_url'],
        'external_url': config['external_url'],
        'files_count': 0,
        'issues': []
    }
    
    if status['is_mounted']:
        status['has_write_access'] = check_webdav_write_access(mount_point)
        try:
            files = os.listdir(mount_point)
            status['files_count'] = len([f for f in files if os.path.isfile(os.path.join(mount_point, f))])
        except:
            status['files_count'] = 0
    else:
        status['issues'].append('WebDAV not mounted')
    
    if not status['has_write_access']:
        status['issues'].append('No write access to mount point')
    
    return status


def log_webdav_status():
    """Log current WebDAV status for debugging."""
    status = get_webdav_status()
    
    current_app.logger.info("=== WebDAV Status ===")
    current_app.logger.info(f"Mount Point: {status['mount_point']}")
    current_app.logger.info(f"Is Mounted: {status['is_mounted']}")
    current_app.logger.info(f"Write Access: {status['has_write_access']}")
    current_app.logger.info(f"Files Count: {status['files_count']}")
    current_app.logger.info(f"Internal URL: {status['internal_url']}")
    current_app.logger.info(f"External URL: {status['external_url']}")
    
    if status['issues']:
        current_app.logger.warning(f"Issues: {', '.join(status['issues'])}")
    
    return status