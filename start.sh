#!/bin/bash

# Set variables
APP_NAME="component_app"
APP_PORT=6002
CONTAINER_NAME="component_app"

# Remote deployment configuration (will be set interactively)
REMOTE_HOST=""
REMOTE_PORT=""
REMOTE_USER=""
REMOTE_SSH=""
REMOTE_SCP=""
REMOTE_DOCKER_COMPOSE_DIR=""

# Color definitions
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print banner
echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}   Component Management System Tool    ${NC}"
echo -e "${BLUE}=======================================${NC}"

# Function to check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}Docker Compose is not installed. Please install Docker Compose first.${NC}"
        exit 1
    fi
}

# Function to stop any process using the app port
stop_port_usage() {
    PORT_CHECK=$(lsof -i:${APP_PORT} | grep LISTEN)
    if [ ! -z "$PORT_CHECK" ]; then
        echo -e "${YELLOW}Port ${APP_PORT} is in use.${NC}"
        echo -e "Running process: ${PORT_CHECK}"
        
        # Check if it's our Docker container
        DOCKER_PORT_CHECK=$(docker ps | grep ${APP_PORT})
        if [ ! -z "$DOCKER_PORT_CHECK" ]; then
            echo -e "${YELLOW}Found Docker container using port ${APP_PORT}. Stopping...${NC}"
            docker stop $(echo "$DOCKER_PORT_CHECK" | awk '{print $1}')
            return 0
        fi
        
        # Otherwise ask to stop the process
        echo -e "${YELLOW}Would you like to stop the process using port ${APP_PORT}? (y/n)${NC}"
        read -r answer
        if [ "$answer" = "y" ]; then
            echo "Attempting to free up port ${APP_PORT}..."
            PID=$(echo "$PORT_CHECK" | awk '{print $2}')
            kill -9 "$PID" 2>/dev/null || sudo kill -9 "$PID" || echo -e "${RED}Failed to kill process.${NC}"
        else
            echo "Cannot continue with port ${APP_PORT} in use. Exiting..."
            exit 1
        fi
    fi
}

# Function to start the application
start_app() {
    echo -e "${GREEN}Starting Component Management System...${NC}"
    docker-compose up -d --build
    
    # Wait for the application to start
    echo -e "Waiting for application to start..."
    for i in {1..30}; do
        if curl -s http://localhost:${APP_PORT} > /dev/null; then
            echo -e "${GREEN}Application is up and running!${NC}"
            echo -e "${GREEN}You can access it at:${NC} http://localhost:${APP_PORT}"
            break
        fi
        echo -n "."
        sleep 1
        if [ $i -eq 30 ]; then
            echo -e "\n${YELLOW}Application might not be fully started. Please check logs:${NC}"
            echo -e "  docker-compose logs"
        fi
    done
    
    # Output container status
    echo -e "\n${GREEN}Container status:${NC}"
    docker ps | grep ${APP_NAME}
}

# Function to stop the application
stop_app() {
    echo -e "${YELLOW}Stopping Component Management System...${NC}"
    docker-compose down
    
    # Check for any remaining containers
    REMAINING=$(docker ps -a | grep ${APP_NAME})
    if [ ! -z "$REMAINING" ]; then
        echo -e "${YELLOW}Found remaining containers. Removing...${NC}"
        docker rm -f $(docker ps -a | grep ${APP_NAME} | awk '{print $1}') 2>/dev/null || true
    fi
    
    echo -e "${GREEN}Application stopped successfully.${NC}"
}

# Function to restart the application
restart_app() {
    echo -e "${YELLOW}Restarting Component Management System...${NC}"
    stop_app
    start_app
}

# Function to show application status
show_status() {
    echo -e "${BLUE}Application Status:${NC}"
    
    # Check if container is running
    if docker ps | grep -q ${CONTAINER_NAME}; then
        echo -e "${GREEN}Container Status: Running${NC}"
        docker ps | grep ${CONTAINER_NAME}
    else
        echo -e "${YELLOW}Container Status: Not Running${NC}"
    fi
    
    # Check if port is in use
    PORT_CHECK=$(lsof -i:${APP_PORT} | grep LISTEN)
    if [ ! -z "$PORT_CHECK" ]; then
        echo -e "${GREEN}Port ${APP_PORT}: In Use${NC}"
        echo -e "$PORT_CHECK"
    else
        echo -e "${YELLOW}Port ${APP_PORT}: Available${NC}"
    fi
}

