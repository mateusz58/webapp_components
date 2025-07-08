#!/usr/bin/env python3
"""
Comprehensive Unit Tests for ComponentService
Testing all methods with mocked dependencies for fast execution
"""
import unittest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add app directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.services.component_service import ComponentService
from app.models import Component, ComponentType, Supplier, Color, ComponentVariant, Picture


class ComponentServiceUnitTests(unittest.TestCase):
    """Unit tests for ComponentService with mocked dependencies"""

    def setUp(self):
        """Set up test fixtures with debug logging"""
        print(f"\n🧪 UNIT TEST SETUP: {self._testMethodName}")
        print(f"🔧 Setting up mocked dependencies for ComponentService...")
        
        # Create simple mock objects without SQLAlchemy specs to avoid context issues
        self.mock_component = Mock()
        self.mock_component.id = 1
        self.mock_component.product_number = 'TEST-001'
        self.mock_component.description = 'Test component'
        self.mock_component.component_type_id = 1
        self.mock_component.supplier_id = 1
        self.mock_component.properties = {}
        
        print(f"✅ Unit test setup complete for: {self._testMethodName}")

    def test_update_basic_fields_product_number_change(self):
        """Test _update_basic_fields with product number change"""
        print(f"\n🧪 UNIT TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test basic field updates with product number change")
        
        # Arrange
        component = Mock()
        component.product_number = 'OLD-001'
        component.description = 'Old description'
        component.component_type_id = 1
        component.supplier_id = 1
        component.properties = {}
        
        data = {
            'product_number': 'NEW-001',
            'description': 'New description',
            'component_type_id': 2,
            'supplier_id': 2,
            'properties': {'test': 'value'}
        }
        
        print(f"🔍 Input component: {component.product_number}")
        print(f"🔍 Update data: {json.dumps(data, indent=2)}")
        
        # Act
        changes = ComponentService._update_basic_fields(component, data)
        
        # Assert
        print(f"📊 Changes detected: {json.dumps(changes, indent=2, default=str)}")
        
        self.assertIn('product_number', changes)
        self.assertEqual(changes['product_number']['old'], 'OLD-001')
        self.assertEqual(changes['product_number']['new'], 'NEW-001')
        
        self.assertIn('description', changes)
        self.assertEqual(changes['description']['old'], 'Old description')
        self.assertEqual(changes['description']['new'], 'New description')
        
        self.assertIn('component_type_id', changes)
        self.assertEqual(changes['component_type_id']['old'], 1)
        self.assertEqual(changes['component_type_id']['new'], 2)
        
        self.assertIn('supplier_id', changes)
        self.assertEqual(changes['supplier_id']['old'], 1)
        self.assertEqual(changes['supplier_id']['new'], 2)
        
        self.assertIn('properties', changes)
        self.assertEqual(changes['properties']['old'], {})
        self.assertEqual(changes['properties']['new'], {'test': 'value'})
        
        # Verify component was updated
        self.assertEqual(component.product_number, 'NEW-001')
        self.assertEqual(component.description, 'New description')
        self.assertEqual(component.component_type_id, 2)
        self.assertEqual(component.supplier_id, 2)
        self.assertEqual(component.properties, {'test': 'value'})
        
        print(f"✅ UNIT TEST PASSED: Basic fields updated correctly")

    def test_update_basic_fields_no_changes(self):
        """Test _update_basic_fields when no changes are made"""
        print(f"\n🧪 UNIT TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test basic field updates with no actual changes")
        
        # Arrange
        component = Mock()
        component.product_number = 'SAME-001'
        component.description = 'Same description'
        component.component_type_id = 1
        component.supplier_id = 1
        component.properties = {'existing': 'property'}
        
        # Same data as current component
        data = {
            'product_number': 'SAME-001',
            'description': 'Same description',
            'component_type_id': 1,
            'supplier_id': 1,
            'properties': {'existing': 'property'}
        }
        
        print(f"🔍 Component unchanged test")
        print(f"🔍 Data: {json.dumps(data, indent=2)}")
        
        # Act
        changes = ComponentService._update_basic_fields(component, data)
        
        # Assert
        print(f"📊 Changes detected: {changes}")
        self.assertEqual(changes, {}, "No changes should be detected when data is identical")
        
        print(f"✅ UNIT TEST PASSED: No changes detected correctly")

    def test_update_basic_fields_properties_json_string(self):
        """Test _update_basic_fields with properties as JSON string"""
        print(f"\n🧪 UNIT TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test properties handling when sent as JSON string")
        
        # Arrange
        component = Mock()
        component.product_number = 'TEST-001'
        component.description = 'Test'
        component.component_type_id = 1
        component.supplier_id = 1
        component.properties = {}
        
        # Properties as JSON string (as might come from frontend)
        data = {
            'properties': '{"test_property": "test_value", "another": "value"}'
        }
        
        print(f"🔍 Properties as JSON string: {data['properties']}")
        print(f"🔍 Type: {type(data['properties'])}")
        
        # Act
        changes = ComponentService._update_basic_fields(component, data)
        
        # Assert
        print(f"📊 Changes: {json.dumps(changes, indent=2, default=str)}")
        
        self.assertIn('properties', changes)
        self.assertEqual(changes['properties']['old'], {})
        self.assertEqual(changes['properties']['new'], {"test_property": "test_value", "another": "value"})
        
        # Verify component properties were updated correctly
        expected_properties = {"test_property": "test_value", "another": "value"}
        self.assertEqual(component.properties, expected_properties)
        
        print(f"✅ UNIT TEST PASSED: JSON string properties parsed correctly")

    def test_check_duplicate_component_with_supplier(self):
        """Test _check_duplicate_component with supplier"""
        print(f"\n🧪 UNIT TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test duplicate component checking with supplier")
        
        # Mock database query
        with patch('app.services.component_service.Component') as MockComponent:
            mock_query = Mock()
            mock_filter_by = Mock()
            mock_query.filter_by.return_value = mock_filter_by
            mock_filter_by.filter_by.return_value = mock_filter_by
            mock_filter_by.first.return_value = Mock()  # Found duplicate
            
            MockComponent.query = mock_query
            
            print(f"🔍 Testing duplicate check: product='TEST-001', supplier=1")
            
            # Act
            result = ComponentService._check_duplicate_component('TEST-001', 1)
            
            # Assert
            print(f"📊 Duplicate found: {result is not None}")
            self.assertIsNotNone(result, "Should find duplicate component")
            
            # Verify query calls
            mock_query.filter_by.assert_called_with(product_number='TEST-001')
            mock_filter_by.filter_by.assert_called_with(supplier_id=1)
            mock_filter_by.first.assert_called_once()
            
            print(f"✅ UNIT TEST PASSED: Duplicate detection works with supplier")

    def test_check_duplicate_component_without_supplier(self):
        """Test _check_duplicate_component without supplier"""
        print(f"\n🧪 UNIT TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test duplicate component checking without supplier")
        
        # Mock database query
        with patch('app.services.component_service.Component') as MockComponent:
            mock_query = Mock()
            mock_filter_by = Mock()
            mock_filter = Mock()
            
            mock_query.filter_by.return_value = mock_filter_by
            mock_filter_by.filter.return_value = mock_filter
            mock_filter.first.return_value = None  # No duplicate found
            
            MockComponent.query = mock_query
            MockComponent.supplier_id.is_.return_value = 'supplier_is_null_condition'
            
            print(f"🔍 Testing duplicate check: product='TEST-002', supplier=None")
            
            # Act
            result = ComponentService._check_duplicate_component('TEST-002', None)
            
            # Assert
            print(f"📊 Duplicate found: {result is not None}")
            self.assertIsNone(result, "Should not find duplicate component")
            
            # Verify query calls
            mock_query.filter_by.assert_called_with(product_number='TEST-002')
            MockComponent.supplier_id.is_.assert_called_with(None)
            mock_filter_by.filter.assert_called_with('supplier_is_null_condition')
            mock_filter.first.assert_called_once()
            
            print(f"✅ UNIT TEST PASSED: No duplicate found without supplier")

    def test_check_duplicate_component_with_exclude_id(self):
        """Test _check_duplicate_component with exclude_id for updates"""
        print(f"\n🧪 UNIT TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test duplicate checking excluding current component ID")
        
        # Mock database query
        with patch('app.services.component_service.Component') as MockComponent:
            mock_query = Mock()
            mock_filter_by = Mock()
            mock_filter = Mock()
            
            mock_query.filter_by.return_value = mock_filter_by
            mock_filter_by.filter_by.return_value = mock_filter
            mock_filter.filter.return_value = mock_filter
            mock_filter.first.return_value = None  # No duplicate (excluding self)
            
            MockComponent.query = mock_query
            MockComponent.id = Mock()
            MockComponent.id.__ne__ = Mock(return_value='id_not_equal_condition')
            
            print(f"🔍 Testing duplicate check: product='TEST-001', supplier=1, exclude_id=5")
            
            # Act
            result = ComponentService._check_duplicate_component('TEST-001', 1, exclude_id=5)
            
            # Assert
            print(f"📊 Duplicate found (excluding self): {result is not None}")
            self.assertIsNone(result, "Should not find duplicate when excluding self")
            
            # Verify exclude condition was applied
            MockComponent.id.__ne__.assert_called_with(5)
            
            print(f"✅ UNIT TEST PASSED: Exclude ID functionality works")

    def test_update_component_method_structure(self):
        """Test update_component method structure and interface"""
        print(f"\n🧪 UNIT TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test update_component method exists with proper interface")
        
        # Test method exists
        self.assertTrue(hasattr(ComponentService, 'update_component'))
        self.assertTrue(callable(getattr(ComponentService, 'update_component')))
        
        # Test it's a static method (doesn't require instance)
        import inspect
        self.assertTrue(inspect.isfunction(ComponentService.update_component))
        
        print(f"✅ UNIT TEST PASSED: ComponentService.update_component has proper structure")

    def test_component_service_helper_methods_exist(self):
        """Test that ComponentService has required helper methods"""
        print(f"\n🧪 UNIT TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Verify ComponentService helper methods exist")
        
        required_methods = [
            '_update_basic_fields',
            '_check_duplicate_component',
            '_handle_component_associations',
            '_handle_picture_order_changes',
            '_handle_comprehensive_picture_renaming'
        ]
        
        for method_name in required_methods:
            self.assertTrue(hasattr(ComponentService, method_name), 
                          f"Method {method_name} should exist")
            self.assertTrue(callable(getattr(ComponentService, method_name)),
                          f"Method {method_name} should be callable")
            print(f"🔍 Verified method: {method_name}")
        
        print(f"✅ UNIT TEST PASSED: All ComponentService helper methods exist")

    def test_build_component_data_complete(self):
        """Test _build_component_data with complete component data"""
        print(f"\n🧪 UNIT TEST: {self._testMethodName}")
        print(f"🎯 Purpose: Test component data building for API responses")
        
        # Arrange - Create mock component with all relationships
        mock_component = Mock()
        mock_component.id = 1
        mock_component.product_number = 'TEST-001'
        mock_component.description = 'Test component'
        mock_component.properties = {'test_prop': 'test_value'}
        mock_component.created_at = Mock()
        mock_component.created_at.isoformat.return_value = '2025-01-01T00:00:00'
        mock_component.updated_at = Mock()
        mock_component.updated_at.isoformat.return_value = '2025-01-02T00:00:00'
        
        # Mock status fields
        mock_component.proto_status = 'ok'
        mock_component.proto_comment = 'Proto approved'
        mock_component.proto_date = Mock()
        mock_component.proto_date.isoformat.return_value = '2025-01-01T10:00:00'
        mock_component.sms_status = 'pending'
        mock_component.sms_comment = None
        mock_component.sms_date = None
        mock_component.pps_status = 'pending'
        mock_component.pps_comment = None
        mock_component.pps_date = None
        
        # Mock relationships
        mock_component_type = Mock()
        mock_component_type.id = 1
        mock_component_type.name = 'Test Type'
        mock_component.component_type = mock_component_type
        
        mock_supplier = Mock()
        mock_supplier.id = 1
        mock_supplier.supplier_code = 'SUP001'
        mock_component.supplier = mock_supplier
        
        # Mock brand associations
        mock_brand_assoc = Mock()
        mock_brand_assoc.brand = Mock()
        mock_brand_assoc.brand.id = 1
        mock_brand_assoc.brand.name = 'Test Brand'
        mock_component.brand_associations = [mock_brand_assoc]
        
        # Mock categories and keywords
        mock_category = Mock()
        mock_category.id = 1
        mock_category.name = 'Test Category'
        mock_component.categories = [mock_category]
        
        mock_keyword = Mock()
        mock_keyword.id = 1
        mock_keyword.name = 'test'
        mock_component.keywords = [mock_keyword]
        
        # Mock variants
        mock_component.variants = []
        
        print(f"🔍 Building component data for component: {mock_component.product_number}")
        
        # Act
        with patch.object(ComponentService, '_build_variants_data', return_value=[]) as mock_build_variants:
            result = ComponentService._build_component_data(mock_component)
        
        # Assert
        print(f"📊 Built component data: {json.dumps(result, indent=2, default=str)}")
        
        self.assertEqual(result['id'], 1)
        self.assertEqual(result['product_number'], 'TEST-001')
        self.assertEqual(result['description'], 'Test component')
        self.assertEqual(result['properties'], {'test_prop': 'test_value'})
        
        # Check component type
        self.assertIsNotNone(result['component_type'])
        self.assertEqual(result['component_type']['id'], 1)
        self.assertEqual(result['component_type']['name'], 'Test Type')
        
        # Check supplier
        self.assertIsNotNone(result['supplier'])
        self.assertEqual(result['supplier']['id'], 1)
        self.assertEqual(result['supplier']['supplier_code'], 'SUP001')
        
        # Check status fields
        self.assertEqual(result['proto_status'], 'ok')
        self.assertEqual(result['proto_comment'], 'Proto approved')
        self.assertEqual(result['proto_date'], '2025-01-01T10:00:00')
        self.assertEqual(result['sms_status'], 'pending')
        self.assertIsNone(result['sms_comment'])
        self.assertIsNone(result['sms_date'])
        
        # Check relationships
        self.assertEqual(len(result['brands']), 1)
        self.assertEqual(result['brands'][0]['name'], 'Test Brand')
        
        self.assertEqual(len(result['categories']), 1)
        self.assertEqual(result['categories'][0]['name'], 'Test Category')
        
        self.assertEqual(len(result['keywords']), 1)
        self.assertEqual(result['keywords'][0]['name'], 'test')
        
        mock_build_variants.assert_called_once_with([])
        
        print(f"✅ UNIT TEST PASSED: Component data built correctly")


if __name__ == '__main__':
    print("🚀 Running ComponentService Unit Tests")
    print("=" * 70)
    print("🎯 Testing ComponentService methods with mocked dependencies")
    print("=" * 70)
    
    unittest.main(verbosity=2)