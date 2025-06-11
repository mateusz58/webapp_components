echo "🚀 Deploying Shopify Analytics to Production..."

# Check if production environment file exists
if [ ! -f .env.production ]; then
    echo "❌ Error: .env.production file not found!"
    echo "Please create .env.production from .env.example and configure for production."
    exit 1
fi

# Backup current deployment (if exists)
if [ "$(docker ps -q -f name=shopify-analytics)" ]; then
    echo "📦 Creating backup of current deployment..."
    docker-compose -f docker-compose.prod.yml down
    docker image tag shopify-analytics_web:latest shopify-analytics_web:backup-$(date +%Y%m%d-%H%M%S)
fi

# Build and deploy
echo "🔨 Building application..."
docker-compose -f docker-compose.prod.yml build --no-cache

echo "🌐 Starting services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Health check
echo "🔍 Performing health check..."
if curl -f http://localhost/ >/dev/null 2>&1; then
    echo "✅ Deployment successful!"
    echo "🌍 Application is available at: http://localhost/"

    # Show running containers
    echo ""
    echo "📊 Running containers:"
    docker-compose -f docker-compose.prod.yml ps

    # Show logs
    echo ""
    echo "📝 Recent logs:"
    docker-compose -f docker-compose.prod.yml logs --tail=20
else
    echo "❌ Deployment failed! Check logs:"
    docker-compose -f docker-compose.prod.yml logs
    exit 1
fi