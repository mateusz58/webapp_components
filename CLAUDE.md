# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Component Management System - Architecture Summary

This is a comprehensive Flask-based web application for managing manufacturing components, their variants, suppliers, brands, and associated pictures. The system supports complex component lifecycle management with approval workflows.

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
- **Flask Application**: Main web application using Flask framework with Blueprint architecture
- **Database**: PostgreSQL with custom schema `component_app` 
- **Containerization**: Docker-based deployment with docker-compose
- **Modular Design**: Blueprint-based routing with separation of concerns

### Application Structure

#### Flask App Initialization (`app/__init__.py`)
- Factory pattern with `create_app()` function
- SQLAlchemy with custom schema support (`component_app`)
- Flask-Migrate for database migrations
- Blueprint registration for modular routing
- Custom Jinja2 filters and template functions
- File upload directory management

#### Database Models (`app/models.py`)
**Core Models:**
- `Component` - Main product entity with flexible JSON properties
- `ComponentVariant` - Color variants of components with auto-generated SKUs
- `ComponentType` - Categories of components (with dynamic properties)
- `Supplier` - Supplier management
- `Brand`/`Subbrand` - Brand hierarchy
- `Category`, `Color`, `Material` - Reference data
- `Picture` - Image management with automatic naming
- `Keyword` - Tagging system

**Key Features:**
- Auto-generated SKUs and picture names via database triggers
- Complex approval workflow (Proto → SMS → PPS status tracking)
- JSON properties for flexible component attributes
- Automatic timestamp management via database triggers
- Many-to-many relationships (component-brand, component-keyword)

#### Routing Architecture
- **Main Routes** (`app/routes.py`): Legacy main application routes
- **Supplier Routes** (`app/web/supplier_routes.py`): Web interface for supplier management
- **Supplier API** (`app/api/supplier_api.py`): REST API endpoints
- **Brand Routes** (`app/brand_routes.py`): Brand and subbrand management

#### Services & Repositories
- **Services** (`app/services/`): Business logic layer
  - `csv_service.py` - Bulk data import/export
  - `supplier_service.py` - Supplier operations
- **Repositories** (`app/repositories/`): Data access layer
  - `supplier_repository.py` - Supplier data operations
- **Utils** (`app/utils/`): Utility functions
  - `database.py`, `file_handling.py`, `response.py`, `validators.py`

### Frontend Architecture

#### Template System
- **Base Template** (`templates/base.html`): Modern responsive design
- Uses Bootstrap 5.3.2 + Alpine.js for interactivity
- Lucide icons and Inter font for modern UI
- Responsive navigation with component-based structure

#### Static Assets
- **CSS Architecture**: Modular CSS with imports
  - `base/` - Core styles (variables, reset, animations, utilities, responsive)
  - `components/` - Reusable UI components (buttons, forms, cards, etc.)
  - `pages/` - Page-specific styles
- **JavaScript**: Modern ES6+ with utilities
  - `components/` - Reusable JS components
  - `utils/` - Common utilities (API, validation)
  - `pages/` - Page-specific functionality

### Database Schema (`component_app`)

#### Core Tables
- **component** - Main products with JSON properties, approval status tracking
- **component_variant** - Color variations with auto-generated SKUs
- **component_type** - Product categories with dynamic property definitions
- **supplier** - Supplier information with unique codes
- **brand/subbrand** - Brand hierarchy
- **picture** - Image management with automatic naming system
- **color/material/category** - Reference data tables

#### Key Database Features
- **Auto-Generated Fields**: SKUs and picture names via PostgreSQL functions
- **Status Tracking**: Three-stage approval process (Proto/SMS/PPS)
- **Flexible Properties**: JSON-based component attributes
- **Association Tables**: Many-to-many relationships
- **Database Triggers**: Automatic updates for timestamps, SKUs, and naming

### Configuration
- **Database**: PostgreSQL connection string: `postgresql://component_user:component_app_123@192.168.100.35:5432/promo_database`
- **Schema**: All tables use `component_app` schema
- **File Uploads**: Stored in `app/static/uploads/` with 16MB limit
- **Port**: Application runs on port 6002
- **Security**: SECRET_KEY configuration, secure file handling

