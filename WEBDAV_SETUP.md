# WebDAV Setup for Component Pictures

This guide explains how to set up WebDAV mounting for component picture storage.

## Quick Setup

### Option 1: Automated Setup (Recommended)

Run the automated Docker setup script:

```bash
sudo ./docker-mount-webdav.sh
```

This script will:
- Install davfs2 if needed
- Create the mount point `/components`
- Mount the WebDAV share
- Set proper permissions
- Test Docker integration

### Option 2: Manual Setup

1. **Install davfs2:**
   ```bash
   sudo apt-get update
   sudo apt-get install davfs2 fuse
   ```

2. **Create mount point:**
   ```bash
   sudo mkdir -p /components
   ```

3. **Mount WebDAV:**
   ```bash
   sudo mount -t davfs http://192.168.100.245:30034/webdav/components /components
   ```

4. **Set permissions:**
   ```bash
   sudo chown -R 1000:1000 /components
   sudo chmod -R 755 /components
   sudo mkdir -p /components/uploads /components/variant_uploads
   ```

## Configuration Details

### WebDAV URLs
- **Internal mount:** `http://192.168.100.245:30034/webdav/components`
- **External access:** `http://31.182.67.115/webdav/components`

### Application Configuration
The application is configured to:
- Save files directly to: `/components/` (mounted WebDAV root)
- Return URLs with format: `http://31.182.67.115/webdav/components/filename.jpg`
- Fall back to local storage if WebDAV is unavailable

### Docker Configuration
The `docker-compose.yml` includes:
- Volume mount: `/components:/components:rw`
- Privileged mode for mounting
- FUSE device access
- SYS_ADMIN capability

## Starting the Application

After WebDAV is mounted:

```bash
# Restart the application to use new configuration
./restart.sh
```

The application will automatically:
- Use WebDAV storage when available
- Generate proper external URLs for pictures
- Fall back to local storage if WebDAV fails

## Verification

1. **Check mount status:**
   ```bash
   mountpoint /components
   df -h /components
   ```

2. **Test file creation:**
   ```bash
   sudo touch /components/test.txt
   ls -la /components/test.txt
   sudo rm /components/test.txt
   ```

3. **Test application:**
   - Create a new component with pictures
   - Verify pictures appear in component detail view
   - Check that URLs use `http://31.182.67.115/webdav/components/` prefix

## Troubleshooting

### Mount Issues
- Ensure WebDAV server is accessible: `ping 192.168.100.245`
- Check davfs2 logs: `dmesg | grep davfs2`
- Verify permissions: `ls -la /components`

### Application Issues
- Check application logs: `docker-compose logs`
- Verify configuration in browser developer tools
- Test with small image files first

### Unmounting
```bash
sudo umount /components
```

## Persistent Mounting

To automatically mount on system boot, add to `/etc/fstab`:
```
http://192.168.100.245:30034/webdav/components /components davfs rw,user,noauto 0 0
```

## Files Modified

- `config.py`: Added WebDAV configuration
- `app/utils/file_handling.py`: Updated to use WebDAV URLs
- `docker-compose.yml`: Added volume mounts and permissions
- `docker/app/Dockerfile`: Added davfs2 package