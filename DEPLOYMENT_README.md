# Deployment Scripts for Performance Optimizations

This directory contains deployment scripts to apply all performance optimizations to your Component Management System.

## 🚀 Initial Deployment (First Time)

Run this to deploy all performance optimizations:

```bash
./deploy_optimizations.sh
```

### What this script does:
1. **Stops** the current application safely
2. **Backs up** your current configuration
3. **Updates** dependencies (Flask-Caching, Redis)
4. **Modifies** app initialization for performance
5. **Creates** database indexes for faster queries
6. **Installs** frontend performance optimizations
7. **Starts** the application with all optimizations
8. **Warms up** the cache for immediate performance gains
9. **Runs** health checks to ensure everything works

### Expected output:
```
🚀 Starting Performance Optimization Deployment...
✓ Step 1: Stopping current application...
✓ Step 2: Creating backup...
✓ Step 3: Updating dependencies...
✓ Step 4: Updating application initialization...
✓ Step 5: Updating templates...
✓ Step 6: Installing dependencies...
✓ Step 7: Creating database indexes...
✓ Step 8: Starting application...
✓ Step 9: Warming up cache...
✓ Step 10: Running health check...
🎉 Performance Optimization Deployment Complete!
```

## 🔄 Daily Restarts (After Initial Setup)

For regular restarts without reapplying optimizations:

```bash
./quick_restart.sh
```

This is faster and just restarts the application with existing optimizations.

## 📋 Prerequisites

Before running the deployment script, ensure you have:

- ✅ **Database running** (PostgreSQL)
- ✅ **Docker or Python environment** set up
- ✅ **Write permissions** to the application directory
- ✅ **Network access** for downloading dependencies

## 🔧 Troubleshooting

### If deployment fails:

1. **Check the backup**: A backup is automatically created in `backup_YYYYMMDD_HHMMSS/`
2. **Restore if needed**: 
   ```bash
   cp -r backup_*/app/* app/
   ./quick_restart.sh
   ```
3. **Check logs**: 
   ```bash
   docker-compose logs  # For Docker
   # or check application logs
   ```

### Common issues:

**Database connection failed:**
- Ensure PostgreSQL is running
- Check database credentials in `config.py`
- Verify database schema `component_app` exists

**Dependencies installation failed:**
- Check internet connection
- Verify Python/pip version compatibility
- Try manual installation: `pip install Flask-Caching redis`

**Port 6002 already in use:**
- Stop other applications using the port
- Or modify port in `docker-compose.yml` or startup script

**Permission denied:**
- Make scripts executable: `chmod +x *.sh`
- Check file permissions for the app directory

## 📊 Performance Verification

After deployment, verify performance improvements:

### 1. Check application startup:
```bash
curl http://localhost:6002/
```

### 2. Test component listing speed:
```bash
time curl "http://localhost:6002/components"
```

### 3. Verify cache is working:
```bash
# First request (cache miss)
time curl "http://localhost:6002/components"

# Second request (cache hit - should be faster)
time curl "http://localhost:6002/components"
```

### 4. Check database indexes:
Connect to PostgreSQL and run:
```sql
SELECT indexname FROM pg_indexes WHERE schemaname = 'component_app';
```

## 🔄 Rollback Plan

If you need to rollback the optimizations:

### 1. Stop the application:
```bash
./start.sh stop  # or docker-compose down
```

### 2. Restore from backup:
```bash
# Find your backup directory
ls -la backup_*

# Restore (replace YYYYMMDD_HHMMSS with your backup timestamp)
cp -r backup_YYYYMMDD_HHMMSS/* .
```

### 3. Remove optimization files:
```bash
rm -f app/optimized_routes.py
rm -f app/cache_config.py
rm -f app/static/js/performance.js
```

### 4. Restart:
```bash
./quick_restart.sh
```

## 📈 Monitoring Performance

After deployment, monitor these metrics:

### Database Performance:
- Query execution times
- Index usage statistics
- Connection pool usage

### Cache Performance:
- Cache hit/miss ratio
- Memory usage
- Response times for cached vs uncached requests

### Application Performance:
- Page load times
- Server response times
- Memory and CPU usage

## 🆘 Support

If you encounter issues:

1. **Check logs first**: Look at application and database logs
2. **Try rollback**: Use the backup to restore previous working state
3. **Manual verification**: Test each component individually
4. **Database check**: Ensure all migrations are applied

### Logs locations:
- **Docker**: `docker-compose logs app`
- **Local**: Check Flask application logs
- **Database**: PostgreSQL logs
- **Deployment**: `deployment.log` (created by script)

## 📝 Customization

You can customize the deployment by modifying:

- **Cache timeout**: Edit `app/cache_config.py`
- **Database indexes**: Edit the indexes list in `deploy_optimizations.sh`
- **Dependencies**: Modify `requirements.txt` before running
- **Startup behavior**: Edit `app/__init__.py` after deployment

## 🔄 Regular Maintenance

### Weekly:
- Run `./quick_restart.sh` to refresh the application
- Check `deployment.log` for any issues
- Monitor cache performance

### Monthly:
- Review database index usage
- Check for new performance optimizations
- Update dependencies if needed

### When adding new features:
- Consider cache invalidation needs
- Add appropriate database indexes
- Test performance impact

---

**Ready to deploy?** Run `./deploy_optimizations.sh` and enjoy significantly faster performance! 🚀