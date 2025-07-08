"""
Test configuration for pytest
Provides fixtures and setup for all test modules
"""
import pytest
import sys
import os

# Add app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from config import Config

class TestConfig(Config):
    """Test configuration that uses PostgreSQL database from config.py"""
    TESTING = True
    WTF_CSRF_ENABLED = False
    # Use the same PostgreSQL database - schema component_app already exists

@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    app = create_app(TestConfig)
    
    with app.app_context():
        yield app

@pytest.fixture(scope='session') 
def client(app):
    """Create test client."""
    return app.test_client()

@pytest.fixture(scope='function')
def db_session(app):
    """Provide database session with transaction rollback for isolation."""
    with app.app_context():
        # Start a transaction that we'll rollback
        connection = db.engine.connect()
        transaction = connection.begin()
        
        # Configure session to use this transaction
        db.session.configure(bind=connection)
        
        yield db.session
        
        # Rollback transaction to clean up changes
        transaction.rollback()
        connection.close()
        db.session.remove()

# Simple fixtures that work with existing PostgreSQL data
@pytest.fixture
def sample_data(db_session):
    """Use existing database data for testing."""
    from app.models import ComponentType, Supplier, Brand, Color
    
    # Get existing data from the PostgreSQL database
    component_type = ComponentType.query.first()
    supplier = Supplier.query.first() 
    brand = Brand.query.first()
    color = Color.query.first()
    
    return {
        'component_type': component_type,
        'supplier': supplier, 
        'brand': brand,
        'color': color
    }