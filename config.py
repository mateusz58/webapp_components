import os
from dotenv import load_dotenv

# Load environment variables from .env file
# This allows you to store sensitive information outside your code
load_dotenv()


class Config:
    """
    Base configuration class containing all application settings.
    Settings are loaded from environment variables with fallback defaults.
    """

    # Secret key for Flask sessions and CSRF protection
    # CRITICAL: Change this in production!
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Database connection URL
    # Format: postgresql://username:password@host:port/database_name
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'postgresql://username:password@localhost/dbname'

    # Disable SQLAlchemy event system (improves performance)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Database connection pool settings for better performance
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,      # Verify connections before use
        'pool_recycle': 300,        # Recycle connections every 5 minutes
    }

# Example of how to create different environment configs:
class DevelopmentConfig(Config):
    """Development-specific configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production-specific configuration"""
    DEBUG = False
    # Add production-specific settings here

class TestingConfig(Config):
    """Testing-specific configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # In-memory database for tests

# Configuration dictionary for easy switching between environments
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}