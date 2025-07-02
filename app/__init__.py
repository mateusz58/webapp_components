import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import Config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()


def pluralize(count, singular='', plural='s'):
    """
    Flask/Jinja2 pluralize filter similar to Django's pluralize
    Usage: {{ count|pluralize }} or {{ count|pluralize:'y,ies' }}
    """
    if count == 1:
        return singular
    return plural


def register_template_filters(app):
    """Register custom template filters"""
    app.jinja_env.filters['pluralize'] = pluralize

def register_template_globals(app):
    """Register custom template global functions"""
    app.jinja_env.globals['hasattr'] = hasattr

def register_context_processors(app):
    """Register template context processors"""
    import time
    
    @app.context_processor
    def inject_cache_bust():
        return {
            'cache_bust_version': int(time.time())
        }


def create_app(config_class=Config):
    # Initialize the app
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with the app
    db.init_app(app)
    csrf.init_app(app)
    
    # Set up migrations without auto migration
    migrate.init_app(
        app, 
        db, 
        compare_type=True,
        render_as_batch=True,
        version_table_schema='component_app'
    )

    # Register custom template filters
    register_template_filters(app)
    
    # Register custom template globals
    register_template_globals(app)
    
    # Register context processors
    register_context_processors(app)

    # Create upload directory if it doesn't exist
    uploads_dir = app.config.get('UPLOAD_FOLDER')
    if uploads_dir:
        os.makedirs(uploads_dir, exist_ok=True)

    # Register API blueprints with /api prefix
    try:
        from app.api.component_api import component_api
        app.register_blueprint(component_api, url_prefix='/api')
    except ImportError as e:
        app.logger.warning(f"Component API routes not available: {e}")
    
    try:
        from app.api.category_api import category_api
        app.register_blueprint(category_api, url_prefix='/api')
    except ImportError as e:
        app.logger.warning(f"Category API routes not available: {e}")
    
    try:
        from app.api.picture_api import picture_api
        app.register_blueprint(picture_api, url_prefix='/api')
    except ImportError as e:
        app.logger.warning(f"Picture API routes not available: {e}")
    
    try:
        from app.api.brand_api import brand_api_bp
        app.register_blueprint(brand_api_bp)  # Already has url_prefix
    except ImportError as e:
        app.logger.warning(f"Brand API routes not available: {e}")
    
    try:
        from app.api.supplier_api import supplier_api_bp
        app.register_blueprint(supplier_api_bp)  # Already has url_prefix
    except ImportError as e:
        app.logger.warning(f"Supplier API routes not available: {e}")
    
    try:
        from app.api.variant_api import variant_api
        app.register_blueprint(variant_api)  # Already has url_prefix
    except ImportError as e:
        app.logger.warning(f"Variant API routes not available: {e}")
    
    try:
        from app.api.keyword_api import keyword_api
        app.register_blueprint(keyword_api)  # Already has url_prefix
    except ImportError as e:
        app.logger.warning(f"Keyword API routes not available: {e}")
    
    # Register web blueprints
    try:
        from app.web.component_routes import component_web
        app.register_blueprint(component_web)
    except ImportError as e:
        app.logger.warning(f"Component web routes not available: {e}")
    
    try:
        from app.web.variant_routes import variant_web
        app.register_blueprint(variant_web)
    except ImportError as e:
        app.logger.warning(f"Variant web routes not available: {e}")
    
    try:
        from app.web.utility_routes import utility_web
        app.register_blueprint(utility_web)
    except ImportError as e:
        app.logger.warning(f"Utility web routes not available: {e}")
    
    try:
        from app.web.supplier_routes import supplier_bp, suppliers_bp
        app.register_blueprint(supplier_bp)
        app.register_blueprint(suppliers_bp)
    except ImportError as e:
        app.logger.warning(f"Supplier web routes not available: {e}")
    
    try:
        from app.web.brand_routes import brand_bp
        app.register_blueprint(brand_bp)
    except ImportError as e:
        app.logger.warning(f"Brand web routes not available: {e}")
    
    try:
        from app.web.admin_routes import admin_web
        app.register_blueprint(admin_web)
    except ImportError as e:
        app.logger.warning(f"Admin web routes not available: {e}")

    return app