### Key Features
1. **Component Lifecycle Management**: Complete product lifecycle with approval workflows
2. **Variant Management**: Color variants with automatic SKU generation
3. **Brand Association**: Many-to-many component-brand relationships
4. **Picture Management**: Automatic naming and organization system
5. **CSV Import/Export**: Bulk data operations
6. **Search & Filtering**: Advanced filtering with pagination
7. **Responsive UI**: Modern, mobile-friendly interface
8. **Performance Optimization**: Efficient queries with pagination and caching

## Important Development Notes
- Database uses custom schema `component_app` - ensure all models inherit from `Base`
- File uploads limited to 16MB with automatic optimization
- Application runs on port 6002 by default via Docker
- Uses external PostgreSQL database (not containerized)
- All database changes should use Flask-Migrate migrations
- SKUs and picture names are auto-generated by database triggers - don't manually set them
- Always use database functions for complex operations (SKU generation, etc.)


Integrate with Version Control: Always use Claude Code in conjunction with a version control system (like Git). This helps mitigate the risk of Claude becoming "overly ambitious" and introducing breaking changes that are difficult to roll back
.
2.
Commit Frequently: Instruct Claude Code to commit after every major change it makes
. This practice creates frequent save points, making it easier to track progress and revert if necessary.
3.
Generate High-Quality Commit Messages: Have Claude Code write your commit messages. The sources suggest that Claude often generates very high-quality commit messages
.
4.
Be Prepared to Revert: Understand that when working with Claude Code, you may need to revert changes more often than you are typically used to
.
5.
Clear Conversation and Revert for Issues: If you encounter problems or if Claude goes off-track, a common and effective solution is to clear the conversation history in Claude Code, revert to a previous save point in your version control, and then try again with more specific instructions
.

create table keyword
(
    id   serial
        primary key,
    name text not null
);

alter table keyword
    owner to mpilarczyk;

grant select, update, usage on sequence keyword_id_seq to component_user;

create unique index component_app_keyword_unique_name
    on keyword (name);

create index keyword_name_idx
    on keyword (name);

grant delete, insert, references, select, trigger, truncate, update on keyword to component_user;

create table component_type
(
    id   serial
        primary key,
    name varchar(100) not null
        unique
);

alter table component_type
    owner to mpilarczyk;

grant select, update, usage on sequence component_type_id_seq to component_user;

grant delete, insert, references, select, trigger, truncate, update on component_type to component_user;

create table gender
(
    id   integer default nextval('component_app.color_id_seq'::regclass) not null
        primary key,
    name varchar(50)                                                     not null
);

alter table gender
    owner to mpilarczyk;

create unique index gender_name_key
    on gender (name);

grant delete, insert, references, select, trigger, truncate, update on gender to component_user;

create table style
(
    id   integer default nextval('component_app.color_id_seq'::regclass) not null
        primary key,
    name varchar(50)                                                     not null
);

alter table style
    owner to mpilarczyk;

create unique index style_name_key
    on style (name);

grant delete, insert, references, select, trigger, truncate, update on style to component_user;

create table brand
(
    id         serial
        primary key,
    name       varchar(100) not null
        unique,
    created_at timestamp default CURRENT_TIMESTAMP,
    updated_at timestamp default CURRENT_TIMESTAMP
);

alter table brand
    owner to component_user;

create index brand_name_idx
    on brand (name);

create table subbrand
(
    id         serial
        primary key,
    name       varchar(100) not null,
    brand_id   integer      not null
        references brand
            on delete cascade,
    created_at timestamp default CURRENT_TIMESTAMP,
    updated_at timestamp default CURRENT_TIMESTAMP,
    unique (name, brand_id)
);

alter table subbrand
    owner to component_user;

create index subbrand_name_idx
    on subbrand (name);

create index subbrand_brand_idx
    on subbrand (brand_id);

create table component_type_property
(
    id                serial
        primary key,
    component_type_id integer      not null
        references component_type
            on delete cascade,
    property_name     varchar(100) not null,
    property_type     varchar(50)  not null,
    is_required       boolean default false,
    display_order     integer default 0,
    unique (component_type_id, property_name)
);

alter table component_type_property
    owner to component_user;

create index idx_component_type_property_type
    on component_type_property (component_type_id);

create index idx_component_type_property_name
    on component_type_property (property_name);

