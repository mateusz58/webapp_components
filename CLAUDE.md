# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Application Management
- Start application: `./start.sh` or `./start.sh start`
- Stop application: `./start.sh stop`
- Restart application: `./start.sh restart` or `./restart.sh`
- Check status: `./start.sh status`

### Database Management
- Initialize database: `docker-compose exec app flask db init`
- Create migration: `docker-compose exec app flask db migrate -m "Migration description"`
- Apply migrations: `docker-compose exec app flask db upgrade`

### Docker Operations
- Build and run: `docker-compose up --build`
- Run in background: `docker-compose up -d --build`
- Stop containers: `docker-compose down`
- View logs: `docker-compose logs`

## Architecture Overview

### Core Structure
- **Flask Application**: Main web application using Flask framework
- **Database**: PostgreSQL with custom schema `component_app`
- **Containerization**: Docker-based deployment with docker-compose
- **Modular Design**: Blueprint-based routing with separation of concerns

### Key Components
- **Models**: SQLAlchemy models in `app/models.py` with custom schema support
- **Routes**: Multiple blueprint modules:
  - `app/routes.py` - Main legacy routes
  - `app/web/supplier_routes.py` - Supplier web interface
  - `app/api/supplier_api.py` - Supplier API endpoints
  - `app/brand_routes.py` - Brand management routes
- **Services**: Business logic in `app/services/`
- **Repositories**: Data access layer in `app/repositories/`

### Database Schema
- Uses PostgreSQL with custom schema `component_app`
- All models inherit from `Base` class which sets the schema
- Relationships include: Components, Suppliers, Categories, Colors, Materials, Pictures, Brands, Subbrands, Variants
- Association tables for many-to-many relationships (keywords, component-brand)

### File Structure Patterns
- Static files organized by type: `app/static/css/`, `app/static/js/`
- Templates use Jinja2 with base template inheritance
- Utilities split between `app/utils/` (new modular) and legacy files
- Migrations handled by Flask-Migrate in `component_app` schema

### Configuration
- Environment-based configuration in `config.py`
- Database connection points to external PostgreSQL server
- File uploads stored in `app/static/uploads/`
- Port 6002 for application access

### CSV Import System
- Bulk operations via CSV with semicolon delimiter
- Supports component and picture data import
- Processing handled by `app/services/csv_service.py`

## Important Notes
- Database uses custom schema `component_app` - ensure all models inherit from `Base`
- File uploads limited to 16MB with thumbnail generation
- Application runs on port 6002 by default
- Uses external PostgreSQL database, not containerized