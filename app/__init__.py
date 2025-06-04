import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()


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


def create_app(config_class=Config):
    # Initialize the app
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with the app
    db.init_app(app)
    
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

    # Create upload directory if it doesn't exist
    uploads_dir = app.config.get('UPLOAD_FOLDER')
    if uploads_dir:
        os.makedirs(uploads_dir, exist_ok=True)
    
    # Register blueprints
    from app.routes import main
    app.register_blueprint(main)

    return app