create index idx_component_type_property_order
    on component_type_property (display_order);

create table property
(
    id           serial
        primary key,
    property_key varchar(100) not null
        unique,
    display_name varchar(100) not null,
    data_type    varchar(50)  not null,
    description  text,
    is_active    boolean,
    created_at   timestamp,
    updated_at   timestamp,
    options      json
);

alter table property
    owner to mpilarczyk;

grant select, update, usage on sequence property_id_seq to component_user;

create index idx_property_key
    on property (property_key);

create index idx_property_data_type
    on property (data_type);

create index idx_property_active
    on property (is_active);

grant delete, insert, references, select, trigger, truncate, update on property to component_user;

create table supplier
(
    id            serial
        primary key,
    supplier_code varchar(50) default 'NO CODE'::character varying not null
        unique,
    address       varchar(255),
    created_at    timestamp   default CURRENT_TIMESTAMP,
    updated_at    timestamp   default CURRENT_TIMESTAMP
);

alter table supplier
    owner to component_user;

create table category
(
    id   serial
        primary key,
    name varchar(100) not null
        unique
);

alter table category
    owner to component_user;

create table type_category
(
    id                serial
        primary key,
    component_type_id integer not null
        references component_type,
    category_id       integer not null
        references category,
    unique (component_type_id, category_id)
);

alter table type_category
    owner to mpilarczyk;

grant select, update, usage on sequence type_category_id_seq to component_user;

create index type_category_type_idx
    on type_category (component_type_id);

create index type_category_category_idx
    on type_category (category_id);

grant delete, insert, references, select, trigger, truncate, update on type_category to component_user;

create table color
(
    id   serial
        primary key,
    name varchar(50) not null
        unique
);

alter table color
    owner to component_user;

create table material
(
    id   serial
        primary key,
    name varchar(100) not null
        unique
);

alter table material
    owner to component_user;

create table component
(
    id                serial
        primary key,
    product_number    varchar(50) not null,
    description       text,
    supplier_id       integer
        references supplier,
    category_id       integer
        references category,
    created_at        timestamp   default CURRENT_TIMESTAMP,
    updated_at        timestamp   default CURRENT_TIMESTAMP,
    properties        jsonb       default '{}'::jsonb,
    component_type_id integer     not null
        references component_type,
    proto_status      varchar(20) default 'pending'::character varying
        constraint component_proto_status_check
            check ((proto_status)::text = ANY
                   ((ARRAY ['pending'::character varying, 'ok'::character varying, 'not_ok'::character varying])::text[])),
    proto_comment     text,
    proto_date        timestamp,
    sms_status        varchar(20) default 'pending'::character varying
        constraint component_sms_status_check
            check ((sms_status)::text = ANY
                   ((ARRAY ['pending'::character varying, 'ok'::character varying, 'not_ok'::character varying])::text[])),
    sms_comment       text,
    sms_date          timestamp,
    pps_status        varchar(20) default 'pending'::character varying
        constraint component_pps_status_check
            check ((pps_status)::text = ANY
                   ((ARRAY ['pending'::character varying, 'ok'::character varying, 'not_ok'::character varying])::text[])),
    pps_comment       text,
    pps_date          timestamp
);

alter table component
    owner to component_user;

create table keyword_component
(
    id           serial
        primary key,
    component_id bigint not null
        references component,
    keyword_id   bigint not null
        references keyword,
    unique (component_id, keyword_id)
);

alter table keyword_component
    owner to mpilarczyk;

grant select, update, usage on sequence keyword_component_id_seq to component_user;

create index keyword_component_component_idx
    on keyword_component (component_id);

create index keyword_component_keyword_idx
    on keyword_component (keyword_id);

create index idx_keyword_component_comp
    on keyword_component (component_id);

create index idx_keyword_component_keyword
    on keyword_component (keyword_id);

grant delete, insert, references, select, trigger, truncate, update on keyword_component to component_user;

create table component_variant
(
    id           serial
        primary key,
    component_id integer not null
        references component
            on delete cascade,
    color_id     integer not null
        references color
            on delete restrict,
    variant_name varchar(100),
    description  text,
    is_active    boolean   default true,
    created_at   timestamp default CURRENT_TIMESTAMP,
    updated_at   timestamp default CURRENT_TIMESTAMP,
    variant_sku  varchar(255)
        constraint component_variant_sku_unique
            unique,
    unique (component_id, color_id)
);

