# Component Management System

A simple web application for managing component inventory with PostgreSQL database backend, containerized with Docker.

## Project Structure

```
project-root/
├── app/                      # Application code
│   ├── static/               # Static files (CSS, JS)
│   ├── templates/            # HTML templates
│   ├── __init__.py           # App initialization
│   ├── models.py             # Database models
│   ├── routes.py             # Route handlers
│   └── utils.py              # Utility functions
├── docker/                   # Docker configuration
│   └── app/
│       └── Dockerfile        # Python app Dockerfile
├── docker-compose.yml        # Docker Compose config
├── requirements.txt          # Python dependencies
├── config.py                 # App configuration
└── run.py                    # Application entry point
```

## Features

* List, view, add, edit, and delete components
* Filter components by various criteria
* Upload and process CSV for bulk operations
* Component pictures management (up to 5 per component)
* Supplier management

## Prerequisites

* Docker and Docker Compose installed on your system
* No other dependencies required locally

## Getting Started

1. Clone or download this repository to your local machine.

2. Create the required directory structure:

```
mkdir -p app/static/css app/static/uploads app/templates docker/app
```

3. Place all the files in their respective directories as shown in the project structure.

4. Build and start the application:

```bash
docker-compose up --build
```

5. Once the services are running, access the application:
   - Web interface: http://localhost:5000
   - PostgreSQL database: localhost:5432 (user: postgres, password: postgres, database: components_db)

6. Initialize the database (first-time setup):

```bash
# In another terminal, run:
docker-compose exec app flask db init
docker-compose exec app flask db migrate -m "Initial migration"
docker-compose exec app flask db upgrade
```

## CSV Bulk Upload Format

The system supports bulk upload and updates via CSV files. The CSV should:

- Use semicolon (;) as delimiter
- Include headers in the first row
- Follow this structure:

```
product_number;description;supplier_code;category_name;color_name;material_name;picture_1_name;picture_1_url;picture_1_order;picture_2_name;picture_2_url;picture_2_order;...
```

Example:
```
product_number;description;supplier_code;category_name;color_name;material_name;picture_1_name;picture_1_url;picture_1_order;picture_2_name;picture_2_url;picture_2_order;picture_3_name;picture_3_url;picture_3_order;picture_4_name;picture_4_url;picture_4_order;picture_5_name;picture_5_url;picture_5_order
ABC123;High quality resistor;SUPP001;Electronics;Black;Silicon;front_view.jpg;http://example.com/images/front_view.jpg;1;side_view.jpg;http://example.com/images/side_view.jpg;2;diagram.jpg;http://example.com/images/diagram.jpg;3;;;;;;;
XYZ456;Capacitor 1000uF;SUPP002;Electronic Parts;Blue;Ceramic;main.jpg;http://example.com/images/main.jpg;1;;;;;;;;;;;;;
```

## Stopping the Application

To stop the application:

```bash
# If running in foreground (with logs showing)
# Press Ctrl+C

# Or to stop in background mode
docker-compose down
```

## Data Persistence

The PostgreSQL data is stored in a named volume `postgres_data`. This ensures your data persists between container restarts.

To completely remove all data and start fresh:

```bash
docker-compose down -v
```
