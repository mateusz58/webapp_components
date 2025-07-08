import unittest
import json
from unittest.mock import patch, Mock

from app import create_app, db
from app.models import Component, ComponentType, Supplier

class TestComponentValidationEndpoints(unittest.TestCase):
    """API tests for component validation endpoints"""
    
    @classmethod
    def setUpClass(cls):
        """Set up Flask test client for all tests"""
        print(f"\n🔧 API TEST SETUP: Setting up Flask test client...")
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        cls.app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        
        cls.client = cls.app.test_client()
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        
        # Create tables
        db.create_all()
        print(f"✅ Flask test client established")

    @classmethod
    def tearDownClass(cls):
        """Clean up Flask test client"""
        print(f"\n🧹 API TEST TEARDOWN: Cleaning up Flask test client...")
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()
        print(f"✅ Flask test client cleaned up")

    def setUp(self):
        """Set up test data before each test"""
        print(f"\n🧪 API TEST SETUP: {self._testMethodName}")
        print(f"🔧 Setting up test data for validation endpoints...")
        
        # Create test data
        self.test_component_type = ComponentType(id=1, name='Test Type')
        self.test_supplier = Supplier(id=1, supplier_code='TEST-SUP', address='Test Address')
        
        db.session.add_all([self.test_component_type, self.test_supplier])
        db.session.commit()
        
        print(f"✅ API test setup complete for: {self._testMethodName}")

    def tearDown(self):
        """Clean up after each test"""
        print(f"🧹 Cleaning up test data...")
        db.session.rollback()
        Component.query.delete()
        db.session.commit()

    def test_validate_product_number_unique(self):
        """Test product number validation endpoint - unique product number"""
        print(f"\n🧪 API TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test product number validation for unique values")
        
        # Test data
        product_number = 'UNIQUE-001'
        supplier_id = 1
        
        print(f"🔍 Testing unique product number: {product_number}")
        print(f"🔍 With supplier ID: {supplier_id}")
        
        # Make API request
        response = self.client.post('/api/component/validate-product-number', 
                                  data={
                                      'product_number': product_number,
                                      'supplier_id': supplier_id
                                  })
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response data: {response.get_data(as_text=True)}")
        
        # Assert response
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.get_data(as_text=True))
        self.assertIn('unique', response_data)
        self.assertTrue(response_data['unique'])
        
        print(f"✅ API TEST PASSED: Unique product number validation works")

    def test_validate_product_number_duplicate(self):
        """Test product number validation endpoint - duplicate product number"""
        print(f"\n🧪 API TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test product number validation for duplicate values")
        
        # Create existing component
        existing_component = Component(
            product_number='DUPLICATE-001',
            description='Existing component',
            supplier_id=1,
            component_type_id=1
        )
        db.session.add(existing_component)
        db.session.commit()
        
        print(f"🔍 Created existing component: {existing_component.product_number}")
        
        # Test duplicate product number
        response = self.client.post('/api/component/validate-product-number',
                                  data={
                                      'product_number': 'DUPLICATE-001',
                                      'supplier_id': 1
                                  })
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response data: {response.get_data(as_text=True)}")
        
        # Assert response
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.get_data(as_text=True))
        self.assertIn('unique', response_data)
        self.assertFalse(response_data['unique'])
        
        print(f"✅ API TEST PASSED: Duplicate product number validation works")

    def test_validate_product_number_missing_data(self):
        """Test product number validation with missing required data"""
        print(f"\n🧪 API TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test validation endpoint with missing data")
        
        # Test without product_number
        response = self.client.post('/api/component/validate-product-number',
                                  data={'supplier_id': 1})
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response data: {response.get_data(as_text=True)}")
        
        # Should return error for missing data
        self.assertEqual(response.status_code, 400)
        
        print(f"✅ API TEST PASSED: Missing data validation works")

    def test_validate_product_number_with_exclude_id(self):
        """Test product number validation with exclude_component_id parameter"""
        print(f"\n🧪 API TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test validation with component ID exclusion for editing")
        
        # Create existing component
        existing_component = Component(
            product_number='EDIT-001',
            description='Component being edited',
            supplier_id=1,
            component_type_id=1
        )
        db.session.add(existing_component)
        db.session.commit()
        
        component_id = existing_component.id
        print(f"🔍 Created component to edit: ID={component_id}, product_number={existing_component.product_number}")
        
        # Test validation excluding the component being edited
        response = self.client.post('/api/component/validate-product-number',
                                  data={
                                      'product_number': 'EDIT-001',
                                      'supplier_id': 1,
                                      'exclude_component_id': component_id
                                  })
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response data: {response.get_data(as_text=True)}")
        
        # Should be unique because we're excluding the same component
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.get_data(as_text=True))
        self.assertTrue(response_data['unique'])
        
        print(f"✅ API TEST PASSED: Exclude component ID validation works")

    def test_component_api_create_endpoint_exists(self):
        """Test that component creation API endpoint exists"""
        print(f"\n🧪 API TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test component creation endpoint accessibility")
        
        # Test POST to component creation endpoint (should fail without proper data but endpoint should exist)
        response = self.client.post('/api/component/create',
                                  content_type='application/json',
                                  data=json.dumps({}))
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response data: {response.get_data(as_text=True)}")
        
        # Should not be 404 (endpoint exists), but may be 400 (bad request) due to missing data
        self.assertNotEqual(response.status_code, 404)
        
        print(f"✅ API TEST PASSED: Component creation endpoint exists")

    def test_component_api_update_endpoint_exists(self):
        """Test that component update API endpoint exists"""
        print(f"\n🧪 API TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test component update endpoint accessibility")
        
        # Create test component first
        test_component = Component(
            product_number='UPDATE-TEST-001',
            description='Test component for update',
            supplier_id=1,
            component_type_id=1
        )
        db.session.add(test_component)
        db.session.commit()
        
        component_id = test_component.id
        print(f"🔍 Created test component: ID={component_id}")
        
        # Test PUT to component update endpoint
        response = self.client.put(f'/api/component/{component_id}',
                                 content_type='application/json',
                                 data=json.dumps({'description': 'Updated description'}))
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response data: {response.get_data(as_text=True)}")
        
        # Should not be 404 (endpoint exists)
        self.assertNotEqual(response.status_code, 404)
        
        print(f"✅ API TEST PASSED: Component update endpoint exists")

    def test_api_response_format_consistency(self):
        """Test that API responses follow consistent format"""
        print(f"\n🧪 API TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test API response format consistency")
        
        # Test validation endpoint response format
        response = self.client.post('/api/component/validate-product-number',
                                  data={
                                      'product_number': 'FORMAT-TEST-001',
                                      'supplier_id': 1
                                  })
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response data: {response.get_data(as_text=True)}")
        
        # Parse response
        response_data = json.loads(response.get_data(as_text=True))
        
        # Check response structure
        self.assertIsInstance(response_data, dict)
        self.assertIn('unique', response_data)
        
        # Response should be valid JSON
        self.assertTrue(json.dumps(response_data))
        
        print(f"✅ API TEST PASSED: API response format is consistent")

    def test_api_error_handling(self):
        """Test API error handling and response format"""
        print(f"\n🧪 API TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test API error handling consistency")
        
        # Test with invalid supplier_id (non-numeric)
        response = self.client.post('/api/component/validate-product-number',
                                  data={
                                      'product_number': 'ERROR-TEST-001',
                                      'supplier_id': 'invalid'
                                  })
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response data: {response.get_data(as_text=True)}")
        
        # Should handle error gracefully
        self.assertIn(response.status_code, [200, 400, 422])  # Valid error codes
        
        # Response should be valid JSON even for errors
        try:
            response_data = json.loads(response.get_data(as_text=True))
            self.assertIsInstance(response_data, dict)
        except json.JSONDecodeError:
            self.fail("API should return valid JSON even for errors")
        
        print(f"✅ API TEST PASSED: API error handling works")


if __name__ == '__main__':
    unittest.main()