alter table component_variant
    owner to component_user;

create index component_variant_component_idx
    on component_variant (component_id);

create index component_variant_color_idx
    on component_variant (color_id);

create index idx_variant_component
    on component_variant (component_id);

create index idx_variant_color
    on component_variant (color_id);

create index idx_component_variant_sku
    on component_variant (variant_sku);

create table component_brand
(
    id           serial
        primary key,
    component_id integer not null
        references component
            on delete cascade,
    brand_id     integer not null
        references brand
            on delete cascade,
    created_at   timestamp default CURRENT_TIMESTAMP,
    unique (component_id, brand_id)
);

alter table component_brand
    owner to mpilarczyk;

grant select, update, usage on sequence component_brand_id_seq to component_user;

create index component_brand_component_idx
    on component_brand (component_id);

create index component_brand_brand_idx
    on component_brand (brand_id);

grant delete, insert, references, select, trigger, truncate, update on component_brand to component_user;

create unique index serial_key_unique_index
    on component (product_number, supplier_id);

create index component_product_idx
    on component (product_number);

create index component_type_idx
    on component (component_type_id);

create index component_supplier_idx
    on component (supplier_id);

create index component_category_idx
    on component (category_id);

create index component_properties_idx
    on component using gin (properties);

create index component_proto_status_idx
    on component (proto_status);

create index component_sms_status_idx
    on component (sms_status);

create index component_pps_status_idx
    on component (pps_status);

create index idx_component_product_number
    on component (product_number);

create index idx_component_supplier
    on component (supplier_id);

create index idx_component_category
    on component (category_id);

create index idx_component_type
    on component (component_type_id);

create index idx_component_properties
    on component using gin (properties);

create index idx_component_status
    on component (proto_status, sms_status, pps_status);

create index idx_component_brand_property
    on component using gin ((properties -> 'brand'::text));

create table picture
(
    id            serial
        primary key,
    component_id  integer      not null
        references component,
    picture_name  varchar(255) not null
        constraint picture_name_unique
            unique,
    url           varchar(255) not null,
    picture_order integer      not null,
    variant_id    integer
        references component_variant
            on delete cascade,
    alt_text      varchar(500),
    file_size     integer,
    is_primary    boolean   default false,
    created_at    timestamp default CURRENT_TIMESTAMP
);

alter table picture
    owner to component_user;

create index picture_component_idx
    on picture (component_id);

create index idx_picture_component
    on picture (component_id);

create index idx_picture_variant
    on picture (variant_id);

create index idx_picture_order
    on picture (picture_order);

create unique index component_index_unique
    on picture (variant_id, picture_order);

create index idx_picture_name
    on picture (picture_name);

create table alembic_version
(
    version_num varchar(32) not null
        constraint alembic_version_pkc
            primary key
);

alter table alembic_version
    owner to component_user;

create view component_brand_view
            (component_id, product_number, description, brand_id, brand_name, association_created) as
SELECT c.id          AS component_id,
       c.product_number,
       c.description,
       b.id          AS brand_id,
       b.name        AS brand_name,
       cb.created_at AS association_created
FROM component_app.component c
         JOIN component_app.component_brand cb ON c.id = cb.component_id
         JOIN component_app.brand b ON cb.brand_id = b.id
ORDER BY c.product_number, b.name;

alter table component_brand_view
    owner to mpilarczyk;

grant delete, insert, references, select, trigger, truncate, update on component_brand_view to component_user;

create function update_updated_at_column() returns trigger
    language plpgsql
as
$$
BEGIN
    NEW.updated_at = current_timestamp;
    RETURN NEW;
END;
$$;

alter function update_updated_at_column() owner to mpilarczyk;

create trigger update_component_variant_updated_at
    before update
    on component_variant
    for each row
execute procedure update_updated_at_column();

create trigger update_brand_updated_at
    before update
    on brand
    for each row
execute procedure update_updated_at_column();

create trigger update_subbrand_updated_at
    before update
    on subbrand
    for each row
execute procedure update_updated_at_column();

create trigger update_component_type_property_updated_at
    before update
    on component_type_property
    for each row
execute procedure update_updated_at_column();

