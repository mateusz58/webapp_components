# tests/conftest.py
"""
Pytest configuration and shared fixtures.

This file contains setup code that's shared across all test files.
"""

import pytest
import tempfile
import os
from app import create_app, db
from config import Config

class TestConfig(Config):
    """Configuration for testing environment."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # In-memory database for tests
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'

@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app(TestConfig)

    with app.app_context():
        # Create all database tables
        db.create_all()
        yield app
        # Clean up after tests
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()

@pytest.fixture
def sample_product_data():
    """Sample product data for testing."""
    return [
        {
            'ordinal_number': 1,
            'shop_technical_name': 'test_shop',
            'shop_technical_id': 1,
            'product_id': 123,
            'handle': 'test-product',
            'title': 'Test Product',
            'vendor': 'Test Vendor',
            'type': 'Test Type',
            'status': 'active',
            'variant_id': 456,
            'variant_sku': 'TEST-SKU-001',
            'variant_barcode': '1234567890',
            'variant_inventory_quantity': 10,
            'variant_available_for_sale': True,
            'image_src': 'https://example.com/image.jpg',
            'Metafield: custom.deals': 'Sale',
            'Metafield: gender': 'Unisex'
        },
        {
            'ordinal_number': 2,
            'shop_technical_name': 'test_shop',
            'shop_technical_id': 1,
            'product_id': 124,
            'handle': 'test-product-2',
            'title': 'Test Product 2',
            'vendor': 'Test Vendor',
            'type': 'Test Type',
            'status': 'draft',
            'variant_id': 457,
            'variant_sku': '',  # Missing SKU for testing
            'variant_barcode': '1234567891',
            'variant_inventory_quantity': 0,
            'variant_available_for_sale': False,
            'image_src': '',  # Missing image for testing
            'Metafield: custom.deals': '',
            'Metafield: gender': 'Male'
        }
    ]

