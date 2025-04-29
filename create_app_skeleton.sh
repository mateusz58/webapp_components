#!/bin/bash
set -e

# ANSI color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================${NC}"
echo -e "${GREEN}Component Management System Setup${NC}"
echo -e "${BLUE}=================================${NC}"
echo "This script will create the project structure and empty files."

# Create project structure
echo -e "\n${BLUE}Creating project structure...${NC}"

# Create directories
mkdir -p app/static/css app/static/uploads app/templates docker/app migrations

# Create configuration files (empty)
echo -e "\n${BLUE}Creating empty configuration files...${NC}"
touch docker-compose.yml
touch docker/app/Dockerfile
touch docker/app/init.sh
chmod +x docker/app/init.sh
touch requirements.txt
touch config.py
touch run.py

# Create app files (empty)
echo -e "\n${BLUE}Creating empty application files...${NC}"
touch app/__init__.py
touch app/models.py
touch app/routes.py
touch app/utils.py

# Create CSS file (empty)
touch app/static/css/style.css

# Create HTML Templates (empty)
echo -e "\n${BLUE}Creating empty HTML templates...${NC}"
touch app/templates/base.html
touch app/templates/index.html
touch app/templates/component_detail.html
touch app/templates/component_form.html
touch app/templates/component_edit_form.html
touch app/templates/upload.html
touch app/templates/csv_template.html
touch app/templates/suppliers.html
touch app/templates/supplier_form.html

# Create README.md (empty)
touch README.md

echo -e "\n${GREEN}Project structure created successfully!${NC}"
echo -e "The following structure has been created:\n"
find . -type d -not -path "*/\.*" | sort
echo -e "\nYou can now add content to these files."