create trigger update_supplier_updated_at
    before update
    on supplier
    for each row
execute procedure update_updated_at_column();

create trigger update_component_updated_at
    before update
    on component
    for each row
execute procedure update_updated_at_column();

grant execute on function update_updated_at_column() to component_user;

create function generate_variant_sku(p_component_id integer, p_color_id integer) returns character varying
    language plpgsql
as
$$
            DECLARE
                v_supplier_code VARCHAR(50);
                v_product_number VARCHAR(50);
                v_color_name VARCHAR(50);
                v_sku VARCHAR(255);
            BEGIN
                -- Get component details with supplier code
                SELECT 
                    COALESCE(s.supplier_code, '') as supplier_code,
                    c.product_number
                INTO v_supplier_code, v_product_number
                FROM component_app.component c
                LEFT JOIN component_app.supplier s ON c.supplier_id = s.id
                WHERE c.id = p_component_id;
                
                -- Get color name
                SELECT name INTO v_color_name
                FROM component_app.color
                WHERE id = p_color_id;
                
                -- Normalize product number: lowercase and replace spaces with underscores
                v_product_number := LOWER(REPLACE(v_product_number, ' ', '_'));
                
                -- Normalize color name: lowercase and replace spaces with underscores
                v_color_name := LOWER(REPLACE(v_color_name, ' ', '_'));
                
                -- Generate SKU based on whether supplier exists
                IF v_supplier_code IS NOT NULL AND v_supplier_code != '' THEN
                    -- Pattern: <supplier_code>_<product_number>_<color_name>
                    v_sku := v_supplier_code || '_' || v_product_number || '_' || v_color_name;
                ELSE
                    -- Pattern: <product_number>_<color_name>
                    v_sku := v_product_number || '_' || v_color_name;
                END IF;
                
                RETURN v_sku;
            END;
            $$;

alter function generate_variant_sku(integer, integer) owner to component_user;

create function update_variant_sku() returns trigger
    language plpgsql
as
$$
            BEGIN
                -- Update the variant_sku when insert or update occurs
                IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
                    NEW.variant_sku := component_app.generate_variant_sku(NEW.component_id, NEW.color_id);
                    NEW.updated_at := CURRENT_TIMESTAMP;
                    RETURN NEW;
                END IF;
                
                RETURN NULL;
            END;
            $$;

alter function update_variant_sku() owner to component_user;

create trigger trigger_update_variant_sku
    before insert or update
    on component_variant
    for each row
execute procedure update_variant_sku();

create function update_variant_skus_on_component_change() returns trigger
    language plpgsql
as
$$
            BEGIN
                -- Update all variant SKUs when component product_number or supplier changes
                IF TG_OP = 'UPDATE' THEN
                    -- Check if product_number or supplier_id changed
                    IF OLD.product_number != NEW.product_number OR 
                       COALESCE(OLD.supplier_id, -1) != COALESCE(NEW.supplier_id, -1) THEN
                        
                        -- Update all variants for this component
                        UPDATE component_app.component_variant 
                        SET variant_sku = component_app.generate_variant_sku(component_id, color_id),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE component_id = NEW.id;
                    END IF;
                END IF;
                
                RETURN NEW;
            END;
            $$;

alter function update_variant_skus_on_component_change() owner to component_user;

create trigger trigger_update_variant_skus_on_component_change
    after update
    on component
    for each row
execute procedure update_variant_skus_on_component_change();

create function update_variant_skus_on_supplier_change() returns trigger
    language plpgsql
as
$$
            BEGIN
                -- Update all variant SKUs when supplier code changes
                IF TG_OP = 'UPDATE' THEN
                    IF OLD.supplier_code != NEW.supplier_code THEN
                        -- Update all variants for components using this supplier
                        UPDATE component_app.component_variant cv
                        SET variant_sku = component_app.generate_variant_sku(cv.component_id, cv.color_id),
                            updated_at = CURRENT_TIMESTAMP
                        FROM component_app.component c
                        WHERE cv.component_id = c.id 
                        AND c.supplier_id = NEW.id;
                    END IF;
                END IF;
                
                RETURN NEW;
            END;
            $$;

alter function update_variant_skus_on_supplier_change() owner to component_user;

create trigger trigger_update_variant_skus_on_supplier_change
    after update
    on supplier
    for each row
