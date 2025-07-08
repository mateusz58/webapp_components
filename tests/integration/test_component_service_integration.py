import unittest
import json
import pytest
from unittest.mock import Mock, patch

from app import create_app, db
from app.services.component_service import ComponentService
from app.models import Component, ComponentType, Supplier, Color

class TestComponentServiceIntegration(unittest.TestCase):
    """Integration tests for ComponentService with Flask application context"""
    
    @classmethod
    def setUpClass(cls):
        """Set up Flask application context for all tests"""
        print(f"\n🔧 INTEGRATION TEST SETUP: Setting up Flask application...")
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        
        # Create tables
        db.create_all()
        print(f"✅ Flask application context established")

    @classmethod
    def tearDownClass(cls):
        """Clean up Flask application context"""
        print(f"\n🧹 INTEGRATION TEST TEARDOWN: Cleaning up Flask context...")
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()
        print(f"✅ Flask application context cleaned up")

    def setUp(self):
        """Set up test fixtures before each test"""
        print(f"\n🧪 INTEGRATION TEST SETUP: {self._testMethodName}")
        print(f"🔧 Setting up test data for ComponentService integration...")
        
        # Create test data
        self.test_component_type = ComponentType(id=1, name='Test Type')
        self.test_supplier = Supplier(id=1, supplier_code='TEST-SUP', address='Test Address')
        self.test_color = Color(id=1, name='Red')
        
        db.session.add_all([self.test_component_type, self.test_supplier, self.test_color])
        db.session.commit()
        
        print(f"✅ Integration test setup complete for: {self._testMethodName}")

    def tearDown(self):
        """Clean up after each test"""
        print(f"🧹 Cleaning up test data...")
        db.session.rollback()
        # Clean up any test data
        Component.query.delete()
        db.session.commit()

    @patch('app.services.component_service.ComponentService._handle_component_associations')
    @patch('app.services.component_service.ComponentService._handle_picture_order_changes')
    @patch('app.services.component_service.ComponentService._handle_comprehensive_picture_renaming')
    def test_update_component_success_with_context(self, mock_rename, mock_picture_order, mock_associations):
        """Test ComponentService.update_component with proper Flask context"""
        print(f"\n🧪 INTEGRATION TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test component update with Flask application context")
        
        # Create test component
        test_component = Component(
            id=1,
            product_number='TEST-001',
            description='Test component',
            supplier_id=1,
            component_type_id=1
        )
        db.session.add(test_component)
        db.session.commit()
        
        # Mock method returns
        mock_associations.return_value = None
        mock_picture_order.return_value = None
        mock_rename.return_value = {'renamed_files': []}
        
        # Test data
        update_data = {
            'product_number': 'UPDATED-001',
            'description': 'Updated description',
            'supplier_id': 1
        }
        
        print(f"🔍 Testing component update: ID={test_component.id}")
        print(f"🔍 Update data: {json.dumps(update_data, indent=2)}")
        
        # Act
        result = ComponentService.update_component(test_component.id, update_data)
        
        # Assert
        print(f"📊 Update result: {json.dumps(result, indent=2, default=str)}")
        
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        self.assertTrue(result['success'])
        self.assertEqual(result['component_id'], test_component.id)
        
        # Verify database was updated
        updated_component = Component.query.get(test_component.id)
        self.assertEqual(updated_component.product_number, 'UPDATED-001')
        self.assertEqual(updated_component.description, 'Updated description')
        
        print(f"✅ INTEGRATION TEST PASSED: Component update with context works")

    def test_update_component_not_found_with_context(self):
        """Test ComponentService.update_component with non-existent component"""
        print(f"\n🧪 INTEGRATION TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test component update with invalid ID and Flask context")
        
        non_existent_id = 999999
        update_data = {'product_number': 'TEST-001'}
        
        print(f"🔍 Testing with non-existent component ID: {non_existent_id}")
        
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            ComponentService.update_component(non_existent_id, update_data)
        
        error_message = str(context.exception)
        print(f"📊 Expected error raised: {error_message}")
        
        self.assertIn('not found', error_message.lower())
        self.assertIn(str(non_existent_id), error_message)
        
        print(f"✅ INTEGRATION TEST PASSED: Component not found error with context works")

    def test_component_crud_operations(self):
        """Test basic CRUD operations on Component model"""
        print(f"\n🧪 INTEGRATION TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test Component model CRUD operations")
        
        # Create
        component = Component(
            product_number='CRUD-001',
            description='CRUD Test Component',
            supplier_id=1,
            component_type_id=1,
            properties={'test': 'value'}
        )
        db.session.add(component)
        db.session.commit()
        
        component_id = component.id
        print(f"🔍 Created component with ID: {component_id}")
        
        # Read
        retrieved = Component.query.get(component_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.product_number, 'CRUD-001')
        self.assertEqual(retrieved.properties['test'], 'value')
        
        print(f"🔍 Retrieved component: {retrieved.product_number}")
        
        # Update
        retrieved.description = 'Updated CRUD Component'
        retrieved.properties = {'test': 'updated_value', 'new_prop': 'new'}
        db.session.commit()
        
        updated = Component.query.get(component_id)
        self.assertEqual(updated.description, 'Updated CRUD Component')
        self.assertEqual(updated.properties['new_prop'], 'new')
        
        print(f"🔍 Updated component description: {updated.description}")
        
        # Delete
        db.session.delete(updated)
        db.session.commit()
        
        deleted = Component.query.get(component_id)
        self.assertIsNone(deleted)
        
        print(f"🔍 Component deleted successfully")
        print(f"✅ INTEGRATION TEST PASSED: Component CRUD operations work")

    def test_component_relationships(self):
        """Test Component model relationships"""
        print(f"\n🧪 INTEGRATION TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test Component relationships with Supplier and ComponentType")
        
        # Create component with relationships
        component = Component(
            product_number='REL-001',
            description='Relationship Test',
            supplier_id=1,
            component_type_id=1
        )
        db.session.add(component)
        db.session.commit()
        
        print(f"🔍 Created component with relationships")
        
        # Test supplier relationship
        retrieved = Component.query.get(component.id)
        self.assertIsNotNone(retrieved.supplier)
        self.assertEqual(retrieved.supplier.supplier_code, 'TEST-SUP')
        
        print(f"🔍 Supplier relationship: {retrieved.supplier.supplier_code}")
        
        # Test component_type relationship
        self.assertIsNotNone(retrieved.component_type)
        self.assertEqual(retrieved.component_type.name, 'Test Type')
        
        print(f"🔍 ComponentType relationship: {retrieved.component_type.name}")
        
        print(f"✅ INTEGRATION TEST PASSED: Component relationships work")

    @patch('app.services.component_service.ComponentService._check_duplicate_component')
    def test_duplicate_component_check_integration(self, mock_check_duplicate):
        """Test duplicate component checking with database"""
        print(f"\n🧪 INTEGRATION TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test duplicate component detection")
        
        # Create existing component
        existing = Component(
            product_number='DUP-001',
            description='Existing Component',
            supplier_id=1,
            component_type_id=1
        )
        db.session.add(existing)
        db.session.commit()
        
        print(f"🔍 Created existing component: {existing.product_number}")
        
        # Mock duplicate check to simulate finding duplicate
        mock_check_duplicate.return_value = existing
        
        # Try to update another component with same product_number
        another_component = Component(
            product_number='ANOTHER-001',
            description='Another Component',
            supplier_id=1,
            component_type_id=1
        )
        db.session.add(another_component)
        db.session.commit()
        
        update_data = {
            'product_number': 'DUP-001',  # Duplicate product number
            'description': 'Trying to duplicate'
        }
        
        print(f"🔍 Attempting to create duplicate with: {update_data['product_number']}")
        
        # This should raise an error due to duplicate
        with self.assertRaises(ValueError) as context:
            ComponentService.update_component(another_component.id, update_data)
        
        error_message = str(context.exception)
        print(f"📊 Duplicate error raised: {error_message}")
        
        self.assertIn('duplicate', error_message.lower())
        
        print(f"✅ INTEGRATION TEST PASSED: Duplicate detection works")

    def test_component_properties_json_handling(self):
        """Test Component properties JSON field handling"""
        print(f"\n🧪 INTEGRATION TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test JSON properties field operations")
        
        # Test with dict properties
        component = Component(
            product_number='JSON-001',
            description='JSON Test',
            supplier_id=1,
            component_type_id=1,
            properties={'color': 'red', 'material': 'plastic', 'weight': 100}
        )
        db.session.add(component)
        db.session.commit()
        
        print(f"🔍 Created component with dict properties")
        
        # Retrieve and verify JSON handling
        retrieved = Component.query.get(component.id)
        self.assertIsInstance(retrieved.properties, dict)
        self.assertEqual(retrieved.properties['color'], 'red')
        self.assertEqual(retrieved.properties['weight'], 100)
        
        print(f"🔍 Properties retrieved: {retrieved.properties}")
        
        # Update properties
        retrieved.properties['size'] = 'large'
        retrieved.properties['weight'] = 150
        db.session.commit()
        
        updated = Component.query.get(component.id)
        self.assertEqual(updated.properties['size'], 'large')
        self.assertEqual(updated.properties['weight'], 150)
        self.assertEqual(updated.properties['color'], 'red')  # Should persist
        
        print(f"🔍 Updated properties: {updated.properties}")
        print(f"✅ INTEGRATION TEST PASSED: JSON properties handling works")


if __name__ == '__main__':
    unittest.main()