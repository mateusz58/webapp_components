#!/bin/bash

# =====================================================
# REMOTE DOCKER DEPLOYMENT SCRIPT
# =====================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REMOTE_HOST="192.168.100.30"
REMOTE_PORT="2222"
REMOTE_USER="rdp"
REMOTE_SSH="ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST"
REMOTE_DOCKER_COMPOSE_DIR="/home/$REMOTE_USER/webapp_components"
LOCAL_PROJECT_DIR="$(pwd)"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check SSH connection
check_ssh_connection() {
    print_status "Checking SSH connection to $REMOTE_USER@$REMOTE_HOST:$REMOTE_PORT..."
    if $REMOTE_SSH "echo 'SSH connection successful'" >/dev/null 2>&1; then
        print_success "SSH connection established"
        return 0
    else
        print_error "SSH connection failed. Please check your SSH configuration."
        return 1
    fi
}

# Function to check Docker on remote machine
check_remote_docker() {
    print_status "Checking Docker installation on remote machine..."
    if $REMOTE_SSH "docker --version" >/dev/null 2>&1; then
        print_success "Docker is installed on remote machine"
        return 0
    else
        print_error "Docker is not installed on remote machine"
        return 1
    fi
}

# Function to check Docker Compose on remote machine
check_remote_docker_compose() {
    print_status "Checking Docker Compose on remote machine..."
    if $REMOTE_SSH "docker-compose --version" >/dev/null 2>&1; then
        print_success "Docker Compose is installed on remote machine"
        return 0
    else
        print_error "Docker Compose is not installed on remote machine"
        return 1
    fi
}

# Function to create remote directory structure
setup_remote_directory() {
    print_status "Setting up remote directory structure..."
    
    $REMOTE_SSH "mkdir -p $REMOTE_DOCKER_COMPOSE_DIR" || {
        print_error "Failed to create remote directory"
        return 1
    }
    
    print_success "Remote directory created: $REMOTE_DOCKER_COMPOSE_DIR"
    return 0
}

# Function to copy project files to remote machine
copy_project_files() {
    print_status "Copying project files to remote machine..."
    
    # Create a temporary tar file
    local temp_tar="webapp_components_$(date +%Y%m%d_%H%M%S).tar.gz"
    
    print_status "Creating project archive..."
    tar --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='node_modules' \
        --exclude='.env' --exclude='*.log' --exclude='backup_*' \
        -czf "$temp_tar" . || {
        print_error "Failed to create project archive"
        return 1
    }
    
    print_status "Copying archive to remote machine..."
    scp -P "$REMOTE_PORT" "$temp_tar" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DOCKER_COMPOSE_DIR/" || {
        print_error "Failed to copy archive to remote machine"
        rm -f "$temp_tar"
        return 1
    }
    
    print_status "Extracting archive on remote machine..."
    $REMOTE_SSH "cd $REMOTE_DOCKER_COMPOSE_DIR && tar -xzf $temp_tar --strip-components=1 && rm $temp_tar" || {
        print_error "Failed to extract archive on remote machine"
        return 1
    }
    
    # Clean up local temp file
    rm -f "$temp_tar"
    
    print_success "Project files copied successfully"
    return 0
}

# Function to copy Docker images to remote machine
copy_docker_images() {
    print_status "Copying Docker images to remote machine..."
    
    # Save Docker images locally
    local image_tar="webapp_images_$(date +%Y%m%d_%H%M%S).tar"
    
    print_status "Saving Docker images..."
    docker-compose images -q | xargs docker save -o "$image_tar" || {
        print_error "Failed to save Docker images"
        return 1
    }
    
    print_status "Copying images to remote machine..."
    scp -P "$REMOTE_PORT" "$image_tar" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DOCKER_COMPOSE_DIR/" || {
        print_error "Failed to copy images to remote machine"
        rm -f "$image_tar"
        return 1
    }
    
    print_status "Loading images on remote machine..."
    $REMOTE_SSH "cd $REMOTE_DOCKER_COMPOSE_DIR && docker load -i $image_tar && rm $image_tar" || {
        print_error "Failed to load images on remote machine"
        return 1
    }
    
    # Clean up local temp file
    rm -f "$image_tar"
    
    print_success "Docker images copied successfully"
    return 0
}

# Function to deploy on remote machine
deploy_on_remote() {
    print_status "Deploying application on remote machine..."
    
    $REMOTE_SSH "cd $REMOTE_DOCKER_COMPOSE_DIR && docker-compose down" 2>/dev/null
    
    print_status "Starting application on remote machine..."
    $REMOTE_SSH "cd $REMOTE_DOCKER_COMPOSE_DIR && docker-compose up -d --build" || {
        print_error "Failed to start application on remote machine"
        return 1
    }
    
    print_status "Waiting for application to start..."
    sleep 10
    
    # Check if application is running
    if $REMOTE_SSH "cd $REMOTE_DOCKER_COMPOSE_DIR && docker-compose ps | grep -q 'Up'"; then
        print_success "Application deployed successfully on remote machine"
        return 0
    else
        print_error "Application failed to start on remote machine"
        return 1
    fi
}

# Function to get remote application URL
get_remote_url() {
    print_status "Getting remote application URL..."
    
    # Try to get the port from docker-compose.yml
    local port=$(grep -E "ports:" docker-compose.yml | grep -oE "[0-9]+:[0-9]+" | head -1 | cut -d: -f1)
    
    if [ -n "$port" ]; then
        echo "http://$REMOTE_HOST:$port"
    else
        echo "http://$REMOTE_HOST:6002"  # Default port
    fi
}