execute procedure update_variant_skus_on_supplier_change();

create function update_variant_skus_on_color_change() returns trigger
    language plpgsql
as
$$
            BEGIN
                -- Update all variant SKUs when color name changes
                IF TG_OP = 'UPDATE' THEN
                    IF OLD.name != NEW.name THEN
                        -- Update all variants using this color
                        UPDATE component_app.component_variant 
                        SET variant_sku = component_app.generate_variant_sku(component_id, color_id),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE color_id = NEW.id;
                    END IF;
                END IF;
                
                RETURN NEW;
            END;
            $$;

alter function update_variant_skus_on_color_change() owner to component_user;

create trigger trigger_update_variant_skus_on_color_change
    after update
    on color
    for each row
execute procedure update_variant_skus_on_color_change();

create function generate_picture_name(p_component_id integer DEFAULT NULL::integer, p_variant_id integer DEFAULT NULL::integer, p_picture_order integer DEFAULT 1) returns character varying
    language plpgsql
as
$$
            DECLARE
                v_supplier_code VARCHAR(50);
                v_product_number VARCHAR(50);
                v_color_name VARCHAR(50);
                v_picture_name VARCHAR(255);
            BEGIN
                -- Determine if this is a component or variant picture
                IF p_variant_id IS NOT NULL THEN
                    -- Variant picture: get component info through variant
                    SELECT 
                        COALESCE(s.supplier_code, '') as supplier_code,
                        c.product_number,
                        co.name as color_name
                    INTO v_supplier_code, v_product_number, v_color_name
                    FROM component_app.component_variant cv
                    JOIN component_app.component c ON cv.component_id = c.id
                    JOIN component_app.color co ON cv.color_id = co.id
                    LEFT JOIN component_app.supplier s ON c.supplier_id = s.id
                    WHERE cv.id = p_variant_id;
                ELSIF p_component_id IS NOT NULL THEN
                    -- Component picture: get component info directly
                    SELECT 
                        COALESCE(s.supplier_code, '') as supplier_code,
                        c.product_number,
                        'main' as color_name  -- Use 'main' for component pictures
                    INTO v_supplier_code, v_product_number, v_color_name
                    FROM component_app.component c
                    LEFT JOIN component_app.supplier s ON c.supplier_id = s.id
                    WHERE c.id = p_component_id;
                ELSE
                    RAISE EXCEPTION 'Either component_id or variant_id must be provided';
                END IF;
                
                -- Check if we found the data
                IF v_product_number IS NULL THEN
                    RAISE EXCEPTION 'Component or variant not found';
                END IF;
                
                -- Normalize strings: lowercase and replace spaces with underscores
                v_product_number := LOWER(REPLACE(v_product_number, ' ', '_'));
                v_color_name := LOWER(REPLACE(v_color_name, ' ', '_'));
                
                -- Generate picture name based on whether supplier exists
                IF v_supplier_code IS NOT NULL AND v_supplier_code != '' THEN
                    -- Pattern: <supplier_code>_<product_number>_<color_name>_<picture_order>
                    v_picture_name := LOWER(v_supplier_code) || '_' || v_product_number || '_' || v_color_name || '_' || p_picture_order::text;
                ELSE
                    -- Pattern: <product_number>_<color_name>_<picture_order>
                    v_picture_name := v_product_number || '_' || v_color_name || '_' || p_picture_order::text;
                END IF;
                
                RETURN v_picture_name;
            END;
            $$;

alter function generate_picture_name(integer, integer, integer) owner to component_user;

create function update_picture_name() returns trigger
    language plpgsql
as
$$
            BEGIN
                -- Update the picture_name when insert or update occurs
                IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
                    NEW.picture_name := component_app.generate_picture_name(NEW.component_id, NEW.variant_id, NEW.picture_order);
                    RETURN NEW;
                END IF;
                
                RETURN NULL;
            END;
            $$;

alter function update_picture_name() owner to component_user;

create trigger trigger_update_picture_name
    before insert or update
    on picture
    for each row
execute procedure update_picture_name();

create function update_picture_names_on_component_change() returns trigger
    language plpgsql
