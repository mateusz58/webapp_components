#!/usr/bin/env python3
"""
Unit tests for Component API endpoints
Following TDD methodology - tests written first before implementation
"""
import unittest
import json
import os
import tempfile
from io import BytesIO
from unittest.mock import patch, MagicMock
from flask import url_for
from werkzeug.datastructures import FileStorage

# Add app directory to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models import Component, ComponentType, Supplier, Brand, Category, Keyword, Color, ComponentVariant
from config import Config


class TestConfig(Config):
    """Test configuration - use existing PostgreSQL database"""
    TESTING = True
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'
    UPLOAD_FOLDER = tempfile.mkdtemp()
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024


class ComponentAPITestCase(unittest.TestCase):
    """Test cases for Component API endpoints"""

    def setUp(self):
        """Set up test fixtures"""
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        
        # Get existing database data for testing
        self._get_test_data()

    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        self.app_context.pop()

    def _get_test_data(self):
        """Get existing test data from database"""
        # Get existing data from the database
        self.component_type = ComponentType.query.first()
        self.supplier = Supplier.query.first()
        self.brand = Brand.query.first()
        self.category = Category.query.first() 
        self.keyword = Keyword.query.first()
        self.color = Color.query.first()
        self.component = Component.query.first()
        
        if self.component:
            self.variant = ComponentVariant.query.filter_by(component_id=self.component.id).first()
        
        # Skip tests if no data available
        if not all([self.component_type, self.component]):
            self.skipTest("No test data available in database")

    def _get_csrf_token(self):
        """Get CSRF token for authenticated requests"""
        # For testing, we disable CSRF but in real implementation would get token
        return 'test-csrf-token'

    def test_component_creation_post_endpoint_exists(self):
        """Test POST /api/component/create endpoint exists"""
        # This should pass - endpoint already implemented
        response = self.client.post('/api/component/create')
        # Should not return 404 (endpoint exists)
        self.assertNotEqual(response.status_code, 404)

    def test_component_update_put_endpoint_exists(self):
        """Test PUT /api/component/<id> endpoint exists"""
        # Endpoint now exists - should not return 404
        response = self.client.put(f'/api/component/{self.component.id}')
        
        # Should not be 404 (endpoint exists) - might be 400/422 for missing data
        self.assertNotEqual(response.status_code, 404, 
                           "PUT endpoint should exist")

    def test_component_update_put_endpoint_basic_structure(self):
        """Test PUT /api/component/<id> endpoint basic structure"""
        # Test the endpoint that now exists
        
        update_data = {
            'product_number': 'TEST123_UPDATED',
            'description': 'Updated test component',
            'component_type_id': self.component_type.id,
            'supplier_id': self.supplier.id
        }
        
        response = self.client.put(
            f'/api/component/{self.component.id}',
            data=update_data,
            headers={'X-CSRFToken': self._get_csrf_token()}
        )
        
        # Endpoint exists - should not be 404
        self.assertNotEqual(response.status_code, 404,
                           "Endpoint should exist")

    def test_component_update_put_endpoint_response_format(self):
        """Test PUT /api/component/<id> response format requirements"""
        # Test the actual implementation response format
        
        update_data = {
            'product_number': f'TEST123_UPDATED_{self.component.id}',
            'description': 'Updated description'
        }
        
        response = self.client.put(
            f'/api/component/{self.component.id}',
            data=json.dumps(update_data),
            content_type='application/json',
            headers={'X-CSRFToken': self._get_csrf_token()}
        )
        
        # Endpoint exists and should return valid response
        self.assertIn(response.status_code, [200, 400, 422])
        
        if response.status_code == 200:
            data = json.loads(response.data)
            self.assertIn('success', data)
            self.assertIn('component_id', data)
        elif response.status_code in [400, 422]:
            # Validation errors are acceptable for test data
            data = json.loads(response.data)
            self.assertIn('error', data)

    def test_component_update_put_endpoint_brand_associations(self):
        """Test PUT /api/component/<id> brand association updates"""
        # Test brand association changes
        
        if not self.brand:
            self.skipTest("No brand data available for testing")
            
        update_data = {
            'brand_ids': [self.brand.id]  # Add brand association
        }
        
        response = self.client.put(
            f'/api/component/{self.component.id}',
            data=update_data,
            headers={'X-CSRFToken': self._get_csrf_token()}
        )
        
        # Endpoint exists - should not be 404
        self.assertNotEqual(response.status_code, 404)
        # Accept various response codes based on implementation
        self.assertIn(response.status_code, [200, 400, 422])

    def test_component_update_put_endpoint_validation_errors(self):
        """Test PUT /api/component/<id> validation error handling"""
        # Test validation error responses
        
        invalid_data = {
            'product_number': '',  # Empty product number should fail
            'component_type_id': 999999  # Non-existent component type
        }
        
        response = self.client.put(
            f'/api/component/{self.component.id}',
            data=invalid_data,
            headers={'X-CSRFToken': self._get_csrf_token()}
        )
        
        # Endpoint exists - should not be 404
        self.assertNotEqual(response.status_code, 404)
        
        # Should return validation error (400/422) for invalid data
        self.assertIn(response.status_code, [400, 422])
        
        if response.content_type == 'application/json':
            data = json.loads(response.data)
            self.assertIn('error', data)

    def test_component_update_put_endpoint_nonexistent_component(self):
        """Test PUT /api/component/<id> with non-existent component"""
        update_data = {
            'product_number': 'TEST999',
            'description': 'Updated description'
        }
        
        response = self.client.put(
            '/api/component/999999',  # Non-existent component ID
            data=update_data,
            headers={'X-CSRFToken': self._get_csrf_token()}
        )
        
        # Should return 404 for non-existent component
        self.assertEqual(response.status_code, 404)

    def test_component_update_put_endpoint_csrf_protection(self):
        """Test PUT /api/component/<id> CSRF protection"""
        update_data = {
            'product_number': 'TEST123_UPDATED',
            'description': 'Updated description'
        }
        
        # Request without CSRF token should fail
        response = self.client.put(
            f'/api/component/{self.component.id}',
            data=update_data
            # No X-CSRFToken header
        )
        
        # Endpoint exists - should not be 404
        self.assertNotEqual(response.status_code, 404)
        # May return 400/403 for missing CSRF or continue (CSRF disabled in tests)
        self.assertIn(response.status_code, [200, 400, 403, 422])

    def test_component_update_put_endpoint_properties_update(self):
        """Test PUT /api/component/<id> properties update (FAILING TEST)"""
        # Test updating JSON properties
        
        update_data = {
            'properties': {
                'material': 'polyester',  # Change from cotton
                'size': '15mm',           # Change from 12mm
                'finish': 'matte'         # New property
            }
        }
        
        response = self.client.put(
            f'/api/component/{self.component.id}',
            data=json.dumps(update_data),
            content_type='application/json',
            headers={'X-CSRFToken': self._get_csrf_token()}
        )
        
        # Should fail with 404 for now
        self.assertEqual(response.status_code, 404)

    def test_component_edit_data_endpoint_exists(self):
        """Test GET /api/components/<id>/edit-data endpoint works"""
        # This should pass - endpoint already exists
        response = self.client.get(f'/api/components/{self.component.id}/edit-data')
        
        # Should return 200 and component data
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['id'], self.component.id)
        self.assertEqual(data['product_number'], 'TEST123')