# Function to get remote deployment configuration
get_remote_config() {
    echo -e "${BLUE}Remote Deployment Configuration${NC}"
    echo -e "Please provide the remote server details:"
    echo ""
    
    # Get remote host
    while [ -z "$REMOTE_HOST" ]; do
        read -p "Remote Host IP/Hostname: " REMOTE_HOST
        if [ -z "$REMOTE_HOST" ]; then
            echo -e "${RED}Host cannot be empty. Please enter a valid IP address or hostname.${NC}"
        fi
    done
    
    # Get remote port (default 22)
    read -p "SSH Port (default: 22): " REMOTE_PORT
    if [ -z "$REMOTE_PORT" ]; then
        REMOTE_PORT="22"
    fi
    
    # Get remote user
    while [ -z "$REMOTE_USER" ]; do
        read -p "Remote Username: " REMOTE_USER
        if [ -z "$REMOTE_USER" ]; then
            echo -e "${RED}Username cannot be empty.${NC}"
        fi
    done
    
    # Set remote directory
    REMOTE_DOCKER_COMPOSE_DIR="/home/$REMOTE_USER/webapp_components"
    read -p "Remote Directory (default: $REMOTE_DOCKER_COMPOSE_DIR): " custom_dir
    if [ ! -z "$custom_dir" ]; then
        REMOTE_DOCKER_COMPOSE_DIR="$custom_dir"
    fi
    
    # Set SSH commands with password authentication preference
    REMOTE_SSH="ssh -o ConnectTimeout=15 -o StrictHostKeyChecking=no -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST"
    REMOTE_SCP="scp -o ConnectTimeout=15 -o StrictHostKeyChecking=no -P $REMOTE_PORT"
    
    echo ""
    echo -e "${GREEN}Configuration Summary:${NC}"
    echo -e "Host: $REMOTE_HOST"
    echo -e "Port: $REMOTE_PORT"
    echo -e "User: $REMOTE_USER"
    echo -e "Directory: $REMOTE_DOCKER_COMPOSE_DIR"
    echo ""
}

# Function to check SSH connection
check_ssh_connection() {
    echo -e "${BLUE}Testing SSH connection to $REMOTE_USER@$REMOTE_HOST:$REMOTE_PORT...${NC}"
    
    # First check if host is reachable
    echo -e "${BLUE}Checking if host is reachable...${NC}"
    if ! ping -c 1 -W 3 "$REMOTE_HOST" >/dev/null 2>&1; then
        echo -e "${RED}Warning: Host $REMOTE_HOST is not responding to ping${NC}"
        echo -e "${YELLOW}This might be normal if ICMP is disabled, continuing with SSH test...${NC}"
    else
        echo -e "${GREEN}Host is reachable${NC}"
    fi
    
    # Try SSH connection with password authentication
    echo -e "${BLUE}Testing SSH connection (you will be prompted for password)...${NC}"
    if ssh -o ConnectTimeout=15 -o StrictHostKeyChecking=no -o BatchMode=no -p "$REMOTE_PORT" "$REMOTE_USER@$REMOTE_HOST" "echo 'SSH connection successful'"; then
        echo -e "${GREEN}SSH connection established successfully${NC}"
        return 0
    else
        echo -e "${RED}SSH connection failed.${NC}"
        echo -e "${YELLOW}Please check:${NC}"
        echo -e "  1. Remote host is accessible: $REMOTE_HOST"
        echo -e "  2. SSH service is running on port $REMOTE_PORT"
        echo -e "  3. Username '$REMOTE_USER' exists on remote machine"
        echo -e "  4. Password is correct"
        echo -e "  5. SSH is not blocked by firewall"
        return 1
    fi
}

