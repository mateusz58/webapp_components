#!/bin/bash

echo "📊 Shopify Analytics - System Monitoring"
echo "========================================"

# Function to check service status
check_service() {
    local service=$1
    if docker-compose ps | grep -q "$service.*Up"; then
        echo "✅ $service: Running"
    else
        echo "❌ $service: Not running"
    fi
}

# Check Docker Compose services
echo ""
echo "🔍 Service Status:"
check_service "web"
check_service "db"

# Check disk usage
echo ""
echo "💾 Disk Usage:"
df -h | grep -E "(Filesystem|/dev/)"

# Check memory usage
echo ""
echo "🧠 Memory Usage:"
free -h

# Check Docker stats
echo ""
echo "🐳 Docker Container Stats:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# Check recent logs for errors
echo ""
echo "📝 Recent Errors (last 50 lines):"
docker-compose logs --tail=50 | grep -i error || echo "No recent errors found"

# Database connection test
echo ""
echo "🗄️  Database Connection Test:"
if docker-compose exec -T db psql -U postgres -d shopify_analytics -c "SELECT 1;" >/dev/null 2>&1; then
    echo "✅ Database: Connected"
else
    echo "❌ Database: Connection failed"
fi

# Show application metrics
echo ""
echo "📈 Application Metrics:"
curl -s http://localhost/api/shops | jq -r '. | length' 2>/dev/null | xargs -I {} echo "Shops available: {}" || echo "Could not fetch shop metrics"

echo ""
echo "🕐 Monitor completed at: $(date)"
