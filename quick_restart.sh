#!/bin/bash

# Quick restart script for daily use (after initial optimization deployment)
# Use this for regular restarts without reapplying optimizations

echo "🔄 Quick Restart - Component Management System"
echo "=============================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if we're using Docker or local setup
if [ -f "docker-compose.yml" ] && command -v docker-compose &> /dev/null; then
    print_status "Using Docker setup..."
    
    # Stop containers
    print_status "Stopping containers..."
    docker-compose down
    
    # Start containers
    print_status "Starting containers..."
    docker-compose up -d
    
    # Wait for services
    print_status "Waiting for services to be ready..."
    sleep 10
    
    # Check health
    if curl -f -s http://localhost:6002/ > /dev/null 2>&1; then
        print_status "Application is ready at http://localhost:6002"
    else
        print_warning "Application starting... (check http://localhost:6002 in a moment)"
    fi
    
elif [ -f "./start.sh" ]; then
    print_status "Using start.sh script..."
    
    # Restart using existing script
    ./start.sh restart
    
    # Wait a moment
    sleep 5
    
    # Check health
    if curl -f -s http://localhost:6002/ > /dev/null 2>&1; then
        print_status "Application restarted successfully"
    else
        print_warning "Application may still be starting..."
    fi
    
else
    print_warning "No recognized startup method found"
    echo "Available options:"
    echo "  1. Use docker-compose: docker-compose up -d"
    echo "  2. Use start.sh: ./start.sh restart"
    echo "  3. Manual: python run.py"
    exit 1
fi

echo ""
print_status "Quick restart completed!"
echo "🌐 Application: http://localhost:6002"