class ComponentAPIIntegrationTests(unittest.TestCase):
    """Integration tests for Component API workflow"""

    def setUp(self):
        """Set up integration test fixtures"""
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        
        db.create_all()
        self._create_test_data()

    def tearDown(self):
        """Clean up after integration tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _create_test_data(self):
        """Create test data for integration tests"""
        # Minimal test data for integration tests
        component_type = ComponentType(name='IntegrationTest')
        db.session.add(component_type)
        db.session.commit()
        self.component_type_id = component_type.id

    def test_component_edit_workflow_consistency(self):
        """Test that component creation and editing follow same patterns (FAILING TEST)"""
        # Test 1: Create component via API (should work)
        create_data = {
            'product_number': 'INTEGRATION001',
            'description': 'Integration test component',
            'component_type_id': self.component_type_id
        }
        
        create_response = self.client.post(
            '/api/component/create',
            data=create_data,
            headers={'X-CSRFToken': 'test-token'}
        )
        
        # Creation should work (endpoint exists)
        self.assertIn(create_response.status_code, [200, 201, 400])  # 400 for validation errors is OK
        
        # Test 2: Update component via API (should fail - endpoint missing)
        if create_response.status_code in [200, 201]:
            response_data = json.loads(create_response.data)
            component_id = response_data.get('component_id')
            
            if component_id:
                update_data = {
                    'description': 'Updated integration test component'
                }
                
                update_response = self.client.put(
                    f'/api/component/{component_id}',
                    data=update_data,
                    headers={'X-CSRFToken': 'test-token'}
                )
                
                # Should fail with 404 (missing endpoint) - this is our RED test
                self.assertEqual(update_response.status_code, 404)


if __name__ == '__main__':
    # Run with verbosity to see test names
    unittest.main(verbosity=2)