as
$$
            BEGIN
                -- Update all picture names when component product_number or supplier changes
                IF TG_OP = 'UPDATE' THEN
                    -- Check if product_number or supplier_id changed
                    IF OLD.product_number != NEW.product_number OR 
                       COALESCE(OLD.supplier_id, -1) != COALESCE(NEW.supplier_id, -1) THEN
                        
                        -- Update component pictures for this component
                        UPDATE component_app.picture 
                        SET picture_name = component_app.generate_picture_name(component_id, variant_id, picture_order)
                        WHERE component_id = NEW.id;
                        
                        -- Update variant pictures for variants of this component
                        UPDATE component_app.picture p
                        SET picture_name = component_app.generate_picture_name(p.component_id, p.variant_id, p.picture_order)
                        FROM component_app.component_variant cv
                        WHERE p.variant_id = cv.id 
                        AND cv.component_id = NEW.id;
                    END IF;
                END IF;
                
                RETURN NEW;
            END;
            $$;

alter function update_picture_names_on_component_change() owner to component_user;

create trigger trigger_update_picture_names_on_component_change
    after update
    on component
    for each row
execute procedure update_picture_names_on_component_change();

create function update_picture_names_on_supplier_change() returns trigger
    language plpgsql
as
$$
            BEGIN
                -- Update all picture names when supplier code changes
                IF TG_OP = 'UPDATE' THEN
                    IF OLD.supplier_code != NEW.supplier_code THEN
                        -- Update component pictures for components using this supplier
                        UPDATE component_app.picture p
                        SET picture_name = component_app.generate_picture_name(p.component_id, p.variant_id, p.picture_order)
                        FROM component_app.component c
                        WHERE p.component_id = c.id 
                        AND c.supplier_id = NEW.id;
                        
                        -- Update variant pictures for components using this supplier
                        UPDATE component_app.picture p
                        SET picture_name = component_app.generate_picture_name(p.component_id, p.variant_id, p.picture_order)
                        FROM component_app.component_variant cv
                        JOIN component_app.component c ON cv.component_id = c.id
                        WHERE p.variant_id = cv.id 
                        AND c.supplier_id = NEW.id;
                    END IF;
                END IF;
                
                RETURN NEW;
            END;
            $$;

alter function update_picture_names_on_supplier_change() owner to component_user;

create trigger trigger_update_picture_names_on_supplier_change
    after update
    on supplier
    for each row
execute procedure update_picture_names_on_supplier_change();

create function update_picture_names_on_color_change() returns trigger
    language plpgsql
as
$$
            BEGIN
                -- Update all picture names when color name changes
                IF TG_OP = 'UPDATE' THEN
                    IF OLD.name != NEW.name THEN
                        -- Update variant pictures using this color
                        UPDATE component_app.picture p
                        SET picture_name = component_app.generate_picture_name(p.component_id, p.variant_id, p.picture_order)
                        FROM component_app.component_variant cv
                        WHERE p.variant_id = cv.id 
                        AND cv.color_id = NEW.id;
                    END IF;
                END IF;
                
                RETURN NEW;
            END;
            $$;

alter function update_picture_names_on_color_change() owner to component_user;

create trigger trigger_update_picture_names_on_color_change
    after update
    on color
    for each row
execute procedure update_picture_names_on_color_change();

create function ensure_picture_component_id() returns trigger
    language plpgsql
as
$$
BEGIN
    -- If variant_id is being set, automatically set component_id
    IF NEW.variant_id IS NOT NULL THEN
        SELECT component_id INTO NEW.component_id
        FROM component_app.component_variant
        WHERE id = NEW.variant_id;

        IF NEW.component_id IS NULL THEN
            RAISE EXCEPTION 'Cannot find component for variant_id %', NEW.variant_id;
        END IF;
    END IF;

    -- Ensure component_id is never NULL
    IF NEW.component_id IS NULL THEN
        RAISE EXCEPTION 'component_id cannot be NULL for pictures';
    END IF;

    RETURN NEW;
END;
$$;

alter function ensure_picture_component_id() owner to mpilarczyk;

create trigger ensure_picture_component_id_trigger
    before insert or update
    on picture
    for each row
execute procedure ensure_picture_component_id();

grant execute on function ensure_picture_component_id() to component_user;



grant execute on function update_updated_at_column() to component_user;



Postgresql connection string:
postgresql://component_user:component_app_123@192.168.100.35:5432/promo_database