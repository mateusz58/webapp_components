.PHONY: help install start stop restart logs clean backup deploy monitor

# Default target
help:
	@echo "🚀 Shopify Analytics - Available Commands"
	@echo "========================================"
	@echo ""
	@echo "Development Commands:"
	@echo "  make install    Install dependencies and setup"
	@echo "  make start      Start the application (development)"
	@echo "  make stop       Stop the application"
	@echo "  make restart    Restart the application"
	@echo "  make logs       Show application logs"
	@echo ""
	@echo "Production Commands:"
	@echo "  make deploy     Deploy to production"
	@echo "  make backup     Create backup"
	@echo "  make monitor    Show system status"
	@echo ""
	@echo "Maintenance Commands:"
	@echo "  make clean      Clean up Docker resources"
	@echo "  make test       Run tests (when available)"

install:
	@echo "📦 Installing Shopify Analytics..."
	@./create_app_skeleton.sh
	@cp .env.example .env
	@echo "✅ Installation complete!"
	@echo "📝 Please edit .env file with your database credentials"

start:
	@echo "🚀 Starting Shopify Analytics (Development)..."
	@docker-compose up --build

start-bg:
	@echo "🚀 Starting Shopify Analytics in background..."
	@docker-compose up -d --build

stop:
	@echo "🛑 Stopping Shopify Analytics..."
	@docker-compose down

restart:
	@echo "🔄 Restarting Shopify Analytics..."
	@./restart.sh

logs:
	@echo "📝 Showing logs..."
	@./logs.sh

deploy:
	@echo "🚀 Deploying to production..."
	@./deploy.sh

backup:
	@echo "💾 Creating backup..."
	@./backup.sh

monitor:
	@echo "📊 System monitoring..."
	@./monitoring.sh

clean:
	@echo "🧹 Cleaning up Docker resources..."
	@docker-compose down --volumes --remove-orphans
	@docker system prune -f
	@echo "✅ Cleanup complete!"

test:
	@echo "🧪 Running tests..."
	@echo "⚠️  Tests not implemented yet"

# Set executable permissions for scripts
setup-permissions:
	@chmod +x *.sh