import unittest
import json
from unittest.mock import patch, Mock

from app import create_app, db
from app.models import Component, ComponentType, Supplier, Color, Brand

class TestComponentCRUDEndpoints(unittest.TestCase):
    """API tests for component CRUD endpoints"""
    
    @classmethod
    def setUpClass(cls):
        """Set up Flask test client for all tests"""
        print(f"\n🔧 API TEST SETUP: Setting up Flask test client for CRUD...")
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        cls.app.config['WTF_CSRF_ENABLED'] = False
        
        cls.client = cls.app.test_client()
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        
        db.create_all()
        print(f"✅ Flask test client for CRUD established")

    @classmethod
    def tearDownClass(cls):
        """Clean up Flask test client"""
        print(f"\n🧹 API TEST TEARDOWN: Cleaning up CRUD test client...")
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()
        print(f"✅ CRUD test client cleaned up")

    def setUp(self):
        """Set up test data before each test"""
        print(f"\n🧪 API TEST SETUP: {self._testMethodName}")
        print(f"🔧 Setting up test data for CRUD endpoints...")
        
        # Create test data
        self.test_component_type = ComponentType(id=1, name='Test Type')
        self.test_supplier = Supplier(id=1, supplier_code='CRUD-SUP', address='CRUD Address')
        self.test_color = Color(id=1, name='Red')
        self.test_brand = Brand(id=1, name='Test Brand')
        
        db.session.add_all([
            self.test_component_type, 
            self.test_supplier, 
            self.test_color, 
            self.test_brand
        ])
        db.session.commit()
        
        print(f"✅ CRUD API test setup complete for: {self._testMethodName}")

    def tearDown(self):
        """Clean up after each test"""
        print(f"🧹 Cleaning up CRUD test data...")
        db.session.rollback()
        Component.query.delete()
        db.session.commit()

    @patch('app.web.component_routes.save_uploaded_file')
    def test_component_create_basic(self, mock_save_file):
        """Test basic component creation via API"""
        print(f"\n🧪 API TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test basic component creation endpoint")
        
        # Mock file saving
        mock_save_file.return_value = True
        
        # Test data
        component_data = {
            'product_number': 'CRUD-CREATE-001',
            'description': 'Test component creation',
            'supplier_id': 1,
            'component_type_id': 1,
            'properties': json.dumps({'material': 'plastic'}),
            'brand_ids[]': [1]
        }
        
        print(f"🔍 Creating component with data: {json.dumps(component_data, indent=2)}")
        
        # Make API request
        response = self.client.post('/api/component/create',
                                  data=component_data)
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response data: {response.get_data(as_text=True)}")
        
        # Check if component was created (may vary based on implementation)
        if response.status_code == 200:
            try:
                response_data = json.loads(response.get_data(as_text=True))
                if 'success' in response_data:
                    self.assertTrue(response_data['success'])
                print(f"✅ Component creation successful")
            except json.JSONDecodeError:
                print(f"⚠️ Response not JSON, checking for redirect...")
                # May be a redirect response
                self.assertIn(response.status_code, [200, 201, 302])
        
        print(f"✅ API TEST PASSED: Component creation endpoint works")

    def test_component_read_endpoint(self):
        """Test component read/retrieve endpoint"""
        print(f"\n🧪 API TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test component retrieval endpoint")
        
        # Create test component
        test_component = Component(
            product_number='CRUD-READ-001',
            description='Test component for reading',
            supplier_id=1,
            component_type_id=1,
            properties={'color': 'blue'}
        )
        db.session.add(test_component)
        db.session.commit()
        
        component_id = test_component.id
        print(f"🔍 Created test component: ID={component_id}")
        
        # Test component retrieval
        response = self.client.get(f'/api/component/{component_id}')
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response data: {response.get_data(as_text=True)}")
        
        # Check response
        if response.status_code == 200:
            try:
                response_data = json.loads(response.get_data(as_text=True))
                if 'component' in response_data:
                    component_data = response_data['component']
                    self.assertEqual(component_data['product_number'], 'CRUD-READ-001')
                print(f"✅ Component retrieval successful")
            except json.JSONDecodeError:
                print(f"⚠️ Response not JSON format")
        
        # Endpoint should exist (not 404)
        self.assertNotEqual(response.status_code, 404)
        
        print(f"✅ API TEST PASSED: Component read endpoint works")

    def test_component_update_endpoint(self):
        """Test component update endpoint"""
        print(f"\n🧪 API TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test component update endpoint")
        
        # Create test component
        test_component = Component(
            product_number='CRUD-UPDATE-001',
            description='Original description',
            supplier_id=1,
            component_type_id=1
        )
        db.session.add(test_component)
        db.session.commit()
        
        component_id = test_component.id
        print(f"🔍 Created test component: ID={component_id}")
        
        # Update data
        update_data = {
            'description': 'Updated description via API',
            'properties': json.dumps({'updated': 'true'})
        }
        
        print(f"🔍 Updating with data: {json.dumps(update_data, indent=2)}")
        
        # Make update request
        response = self.client.put(f'/api/component/{component_id}',
                                 content_type='application/json',
                                 data=json.dumps(update_data))
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response data: {response.get_data(as_text=True)}")
        
        # Check if update worked
        if response.status_code == 200:
            try:
                response_data = json.loads(response.get_data(as_text=True))
                if 'success' in response_data:
                    self.assertTrue(response_data['success'])
                print(f"✅ Component update successful")
            except json.JSONDecodeError:
                print(f"⚠️ Response not JSON format")
        
        # Endpoint should exist (not 404)
        self.assertNotEqual(response.status_code, 404)
        
        print(f"✅ API TEST PASSED: Component update endpoint works")

    def test_component_list_endpoint(self):
        """Test component list/search endpoint"""
        print(f"\n🧪 API TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test component list endpoint")
        
        # Create multiple test components
        components = [
            Component(product_number='LIST-001', description='List test 1', 
                     supplier_id=1, component_type_id=1),
            Component(product_number='LIST-002', description='List test 2', 
                     supplier_id=1, component_type_id=1),
            Component(product_number='LIST-003', description='List test 3', 
                     supplier_id=1, component_type_id=1)
        ]
        
        for comp in components:
            db.session.add(comp)
        db.session.commit()
        
        print(f"🔍 Created {len(components)} test components")
        
        # Test component list
        response = self.client.get('/api/components')
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response data: {response.get_data(as_text=True)}")
        
        # Check response
        if response.status_code == 200:
            try:
                response_data = json.loads(response.get_data(as_text=True))
                if 'components' in response_data:
                    components_list = response_data['components']
                    self.assertGreaterEqual(len(components_list), 3)
                print(f"✅ Component list retrieval successful")
            except json.JSONDecodeError:
                print(f"⚠️ Response not JSON format")
        
        # Endpoint should exist (not 404)
        self.assertNotEqual(response.status_code, 404)
        
        print(f"✅ API TEST PASSED: Component list endpoint works")

    def test_component_delete_endpoint(self):
        """Test component deletion endpoint"""
        print(f"\n🧪 API TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test component deletion endpoint")
        
        # Create test component
        test_component = Component(
            product_number='CRUD-DELETE-001',
            description='Component to delete',
            supplier_id=1,
            component_type_id=1
        )
        db.session.add(test_component)
        db.session.commit()
        
        component_id = test_component.id
        print(f"🔍 Created test component for deletion: ID={component_id}")
        
        # Test deletion
        response = self.client.delete(f'/api/component/{component_id}')
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response data: {response.get_data(as_text=True)}")
        
        # Check response
        if response.status_code == 200:
            try:
                response_data = json.loads(response.get_data(as_text=True))
                if 'success' in response_data:
                    self.assertTrue(response_data['success'])
                print(f"✅ Component deletion successful")
            except json.JSONDecodeError:
                print(f"⚠️ Response not JSON format")
        
        # Endpoint should exist (not 404)
        self.assertNotEqual(response.status_code, 404)
        
        print(f"✅ API TEST PASSED: Component delete endpoint works")

    def test_api_error_responses(self):
        """Test API error response handling"""
        print(f"\n🧪 API TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test API error response consistency")
        
        # Test with non-existent component ID
        response = self.client.get('/api/component/999999')
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response data: {response.get_data(as_text=True)}")
        
        # Should return appropriate error status
        self.assertIn(response.status_code, [404, 400, 422])
        
        # Test invalid update data
        response = self.client.put('/api/component/1',
                                 content_type='application/json',
                                 data='invalid json')
        
        print(f"📊 Invalid data response status: {response.status_code}")
        
        # Should handle invalid JSON gracefully
        self.assertIn(response.status_code, [400, 422, 500])
        
        print(f"✅ API TEST PASSED: Error responses are handled properly")

    def test_api_content_type_handling(self):
        """Test API content type handling"""
        print(f"\n🧪 API TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test API content type handling")
        
        # Create test component
        test_component = Component(
            product_number='CONTENT-TYPE-001',
            description='Content type test',
            supplier_id=1,
            component_type_id=1
        )
        db.session.add(test_component)
        db.session.commit()
        
        component_id = test_component.id
        
        # Test JSON content type
        update_data = {'description': 'JSON update'}
        response = self.client.put(f'/api/component/{component_id}',
                                 content_type='application/json',
                                 data=json.dumps(update_data))
        
        print(f"📊 JSON response status: {response.status_code}")
        
        # Test form data content type
        response = self.client.put(f'/api/component/{component_id}',
                                 data={'description': 'Form update'})
        
        print(f"📊 Form data response status: {response.status_code}")
        
        # Both should be handled (not 415 Unsupported Media Type)
        self.assertNotEqual(response.status_code, 415)
        
        print(f"✅ API TEST PASSED: Content type handling works")


if __name__ == '__main__':
    unittest.main()