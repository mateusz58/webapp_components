BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "💾 Creating backup in $BACKUP_DIR..."

# Backup database
echo "📊 Backing up database..."
docker-compose exec -T db pg_dump -U postgres shopify_analytics > "$BACKUP_DIR/database.sql"

# Backup application code
echo "📁 Backing up application code..."
tar -czf "$BACKUP_DIR/application.tar.gz" \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='backups' \
    --exclude='.env*' \
    .

# Backup Docker images
echo "🐳 Backing up Docker images..."
docker save shopify-analytics_web:latest | gzip > "$BACKUP_DIR/docker_images.tar.gz"

# Create backup info
echo "📋 Creating backup info..."
cat > "$BACKUP_DIR/backup_info.txt" << EOF
Backup created: $(date)
Application version: 1.0.0
Database size: $(du -h "$BACKUP_DIR/database.sql" | cut -f1)
Application size: $(du -h "$BACKUP_DIR/application.tar.gz" | cut -f1)
Docker images size: $(du -h "$BACKUP_DIR/docker_images.tar.gz" | cut -f1)

To restore:
1. Stop current services: docker-compose down
2. Restore database: docker-compose exec -T db psql -U postgres shopify_analytics < database.sql
3. Extract application: tar -xzf application.tar.gz
4. Load Docker images: docker load < docker_images.tar.gz
5. Start services: docker-compose up -d
EOF

echo "✅ Backup completed successfully!"
echo "📍 Backup location: $BACKUP_DIR"
echo "📊 Backup size: $(du -sh "$BACKUP_DIR" | cut -f1)"

# Clean up old backups (keep last 7 days)
find ./backups -type d -mtime +7 -exec rm -rf {} + 2>/dev/null || true