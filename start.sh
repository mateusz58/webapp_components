#!/bin/bash

# Set variables
APP_NAME="component_app"
APP_PORT=6002
CONTAINER_NAME="component_app"

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
}

# Main script logic
check_docker

# Process command line arguments
case "$1" in
    start)
        stop_port_usage
        start_app
        ;;
    stop)
        stop_app
        ;;
    restart)
        restart_app
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
        else
            stop_port_usage
            start_app
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
