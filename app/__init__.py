"""
This file creates the Flask application using the "Application Factory" pattern.
This pattern allows you to create multiple instances of your app with different
configurations (useful for testing, development, production).
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

# Create the database object
# This will be initialized later with the app
db = SQLAlchemy()

def create_app(config_class=Config):
    """
    Application Factory Function
    
    This function creates and configures a Flask application instance.
    
    Args:
        config_class: Configuration class to use (default: Config)
        
    Returns:
        Flask application instance
    """

    # Create Flask application instance
    app = Flask(__name__)

    # Load configuration from the config class
    app.config.from_object(config_class)

    # Initialize extensions with the app
    # This connects SQLAlchemy to our Flask app
    db.init_app(app)

    # Register blueprints (route modules)
    # Blueprints allow you to organize routes into separate modules
    from app.routes import main
    app.register_blueprint(main)

    # Optional: Add error handlers, custom filters, etc.
    register_error_handlers(app)

    return app

def register_error_handlers(app):
    """
    Register custom error handlers for the application.
    
    This function sets up how the app responds to different types of errors.
    """

    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 (Page Not Found) errors"""
        from flask import render_template
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 (Internal Server Error) errors"""
        from flask import render_template
        # Rollback database session in case of error
        db.session.rollback()
        return render_template('500.html'), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle 403 (Forbidden) errors"""
        from flask import render_template
        return render_template('403.html'), 403