# Function to show deployment status
show_deployment_status() {
    print_status "Deployment Status:"
    echo "=================="
    echo "Remote Host: $REMOTE_HOST"
    echo "Remote Port: $REMOTE_PORT"
    echo "Remote User: $REMOTE_USER"
    echo "Remote Directory: $REMOTE_DOCKER_COMPOSE_DIR"
    echo "Application URL: $(get_remote_url)"
    echo ""
    
    print_status "Container Status on Remote Machine:"
    $REMOTE_SSH "cd $REMOTE_DOCKER_COMPOSE_DIR && docker-compose ps"
}

# Function to rollback deployment
rollback_deployment() {
    print_warning "Rolling back deployment..."
    
    $REMOTE_SSH "cd $REMOTE_DOCKER_COMPOSE_DIR && docker-compose down" 2>/dev/null
    $REMOTE_SSH "rm -rf $REMOTE_DOCKER_COMPOSE_DIR" 2>/dev/null
    
    print_success "Rollback completed"
}

# Main deployment function
deploy_to_remote() {
    print_status "Starting remote deployment process..."
    
    # Check prerequisites
    if ! check_ssh_connection; then
        return 1
    fi
    
    if ! check_remote_docker; then
        return 1
    fi
    
    if ! check_remote_docker_compose; then
        return 1
    fi
    
    # Setup and copy
    if ! setup_remote_directory; then
        rollback_deployment
        return 1
    fi
    
    if ! copy_project_files; then
        rollback_deployment
        return 1
    fi
    
    if ! copy_docker_images; then
        rollback_deployment
        return 1
    fi
    
    # Deploy
    if ! deploy_on_remote; then
        rollback_deployment
        return 1
    fi
    
    print_success "Remote deployment completed successfully!"
    show_deployment_status
    return 0
}

# Function to ask user for deployment confirmation
ask_deployment_confirmation() {
    echo ""
    echo "=========================================="
    echo "REMOTE DOCKER DEPLOYMENT"
    echo "=========================================="
    echo "This script will deploy your webapp_components"
    echo "to a remote machine via SSH."
    echo ""
    echo "Remote Configuration:"
    echo "- Host: $REMOTE_HOST"
    echo "- Port: $REMOTE_PORT"
    echo "- User: $REMOTE_USER"
    echo "- Directory: $REMOTE_DOCKER_COMPOSE_DIR"
    echo ""
    echo "The deployment will:"
    echo "1. Copy all project files to remote machine"
    echo "2. Copy Docker images to remote machine"
    echo "3. Start the application on remote machine"
    echo "4. Verify the deployment"
    echo ""
    
    read -p "Do you want to proceed with remote deployment? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        return 0
    else
        print_status "Deployment cancelled by user"
        return 1
    fi
}

# Function to configure remote settings
configure_remote_settings() {
    echo ""
    echo "=========================================="
    echo "REMOTE DEPLOYMENT CONFIGURATION"
    echo "=========================================="
    
    read -p "Remote host [$REMOTE_HOST]: " new_host
    if [ -n "$new_host" ]; then
        REMOTE_HOST="$new_host"
    fi
    
    read -p "Remote SSH port [$REMOTE_PORT]: " new_port
    if [ -n "$new_port" ]; then
        REMOTE_PORT="$new_port"
    fi
    
    read -p "Remote user [$REMOTE_USER]: " new_user
    if [ -n "$new_user" ]; then
        REMOTE_USER="$new_user"
    fi
    
    read -p "Remote directory [$REMOTE_DOCKER_COMPOSE_DIR]: " new_dir
    if [ -n "$new_dir" ]; then
        REMOTE_DOCKER_COMPOSE_DIR="$new_dir"
    fi
    
    # Update SSH command
    REMOTE_SSH="ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST"
    
    echo ""
    echo "Updated Configuration:"
    echo "- Host: $REMOTE_HOST"
    echo "- Port: $REMOTE_PORT"
    echo "- User: $REMOTE_USER"
    echo "- Directory: $REMOTE_DOCKER_COMPOSE_DIR"
    echo ""
}

# Main script execution
main() {
    echo "=========================================="
    echo "WEBAPP COMPONENTS - DEPLOYMENT SCRIPT"
    echo "=========================================="
    
    # Check if we're in the right directory
    if [ ! -f "docker-compose.yml" ]; then
        print_error "docker-compose.yml not found. Please run this script from the project root directory."
        exit 1
    fi
    
    # Check if Docker is running locally
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running locally. Please start Docker first."
        exit 1
    fi
    
    # Check if local application is running
    if docker-compose ps | grep -q "Up"; then
        print_warning "Local application is running. It's recommended to stop it before deployment."
        read -p "Stop local application before deployment? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_status "Stopping local application..."
            docker-compose down
        fi
    fi
    
    # Ask if user wants to configure remote settings
    read -p "Configure remote deployment settings? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        configure_remote_settings
    fi
    
    # Ask for deployment confirmation
    if ask_deployment_confirmation; then
        deploy_to_remote
        if [ $? -eq 0 ]; then
            print_success "Deployment completed successfully!"
            echo ""
            echo "Your application is now running at: $(get_remote_url)"
            echo ""
            echo "To check status: $REMOTE_SSH \"cd $REMOTE_DOCKER_COMPOSE_DIR && docker-compose ps\""
            echo "To view logs: $REMOTE_SSH \"cd $REMOTE_DOCKER_COMPOSE_DIR && docker-compose logs -f\""
            echo "To stop: $REMOTE_SSH \"cd $REMOTE_DOCKER_COMPOSE_DIR && docker-compose down\""
        else
            print_error "Deployment failed!"
            exit 1
        fi
    fi
}

# Run main function
main "$@" 