# Function to setup SSH key authentication for passwordless deployment
setup_ssh_keys() {
    echo -e "${BLUE}Setting up SSH key authentication for passwordless deployment...${NC}"
    
    # Check if SSH key exists
    if [ ! -f ~/.ssh/id_rsa ]; then
        echo -e "${BLUE}Generating SSH key for passwordless authentication...${NC}"
        ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N "" -q || {
            echo -e "${RED}Failed to generate SSH key${NC}"
            return 1
        }
        echo -e "${GREEN}SSH key generated successfully${NC}"
    fi
    
    # Test if key authentication already works
    echo -e "${BLUE}Testing if SSH key is already authorized...${NC}"
    if ssh -o ConnectTimeout=15 -o StrictHostKeyChecking=no -o PreferredAuthentications=publickey -o PasswordAuthentication=no -p "$REMOTE_PORT" "$REMOTE_USER@$REMOTE_HOST" "echo 'SSH key test successful'" 2>/dev/null; then
        echo -e "${GREEN}SSH key authentication is already working${NC}"
        # Update SSH commands to use key authentication
        REMOTE_SSH="ssh -o ConnectTimeout=15 -o StrictHostKeyChecking=no -o PreferredAuthentications=publickey -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST"
        REMOTE_SCP="scp -o ConnectTimeout=15 -o StrictHostKeyChecking=no -o PreferredAuthentications=publickey -P $REMOTE_PORT"
        return 0
    fi
    
    # Key authentication not working, copy the key (this will ask for password once)
    echo -e "${BLUE}Copying SSH key to remote machine...${NC}"
    echo -e "${YELLOW}You will be prompted for your password ONCE to set up passwordless authentication.${NC}"
    echo -e "${YELLOW}After this, the deployment will proceed without further password prompts.${NC}"
    
    if ssh-copy-id -o ConnectTimeout=15 -o StrictHostKeyChecking=no -p "$REMOTE_PORT" "$REMOTE_USER@$REMOTE_HOST" 2>/dev/null; then
        echo -e "${GREEN}SSH key copied successfully${NC}"
        # Update SSH commands to use key authentication
        REMOTE_SSH="ssh -o ConnectTimeout=15 -o StrictHostKeyChecking=no -o PreferredAuthentications=publickey -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST"
        REMOTE_SCP="scp -o ConnectTimeout=15 -o StrictHostKeyChecking=no -o PreferredAuthentications=publickey -P $REMOTE_PORT"
        
        # Verify key authentication is working
        if ssh -o ConnectTimeout=15 -o StrictHostKeyChecking=no -o PreferredAuthentications=publickey -o PasswordAuthentication=no -p "$REMOTE_PORT" "$REMOTE_USER@$REMOTE_HOST" "echo 'SSH key verification successful'" 2>/dev/null; then
            echo -e "${GREEN}Passwordless SSH authentication is now active${NC}"
            return 0
        else
            echo -e "${RED}SSH key setup verification failed${NC}"
            return 1
        fi
    else
        echo -e "${RED}Failed to copy SSH key${NC}"
        echo -e "${YELLOW}Deployment will use password authentication (multiple prompts)${NC}"
        return 1
    fi
}

