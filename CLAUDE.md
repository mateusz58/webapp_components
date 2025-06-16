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
    component_id  integer
        references component,
    picture_name  varchar(255) not null,
    url           varchar(255) not null,
    picture_order integer      not null,
    variant_id    integer
        references component_variant
            on delete cascade,
    alt_text      varchar(500),
    file_size     integer,
    is_primary    boolean   default false,
    created_at    timestamp default CURRENT_TIMESTAMP,
    unique (component_id, picture_order),
    constraint picture_belongs_to_component_or_variant
        check (((component_id IS NOT NULL) AND (variant_id IS NULL)) OR
               ((component_id IS NULL) AND (variant_id IS NOT NULL)))
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



Postgresql connection string:
postgresql://component_user:component_app_123@192.168.100.35:5432/promo_database