# Function to check Docker on remote machine
check_remote_docker() {
    echo -e "${BLUE}Checking Docker installation on remote machine...${NC}"
    
    # Check if Docker is installed
    if ! $REMOTE_SSH "which docker" >/dev/null 2>&1; then
        echo -e "${RED}Docker is not installed on remote machine${NC}"
        echo -e "${YELLOW}Please install Docker on the remote machine first${NC}"
        return 1
    fi
    
    # Check Docker version
    docker_version=$($REMOTE_SSH "docker --version" 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Docker is installed: $docker_version${NC}"
    else
        echo -e "${RED}Docker is installed but not accessible. Check if user '$REMOTE_USER' is in docker group${NC}"
        echo -e "${YELLOW}Run on remote machine: sudo usermod -aG docker $REMOTE_USER${NC}"
        return 1
    fi
    
    # Check if Docker daemon is running
    if ! $REMOTE_SSH "docker info" >/dev/null 2>&1; then
        echo -e "${RED}Docker daemon is not running on remote machine${NC}"
        echo -e "${YELLOW}Start Docker on remote machine: sudo systemctl start docker${NC}"
        return 1
    fi
    
    return 0
}

# Function to check Docker Compose on remote machine
check_remote_docker_compose() {
    echo -e "${BLUE}Checking Docker Compose on remote machine...${NC}"
    
    # Check for docker-compose command
    if $REMOTE_SSH "docker-compose --version" >/dev/null 2>&1; then
        compose_version=$($REMOTE_SSH "docker-compose --version" 2>/dev/null)
        echo -e "${GREEN}Docker Compose is installed: $compose_version${NC}"
        return 0
    fi
    
    # Check for docker compose plugin
    if $REMOTE_SSH "docker compose version" >/dev/null 2>&1; then
        compose_version=$($REMOTE_SSH "docker compose version" 2>/dev/null)
        echo -e "${GREEN}Docker Compose plugin is installed: $compose_version${NC}"
        # Update commands to use the plugin syntax
        export DOCKER_COMPOSE_CMD="docker compose"
        return 0
    fi
    
    echo -e "${RED}Docker Compose is not installed on remote machine${NC}"
    echo -e "${YELLOW}Install Docker Compose on remote machine${NC}"
    return 1
}

# Function to copy project files to remote machine
copy_project_files() {
    echo -e "${BLUE}Copying project files to remote machine...${NC}"
    
    # Debug: Show current directory and check for required files
    echo -e "${BLUE}Current directory: $(pwd)${NC}"
    echo -e "${BLUE}Checking for docker-compose.yml...${NC}"
    if [ ! -f "docker-compose.yml" ]; then
        echo -e "${RED}docker-compose.yml not found in current directory${NC}"
        echo -e "${YELLOW}Available files:${NC}"
        ls -la
        return 1
    fi
    
    # Create a temporary tar file
    local temp_tar="webapp_components_$(date +%Y%m%d_%H%M%S).tar.gz"
    
    echo -e "${BLUE}Creating project archive: $temp_tar${NC}"
    
    # Create archive with proper exclusions and error handling
    echo -e "${BLUE}Creating tar archive with exclusions...${NC}"
    
    # Create a temporary exclude file
    local exclude_file=$(mktemp)
    cat > "$exclude_file" << 'EOF'
.git
__pycache__
*.pyc
node_modules
.env
*.log
backup_*
*.tar.gz
*.tar
.DS_Store
Thumbs.db
app/static/uploads/*
migrations/versions/*.py
*.tmp
*.temp
EOF
    
    # Test if tar command works at all
    echo -e "${BLUE}Testing tar command...${NC}"
    if ! tar --version >/dev/null 2>&1; then
        echo -e "${RED}tar command not available${NC}"
        rm -f "$exclude_file"
        return 1
    fi
    
    # Create the archive
    echo -e "${BLUE}Creating archive with exclude file...${NC}"
    if tar -czf "$temp_tar" --exclude-from="$exclude_file" . 2>&1; then
        echo -e "${GREEN}Archive created successfully with exclude file${NC}"
    else
        echo -e "${YELLOW}Exclude file method failed, trying individual excludes...${NC}"
        
        # Alternative method without exclude file
        if tar -czf "$temp_tar" --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='node_modules' --exclude='.env' --exclude='*.log' --exclude='*.tar.gz' --exclude='*.tar' . 2>&1; then
            echo -e "${GREEN}Archive created successfully with individual excludes${NC}"
        else
            echo -e "${YELLOW}Both methods failed, trying basic tar...${NC}"
            
            # Most basic tar command as last resort
            if tar -czf "$temp_tar" . 2>&1; then
                echo -e "${GREEN}Archive created with basic tar (no excludes)${NC}"
            else
                echo -e "${RED}Failed to create archive with all methods${NC}"
                echo -e "${YELLOW}Disk space check:${NC}"
                df -h .
                echo -e "${YELLOW}Directory contents:${NC}"
                ls -la
                rm -f "$exclude_file"
                return 1
            fi
        fi
    fi
    
    # Clean up exclude file
    rm -f "$exclude_file"
    
    # Check if archive was created successfully
    if [ ! -f "$temp_tar" ] || [ ! -s "$temp_tar" ]; then
        echo -e "${RED}Archive creation failed or archive is empty${NC}"
        rm -f "$temp_tar"
        return 1
    fi
    
    echo -e "${BLUE}Copying archive to remote machine...${NC}"
    if ! $REMOTE_SCP "$temp_tar" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DOCKER_COMPOSE_DIR/"; then
        echo -e "${RED}Failed to copy archive to remote machine${NC}"
        echo -e "${YELLOW}Troubleshooting steps:${NC}"
        echo -e "  1. Check if remote directory exists: $REMOTE_DOCKER_COMPOSE_DIR"
        echo -e "  2. Check disk space on remote machine"
        echo -e "  3. Verify SSH connection and permissions"
        rm -f "$temp_tar"
        return 1
    fi
    
    echo -e "${BLUE}Extracting archive on remote machine...${NC}"
    if ! $REMOTE_SSH "cd $REMOTE_DOCKER_COMPOSE_DIR && tar -xzf $temp_tar --strip-components=1 && rm $temp_tar"; then
        echo -e "${RED}Failed to extract archive on remote machine${NC}"
        echo -e "${YELLOW}Troubleshooting steps:${NC}"
        echo -e "  1. Check if tar command is available on remote machine"
        echo -e "  2. Check if archive file was copied successfully"
        echo -e "  3. Check permissions on remote directory"
        return 1
    fi
    
    # Clean up local temp file
    rm -f "$temp_tar"
    
    echo -e "${GREEN}Project files copied successfully${NC}"
    return 0
}

# Function to copy Docker images to remote machine
copy_docker_images() {
    echo -e "${BLUE}Copying Docker images to remote machine...${NC}"
    
    # Save Docker images locally
    local image_tar="webapp_images_$(date +%Y%m%d_%H%M%S).tar"
    
    echo -e "${BLUE}Saving Docker images...${NC}"
    docker-compose images -q | xargs docker save -o "$image_tar" || {
        echo -e "${RED}Failed to save Docker images${NC}"
        return 1
    }
    
    echo -e "${BLUE}Copying images to remote machine (this may take a while)...${NC}"
    if ! $REMOTE_SCP "$image_tar" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DOCKER_COMPOSE_DIR/"; then
        echo -e "${RED}Failed to copy images to remote machine${NC}"
        echo -e "${YELLOW}This might be due to large file size or network issues${NC}"
        rm -f "$image_tar"
        return 1
    fi
    
    echo -e "${BLUE}Loading images on remote machine...${NC}"
    if ! $REMOTE_SSH "cd $REMOTE_DOCKER_COMPOSE_DIR && docker load -i $image_tar && rm $image_tar"; then
        echo -e "${RED}Failed to load images on remote machine${NC}"
        echo -e "${YELLOW}Check if Docker daemon is running and has sufficient disk space${NC}"
        return 1
    fi
    
    # Clean up local temp file
    rm -f "$image_tar"
    
    echo -e "${GREEN}Docker images copied successfully${NC}"
    return 0
}

# Function to deploy on remote machine
deploy_on_remote() {
    echo -e "${BLUE}Deploying application on remote machine...${NC}"
    
    # Set the docker-compose command based on what's available
    local compose_cmd="docker-compose"
    if [ "${DOCKER_COMPOSE_CMD}" ]; then
        compose_cmd="${DOCKER_COMPOSE_CMD}"
    fi
    
    # Stop and clean up any existing containers
    echo -e "${BLUE}Cleaning up existing containers...${NC}"
    
    # First try graceful shutdown
    $REMOTE_SSH "cd $REMOTE_DOCKER_COMPOSE_DIR && $compose_cmd down" 2>/dev/null || true
    
    # Check if container with the same name exists and remove it
    container_check=$($REMOTE_SSH "docker ps -a --filter name=component_app --format '{{.Names}}'" 2>/dev/null || echo "")
    if [ -n "$container_check" ]; then
        echo -e "${YELLOW}Found existing container(s) with name 'component_app': $container_check${NC}"
        echo -e "${YELLOW}This will prevent deployment. Do you want to remove the existing container(s)? (Y/n)${NC}"
        read -p "Remove existing containers? [Y/n]: " -r
        echo
        if [[ $REPLY =~ ^[Nn]$ ]]; then
            echo -e "${RED}Deployment cancelled. Please remove existing containers manually or choose a different container name.${NC}"
            echo -e "${YELLOW}Manual cleanup commands:${NC}"
            echo -e "  $REMOTE_SSH \"docker rm -f component_app\""
            echo -e "  $REMOTE_SSH \"docker system prune -f\""
            return 1
        else
            echo -e "${BLUE}Removing existing containers...${NC}"
            
            # Try multiple methods to remove the container
            if $REMOTE_SSH "docker rm -f component_app" 2>/dev/null; then
                echo -e "${GREEN}Container 'component_app' removed successfully${NC}"
            elif $REMOTE_SSH "docker rm -f \$(docker ps -a --filter name=component_app -q)" 2>/dev/null; then
                echo -e "${GREEN}Container(s) removed by filter${NC}"
            else
                echo -e "${RED}Failed to remove existing containers${NC}"
                echo -e "${YELLOW}Manual cleanup required on remote machine:${NC}"
                echo -e "  docker rm -f component_app"
                echo -e "  docker system prune -f"
                return 1
            fi
        fi
    fi
    
    # Also clean up any orphaned containers
    echo -e "${BLUE}Removing any orphaned containers...${NC}"
    $REMOTE_SSH "cd $REMOTE_DOCKER_COMPOSE_DIR && $compose_cmd down --remove-orphans" 2>/dev/null || true
    
    # Start the application
    echo -e "${BLUE}Starting application on remote machine...${NC}"
    if ! $REMOTE_SSH "cd $REMOTE_DOCKER_COMPOSE_DIR && $compose_cmd up -d --build"; then
        echo -e "${RED}Failed to start application on remote machine${NC}"
        
        # Check for specific container conflicts
        conflict_check=$($REMOTE_SSH "docker ps -a --filter name=component_app --format '{{.Names}} {{.Status}}'" 2>/dev/null || echo "")
        if [ -n "$conflict_check" ]; then
            echo -e "${YELLOW}Container conflict detected:${NC}"
            echo -e "$conflict_check"
            echo -e "${YELLOW}Try running the deployment again to handle container cleanup${NC}"
        fi
        
        echo -e "${YELLOW}Checking logs for errors...${NC}"
        $REMOTE_SSH "cd $REMOTE_DOCKER_COMPOSE_DIR && $compose_cmd logs --tail=10" 2>/dev/null || true
        
        echo -e "${YELLOW}Container status:${NC}"
        $REMOTE_SSH "cd $REMOTE_DOCKER_COMPOSE_DIR && $compose_cmd ps -a" 2>/dev/null || true
        
        return 1
    fi
    
    echo -e "${BLUE}Waiting for application to start...${NC}"
    local wait_time=0
    local max_wait=60
    
    while [ $wait_time -lt $max_wait ]; do
        if $REMOTE_SSH "cd $REMOTE_DOCKER_COMPOSE_DIR && $compose_cmd ps | grep -q 'Up'"; then
            echo -e "${GREEN}Application deployed successfully on remote machine${NC}"
            
            # Show container status
            echo -e "${BLUE}Container status:${NC}"
            $REMOTE_SSH "cd $REMOTE_DOCKER_COMPOSE_DIR && $compose_cmd ps"
            return 0
        fi
        
        echo -n "."
        sleep 5
        wait_time=$((wait_time + 5))
    done
    
    echo -e "\n${RED}Application failed to start within $max_wait seconds${NC}"
    echo -e "${YELLOW}Container status:${NC}"
    $REMOTE_SSH "cd $REMOTE_DOCKER_COMPOSE_DIR && $compose_cmd ps" || true
    echo -e "${YELLOW}Recent logs:${NC}"
    $REMOTE_SSH "cd $REMOTE_DOCKER_COMPOSE_DIR && $compose_cmd logs --tail=20" || true
    return 1
}

# Function to get remote application URL
get_remote_url() {
    # Try to get the port from docker-compose.yml
    local port=$(grep -E "ports:" docker-compose.yml | grep -oE "[0-9]+:[0-9]+" | head -1 | cut -d: -f1)
    
    if [ -n "$port" ]; then
        echo "http://$REMOTE_HOST:$port"
    else
        echo "http://$REMOTE_HOST:6002"  # Default port
    fi
}

# Function to ask for remote deployment
ask_remote_deployment() {
    echo ""
    echo -e "${BLUE}==========================================${NC}"
    echo -e "${BLUE}REMOTE DEPLOYMENT OPTION${NC}"
    echo -e "${BLUE}==========================================${NC}"
    echo -e "Your local application is now running at: http://localhost:${APP_PORT}"
    echo ""
    echo -e "Would you like to also deploy this application to a remote machine?"
    echo ""
    echo -e "The deployment will:"
    echo -e "1. Copy all project files to remote machine"
    echo -e "2. Copy Docker images to remote machine"
    echo -e "3. Start the application on remote machine"
    echo ""
    
    read -p "Deploy to remote machine? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}Starting remote deployment...${NC}"
        
        # Get remote configuration from user
        get_remote_config
        
        # Check prerequisites
        if ! check_ssh_connection; then
            echo -e "${RED}Remote deployment failed due to SSH connection issues.${NC}"
            echo -e "${YELLOW}Please verify your connection details and try again.${NC}"
            return 1
        fi
        
        if ! check_remote_docker; then
            echo -e "${RED}Remote deployment failed - Docker not installed on remote machine.${NC}"
            return 1
        fi
        
        if ! check_remote_docker_compose; then
            echo -e "${RED}Remote deployment failed - Docker Compose not installed on remote machine.${NC}"
            return 1
        fi
        
        # Check for existing containers before starting deployment
        echo -e "${BLUE}Checking for existing containers on remote machine...${NC}"
        existing_containers=$($REMOTE_SSH "docker ps -a --filter name=component_app --format '{{.Names}} ({{.Status}})'" 2>/dev/null || echo "")
        if [ -n "$existing_containers" ]; then
            echo -e "${YELLOW}Found existing containers that may conflict:${NC}"
            echo -e "$existing_containers"
            echo -e "${YELLOW}These will be handled during deployment.${NC}"
            echo ""
        fi
        
        # Setup SSH keys for passwordless deployment
        if ! setup_ssh_keys; then
            echo -e "${YELLOW}SSH key setup failed, deployment will use password authentication${NC}"
        fi
        
        # Setup remote directory
        echo -e "${BLUE}Setting up remote directory...${NC}"
        $REMOTE_SSH "mkdir -p $REMOTE_DOCKER_COMPOSE_DIR" || {
            echo -e "${RED}Failed to create remote directory${NC}"
            return 1
        }
        
        # Copy files and deploy
        if copy_project_files && copy_docker_images && deploy_on_remote; then
            echo -e "${GREEN}Remote deployment completed successfully!${NC}"
            echo -e "${GREEN}Your application is now running at: $(get_remote_url)${NC}"
            echo ""
            echo -e "${BLUE}Remote management commands:${NC}"
            echo -e "Check status: $REMOTE_SSH \"cd $REMOTE_DOCKER_COMPOSE_DIR && docker-compose ps\""
            echo -e "View logs: $REMOTE_SSH \"cd $REMOTE_DOCKER_COMPOSE_DIR && docker-compose logs -f\""
            echo -e "Stop: $REMOTE_SSH \"cd $REMOTE_DOCKER_COMPOSE_DIR && docker-compose down\""
            return 0
        else
            echo -e "${RED}Remote deployment failed!${NC}"
            return 1
        fi
    else
        echo -e "${BLUE}Remote deployment skipped.${NC}"
        return 0
    fi
}

# Function to display help
show_help() {
    echo -e "${BLUE}Component Management System - Help${NC}"
    echo -e "Usage: $0 [command]"
    echo -e ""
    echo -e "Commands:"
    echo -e "  start      Start the application"
    echo -e "  stop       Stop the application"
    echo -e "  restart    Restart the application"
    echo -e "  status     Show application status"
    echo -e "  help       Show this help message"
    echo -e ""
    echo -e "If no command is provided, the script will attempt to start the application."
    echo -e ""
    echo -e "Remote Deployment:"
    echo -e "  After starting the application, you'll be asked if you want to"
    echo -e "  deploy it to a remote machine via SSH."
}

# Main script logic
check_docker

# Process command line arguments
case "$1" in
    start)
        stop_port_usage
        start_app
        ask_remote_deployment
        ;;
    stop)
        stop_app
        ;;
    restart)
        restart_app
        ask_remote_deployment
        ;;
    status)
        show_status
        ;;
    help)
        show_help
        ;;
    *)
        # Default behavior: check if app is running, if yes restart, if not start
        if docker ps | grep -q ${CONTAINER_NAME}; then
            echo -e "${YELLOW}Application is already running. Restarting...${NC}"
            restart_app
            ask_remote_deployment
        else
            stop_port_usage
            start_app
            ask_remote_deployment
        fi
        ;;
esac

echo -e "\n${BLUE}=======================================${NC}"
echo -e "${BLUE}   Commands:                           ${NC}"
echo -e "${BLUE}   - Start:    ./$(basename $0) start    ${NC}"
echo -e "${BLUE}   - Stop:     ./$(basename $0) stop     ${NC}"
echo -e "${BLUE}   - Restart:  ./$(basename $0) restart  ${NC}"
echo -e "${BLUE}   - Status:   ./$(basename $0) status   ${NC}"
echo -e "${BLUE}=======================================${NC}"
